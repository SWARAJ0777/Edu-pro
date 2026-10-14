"""
EduPro | Statistical Inference Engine
===============================================================================
Answers the four analytical objectives with scipy.stats (numpy only for linear
algebra). Design rules:

  * Teacher grain (n=60) is the primary inferential unit; pair grain (n=887) is
    used as a robustness check. Transaction grain is never correlated, because
    10,000 rows nested in 60 teachers would fake statistical power.
  * Every correlation reports Pearson r AND Spearman rho (ratings are bounded
    and mildly skewed), with a Fisher-z 95% CI.
  * All p-values in the hypothesis family are Holm-adjusted, so "significant"
    survives multiple testing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from etl_pipeline import EduProData, build_all

ALPHA = 0.05


# --------------------------------------------------------------------------- #
# Primitives
# --------------------------------------------------------------------------- #
def correlate(x, y, label: str, grain: str) -> dict:
    """Pearson + Spearman with Fisher-z confidence interval."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    r, p = stats.pearsonr(x, y)
    rho, p_rho = stats.spearmanr(x, y)
    se = 1 / np.sqrt(n - 3)
    lo, hi = np.tanh(np.arctanh(r) + np.array([-1, 1]) * stats.norm.ppf(0.975) * se)
    return dict(test=label, grain=grain, n=n, r=r, ci_low=lo, ci_high=hi, p=p, spearman_rho=rho, spearman_p=p_rho)


def partial_correlate(df: pd.DataFrame, x: str, y: str, controls: list[str], label: str, grain: str) -> dict:
    """Partial correlation of x,y after residualising both on categorical controls."""
    Z = pd.get_dummies(df[controls], drop_first=True).astype(float)
    Z.insert(0, "const", 1.0)
    Z = Z.to_numpy()
    resid = lambda v: v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
    rx, ry = resid(df[x].to_numpy(float)), resid(df[y].to_numpy(float))
    n, k = len(df), Z.shape[1] - 1
    r = np.corrcoef(rx, ry)[0, 1]
    t = r * np.sqrt((n - 2 - k) / (1 - r**2))
    p = 2 * stats.t.sf(abs(t), n - 2 - k)
    return dict(test=label, grain=grain, n=n, r=r, ci_low=np.nan, ci_high=np.nan, p=p,
                spearman_rho=np.nan, spearman_p=np.nan)


def holm(pvals: pd.Series) -> pd.Series:
    """Holm-Bonferroni step-down adjusted p-values."""
    order = pvals.sort_values().index
    m = len(pvals)
    adj, running = {}, 0.0
    for i, idx in enumerate(order):
        running = max(running, (m - i) * pvals[idx])
        adj[idx] = min(1.0, running)
    return pd.Series(adj).reindex(pvals.index)


def gini(values) -> float:
    v = np.sort(np.asarray(values, float))
    n = len(v)
    return float((2 * np.arange(1, n + 1) - n - 1) @ v / (n * v.sum()))


def eta_squared_kw(groups: list[np.ndarray]) -> float:
    """Epsilon-squared effect size for Kruskal-Wallis."""
    h = stats.kruskal(*groups).statistic
    n = sum(len(g) for g in groups)
    return float(max(0.0, (h - len(groups) + 1) / (n - len(groups))))


# --------------------------------------------------------------------------- #
# Objective 1: distribution & experience
# --------------------------------------------------------------------------- #
def distribution_profile(d: EduProData) -> pd.DataFrame:
    rows = []
    series = {
        "TeacherRating": d.kpis["TeacherRating"],
        "CourseRating": d.courses["CourseRating"],
        "Enrollments per teacher": d.kpis["Enrollments"],
    }
    for name, s in series.items():
        sh = stats.shapiro(s)
        rows.append(dict(metric=name, n=len(s), mean=s.mean(), median=s.median(), sd=s.std(),
                         iqr=s.quantile(.75) - s.quantile(.25), skew=stats.skew(s),
                         kurtosis=stats.kurtosis(s), shapiro_p=sh.pvalue, gini=gini(s)))
    return pd.DataFrame(rows)


def experience_curve(d: EduProData) -> tuple[pd.DataFrame, dict]:
    """
    Compares linear / log / quadratic / segmented ('hinge') fits of TeacherRating on
    tenure to locate diminishing returns. AIC (lower = better) is used for model
    comparison; the hinge breakpoint is chosen by minimum SSE over 2..15 years.
    """
    x = d.kpis["YearsOfExperience"].to_numpy(float)
    y = d.kpis["TeacherRating"].to_numpy(float)
    n = len(x)

    def fit(X):
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(((y - X @ beta) ** 2).sum())
        k = X.shape[1]
        return beta, sse, n * np.log(sse / n) + 2 * (k + 1)

    one = np.ones(n)
    models = {
        "Linear": np.column_stack([one, x]),
        "Log (diminishing)": np.column_stack([one, np.log1p(x)]),
        "Quadratic": np.column_stack([one, x, x**2]),
    }
    best_b, best = None, (None, np.inf, None)
    for b in range(2, 16):
        res = fit(np.column_stack([one, x, np.maximum(x - b, 0)]))
        if res[1] < best[1]:
            best_b, best = b, res
    models[f"Hinge @ {best_b} yrs"] = np.column_stack([one, x, np.maximum(x - best_b, 0)])

    rows = []
    for name, X in models.items():
        beta, sse, aic = fit(X)
        rows.append(dict(model=name, r2=1 - sse / ((y - y.mean()) ** 2).sum(), aic=aic))
    comp = pd.DataFrame(rows).sort_values("aic").reset_index(drop=True)
    comp["delta_aic"] = comp["aic"] - comp["aic"].min()

    beta = best[0]
    info = dict(breakpoint_years=best_b, slope_before=beta[1], slope_after=beta[1] + beta[2])
    return comp, info


