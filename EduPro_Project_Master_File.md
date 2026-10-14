# EduPro — Instructor & Course Quality Evaluation Framework
### Project Master File · Executive Summary, Research Paper, Analytics Code and Dashboard

**Prepared for:** Government stakeholders and EduPro leadership
**Dataset:** `EduPro_Online_Platform.xlsx` — 60 instructors, 60 courses, 10,000 enrollment transactions
**Version:** 1.0 · 11 October 2026

---

## Contents
1. Executive Summary
2. Research Paper (data, method, findings)
3. Strategic Recommendations
4. Module A — ETL & KPI Engineering (`etl_pipeline.py`)
5. Module B — Statistical Inference Engine (`stats_engine.py`)
6. Module C — Executive Dashboard (`app.py`)
7. Deployment & Reproducibility
8. Appendix — Full statistical output

---

# 1. Executive Summary

EduPro evaluates instructors subjectively. This framework replaces that with three deterministic KPIs and a tested set of statistical questions. The headline result is that **the assumptions most platforms use to judge instructors do not hold on EduPro's data.**

| # | Finding | Evidence |
|---|---|---|
| 1 | **Experience improves instructor ratings, but only up to about 8 years.** | r = +0.60 (95% CI 0.41–0.74, p < 0.001, survives multiple-testing correction). Gain is ~0.21 rating points per year up to year 8, then ~0.05. |
| 2 | **Experience does not improve the ratings of the courses instructors teach** (the *Experience Paradox*). | r = −0.14 (p = 0.29) across instructors; −0.01 (p = 0.70) across 887 deliveries. |
| 3 | **There is no positive Instructor Halo.** A highly rated instructor does not lift course ratings. | Delivery-level r = −0.03 (p = 0.32); r ≈ 0.00 after controlling for category and level (p = 0.99). A weak negative link at instructor level (r = −0.30) is an assignment pattern, not an effect (see §2.5). |
| 4 | **Demand is concentrated in two instructors, not driven by ratings.** | Two instructors hold **60.9%** of 10,000 enrollments. Rating vs enrollment: Spearman ρ = −0.01 (p = 0.93). The 3rd and 4th busiest instructors are rated 1.86 and 1.06. |
| 5 | **Category and level explain almost none of the variation in course ratings.** | ANOVA by category p = 0.97; by level p = 0.37. Quality varies *within* categories (ratings from 1.13 to 4.94), not between them. |

**What this means:** course quality is a property of the course and has to be managed at the course level. Instructor ratings are a valid measure of instructors but are a poor predictor of course outcomes or of demand.

**Three recommendations** (detail in §3): (1) build instructor development around the 0–8-year window and stop treating tenure after year 8 as a quality signal; (2) govern course quality directly with a course-level quality gate, starting with the 13 courses rated below 2.0; (3) remove the key-person risk created by two instructors who carry 61% of demand, mostly outside their declared expertise.

---

# 2. Research Paper

## 2.1 Background and objective
In online education, instructor quality and course design drive learner satisfaction, repeat enrollment and platform credibility. EduPro lacked a structured way to answer four questions: which instructors deliver consistently, whether experience translates into better courses, whether some categories depend more on the instructor, and how evenly teaching quality is distributed.

## 2.2 Data and integrity checks
Three sheets are used: **Teachers** (60 rows), **Courses** (60) and **Transactions** (10,000). All primary keys are unique, there are no orphan foreign keys, no missing values, and every instructor and course appears in at least one transaction. Ratings lie within 1–5.

**The structure of the data matters more than its size.** Teachers and courses are *many-to-many*: each course is delivered by 7–30 instructors (median 14) and each instructor delivers 7–55 courses (median 15), giving **887 distinct teacher–course deliveries**. Because `CourseRating` is a single number per course, it cannot differ between two instructors teaching the same course. Consequences:

- Analysis runs at explicit grains: **instructor** (n = 60, primary), **delivery** (n = 887, robustness) and **transaction** (used only to count enrollments). Correlating 10,000 transactions nested in 60 instructors would manufacture statistical power that does not exist.
- The halo test compares instructors *across* courses. It can show whether a relationship exists but cannot prove what causes it (see §2.8).
- Minor data notes: 64% of transactions have zero amount (free courses), and two course names appear twice (*Deep Learning*, *Natural Language Processing*) under different IDs.

## 2.3 Method
- **KPIs:** RCI, EIS and EIR (definitions in §4 and below).
- **Tests:** Pearson r with Fisher-z confidence intervals, Spearman ρ as a rank-based check, ANOVA and Kruskal–Wallis for group differences, Welch t / Mann–Whitney for two groups, segmented regression for diminishing returns, partial correlation to control for course category and level.
- **Multiple testing:** all correlation p-values are Holm-adjusted. "Significant" below means significant after adjustment unless stated.
- **Tiers:** instructors are split into Low / Mid / High by rating tertile (cut-offs 2.97 and 3.53), 20 instructors each.

| KPI | Formula | Interpretation |
|---|---|---|
| **RCI** — Rating Consistency Index (0–100) | `100 × (μ/5) × (1 − σ/μ)` over an instructor's distinct courses | Rewards good *and* reliable portfolios; penalises "one-hit wonders" |
| **EIS** — Experience Impact Score | `(TeacherRating − platform mean) / ln(1 + years)` | Rating points above norm earned per unit of log-tenure. Efficiency, not a quality rank |
| **EIR** — Enrollment Influence Ratio | `actual enrollments ÷ Σ(course enrollments ÷ instructors on that course)` | 1.0× = fair share of the demand its courses generate |

EIR is normalised by course demand so that an instructor is not credited simply for teaching a popular topic. In aggregate it equals exactly 1.0 by construction; the median instructor sits at 0.42 (mean 0.64) because two instructors take far more than their share.

## 2.4 Distribution of instructor ratings *(Objective 1)*

| Metric | Mean | Median | SD | Skew | Gini |
|---|---|---|---|---|---|
| Teacher rating | 3.13 | 3.28 | 0.95 | −0.48 | 0.17 |
| Course rating | 3.10 | 3.07 | 1.17 | −0.05 | 0.22 |
| Enrollments per instructor | 166.7 | 56.5 | 539.8 | 5.17 | **0.68** |

- Instructor ratings span 1.05–4.97 and are mildly left-skewed (more strong performers than weak), close to normal (Shapiro p = 0.058). Quality is spread **evenly** (Gini 0.17): 11 instructors score 4.0 or above and 9 score below 2.0.
- Course ratings are flatter than a bell curve (excess kurtosis −1.2, Shapiro p = 0.008): the platform has many courses at both extremes. 16 courses are rated 4.0+ and 13 are below 2.0.
- Demand, by contrast, is extremely unequal (Gini 0.68, skew 5.2).

## 2.5 The Experience Paradox and the Instructor Halo Effect *(Objectives 1–2)*

### Experience Paradox
> *Experience makes instructors better rated, yet does not make their courses better rated.*

| Relationship | Grain | r | 95% CI | p | Holm-adj. p |
|---|---|---|---|---|---|
| Experience → **TeacherRating** | instructor (60) | **+0.60** | 0.41 to 0.74 | 4.5e-07 | **5.4e-06** |
| Experience → CourseRating (mean of courses) | instructor (60) | −0.14 | −0.38 to 0.12 | 0.29 | 1.00 |
| Experience → CourseRating (enrollment-weighted) | instructor (60) | −0.06 | −0.31 to 0.20 | 0.67 | 1.00 |
| Experience → CourseRating | delivery (887) | −0.01 | −0.08 to 0.05 | 0.70 | 1.00 |

**Diminishing returns.** Four curves were fitted to teacher rating against years of experience. A segmented model with a break at **8 years** fits best (AIC −32.0; R² 0.42 vs 0.36 for a straight line). Before the break, each extra year adds about **0.21** rating points; after it, about **0.05**. The log curve (ΔAIC 3.0) and quadratic (ΔAIC 3.3) also beat the straight line, so the direction of the finding is consistent, but with 60 instructors the exact breakpoint is uncertain.

