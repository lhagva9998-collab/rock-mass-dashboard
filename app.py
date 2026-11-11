"""Streamlit dashboard for rock-mass evaluation with RMR89 and Barton Q.
Run: streamlit run app.py
"""
from datetime import datetime
from io import StringIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from rock_models import (
    APERTURE, GROUNDWATER, INFILL, JN_OPTIONS, JR_OPTIONS, JW_OPTIONS,
    ORIENTATIONS, ORIENTATION_PENALTIES, PERSISTENCE, ROUGHNESS,
    WEATHERING, RockInput, calculate,
)

st.set_page_config(
    page_title="Rock Mass Dashboard | RMR & Q",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.65rem; padding-bottom: 2rem;}
h1 {letter-spacing: -.035em;}
[data-testid="stMetric"] {
    border-radius: 14px; padding: 1rem 1.1rem;
    border: 1px solid rgba(128,128,128,.22);
    background: rgba(120,130,150,.06);
}
.small-muted {color:#77818e;font-size:.93rem;}
</style>
""", unsafe_allow_html=True)


def options_selector(label: str, options: list[tuple[str, float]], *, index: int = 0,
                     key: str | None = None, help_text: str | None = None) -> tuple[str, float]:
    """Keep label and numeric score together to avoid brittle string parsing."""
    selected = st.selectbox(
        label, options=range(len(options)), index=index, key=key,
        format_func=lambda i: options[i][0], help=help_text,
    )
    return options[selected]


def rmr_gauge(score: float):
    colors = ["#dc6b66", "#e9a957", "#e7cb70", "#83c59f", "#50b7a4"]
    ranges = [(0,20), (20,40), (40,60), (60,80), (80,100)]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=max(0, min(100, score)),
        number={"font": {"size": 34}},
        gauge={
            "axis": {"range": [0, 100], "tickvals": [0,20,40,60,80,100]},
            "bar": {"color": "#334155", "thickness": 0.19},
            "steps": [{"range": [a,b], "color": c} for (a,b), c in zip(ranges, colors)],
            "threshold": {"line": {"color": "#17212e", "width": 4}, "value": max(0,min(100,score))},
        },
    ))
    fig.update_layout(margin=dict(t=40, b=10, l=28, r=28), height=260,
                      paper_bgcolor="rgba(0,0,0,0)", font={"size": 13})
    return fig


def q_log_chart(q: float):
    bands = [
        (0.001, .01, "#ad5555"), (.01, .1, "#d47f63"),
        (.1, 1, "#e0a16b"), (1, 4, "#e7b667"),
        (4, 10, "#decf82"), (10, 40, "#9dcb99"),
        (40, 100, "#70bc9d"), (100, 400, "#59b9b0"),
        (400, 1000, "#459dba"),
    ]
    display_q = max(.001, min(1000, q))
    fig = go.Figure()
    for lower, upper, color in bands:
        fig.add_vrect(x0=lower, x1=upper, fillcolor=color, opacity=.65,
                      line_width=0, layer="below")
    fig.add_trace(go.Scatter(
        x=[display_q], y=[.5], mode="markers+text",
        marker={"symbol": "diamond", "size": 19, "color": "#1d2939", "line": {"width":2, "color":"white"}},
        text=[f"Q = {q:.3g}"], textposition="top center",
        hovertemplate="Q = %{text}<extra></extra>", showlegend=False,
    ))
    fig.update_layout(
        xaxis={"type":"log", "range":[-3,3], "tickvals":[.001,.01,.1,1,4,10,40,100,400,1000],
               "ticktext":["0.001","0.01","0.1","1","4","10","40","100","400","1000"],
               "title":"Q (логарифм хуваарь)", "showgrid":False},
        yaxis={"range":[0,1], "visible":False},
        margin=dict(t=37, l=10, r=10, b=48), height=210,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def rmr_waterfall(result: dict):
    labels = list(result["rmr_parts"].keys()) + ["Чиглэлийн засвар", "Эцсийн RMR"]
    numbers = list(result["rmr_parts"].values()) + [result["rmr_orientation"], 0]
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=["relative"]*6 + ["total"],
        x=labels, y=numbers, textposition="outside",
        text=[str(n) if i < 6 else str(result["rmr"]) for i,n in enumerate(numbers)],
        connector={"line":{"color":"#9daabd"}},
        increasing={"marker":{"color":"#4bba9c"}},
        decreasing={"marker":{"color":"#e88b78"}},
        totals={"marker":{"color":"#668aca"}},
    ))
    fig.update_layout(
        title="RMR онооны бүрдэл", showlegend=False,
        margin=dict(l=20,r=20,t=42,b=20), height=345,
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis={"tickangle":-20},
        yaxis={"title":"Оноо", "zeroline":True},
    )
    return fig


st.title("⛰️ Уулын цулын үнэлгээний Dashboard")
st.caption("Bieniawski RMR89 + Barton Q-system  |  Сургалтын зориулалттай Python / Streamlit төсөл")

with st.sidebar:
    st.header("🧭 Үнэлгээний өгөгдөл")
    place = st.text_input("Талбай / уурхайн нэр", value="Жишээ талбай", help="Үнэлгээ хийж буй уурхайн талбай")
    section = st.text_input("Хэмжилтийн цэг", value="Цэг-01")
    st.subheader("Нийтлэг хэмжилт")
    ucs = st.number_input("UCS — шахалтын бат бэх (MPa)", min_value=0.0, max_value=2000.0,
                          value=75.0, step=5.0, help="Нэг тэнхлэгийн шахалтын туршилтын үр дүн")
    rqd = st.number_input("RQD (%)", min_value=0.0, max_value=100.0,
                          value=70.0, step=1.0, help="10 см-ээс урт эрүүл керний нийлбэр / нийт керний урт × 100%")
    spacing = st.number_input("Ан цавын зай (м)", min_value=0.0, max_value=100.0,
                              value=0.40, step=0.05, format="%.2f")

    with st.expander("RMR — ан цавын төлөв", expanded=True):
        persistence = options_selector("Үргэлжлэх урт (persistence)", PERSISTENCE, index=2)[1]
        aperture = options_selector("Ангайлт (aperture)", APERTURE, index=1)[1]
        roughness = options_selector("Барзгаршил (roughness)", ROUGHNESS, index=2)[1]
        infill = options_selector("Дүүргэгч (infilling)", INFILL, index=0)[1]
        weathering = options_selector("Өгөршил (weathering)", WEATHERING, index=2)[1]

    groundwater = options_selector("RMR — усжилтын төлөв", GROUNDWATER, index=1)[1]
    structure = st.selectbox("RMR — хэрэглээний төрөл", list(ORIENTATION_PENALTIES.keys()), index=0)
    orientation_i = st.selectbox(
        "RMR — ан цавын чиглэлийн нөлөө", range(len(ORIENTATIONS)), index=2,
        format_func=lambda i: ORIENTATIONS[i],
        help="Тухайн малталт/налуу ба ан цавын орон зайн хамаарлаар геологич/инженер сонгоно.",
    )

    with st.expander("Q-system — коэффициентууд", expanded=True):
        jn_label, jn = options_selector("Jn — ан цавын системийн тоо", JN_OPTIONS, index=5)
        jr_label, jr = options_selector("Jr — ан цавын барзгаршил", JR_OPTIONS, index=2)
        ja = st.number_input(
            "Ja — ан цавын өөрчлөлт / дүүргэгч", min_value=0.01,
            max_value=50.0, value=2.0, step=0.25, format="%.2f",
            help="Ан цавын шаварлаг дүүргэгч, хувирлыг NGI-ийн Ja хүснэгтээс сонгоно (олон нөхцөлд 0.75–20).",
        )
        jw_label, jw = options_selector("Jw — усны бууралтын коэффициент", JW_OPTIONS, index=1)
        srf = st.number_input(
            "SRF — хүчдэлийн бууралтын коэффициент", min_value=0.01,
            max_value=1000.0, value=2.5, step=0.5, format="%.2f",
            help="SRF нь сул бүс, хүчдэл, шахалт/хөөлтийн нөхцөлөөс хамаардаг; NGI-ийн тусгай хүснэгтээр тодорхойлно.",
        )
    st.info("Дэлгэц дээрх эхний утгууд нь зөвхөн **жишээ**. Бодит талбайн хэмжилт гэж үзэж болохгүй.")

values = RockInput(
    ucs_mpa=ucs, rqd_percent=rqd, spacing_m=spacing,
    persistence=persistence, aperture=aperture, roughness=roughness,
    infill=infill, weathering=weathering, groundwater=groundwater,
    structure=structure, orientation_index=orientation_i,
    jn=jn, jr=jr, ja=ja, jw=jw, srf=srf,
)
result = calculate(values)

st.markdown("### 📍 Одоогийн талбай")
st.write(f"**{place}** · {section} · {structure}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("RMR89", f'{result["rmr"]}', help="Оноо, чиглэлийн засварыг багтаасан")
col2.metric("RMR ангилал", f'{result["rmr_class"]} — {result["rmr_quality"]}')
col3.metric("Barton Q", f'{result["q"]:.3f}')
col4.metric("Q ангилал", result["q_quality"])

if rqd < 10:
    st.warning(f"RQD = {rqd:g}% боловч Q-system-д стандартын дагуу тооцооны RQD = 10% гэж хэрэглэв. RMR нь жинхэнэ {rqd:g}%-ийг ашигласан.")
if result["rmr"] < 0:
    st.warning("Чиглэлийн их хасалтын улмаас RMR сөрөг гарсан. Тоон үр дүнг хэвээр үлдээж, хэмжүүрийн графикт 0 дээр хязгаарлав.")
if result["q"] < .001 or result["q"] > 1000:
    st.warning("Q нь уламжлалт 0.001–1000 ангиллын хязгаараас гарсан. Графикийн тэмдэглэгээг хязгаарын ирмэгт байрлуулав.")

if "saved_records" not in st.session_state:
    st.session_state.saved_records = []

if st.button("＋ Энэ цэгийн үнэлгээг жагсаалтад хадгалах", type="primary"):
    record = {
        "Огноо": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Талбай": place, "Цэг": section, "Хэрэглээ": structure,
        "UCS (MPa)": ucs, "RQD (%)": rqd, "Ан цавын зай (м)": spacing,
        "Persistence оноо": persistence, "Aperture оноо": aperture,
        "Roughness оноо": roughness, "Infilling оноо": infill,
        "Weathering оноо": weathering, "Groundwater оноо": groundwater,
        "RMR чиглэлийн нөхцөл": ORIENTATIONS[orientation_i],
        "RMR үндсэн": result["rmr_basic"], "RMR чиглэлийн засвар": result["rmr_orientation"],
        "RMR": result["rmr"], "RMR ангилал": result["rmr_class"],
        "Jn": jn, "Jr": jr, "Ja": ja, "Jw": jw, "SRF": srf,
        "Q тооцооны RQD (%)": result["q_rqd"],
        "Q": round(result["q"], 6), "Q ангилал": result["q_quality"],
    }
    st.session_state.saved_records.append(record)
    st.success(f"{section} цэгийн үнэлгээг хадгаллаа (энэ browser session-д).")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Үнэлгээ", "🧮 Тооцооны задаргаа", "🗂️ Цэгүүд ба CSV", "📚 Аргачлал",
])

with tab1:
    left, right = st.columns(2)
    with left:
        st.markdown("#### RMR89 — 0–100 онооны хэмжүүр")
        st.plotly_chart(rmr_gauge(result["rmr"]), use_container_width=True)
        st.caption("I: 81–100 · II: 61–80 · III: 41–60 · IV: 21–40 · V: ≤ 20")
    with right:
        st.markdown("#### Barton Q — логарифм хуваарь")
        st.plotly_chart(q_log_chart(result["q"]), use_container_width=True)
        st.caption("Үнэлгээний зааг: 0.001, 0.01, 0.1, 1, 4, 10, 40, 100, 400, 1000")
    st.info("**Тайлбар:** Q ба RMR нь ижил хэмжээсийн тоонууд биш. Зэрэгцүүлсэн график нь хоёр аргын үр дүнг харуулах боловч шууд тоон харьцуулалт биш.")

with tab2:
    left, right = st.columns([1.2, 1])
    with left:
        st.plotly_chart(rmr_waterfall(result), use_container_width=True)
    with right:
        st.markdown("#### RMR тооцоо")
        rmr_df = pd.DataFrame([
            {"Үзүүлэлт": k, "Оноо": v} for k,v in result["rmr_parts"].items()
        ] + [
            {"Үзүүлэлт": "Үндсэн RMR", "Оноо": result["rmr_basic"]},
            {"Үзүүлэлт": "Чиглэлийн засвар", "Оноо": result["rmr_orientation"]},
            {"Үзүүлэлт": "Нийт RMR", "Оноо": result["rmr"]},
        ])
        st.dataframe(rmr_df, hide_index=True, use_container_width=True)
        st.latex(r"RMR = R_{UCS}+R_{RQD}+R_{spacing}+R_{condition}+R_{water}+R_{orientation}")
    st.divider()
    st.markdown("#### Barton Q — үржигдэхүүн тус бүр")
    q_cols = st.columns(3)
    q_cols[0].metric("RQD / Jn", f'{result["q_block"]:.3f}')
    q_cols[1].metric("Jr / Ja", f'{result["q_shear"]:.3f}')
    q_cols[2].metric("Jw / SRF", f'{result["q_stress"]:.3f}')
    st.latex(r"Q=\left(\frac{RQD}{J_n}\right)\left(\frac{J_r}{J_a}\right)\left(\frac{J_w}{SRF}\right)")
    st.code(
        f'Q = ({result["q_rqd"]:g}/{jn:g}) × ({jr:g}/{ja:g}) × ({jw:g}/{srf:g}) '
        f'= {result["q"]:.4f}', language="text",
    )
    st.caption("Анхаар: RMR-ийн усжилтын оноо болон Q-ийн Jw нь өөр хүснэгтээр сонгогддог.")

with tab3:
    st.markdown("#### Үнэлгээний бүртгэл")
    if st.session_state.saved_records:
        df = pd.DataFrame(st.session_state.saved_records)
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ CSV тайлан татах", data=csv_bytes, file_name="rock_mass_assessment.csv",
            mime="text/csv", type="primary",
        )
        chart_df = df.copy()
        chart_df["Шошго"] = chart_df["Талбай"] + " / " + chart_df["Цэг"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Цэгүүдийн RMR**")
            st.bar_chart(chart_df.set_index("Шошго")["RMR"])
        with c2:
            st.markdown("**Цэгүүдийн Q**")
            positive_df = chart_df[chart_df["Q"] > 0]
            fig = go.Figure(go.Bar(x=positive_df["Шошго"], y=positive_df["Q"],
                                   marker_color="#55b29c"))
            fig.update_yaxes(type="log", title="Q (логарифм)")
            fig.update_layout(height=320, margin=dict(t=12,l=25,r=10,b=60),
                              paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        if st.button("🗑️ Бүртгэлийг цэвэрлэх"):
            st.session_state.saved_records = []
            st.rerun()
    else:
        st.info("Эхлээд 'Энэ цэгийн үнэлгээг жагсаалтад хадгалах' товчийг дарна уу.")
    st.caption("Хадгалалт нь зөвхөн нээлттэй browser session-д байна. Удаан хадгалах бол CSV татна уу.")

with tab4:
    st.markdown("""
#### RMR89
- **UCS:** нэг тэнхлэгийн шахалтын бат бэх, MPa (0–15 оноо)
- **RQD:** керний чанарын индекс, % (3–20 оноо)
- **Ан цавын зай:** м (5–20 оноо)
- **Ан цавын төлөв:** үргэлжлэх урт + ангайлт + барзгаршил + дүүргэгч + өгөршил (0–30 оноо)
- **Усжилт:** хуурай / чийгтэй / нойтон / дусалдаг / урсдаг (0–15 оноо)
- **Чиглэл:** малталтын төрөл, ан цавын чиглэлээс хамаарах *хасах засвар*

#### Barton Q-system
- **RQD:** нэгдмэл индекс; Q-ийн тооцоонд RQD < 10 байвал 10 гэж авна.
- **Jn:** ан цавын системийн тоо
- **Jr:** ан цавын гадаргуугийн барзгаршлын коэффициент
- **Ja:** ан цавын өөрчлөлт, дүүргэгчийн коэффициент
- **Jw:** усны нөлөөний коэффициент
- **SRF:** хүчдэл, сул бүсийн нөлөөний коэффициент

**Чухал:** Q-ийг гол төлөв хонгил, далд малталтын нөхцөлд боловсруулсан.
RMR/Q үнэлгээ нь хажуугийн тогтворжилтын **FoS**, бэхэлгээний дэлгэрэнгүй тооцоог орлохгүй.
Бэхэлгээ сонгохдоо малталтын хэмжээ, ESR болон бусад нөхцөл шаардлагатай.

#### Ашигласан эх сурвалж
1. Bieniawski, Z. T. (1989). *Engineering Rock Mass Classifications.* Wiley.
2. Barton, N., Lien, R., & Lunde, J. (1974). Engineering classification of rock masses for the design of tunnel support. *Rock Mechanics*, 6, 189–236.
3. Norwegian Geotechnical Institute (NGI). *Using the Q-system: Rock mass classification and support design* (handbook).
4. [RMR 1989 үнэлгээний хүснэгт](https://docs.geoassistant.org/core_elements/geo_parameters/classification_systems/rmrb)
5. [NGI — Tunnels and the Q-system](https://www.ngi.no/en/research-and-consulting/infrastructure-container/tunnels-and-the-q-system/)
""")
