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