| Experience band | Instructors | Mean teacher rating | Mean EIS |
|---|---|---|---|
| 1–2 years | 13 | 2.64 | −0.67 |
| 3–5 years | 15 | 2.19 | −0.61 |
| 6–8 years | 18 | 3.63 | +0.25 |
| 9–12 years | 9 | 3.92 | +0.33 |
| 13+ years | 5 | 3.95 | +0.27 |

Two points stand out. First, ratings do **not** rise steadily: the 3–5-year group is *below* the 1–2-year group, and the jump happens at 6–8 years. Second, only five instructors have 13+ years, so the plateau is suggestive rather than conclusive. EIS is highest for early-career instructors who rate well (for example a 2-year instructor at 3.99, EIS +0.79) and lowest for new instructors with poor ratings.

### Instructor Halo Effect
If instructors had a halo, courses taught by highly rated instructors would be rated higher. The data show no such effect:

| Relationship | Grain | r | p | Holm-adj. p |
|---|---|---|---|---|
| TeacherRating → CourseRating (enrollment-weighted) | instructor | +0.00 | 1.00 | 1.00 |
| TeacherRating → CourseRating | delivery (887) | −0.03 | 0.32 | 1.00 |
| TeacherRating → CourseRating, controlling for category and level | delivery | −0.00 | 0.99 | 1.00 |
| TeacherRating → CourseRating (mean of courses) | instructor | −0.30 | 0.018 | 0.16 |

The one nominal signal, a **negative** r = −0.30 across instructors (Spearman ρ = −0.40), has three reasons for caution. It is not significant after Holm adjustment; it disappears when instructors are weighted by enrollment or when the delivery grain is used; and because course ratings are fixed per course, it can only reflect *which courses* higher-rated instructors are assigned, not any effect they have. A reasonable reading is that top-rated instructors are, if anything, assigned to weaker courses. This is a hypothesis to test (see Recommendation 2), not a result.

**Conclusion on the halo:** instructor impact and content quality are separable on this platform, and content quality is the larger source of variation in course ratings.

## 2.6 Domain dependency *(Objective 3)*

| Test | Result |
|---|---|
| CourseRating by **category** (12 groups) | ANOVA F = 0.36, p = 0.97; Kruskal p = 0.96 — no detectable difference |
| CourseRating by **level** | ANOVA p = 0.37. Means: Beginner 3.19, Intermediate 3.32, **Advanced 2.81** |
| TeacherRating by **expertise** (10 groups with n ≥ 2) | ANOVA p = 0.044, Kruskal p = 0.074, Holm-adj. 0.31 — suggestive only |
| Female vs male instructor rating | 3.23 vs 3.04; Welch p = 0.46 — no difference |
| Domain-aligned vs cross-domain delivery, course rating | p = 0.97 — no difference (but see the note on identifiability below) |

**Where quality is most volatile.** Category *averages* are similar (2.66 for Machine Learning up to 3.72 for Marketing), but the *spread* differs sharply. Project Management (SD 1.71), Machine Learning (1.56) and Cybersecurity (1.49) contain both excellent and very weak courses, so quality there depends on the individual course. Data Science is the most uniform (SD 0.50). The weakest course-level result in the platform is a Beginner Machine Learning course at 1.13.

**Expertise gaps (training needs).** Mean instructor ratings are lowest in **Business (2.25, n = 2)**, **Design (2.29, n = 4)**, **Web Development (2.51, n = 5)** and **Project Management (2.66, n = 5)**, against 3.13 platform-wide. Highest are Machine Learning (4.23, n = 5) and Marketing (4.29, n = 1). Group sizes are small and the formal test is not significant after correction, so these are priorities for investigation rather than proven gaps.

**Identifiability note.** Within a category, course rating cannot vary by instructor, and in four categories (AI, Cybersecurity, Data Science, Project Management) every instructor delivers every course, so the within-category teacher–course correlation is exactly zero by design. We therefore did not read "where does the instructor matter most" from per-category correlations. A direct answer needs per-delivery ratings (see §2.8).

## 2.7 Demand generation *(Objective 4)*

| Tier | Instructors | Total enrollments | Share | Mean | **Median** | Median EIR |
|---|---|---|---|---|---|---|
| Low (≤ 2.97) | 20 | 1,509 | 15.1% | 75.5 | 61.0 | 0.44 |
| Mid | 20 | 1,032 | 10.3% | 51.6 | 44.0 | 0.24 |
| High (> 3.53) | 20 | 7,459 | **74.6%** | 372.9 | 62.5 | 0.66 |

On totals, high-rated instructors dominate. That is almost entirely a **two-instructor effect**:

- **Yolanda Levine** (Machine Learning, rated 4.97, 21 years) and **Kimberly Miller** (Cybersecurity, rated 4.58, 24 years) hold 3,061 and 3,025 enrollments, together **60.9%** of the platform.
- They deliver **all 60 courses**, averaging 55 enrollments per delivery against 5.0 (median 2) for everyone else.
- Only **16%** of their enrollments are inside their declared expertise, against **80%** for the other 58 instructors.
- The next-largest instructors have 164 and 161 enrollments, and are rated **1.86 and 1.06**.
- Rating vs enrollments across instructors: Spearman ρ = −0.01 (p = 0.93). Excluding the two outliers, r = −0.11 (p = 0.43). The High tier's median (62.5) is barely above Low (61.0). Without the two outliers, the other 18 High-tier instructors hold 1,373 enrollments, about 76 each.

So the data do **not** show that higher-rated instructors attract more learners. They show that two instructors receive a very large share of enrollments across the whole catalogue. That pattern is more consistent with how the platform routes or promotes instructors than with learners choosing on quality. *(We cannot observe routing directly; this is an inference to verify.)*

The formal tier comparison is not stable either: Kruskal–Wallis on enrollments gives p = 0.012 unadjusted (Holm-adjusted 0.55), and without the two outliers the Mid tier is the lowest, not the Low tier, so there is no monotonic rating-to-demand relationship.

High-rated instructors also teach lower-rated courses on average (mean 2.92 vs 3.16 and 3.17; Holm-adj. p = 0.003), which is the same assignment pattern noted in §2.5.

## 2.8 Limitations
1. **Course rating is not per instructor.** The single biggest limit. A true halo or instructor-effect model needs a rating for each (course, instructor) delivery, or learner-level reviews.
2. **Small instructor sample** (n = 60; five with 13+ years; several expertise groups have 1–2 instructors). Band-level and expertise-level differences are directional.
3. **Observational data.** Nothing here supports causal claims; assignment and routing rules are unobserved.
4. **No time dimension used.** Transactions carry dates, but ratings are static, so changes in quality over time cannot be assessed.
5. **Free vs paid:** 64% of transactions are free, and paid courses average 2.94 vs 3.19 for free courses; this was not tested further because price shows no relationship with rating (r = −0.03).

---

# 3. Strategic Recommendations

### Recommendation 1 — Invest in the first 8 years, and stop using tenure as a quality proxy
**Evidence:** rating gain is 0.21 points per year up to ~8 years, then 0.05; tenure has no relationship with course ratings.
**Actions**
- Build onboarding, coaching and peer-review programmes for instructors in years 1–8, with a checkpoint at years 5–6 where ratings begin to separate (the 3–5-year group is the weakest cohort).
- Use **EIS** to find rising instructors (for example 2-year instructors rated near 4.0) and fast-track them; use low-EIS, low-rating instructors for targeted support.
- Do not use years of experience for pricing, assignment or promotion decisions beyond the 8-year mark.
**Success measure:** share of instructors rated below 2.5 (currently 15 of 60) and the 3–5-year cohort's mean rating (currently 2.19).