def experience_bands(d: EduProData) -> pd.DataFrame:
    k = d.kpis
    return (k.groupby("ExperienceBand", observed=True)
              .agg(instructors=("TeacherID", "count"), teacher_rating=("TeacherRating", "mean"),
                   course_rating=("MeanCourseRating", "mean"), rci=("RCI", "mean"), eis=("EIS", "mean"))
              .reset_index())


# --------------------------------------------------------------------------- #
# Full hypothesis battery
# --------------------------------------------------------------------------- #
def correlation_battery(d: EduProData) -> pd.DataFrame:
    k, p = d.kpis, d.pairs
    rows = [
        # Experience paradox
        correlate(k.YearsOfExperience, k.TeacherRating, "Experience vs TeacherRating", "teacher"),
        correlate(k.YearsOfExperience, k.MeanCourseRating, "Experience vs CourseRating (mean of courses)", "teacher"),
        correlate(k.YearsOfExperience, k.WeightedCourseRating, "Experience vs CourseRating (enrollment-weighted)", "teacher"),
        correlate(p.YearsOfExperience, p.CourseRating, "Experience vs CourseRating", "pair"),
        # Halo effect
        correlate(k.TeacherRating, k.MeanCourseRating, "TeacherRating vs CourseRating (mean of courses)", "teacher"),
        correlate(k.TeacherRating, k.WeightedCourseRating, "TeacherRating vs CourseRating (enrollment-weighted)", "teacher"),
        correlate(p.TeacherRating, p.CourseRating, "TeacherRating vs CourseRating", "pair"),
        partial_correlate(p, "TeacherRating", "CourseRating", ["CourseCategory", "CourseLevel"],
                          "TeacherRating vs CourseRating | category + level", "pair"),
        # Demand
        correlate(k.TeacherRating, k.Enrollments, "TeacherRating vs Enrollments", "teacher"),
        correlate(k.TeacherRating, np.log(k.Enrollments), "TeacherRating vs log(Enrollments)", "teacher"),
        correlate(k.TeacherRating, k.EIR, "TeacherRating vs EIR", "teacher"),
    ]
    # Robustness: drop the two mega-enrollment instructors
    core = k[k.Enrollments < k.Enrollments.nlargest(2).min()]
    rows.append(correlate(core.TeacherRating, core.Enrollments,
                          "TeacherRating vs Enrollments (excl. top-2 instructors)", "teacher"))
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(out["p"])
    out["significant"] = out["p_holm"] < ALPHA
    return out


def group_tests(d: EduProData) -> pd.DataFrame:
    """Omnibus tests: does the rating differ across groups?"""
    k, c, p = d.kpis, d.courses, d.pairs
    rows = []

    def omni(label, df, col, val):
        groups = [g[val].to_numpy() for _, g in df.groupby(col, observed=True) if len(g) > 1]
        f = stats.f_oneway(*groups)
        kw = stats.kruskal(*groups)
        rows.append(dict(test=label, groups=len(groups), anova_F=f.statistic, anova_p=f.pvalue,
                         kruskal_H=kw.statistic, kruskal_p=kw.pvalue, effect_eps2=eta_squared_kw(groups)))

    omni("CourseRating by CourseCategory", c, "CourseCategory", "CourseRating")
    omni("CourseRating by CourseLevel", c, "CourseLevel", "CourseRating")
    omni("TeacherRating by Expertise", k, "Expertise", "TeacherRating")
    omni("Mean CourseRating by instructor Expertise", k, "Expertise", "MeanCourseRating")
    omni("Enrollments by RatingTier", k, "RatingTier", "Enrollments")
    omni("Mean CourseRating by RatingTier", k, "RatingTier", "MeanCourseRating")
    omni("Enrollments by RatingTier (excl. top-2)", k[k.Enrollments < k.Enrollments.nlargest(2).min()],
         "RatingTier", "Enrollments")

    # Two-sample comparisons
    m, f = k[k.Gender == "Male"].TeacherRating, k[k.Gender == "Female"].TeacherRating
    t = stats.ttest_ind(f, m, equal_var=False)
    u = stats.mannwhitneyu(f, m)
    rows.append(dict(test="TeacherRating: Female vs Male", groups=2, anova_F=t.statistic, anova_p=t.pvalue,
                     kruskal_H=u.statistic, kruskal_p=u.pvalue, effect_eps2=np.nan))
    al, nal = p[p.DomainAligned].CourseRating, p[~p.DomainAligned].CourseRating
    t = stats.ttest_ind(al, nal, equal_var=False)
    u = stats.mannwhitneyu(al, nal)
    rows.append(dict(test="CourseRating: domain-aligned vs cross-domain delivery", groups=2, anova_F=t.statistic,
                     anova_p=t.pvalue, kruskal_H=u.statistic, kruskal_p=u.pvalue, effect_eps2=np.nan))
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(out["anova_p"])
    return out


