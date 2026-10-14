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