### Recommendation 2 — Govern quality at the course level, not through star instructors
**Evidence:** no halo; course-rating variation sits within categories, not between them; 13 courses score below 2.0.
**Actions**
- Introduce a **course quality gate**: review or rebuild any course below 2.5 (20 courses), starting with the 13 below 2.0. These are concentrated in Machine Learning (3), Cybersecurity (2) and Project Management (2).
- Track course quality as its own KPI, separate from instructor ratings, and review the most volatile categories first (Project Management, Machine Learning, Cybersecurity).
- Run a controlled pilot: assign a high-rated and a low-rated instructor to the same weak course and compare outcomes. This tests the instructor effect directly and addresses the key data limitation.
- **Collect ratings per delivery** (course × instructor) from now on.
**Success measure:** number of courses below 2.5; correlation between instructor and course rating once per-delivery data exists.

### Recommendation 3 — Remove the key-person risk in demand
**Evidence:** two instructors hold 60.9% of enrollments across all 60 courses, 84% of it outside their own expertise; rating does not predict demand.
**Actions**
- Review how learners are routed to instructors and cap any one instructor's share of a course's enrollments; set a succession and continuity plan for the two instructors.
- Test routing on **domain-aligned** instructors for a sample of courses, and compare completion and satisfaction against the current cross-domain pattern.
- Grow the next tier using **EIR**: instructors who draw well above their share while teaching mostly inside their own domain (56–62% of deliveries), for example Alexis Everett (Programming, EIR 2.09), Aaron Kirby (Marketing, 1.81) and Wesley Garcia (Design, 1.75).
- Investigate why instructors rated 1.06 and 1.86 receive the 3rd and 4th highest enrollments.
**Success measure:** top-2 share of enrollments (currently 60.9%) and Gini coefficient of demand (currently 0.68).

---

# 4. Module A — ETL & KPI Engineering

File: `etl_pipeline.py`. Run `python etl_pipeline.py` to validate the data, build the KPIs and write `outputs/teacher_kpis.csv` and `outputs/teacher_course_pairs.csv`.

```python
"""
EduPro | Instructor & Course Quality Framework
ETL + Feature Engineering Pipeline
===============================================================================
Responsibilities
  1. Load the three analytical sheets (Teachers, Courses, Transactions).
  2. Validate keys and the Teacher <-> Course mapping (fail loudly, not silently).
  3. Build a teacher-course "pair fact" table (the true grain of the data).
  4. Engineer instructor-level KPIs:
        RCI  - Rating Consistency Index
        EIS  - Experience Impact Score
        EIR  - Enrollment Influence Ratio

Data-model note (important)
  Transactions carry BOTH CourseID and TeacherID, and the mapping is many-to-many:
  a course is delivered by 7-30 different instructors, and an instructor delivers
  7-55 different courses. CourseRating is a single scalar per course, so it is a
  property of the course, not of a (teacher, course) delivery. All analysis is
  therefore run at three explicit grains:
        teacher (n = 60)  <- primary unit for instructor KPIs
        pair    (n = 887) <- teacher x course deliveries
        transaction       <- used ONLY to count enrollments, never to compute
                             correlations (it would massively inflate n).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).with_name("EduPro_Online_Platform.xlsx")
OUT_DIR = Path(__file__).with_name("outputs")

TIER_LABELS = ["Low", "Mid", "High"]
EXP_BINS = [0, 2, 5, 8, 12, np.inf]
EXP_LABELS = ["1-2 yrs", "3-5 yrs", "6-8 yrs", "9-12 yrs", "13+ yrs"]
RATING_MAX = 5.0


# --------------------------------------------------------------------------- #
# 1. LOAD
# --------------------------------------------------------------------------- #
def load_raw(path: Path | str = DATA_PATH) -> dict[str, pd.DataFrame]:
    """Read the sheets used by the framework. The 'Users' sheet is not required."""
    sheets = pd.read_excel(path, sheet_name=["Teachers", "Courses", "Transactions"])
    for df in sheets.values():
        df.columns = df.columns.str.strip()
    return sheets


# --------------------------------------------------------------------------- #
# 2. VALIDATE
# --------------------------------------------------------------------------- #
def validate(teachers: pd.DataFrame, courses: pd.DataFrame, tx: pd.DataFrame) -> dict:
    """Integrity checks. Hard failures raise; soft findings are returned in the report."""
    # Hard checks -----------------------------------------------------------
    assert teachers["TeacherID"].is_unique, "Duplicate TeacherID"
    assert courses["CourseID"].is_unique, "Duplicate CourseID"
    assert tx["TransactionID"].is_unique, "Duplicate TransactionID"
    assert tx["TeacherID"].isin(teachers["TeacherID"]).all(), "Orphan TeacherID in Transactions"
    assert tx["CourseID"].isin(courses["CourseID"]).all(), "Orphan CourseID in Transactions"
    for name, s in {"TeacherRating": teachers["TeacherRating"],
                    "CourseRating": courses["CourseRating"]}.items():
        assert s.between(1, RATING_MAX).all(), f"{name} outside 1-5 scale"
    assert (teachers["YearsOfExperience"] >= 0).all(), "Negative experience"

    # Soft findings ---------------------------------------------------------
    pairs = tx[["TeacherID", "CourseID"]].drop_duplicates()
    per_course = pairs.groupby("CourseID")["TeacherID"].nunique()
    per_teacher = pairs.groupby("TeacherID")["CourseID"].nunique()
    enr = tx.groupby("TeacherID").size().sort_values(ascending=False)
    return {
        "teachers": len(teachers),
        "courses": len(courses),
        "transactions": len(tx),
        "unique_teacher_course_pairs": len(pairs),
        "teachers_per_course (min/med/max)": (int(per_course.min()), float(per_course.median()), int(per_course.max())),
        "courses_per_teacher (min/med/max)": (int(per_teacher.min()), float(per_teacher.median()), int(per_teacher.max())),
        "teachers_without_transactions": int((~teachers["TeacherID"].isin(tx["TeacherID"])).sum()),
        "courses_without_transactions": int((~courses["CourseID"].isin(tx["CourseID"])).sum()),
        "duplicate_course_names": courses.loc[courses["CourseName"].duplicated(keep=False), "CourseName"].unique().tolist(),
        "top2_teacher_enrollment_share": float(enr.head(2).sum() / enr.sum()),
        "free_transaction_share": float((tx["Amount"] == 0).mean()),
    }


# --------------------------------------------------------------------------- #
# 3. PAIR FACT  (teacher x course)
# --------------------------------------------------------------------------- #
def build_pair_fact(teachers: pd.DataFrame, courses: pd.DataFrame, tx: pd.DataFrame) -> pd.DataFrame:
    """One row per (TeacherID, CourseID) actually delivered, with enrollments."""
    fact = (
        tx.groupby(["TeacherID", "CourseID"], as_index=False)
        .agg(Enrollments=("TransactionID", "nunique"), Revenue=("Amount", "sum"))
        .merge(teachers, on="TeacherID", how="left", validate="m:1")
        .merge(courses, on="CourseID", how="left", validate="m:1")
    )
    # Does the instructor's declared expertise match the course's category?
    fact["DomainAligned"] = fact["Expertise"] == fact["CourseCategory"]

    # Demand baseline: if a course's enrollments were split evenly among its instructors
    fact["CourseEnrollments"] = fact.groupby("CourseID")["Enrollments"].transform("sum")
    fact["TeachersOnCourse"] = fact.groupby("CourseID")["TeacherID"].transform("nunique")
    fact["ExpectedEnrollments"] = fact["CourseEnrollments"] / fact["TeachersOnCourse"]
    return fact


# --------------------------------------------------------------------------- #
# 4. KPI ENGINEERING  (teacher grain)
# --------------------------------------------------------------------------- #
def engineer_teacher_kpis(
    pairs: pd.DataFrame,
    teachers: pd.DataFrame,
    tier_edges: tuple[float, float] | None = None,
    platform_mean: float | None = None,
) -> pd.DataFrame:
    """
    Adds the three custom KPIs plus supporting course-portfolio statistics.

    RCI  (Rating Consistency Index, 0-100)
        RCI = 100 * (mu / 5) * (1 - CV),   mu = mean rating over the instructor's
        distinct courses, CV = sigma / mu (sample std), CV clipped to [0, 1].
        Quality (mu) is multiplied by reliability (1 - CV): a "one-hit wonder" with
        one excellent course and several weak ones has a high sigma and is
        penalised even if the mean looks respectable. Each course counts once
        (unweighted) so a single popular course cannot mask a weak portfolio.

    EIS  (Experience Impact Score)
        EIS = (TeacherRating - platform mean TeacherRating) / ln(1 + YearsOfExperience)
        Rating points above/below the platform norm, earned per unit of
        log-tenure. Log-tenure encodes diminishing returns: year 1 -> 2 matters
        more than year 20 -> 21. EIS > 0 means the instructor out-performs the
        norm relative to the time invested; it is an efficiency measure, NOT a
        quality ranking (it structurally favours early-career excellence).

    EIR  (Enrollment Influence Ratio)
        EIR = actual enrollments / expected enrollments, where expected is the
        sum over the instructor's courses of (course enrollments / number of
        instructors teaching that course). EIR = 1.0 -> draws exactly a fair
        share of demand; >1 pulls demand beyond the course's own appeal.
        Normalising by course demand strips out "popular topic" effects.

    Optional `tier_edges` / `platform_mean` pin the tier cut-offs and the EIS baseline
    to platform-wide values, so KPIs stay comparable when the dashboard filters the
    data to a subset. When omitted they are derived from `teachers` itself.
    """
    p = pairs.copy()
    p["_w_cr"] = p["Enrollments"] * p["CourseRating"]
    g = p.groupby("TeacherID")
    agg = g.agg(
        Courses=("CourseID", "nunique"),
        Enrollments=("Enrollments", "sum"),
        ExpectedEnrollments=("ExpectedEnrollments", "sum"),
        Revenue=("Revenue", "sum"),
        MeanCourseRating=("CourseRating", "mean"),          # each course once
        SDCourseRating=("CourseRating", "std"),
        MinCourseRating=("CourseRating", "min"),
        MaxCourseRating=("CourseRating", "max"),
        HitRate=("CourseRating", lambda s: (s >= 4.0).mean()),
        AlignedShare=("DomainAligned", "mean"),
        _w=("_w_cr", "sum"),
    )
    agg["WeightedCourseRating"] = agg["_w"] / agg["Enrollments"]  # enrollment-weighted
    agg = agg.drop(columns="_w")
    agg["SDCourseRating"] = agg["SDCourseRating"].fillna(0.0)

    t = teachers.merge(agg, on="TeacherID", how="left", validate="1:1")

    # --- RCI ---------------------------------------------------------------
    cv = (t["SDCourseRating"] / t["MeanCourseRating"]).clip(0, 1)
    t["RCI"] = 100 * (t["MeanCourseRating"] / RATING_MAX) * (1 - cv)

    # --- EIS ---------------------------------------------------------------
    baseline = t["TeacherRating"].mean() if platform_mean is None else platform_mean
    t["EIS"] = (t["TeacherRating"] - baseline) / np.log1p(t["YearsOfExperience"])

    # --- EIR ---------------------------------------------------------------
    t["EIR"] = t["Enrollments"] / t["ExpectedEnrollments"]

    # --- Segmentation ------------------------------------------------------
    edges = tier_edges or tuple(t["TeacherRating"].quantile([1 / 3, 2 / 3]))
    t["RatingTier"] = pd.cut(t["TeacherRating"], bins=[-np.inf, *edges, np.inf], labels=TIER_LABELS)
    t["ExperienceBand"] = pd.cut(t["YearsOfExperience"], bins=EXP_BINS, labels=EXP_LABELS)
    t["EnrollmentShare"] = t["Enrollments"] / t["Enrollments"].sum()
    return t


# --------------------------------------------------------------------------- #
# 5. ORCHESTRATION
# --------------------------------------------------------------------------- #
@dataclass
class EduProData:
    teachers: pd.DataFrame
    courses: pd.DataFrame
    tx: pd.DataFrame
    pairs: pd.DataFrame          # teacher x course grain
    kpis: pd.DataFrame           # teacher grain with KPIs
    report: dict = field(default_factory=dict)
    tier_cutoffs: tuple = (0.0, 0.0)      # tertile edges of TeacherRating (unrounded)
    platform_mean_rating: float = 0.0     # EIS baseline


def build_all(path: Path | str = DATA_PATH) -> EduProData:
    raw = load_raw(path)
    T, C, X = raw["Teachers"], raw["Courses"], raw["Transactions"]
    report = validate(T, C, X)
    pairs = build_pair_fact(T, C, X)
    kpis = engineer_teacher_kpis(pairs, T)
    cuts = tuple(float(v) for v in kpis["TeacherRating"].quantile([1 / 3, 2 / 3]))
    return EduProData(T, C, X, pairs, kpis, report, cuts, float(T["TeacherRating"].mean()))


def main() -> None:
    d = build_all()
    OUT_DIR.mkdir(exist_ok=True)
    d.kpis.to_csv(OUT_DIR / "teacher_kpis.csv", index=False)
    d.pairs.to_csv(OUT_DIR / "teacher_course_pairs.csv", index=False)
    print("VALIDATION REPORT")
    for k, v in d.report.items():
        print(f"  {k:<40} {v}")
    print(f"\nRating-tier cutoffs (tertiles): Low <= {d.tier_cutoffs[0]:.3f} < Mid <= {d.tier_cutoffs[1]:.3f} < High")
    cols = ["TeacherName", "Expertise", "YearsOfExperience", "TeacherRating", "RCI", "EIS", "EIR"]
    print("\nKPI summary:\n", d.kpis[["RCI", "EIS", "EIR"]].describe().round(2).to_string())
    print("\nTop 5 by RCI:\n", d.kpis.nlargest(5, "RCI")[cols].round(2).to_string(index=False))
    print("\nTop 5 by EIR:\n", d.kpis.nlargest(5, "EIR")[cols].round(2).to_string(index=False))
    print(f"\nWrote {OUT_DIR}/teacher_kpis.csv and teacher_course_pairs.csv")


if __name__ == "__main__":
    main()
```