def tier_summary(d: EduProData) -> pd.DataFrame:
    k = d.kpis
    s = (k.groupby("RatingTier", observed=True)
           .agg(instructors=("TeacherID", "count"), mean_teacher_rating=("TeacherRating", "mean"),
                total_enrollments=("Enrollments", "sum"), mean_enrollments=("Enrollments", "mean"),
                median_enrollments=("Enrollments", "median"), mean_course_rating=("MeanCourseRating", "mean"),
                mean_eir=("EIR", "mean"), median_eir=("EIR", "median"))
           .reset_index())
    s["enrollment_share"] = s["total_enrollments"] / s["total_enrollments"].sum()
    return s


def domain_profile(d: EduProData) -> pd.DataFrame:
    """
    Per course category: where is quality low / volatile, and who delivers it?

    NOTE - why there is no within-category TeacherRating~CourseRating correlation:
    CourseRating is one scalar per course, so inside a category it cannot vary with
    the instructor. In categories where every instructor delivers every course
    (`fully_crossed`) the correlation is exactly 0 by construction. The halo test is
    therefore run across categories (see correlation_battery), and this table
    reports exposure and volatility instead.
    """
    rows = []
    for cat, g in d.pairs.groupby("CourseCategory"):
        crs = d.courses.loc[d.courses.CourseCategory == cat, "CourseRating"]
        teachers = g.drop_duplicates("TeacherID")
        rows.append(dict(
            category=cat, courses=g.CourseID.nunique(), instructors=g.TeacherID.nunique(),
            mean_course_rating=crs.mean(), course_rating_sd=crs.std(),
            course_rating_range=crs.max() - crs.min(),
            mean_instructor_rating=teachers.TeacherRating.mean(),
            aligned_instructor_share=teachers.DomainAligned.mean(),
            enrollment=int(g.Enrollments.sum()),
            fully_crossed=len(g) == g.TeacherID.nunique() * g.CourseID.nunique()))
    return pd.DataFrame(rows).sort_values("mean_course_rating").reset_index(drop=True)


def demand_concentration(d: EduProData) -> dict:
    """How concentrated is demand, and is it earned inside the instructor's own domain?"""
    k, p = d.kpis, d.pairs
    top = k.nlargest(2, "Enrollments")
    top_ids = top.TeacherID
    aligned = lambda x: float((x.Enrollments * x.DomainAligned).sum() / x.Enrollments.sum())
    return dict(
        gini_enrollments=gini(k.Enrollments),
        top2_share=float(top.Enrollments.sum() / k.Enrollments.sum()),
        top2_names=top.TeacherName.tolist(),
        top2_ratings=top.TeacherRating.tolist(),
        top2_courses_covered=int(p[p.TeacherID.isin(top_ids)].CourseID.nunique()),
        top2_domain_aligned_share=aligned(p[p.TeacherID.isin(top_ids)]),
        rest_domain_aligned_share=aligned(p[~p.TeacherID.isin(top_ids)]),
        top2_enrollments_per_delivery=float(p[p.TeacherID.isin(top_ids)].Enrollments.mean()),
        rest_enrollments_per_delivery=float(p[~p.TeacherID.isin(top_ids)].Enrollments.mean()),
        rest_enrollments_per_delivery_median=float(p[~p.TeacherID.isin(top_ids)].Enrollments.median()),
        aggregate_eir=float(k.Enrollments.sum() / k.ExpectedEnrollments.sum()),
    )


def gender_level_table(d: EduProData) -> pd.DataFrame:
    return d.pairs.pivot_table(index="Gender", columns="CourseLevel", values="CourseRating", aggfunc="mean").round(3)


# --------------------------------------------------------------------------- #
def run_all(d: EduProData | None = None) -> dict[str, pd.DataFrame]:
    d = d or build_all()
    curve, bp = experience_curve(d)
    return dict(distribution=distribution_profile(d), correlations=correlation_battery(d),
                group_tests=group_tests(d), experience_curve=curve, experience_bands=experience_bands(d),
                tiers=tier_summary(d), domain_profile=domain_profile(d),
                gender_level=gender_level_table(d), breakpoint=pd.DataFrame([bp]))


if __name__ == "__main__":
    pd.set_option("display.width", 220, "display.max_columns", 30, "display.float_format", "{:.4g}".format)
    for name, df in run_all().items():
        print(f"\n=== {name.upper()} ===")
        print(df.to_string(index=name in {"gender_level"}))
    print("\n=== DEMAND CONCENTRATION ===")
    for k_, v_ in demand_concentration(build_all()).items():
        print(f"  {k_:<36} {v_}")