---

# 5. Module B — Statistical Inference Engine

File: `stats_engine.py`. Run `python stats_engine.py` for the full report (reproduced in the appendix).

```python
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
```

---

# 6. Module C — Executive Dashboard

File: `app.py`. Run `streamlit run app.py`.

**Modules and controls**

| Tab | Content |
|---|---|
| Overview | KPI strip (Avg Teacher Rating, Avg Course Rating, RCI, EIS, EIR vs platform); rating histogram; box plots by expertise |
| Experience & Halo | Scatter plots with OLS trendlines (experience → rating; instructor rating → course rating), live r / CI / p, experience-band chart |
| Course quality | Switchable heatmaps (category × level, expertise × category, expertise × level), box plots by category and level, gender × level |
| Demand | Enrollments by tier, per-instructor distribution (log scale), cumulative concentration curve, tier table |
| Leaderboard | Sortable, searchable instructor table with progress bars, CSV export, and drill-down to an instructor's course portfolio |
| Method & caveats | KPI definitions and reading guidance |

Sidebar filters: instructor expertise, course category, course level, teacher-rating range, course-rating range, years-of-experience range, and a toggle that removes the two mega-enrollment instructors from demand charts. Filters recompute RCI and EIR on the filtered portfolio while tier cut-offs and the EIS baseline stay platform-wide, so figures remain comparable.

```python
"""
EduPro | Instructor & Course Quality Intelligence  -  Executive Dashboard
Run:  streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from etl_pipeline import DATA_PATH, EXP_LABELS, TIER_LABELS, EduProData, build_all, engineer_teacher_kpis
from stats_engine import correlate, gini

st.set_page_config(page_title="EduPro Instructor Intelligence", page_icon="🎓", layout="wide")

# --------------------------------------------------------------------------- #
# Design tokens (validated blue sequential ramp; orange = reference/trend accent)
# --------------------------------------------------------------------------- #
TIER_COLORS = {"Low": "#86b6ef", "Mid": "#3987e5", "High": "#1c5cab"}   # ordinal ramp
SEQ_SCALE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
ACCENT = "#eb6834"      # trendlines / reference lines
BLUE = "#2a78d6"
LEVEL_ORDER = ["Beginner", "Intermediate", "Advanced"]
FONT = dict(family="Inter, Segoe UI, sans-serif", size=13)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px;}
      [data-testid="stMetricValue"] {font-size: 1.7rem;}
      .insight {border-left: 4px solid #2a78d6; padding: .55rem .9rem; margin: .4rem 0 1rem 0;
                background: rgba(42,120,214,.07); border-radius: 0 6px 6px 0; font-size: .95rem;}
      .insight.warn {border-left-color: #eb6834; background: rgba(235,104,52,.08);}
    </style>
    """,
    unsafe_allow_html=True,
)


def insight(text: str, warn: bool = False) -> None:
    st.markdown(f'<div class="insight {"warn" if warn else ""}">{text}</div>', unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 400) -> go.Figure:
    fig.update_layout(height=height, font=FONT, margin=dict(l=10, r=10, t=85, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""),
                      title=dict(font=dict(size=15), x=0, y=0.97, yanchor="top"))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,.18)")
    return fig


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Building feature store...")
def load() -> EduProData:
    return build_all(DATA_PATH)


if not Path(DATA_PATH).exists():
    st.error(f"Dataset not found at {DATA_PATH}. Place EduPro_Online_Platform.xlsx next to app.py.")
    st.stop()

D = load()
K, P = D.kpis, D.pairs

# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #
sb = st.sidebar
sb.header("Filters")
expertise = sb.multiselect("Instructor expertise", sorted(K.Expertise.unique()), default=sorted(K.Expertise.unique()))
category = sb.multiselect("Course category", sorted(D.courses.CourseCategory.unique()),
                          default=sorted(D.courses.CourseCategory.unique()))
level = sb.multiselect("Course level", LEVEL_ORDER, default=LEVEL_ORDER)
tr_rng = sb.slider("Teacher rating", 1.0, 5.0, (1.0, 5.0), 0.05)
cr_rng = sb.slider("Course rating", 1.0, 5.0, (1.0, 5.0), 0.05)
yoe_rng = sb.slider("Years of experience", int(K.YearsOfExperience.min()), int(K.YearsOfExperience.max()),
                    (int(K.YearsOfExperience.min()), int(K.YearsOfExperience.max())))
sb.divider()
excl_top = sb.toggle("Exclude the 2 mega-enrollment instructors from demand charts", value=False,
                     help="Two instructors account for ~61% of all enrollments and distort every averaged demand metric.")
sb.caption(f"Rating tiers are platform-wide tertiles: Low ≤ {D.tier_cutoffs[0]:.2f} < Mid ≤ {D.tier_cutoffs[1]:.2f} < High.")


def apply_filters() -> tuple[pd.DataFrame, pd.DataFrame]:
    ok = K[K.Expertise.isin(expertise) & K.TeacherRating.between(*tr_rng) & K.YearsOfExperience.between(*yoe_rng)].TeacherID
    p = P[P.TeacherID.isin(ok) & P.CourseCategory.isin(category) & P.CourseLevel.isin(level)
          & P.CourseRating.between(*cr_rng)].copy()
    if p.empty:
        return p, K.iloc[0:0]
    t = D.teachers[D.teachers.TeacherID.isin(p.TeacherID.unique())]
    k = engineer_teacher_kpis(p, t, tier_edges=D.tier_cutoffs, platform_mean=D.platform_mean_rating)
    return p, k


FP, FK = apply_filters()
if FP.empty or len(FK) < 2:
    st.warning("The current filters leave fewer than 2 instructors. Widen the filters in the sidebar.")
    st.stop()
FC = FP.drop_duplicates("CourseID")                       # distinct courses in scope
DK = FK[FK.Enrollments < K.Enrollments.nlargest(2).min()] if excl_top else FK

# --------------------------------------------------------------------------- #
# Header + KPI strip
# --------------------------------------------------------------------------- #
st.title("Instructor & Course Quality Intelligence")
st.caption(f"{len(FK)} of {len(K)} instructors · {len(FC)} of {len(D.courses)} courses · "
           f"{int(FP.Enrollments.sum()):,} of {len(D.tx):,} enrollments in scope")

c = st.columns(5)
c[0].metric("Avg teacher rating", f"{FK.TeacherRating.mean():.2f}", f"{FK.TeacherRating.mean() - K.TeacherRating.mean():+.2f} vs platform", delta_color="off")
c[1].metric("Avg course rating", f"{FC.CourseRating.mean():.2f}", f"{FC.CourseRating.mean() - D.courses.CourseRating.mean():+.2f} vs platform", delta_color="off")
c[2].metric("Rating Consistency (RCI)", f"{FK.RCI.mean():.1f}", f"{FK.RCI.mean() - K.RCI.mean():+.1f} vs platform", delta_color="off",
            help="0-100. Mean course quality × reliability across an instructor's portfolio.")
c[3].metric("Experience Impact (EIS)", f"{FK.EIS.mean():+.2f}", help="Rating points above/below platform norm per ln(1+years).")
c[4].metric("Enrollment Influence (EIR)", f"{FK.EIR.median():.2f}×", help="Median across instructors; 1.0× = fair share of course demand. "
            "Mean is skewed by two outliers.")
st.write("")

tabs = st.tabs(["Overview", "Experience & Halo", "Course quality", "Demand", "Leaderboard", "Method & caveats"])

# --------------------------------------------------------------------------- #
# TAB 1 - Overview
# --------------------------------------------------------------------------- #
with tabs[0]:
    a, b = st.columns(2)
    fig = px.histogram(FK, x="TeacherRating", nbins=16, color_discrete_sequence=[BLUE], title="Distribution of instructor ratings")
    fig.add_vline(x=FK.TeacherRating.mean(), line_dash="dash", line_color=ACCENT,
                  annotation_text=f"mean {FK.TeacherRating.mean():.2f}", annotation_position="top right")
    fig.update_traces(marker_line_width=2, marker_line_color="rgba(255,255,255,.9)")
    fig.update_layout(yaxis_title="Instructors", xaxis_title="Teacher rating", bargap=0.05)
    a.plotly_chart(style(fig), width="stretch")

    order = FK.groupby("Expertise").TeacherRating.median().sort_values().index.tolist()
    fig = px.box(FK, x="TeacherRating", y="Expertise", points="all", category_orders={"Expertise": order},
                 color_discrete_sequence=[BLUE], title="Teacher rating by expertise (training-gap view)")
    fig.add_vline(x=K.TeacherRating.mean(), line_dash="dash", line_color=ACCENT)
    fig.update_layout(xaxis_title="Teacher rating (dashed = platform mean)", yaxis_title="")
    b.plotly_chart(style(fig), width="stretch")

    gap = (FK.groupby("Expertise").agg(n=("TeacherID", "count"), m=("TeacherRating", "mean"))
           .query("n >= 2").sort_values("m").head(3))
    spread = FK.TeacherRating.std()
    insight(f"Rating spread: SD {spread:.2f}, Gini {gini(FK.TeacherRating):.2f} (low = evenly distributed quality). "
            + (f"Largest training gaps: <b>{', '.join(gap.index)}</b> "
               f"(mean {gap.m.min():.2f}-{gap.m.max():.2f} vs platform {K.TeacherRating.mean():.2f})." if len(gap) else ""))

# --------------------------------------------------------------------------- #
# TAB 2 - Experience & Halo
# --------------------------------------------------------------------------- #
with tabs[1]:
    a, b = st.columns(2)
    fig = px.scatter(FK, x="YearsOfExperience", y="TeacherRating", color="RatingTier", trendline="ols",
                     trendline_scope="overall", trendline_color_override=ACCENT, color_discrete_map=TIER_COLORS,
                     category_orders={"RatingTier": TIER_LABELS}, hover_name="TeacherName",
                     hover_data={"Expertise": True, "EIS": ":.2f", "RatingTier": False},
                     title="Experience vs instructor rating (OLS trend)")
    fig.update_traces(marker=dict(size=10, line=dict(width=1.5, color="rgba(255,255,255,.9)")), selector=dict(mode="markers"))
    fig.update_layout(xaxis_title="Years of experience", yaxis_title="Teacher rating", yaxis_range=[0.8, 5.2])
    a.plotly_chart(style(fig, 430), width="stretch")

    fig = px.scatter(FK, x="TeacherRating", y="MeanCourseRating", color="RatingTier", trendline="ols",
                     trendline_scope="overall", trendline_color_override=ACCENT, color_discrete_map=TIER_COLORS,
                     category_orders={"RatingTier": TIER_LABELS}, hover_name="TeacherName",
                     hover_data={"Courses": True, "RatingTier": False},
                     title="Halo test: instructor rating vs rating of the courses they teach")
    fig.update_traces(marker=dict(size=10, line=dict(width=1.5, color="rgba(255,255,255,.9)")), selector=dict(mode="markers"))
    fig.update_layout(xaxis_title="Teacher rating", yaxis_title="Mean rating of courses taught", yaxis_range=[1.5, 4.5])
    b.plotly_chart(style(fig, 430), width="stretch")

    if len(FK) >= 5:
        s1 = correlate(FK.YearsOfExperience, FK.TeacherRating, "", "")
        s2 = correlate(FK.YearsOfExperience, FK.MeanCourseRating, "", "")
        s3 = correlate(FK.TeacherRating, FK.MeanCourseRating, "", "")
        s4 = correlate(FP.TeacherRating, FP.CourseRating, "", "")
        fmt = lambda s: f"r = {s['r']:+.2f} (95% CI {s['ci_low']:+.2f} to {s['ci_high']:+.2f}), p = {s['p']:.3g}, n = {s['n']}"
        st.markdown(
            f"- **Experience → teacher rating:** {fmt(s1)}\n"
            f"- **Experience → course rating:** {fmt(s2)}\n"
            f"- **Teacher rating → course rating (instructor grain):** {fmt(s3)}\n"
            f"- **Teacher rating → course rating (delivery grain):** {fmt(s4)}")
        halo = ("a <b>positive</b> halo is present in this scope" if (s3["r"] > 0.2 and s3["p"] < 0.05)
                else "<b>no positive halo</b> is detected in this scope")
        insight(f"<b>Experience Paradox:</b> compare the experience slope on the left with the course-rating slope above "
                f"(tenure vs course rating: r = {s2['r']:+.2f}). <b>Halo:</b> {halo} "
                f"(instructor-grain r = {s3['r']:+.2f}; an upward orange line on the right chart would indicate one).")

    bands = FK.groupby("ExperienceBand", observed=True).agg(n=("TeacherID", "count"), rating=("TeacherRating", "mean")).reset_index()
    fig = px.bar(bands, x="ExperienceBand", y="rating", text=bands.rating.round(2), color_discrete_sequence=[BLUE],
                 title="Mean teacher rating by experience band (diminishing returns)",
                 hover_data={"n": True}, category_orders={"ExperienceBand": EXP_LABELS})
    fig.update_traces(textposition="outside", marker_cornerradius=4)
    fig.update_layout(yaxis_range=[0, 5], xaxis_title="", yaxis_title="Mean teacher rating")
    st.plotly_chart(style(fig, 340), width="stretch")

# --------------------------------------------------------------------------- #
# TAB 3 - Course quality
# --------------------------------------------------------------------------- #
with tabs[2]:
    mode = st.radio("Heatmap view", ["Category × Level (courses)", "Instructor expertise × Course category (deliveries)",
                                     "Instructor expertise × Course level (deliveries)"], horizontal=True)
    if mode.startswith("Category"):
        pv = FC.pivot_table(index="CourseCategory", columns="CourseLevel", values="CourseRating", aggfunc="mean")
        pv = pv.reindex(columns=[l for l in LEVEL_ORDER if l in pv.columns])
    elif "category" in mode:
        pv = FP.pivot_table(index="Expertise", columns="CourseCategory", values="CourseRating", aggfunc="mean")
    else:
        pv = FP.pivot_table(index="Expertise", columns="CourseLevel", values="CourseRating", aggfunc="mean")
        pv = pv.reindex(columns=[l for l in LEVEL_ORDER if l in pv.columns])
    fig = px.imshow(pv.round(2), text_auto=".2f", aspect="auto", color_continuous_scale=SEQ_SCALE, zmin=1, zmax=5,
                    title="Mean course rating (blank = no data in current filter)")
    fig.update_layout(coloraxis_colorbar=dict(title="Rating", thickness=12), xaxis_title="", yaxis_title="")
    st.plotly_chart(style(fig, 520 if "Expertise" in mode else 440), width="stretch")

    a, b = st.columns(2)
    order = FC.groupby("CourseCategory").CourseRating.median().sort_values().index.tolist()
    fig = px.box(FC, x="CourseRating", y="CourseCategory", points="all", category_orders={"CourseCategory": order},
                 color_discrete_sequence=[BLUE], title="Course rating by category (spread = quality volatility)")
    fig.update_layout(xaxis_title="Course rating", yaxis_title="")
    a.plotly_chart(style(fig, 470), width="stretch")

    fig = px.box(FC, x="CourseLevel", y="CourseRating", points="all", category_orders={"CourseLevel": LEVEL_ORDER},
                 color_discrete_sequence=[BLUE], title="Course rating by level")
    fig.update_layout(xaxis_title="", yaxis_title="Course rating")
    b.plotly_chart(style(fig, 470), width="stretch")

    gl = FP.groupby(["Gender", "CourseLevel"]).CourseRating.mean().reset_index()
    fig = px.bar(gl, x="CourseLevel", y="CourseRating", color="Gender", barmode="group", text_auto=".2f",
                 category_orders={"CourseLevel": LEVEL_ORDER}, color_discrete_map={"Female": "#2a78d6", "Male": "#eb6834"},
                 title="Mean course rating: instructor gender × course level (delivery grain)")
    fig.update_traces(marker_cornerradius=4)
    fig.update_layout(yaxis_range=[0, 5], xaxis_title="", yaxis_title="Mean course rating")
    st.plotly_chart(style(fig, 360), width="stretch")
    cat_sd = FC.groupby("CourseCategory").CourseRating.std().dropna()
    if len(cat_sd):
        insight(f"Most volatile category (quality depends on <i>which</i> course): <b>{cat_sd.idxmax()}</b> (SD {cat_sd.max():.2f}); "
                f"most uniform: <b>{cat_sd.idxmin()}</b> (SD {cat_sd.min():.2f}). Differences in category means are small relative "
                f"to within-category spread.")

# --------------------------------------------------------------------------- #
# TAB 4 - Demand
# --------------------------------------------------------------------------- #
with tabs[3]:
    tier = (DK.groupby("RatingTier", observed=True)
            .agg(Instructors=("TeacherID", "count"), Enrollments=("Enrollments", "sum"), Mean=("Enrollments", "mean"),
                 Median=("Enrollments", "median"), MedianEIR=("EIR", "median"), CourseRating=("MeanCourseRating", "mean"))
            .reindex(TIER_LABELS).dropna(how="all").reset_index())
    a, b = st.columns(2)
    fig = px.bar(tier, x="RatingTier", y="Enrollments", color="RatingTier", color_discrete_map=TIER_COLORS,
                 text=tier.Enrollments.map("{:,.0f}".format), title="Total enrollments by instructor rating tier")
    fig.update_traces(textposition="outside", marker_cornerradius=4)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Enrollments")
    a.plotly_chart(style(fig, 400), width="stretch")

    fig = px.box(DK, x="RatingTier", y="Enrollments", color="RatingTier", points="all", color_discrete_map=TIER_COLORS,
                 category_orders={"RatingTier": TIER_LABELS}, hover_name="TeacherName", log_y=True,
                 title="Enrollments per instructor (log scale; dots = instructors)")
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Enrollments per instructor")
    fig.update_yaxes(tickvals=[10, 30, 100, 300, 1000, 3000], ticktext=["10", "30", "100", "300", "1,000", "3,000"],
                     minor=dict(showgrid=False))
    b.plotly_chart(style(fig, 400), width="stretch")

    srt = FK.sort_values("Enrollments", ascending=False).reset_index(drop=True)
    srt["Rank"] = np.arange(1, len(srt) + 1)
    srt["CumShare"] = srt.Enrollments.cumsum() / srt.Enrollments.sum()
    fig = go.Figure(go.Scatter(x=srt.Rank, y=srt.CumShare, mode="lines+markers", line=dict(color=BLUE, width=2),
                               marker=dict(size=7), customdata=srt[["TeacherName"]],
                               hovertemplate="Top %{x} instructors<br>%{y:.0%} of enrollments<br>last added: %{customdata[0]}<extra></extra>"))
    fig.update_layout(title="Demand concentration: cumulative share of enrollments by instructor rank",
                      xaxis_title="Instructors, ranked by enrollments", yaxis_title="Cumulative share", yaxis_tickformat=".0%",
                      yaxis_range=[0, 1.02])
    st.plotly_chart(style(fig, 360), width="stretch")

    top2 = srt.head(2)
    insight(f"Top 2 instructors hold <b>{top2.Enrollments.sum() / srt.Enrollments.sum():.0%}</b> of in-scope enrollments "
            f"(Gini {gini(srt.Enrollments):.2f}). Median enrollments per instructor by tier are "
            + ", ".join(f"{r.RatingTier}: {r.Median:.0f}" for r in tier.itertuples())
            + " — the tier gap in <i>totals</i> is a two-instructor effect, not a broad rating premium.", warn=True)
    st.dataframe(tier.rename(columns={"Mean": "Mean enroll.", "Median": "Median enroll.", "MedianEIR": "Median EIR",
                                      "CourseRating": "Mean course rating"}),
                 hide_index=True, width="stretch",
                 column_config={"Mean enroll.": st.column_config.NumberColumn(format="%.1f"),
                                "Median enroll.": st.column_config.NumberColumn(format="%.1f"),
                                "Median EIR": st.column_config.NumberColumn(format="%.2f"),
                                "Mean course rating": st.column_config.NumberColumn(format="%.2f")})

# --------------------------------------------------------------------------- #
# TAB 5 - Leaderboard
# --------------------------------------------------------------------------- #
with tabs[4]:
    f1, f2, f3, f4 = st.columns([2, 1, 1, 2])
    sort_by = f1.selectbox("Rank by", ["TeacherRating", "RCI", "EIS", "EIR", "Enrollments", "MeanCourseRating", "YearsOfExperience"])
    direction = f2.radio("Order", ["Highest", "Lowest"], horizontal=True)
    min_courses = f3.number_input("Min. courses", 1, 30, 5)
    q = f4.text_input("Search instructor", "")

    lb = FK[FK.Courses >= min_courses]
    if q:
        lb = lb[lb.TeacherName.str.contains(q, case=False, na=False)]
    lb = lb.sort_values(sort_by, ascending=(direction == "Lowest")).reset_index(drop=True)
    lb.insert(0, "Rank", np.arange(1, len(lb) + 1))
    cols = ["Rank", "TeacherName", "Expertise", "YearsOfExperience", "TeacherRating", "RatingTier", "Courses",
            "MeanCourseRating", "RCI", "EIS", "EIR", "Enrollments"]
    ev = st.dataframe(
        lb[cols], hide_index=True, width="stretch", height=470, on_select="rerun", selection_mode="single-row",
        column_config={
            "TeacherName": "Instructor", "YearsOfExperience": st.column_config.NumberColumn("Yrs exp"),
            "TeacherRating": st.column_config.ProgressColumn("Teacher rating", min_value=1, max_value=5, format="%.2f"),
            "RatingTier": "Tier", "MeanCourseRating": st.column_config.NumberColumn("Avg course rating", format="%.2f"),
            "RCI": st.column_config.ProgressColumn("RCI", min_value=0, max_value=100, format="%.1f"),
            "EIS": st.column_config.NumberColumn("EIS", format="%+.2f"),
            "EIR": st.column_config.NumberColumn("EIR", format="%.2f×"),
            "Enrollments": st.column_config.NumberColumn(format="%d"),
        })
    st.download_button("Download leaderboard (CSV)", lb[cols].to_csv(index=False).encode(), "edupro_leaderboard.csv", "text/csv")
    st.caption(f"{len(lb)} instructors shown. Select a row to open the instructor's course portfolio.")

    sel = ev.selection.rows if ev and ev.selection else []
    if sel:
        who = lb.iloc[sel[0]]
        port = FP[FP.TeacherID == who.TeacherID].sort_values("CourseRating")
        st.subheader(f"{who.TeacherName} · {who.Expertise}")
        m = st.columns(4)
        m[0].metric("Teacher rating", f"{who.TeacherRating:.2f}")
        m[1].metric("RCI", f"{who.RCI:.1f}", help="Best/worst course ratings: "
                    f"{who.MaxCourseRating:.2f} / {who.MinCourseRating:.2f}")
        m[2].metric("EIS", f"{who.EIS:+.2f}")
        m[3].metric("EIR", f"{who.EIR:.2f}×")
        fig = px.bar(port, x="CourseRating", y="CourseName", orientation="h", color="CourseLevel", hover_data=["CourseCategory", "Enrollments"],
                     color_discrete_map={"Beginner": "#86b6ef", "Intermediate": "#3987e5", "Advanced": "#1c5cab"},
                     title="Courses taught (colour = level)")
        fig.add_vline(x=D.courses.CourseRating.mean(), line_dash="dash", line_color=ACCENT,
                      annotation_text="platform mean", annotation_position="top")
        fig.update_traces(marker_cornerradius=3)
        fig.update_layout(xaxis_range=[0, 5], xaxis_title="Course rating", yaxis_title="", yaxis=dict(autorange="reversed"))
        st.plotly_chart(style(fig, max(320, 26 * len(port) + 120)), width="stretch")

# --------------------------------------------------------------------------- #
# TAB 6 - Method
# --------------------------------------------------------------------------- #
with tabs[5]:
    st.markdown(
        """
**KPI definitions**

| KPI | Formula | Reads as |
|---|---|---|
| **RCI** Rating Consistency Index | `100 × (μ/5) × (1 − σ/μ)` over an instructor's distinct courses | High = good *and* reliable portfolio; one standout course among weak ones is penalised |
| **EIS** Experience Impact Score | `(TeacherRating − platform mean) / ln(1 + years)` | Rating earned per unit of log-tenure; positive = outperforming tenure. An efficiency measure, not a quality rank |
| **EIR** Enrollment Influence Ratio | `actual enrollments / Σ(course enrollments ÷ instructors on course)` | 1.0× = fair share of demand; >1 pulls demand beyond the course's own appeal |

**Read before deciding**
- Teachers and courses are **many-to-many** (7-30 instructors per course). `CourseRating` is one number per course, so it cannot
  vary between instructors of the same course. The halo test therefore compares instructors *across* courses and cannot isolate causation.
- Two instructors deliver all 60 courses and carry ~61% of enrollments, mostly outside their declared expertise. Use the sidebar toggle
  to see demand analyses without them.
- Instructor-level samples are small (n = 60; 5 instructors with 13+ years). Treat band-level differences as directional.
- Filters recompute RCI/EIR on the filtered portfolio; tier cut-offs and the EIS baseline stay platform-wide.
"""
    )
```

---

# 7. Deployment & Reproducibility

**Folder layout**
```
edupro/
├── EduPro_Online_Platform.xlsx
├── etl_pipeline.py
├── stats_engine.py
├── app.py
├── requirements.txt
└── .streamlit/config.toml
```

**requirements.txt**
```
pandas>=2.2
numpy>=1.26
scipy>=1.11
plotly>=5.24
statsmodels>=0.14
streamlit>=1.40
openpyxl>=3.1
```

**.streamlit/config.toml**
```toml
[theme]
base = "light"
primaryColor = "#2a78d6"

[server]
headless = true
```

**Run**
```bash
pip install -r requirements.txt
python etl_pipeline.py      # validate data, build KPIs
python stats_engine.py      # print the statistical report
streamlit run app.py        # launch the dashboard
```

**Testing performed:** the pipeline asserts key integrity and rating ranges on load; the dashboard was executed under default filters, a narrowed filter, an empty-result filter and the demand toggle with no runtime errors, and every tab was rendered and inspected. `statsmodels` is required by Plotly's OLS trendlines.

---

# 8. Appendix — Full statistical output

```text

=== DISTRIBUTION ===
                 metric  n  mean  median     sd   iqr     skew  kurtosis  shapiro_p   gini
          TeacherRating 60 3.125   3.275 0.9498  1.34  -0.4848   -0.4035    0.05834 0.1692
           CourseRating 60 3.098   3.065  1.171 1.995 -0.04838    -1.225   0.007639  0.216
Enrollments per teacher 60 166.7    56.5  539.8  47.5    5.165      24.8   3.54e-16  0.681

=== CORRELATIONS ===
                                                  test   grain   n          r   ci_low  ci_high         p  spearman_rho  spearman_p    p_holm  significant
                           Experience vs TeacherRating teacher  60      0.598   0.4057   0.7396 4.518e-07        0.6705   4.603e-09 5.421e-06         True
          Experience vs CourseRating (mean of courses) teacher  60    -0.1375  -0.3782   0.1206    0.2948       -0.2112      0.1052         1        False
      Experience vs CourseRating (enrollment-weighted) teacher  60   -0.05689  -0.3064   0.1999    0.6659      -0.04822      0.7145         1        False
                            Experience vs CourseRating    pair 887   -0.01314 -0.07889  0.05273     0.696      -0.02574       0.444         1        False
       TeacherRating vs CourseRating (mean of courses) teacher  60    -0.3049  -0.5187 -0.05526   0.01785       -0.3966    0.001707    0.1606        False
   TeacherRating vs CourseRating (enrollment-weighted) teacher  60  0.0004787  -0.2535   0.2544    0.9971      -0.05913      0.6536         1        False
                         TeacherRating vs CourseRating    pair 887   -0.03366 -0.09927  0.03223    0.3166      -0.04982      0.1382         1        False
      TeacherRating vs CourseRating | category + level    pair 887 -0.0003727      NaN      NaN    0.9912           NaN         NaN         1        False
                          TeacherRating vs Enrollments teacher  60     0.3183  0.07002   0.5294    0.0132      -0.01202      0.9274     0.132        False
                     TeacherRating vs log(Enrollments) teacher  60     0.1993 -0.05757   0.4314    0.1269      -0.01202      0.9274         1        False
                                  TeacherRating vs EIR teacher  60     0.3439  0.09859   0.5498  0.007137        0.2043      0.1173    0.0785        False
TeacherRating vs Enrollments (excl. top-2 instructors) teacher  58    -0.1067  -0.3552   0.1559    0.4254       -0.1204      0.3678         1        False

=== GROUP_TESTS ===
                                                 test  groups  anova_F   anova_p  kruskal_H  kruskal_p  effect_eps2   p_holm
                       CourseRating by CourseCategory      12   0.3599    0.9653      4.388     0.9572            0        1
                          CourseRating by CourseLevel       3    1.014    0.3694      1.913     0.3842            0        1
                           TeacherRating by Expertise      10    2.143   0.04367      15.67    0.07409        0.139   0.3057
            Mean CourseRating by instructor Expertise      10     3.86 0.0009827       22.8   0.006654       0.2876 0.007862
                            Enrollments by RatingTier       3    2.297    0.1098      8.913     0.0116       0.1213   0.5489
                      Mean CourseRating by RatingTier       3    9.385 0.0002998      14.17  0.0008364       0.2136 0.002698
              Enrollments by RatingTier (excl. top-2)       3    3.251   0.04628      8.195    0.01662       0.1126   0.3057
                        TeacherRating: Female vs Male       2   0.7517    0.4562        551     0.1187          NaN        1
CourseRating: domain-aligned vs cross-domain delivery       2  0.03171    0.9747  8.726e+04     0.8891          NaN        1

=== EXPERIENCE_CURVE ===
            model     r2    aic  delta_aic
    Hinge @ 8 yrs 0.4212    -32          0
Log (diminishing)  0.371 -29.01      2.993
        Quadratic 0.3888 -28.73      3.275
           Linear 0.3576 -27.75      4.255

=== EXPERIENCE_BANDS ===
ExperienceBand  instructors  teacher_rating  course_rating   rci     eis
       1-2 yrs           13           2.644          3.092 36.48 -0.6651
       3-5 yrs           15           2.187          3.196 38.57 -0.6076
       6-8 yrs           18           3.627          3.023 38.17  0.2465
      9-12 yrs            9            3.92          3.021  37.1   0.333
       13+ yrs            5           3.954          3.051 38.83  0.2715

=== TIERS ===
RatingTier  instructors  mean_teacher_rating  total_enrollments  mean_enrollments  median_enrollments  mean_course_rating  mean_eir  median_eir  enrollment_share
       Low           20                2.024               1509             75.45                  61               3.159    0.5214      0.4379            0.1509
       Mid           20                3.263               1032              51.6                  44               3.167    0.3017      0.2359            0.1032
      High           20                4.088               7459             372.9                62.5               2.923     1.101      0.6603            0.7459

=== DOMAIN_PROFILE ===
               category  courses  instructors  mean_course_rating  course_rating_sd  course_rating_range  mean_instructor_rating  aligned_instructor_share  enrollment  fully_crossed
       Machine Learning        5           26               2.658             1.559                  3.6                   2.486                    0.1923         819          False
               Business        5           23               2.688            0.7285                 1.68                   3.904                   0.08696         833          False
        Web Development        5           25               2.846             1.289                 3.44                   3.234                       0.2         844          False
          Cybersecurity        5            9               2.902              1.49                 3.59                   3.469                         1         819           True
                Finance        5            8                3.01               1.1                 2.55                   3.643                      0.75         864          False
            Programming        5           41               3.036             1.327                 3.46                   2.743                   0.02439         806          False
Artificial Intelligence        5            8               3.036             1.241                 3.35                   3.574                      0.75         829           True
     Project Management        5            7               3.142             1.708                 3.61                   3.267                    0.7143         829           True
                 Design        5           24               3.162             1.292                 2.99                   3.227                    0.1667         827          False
           Data Science        5            7               3.316             0.504                 1.17                   3.529                    0.7143         916           True
      Digital Marketing        5           13               3.656             1.029                 2.52                   3.315                    0.8462         808          False
              Marketing        5           42               3.722             1.201                 2.78                   2.763                   0.02381         806          False

=== GENDER_LEVEL ===
CourseLevel  Advanced  Beginner  Intermediate
Gender                                       
Female           2.91     2.966         3.327
Male            2.973     3.152         3.496

=== BREAKPOINT ===
 breakpoint_years  slope_before  slope_after
                8        0.2115       0.0477

=== DEMAND CONCENTRATION ===
  gini_enrollments                     0.68098
  top2_share                           0.6086
  top2_names                           ['Yolanda Levine', 'Kimberly Miller']
  top2_ratings                         [4.97, 4.58]
  top2_courses_covered                 60
  top2_domain_aligned_share            0.15823200788695366
  rest_domain_aligned_share            0.8042922841083291
  top2_enrollments_per_delivery        55.32727272727273
  rest_enrollments_per_delivery        5.037323037323038
  rest_enrollments_per_delivery_median 2.0
  aggregate_eir                        0.9999999999999998
```
