import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.components.kpis import render_kpi_grid
from streamlit_app.data import (
    ensure_data_artifacts,
    load_advanced_ml_metadata,
    load_category_metrics,
    load_marketplace_overview,
    load_ml_metadata,
    load_ml_scores,
    load_public_query_metrics,
)

EXECUTIVE_COLORS = {
    "background": "#0b111a",
    "surface": "#111827",
    "surface_alt": "#162235",
    "primary": "#8fb8d8",
    "secondary": "#7cc7a8",
    "accent": "#d6b25e",
    "risk": "#d97a84",
    "muted": "#a8b3c4",
    "text": "#eef3f8",
    "grid": "#2c394b",
}
COVERAGE_COLORS = {
    "Alta cobertura": "#8fb8d8",
    "Media cobertura": "#7cc7a8",
    "Baixa cobertura": "#d97a84",
}
COVERAGE_LABELS = {
    "high_coverage": "Alta cobertura",
    "medium_coverage": "Media cobertura",
    "low_coverage": "Baixa cobertura",
}
ANOMALY_COLORS = {False: "#8fb8d8", True: "#d97a84"}

st.set_page_config(
    page_title="Mercado Intelligence AI",
    page_icon="MI",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def cached_data():
    ensure_data_artifacts()
    return {
        "categories": load_category_metrics(),
        "overview": load_marketplace_overview(),
        "ml_scores": load_ml_scores(),
        "query_metrics": load_public_query_metrics(),
        "ml_metadata": load_ml_metadata(),
        "advanced_ml": load_advanced_ml_metadata(),
    }


def main() -> None:
    apply_executive_theme()
    try:
        with st.spinner("Preparando dados do dashboard..."):
            data = cached_data()
    except (RuntimeError, OSError, ValueError, KeyError, duckdb.Error, subprocess.CalledProcessError) as exc:
        st.error("Nao foi possivel preparar os dados do dashboard.")
        st.info(
            "No Streamlit Cloud, aguarde alguns instantes e reinicie o app. "
            "Se persistir, verifique os logs do bootstrap na tela Manage app."
        )
        st.exception(exc)
        return

    categories = data["categories"]
    overview = data["overview"]
    ml_scores = data["ml_scores"]

    st.title("Mercado Intelligence AI")
    st.caption("Dashboard executivo de inteligencia de mercado com dados publicos do Mercado Livre")

    tabs = st.tabs(
        [
            "Visao geral",
            "Categorias",
            "Oportunidades",
            "Aprendizado de maquina",
        ]
    )

    with tabs[0]:
        render_overview(overview, categories, ml_scores, data["query_metrics"])

    with tabs[1]:
        render_categories(categories)

    with tabs[2]:
        render_opportunities(ml_scores)

    with tabs[3]:
        render_ml(data["ml_metadata"], data["advanced_ml"], ml_scores)


def apply_executive_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --mi-bg: #0b111a;
            --mi-surface: #111827;
            --mi-surface-alt: #162235;
            --mi-border: #2c394b;
            --mi-text: #eef3f8;
            --mi-muted: #a8b3c4;
            --mi-accent: #d6b25e;
            --mi-accent-blue: #8fb8d8;
        }
        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(143, 184, 216, 0.10), transparent 32rem),
                radial-gradient(circle at 92% 4%, rgba(214, 178, 94, 0.08), transparent 28rem),
                linear-gradient(180deg, #0b111a 0%, #0d1520 48%, #0b111a 100%);
            color: var(--mi-text);
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        h1 {
            color: var(--mi-text);
            font-size: 2rem !important;
            font-weight: 720 !important;
            letter-spacing: 0 !important;
            margin-bottom: 0.15rem !important;
        }
        h2, h3 {
            color: var(--mi-text);
            letter-spacing: 0 !important;
        }
        h3 {
            font-size: 1.28rem !important;
            font-weight: 680 !important;
            margin-top: 1.4rem !important;
        }
        p, label, span {
            color: inherit;
        }
        div[data-testid="stCaptionContainer"] {
            color: var(--mi-muted);
            margin-bottom: 1rem;
        }
        div[data-testid="stTabs"] button {
            color: #d8e0ea;
            background: transparent;
            border-radius: 0;
            font-weight: 520;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #ffffff;
            border-bottom-color: var(--mi-accent);
        }
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 1.1rem;
            border-bottom: 1px solid var(--mi-border);
        }
        section[data-testid="stSidebar"] {
            background: #080d15;
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(22, 34, 53, 0.98), rgba(17, 24, 39, 0.98));
            border: 1px solid var(--mi-border);
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.26);
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--mi-muted);
            font-size: 0.86rem;
            font-weight: 520;
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: 650;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--mi-border);
            border-radius: 8px;
            overflow: hidden;
            background: var(--mi-surface);
        }
        div[data-baseweb="select"] > div {
            background-color: #eef3f8;
            border: 1px solid #cad5e2;
            border-radius: 8px;
            color: #172033;
            min-height: 48px;
        }
        div[data-baseweb="select"] span {
            color: #172033 !important;
            font-weight: 520;
        }
        span[data-baseweb="tag"] {
            background-color: #253247 !important;
            border: 1px solid #40516a !important;
            color: #f8fafc !important;
            border-radius: 6px !important;
        }
        span[data-baseweb="tag"] span {
            color: #f8fafc !important;
        }
        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"] {
            background-color: #ffffff;
            color: #172033;
        }
        .stAlert {
            background: var(--mi-surface-alt);
            border-color: var(--mi-border);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_overview(
    overview: pd.DataFrame,
    categories: pd.DataFrame,
    ml_scores: pd.DataFrame,
    query_metrics: pd.DataFrame,
) -> None:
    row = overview.iloc[0]
    render_kpi_grid(
        {
            "Categorias": int(row["total_categories"]),
            "Dominios": int(row["total_domains"]),
            "Itens mapeados": format_pt_int(int(row["total_items_in_categories"])),
            "Oportunidades": len(ml_scores),
            "Anomalias": int(ml_scores["is_anomaly"].sum()),
        }
    )

    col_left, col_right = st.columns([1.15, 0.85])
    with col_left:
        st.subheader("Tamanho de mercado por termo")
        query_frame = query_metrics.head(8).sort_values("total_items_in_categories")
        fig = px.bar(
            query_frame,
            x="total_items_in_categories",
            y="search_query",
            orientation="h",
            text=query_frame["total_items_in_categories"].map(format_compact),
            color="domain_count",
            color_continuous_scale=["#263247", EXECUTIVE_COLORS["primary"]],
            hover_data={
                "search_query": False,
                "total_items_in_categories": ":,",
                "category_count": True,
                "domain_count": True,
                "avg_catalog_coverage_score": ":.2f",
            },
        )
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        apply_chart_layout(fig, height=390, x_title="Itens mapeados", y_title="")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Top oportunidades")
        top_opportunities = ml_scores.nsmallest(8, "opportunity_rank")[
            ["opportunity_rank", "category_name", "opportunity_score", "is_anomaly"]
        ].copy()
        top_opportunities["opportunity_score"] = top_opportunities["opportunity_score"].round(2)
        top_opportunities = top_opportunities.rename(
            columns={
                "opportunity_rank": "Rank",
                "category_name": "Categoria",
                "opportunity_score": "Score",
                "is_anomaly": "Anomalia",
            }
        )
        st.dataframe(
            top_opportunities,
            use_container_width=True,
            hide_index=True,
        )


def render_categories(categories: pd.DataFrame) -> None:
    categories = categories.copy()
    categories["coverage_label"] = categories["coverage_band"].map(COVERAGE_LABELS).fillna(
        categories["coverage_band"]
    )
    coverage_filter = st.multiselect(
        "Cobertura",
        sorted(categories["coverage_label"].dropna().unique()),
        default=sorted(categories["coverage_label"].dropna().unique()),
    )
    filtered = categories[categories["coverage_label"].isin(coverage_filter)]

    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.subheader("Top categorias por itens")
        top_categories = filtered.nlargest(12, "total_items_in_this_category").sort_values(
            "total_items_in_this_category"
        )
        fig = px.bar(
            top_categories,
            x="total_items_in_this_category",
            y="category_name",
            orientation="h",
            color="coverage_label",
            text=top_categories["total_items_in_this_category"].map(format_compact),
            color_discrete_map=COVERAGE_COLORS,
            labels={
                "total_items_in_this_category": "Itens",
                "category_name": "Categoria",
                "coverage_label": "Cobertura",
            },
            hover_data={
                "category_name": False,
                "category_id": True,
                "domain_count": True,
                "catalog_coverage_score": ":.2f",
                "total_items_in_this_category": ":,",
                "coverage_label": False,
            },
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
            textfont={"color": EXECUTIVE_COLORS["text"], "size": 12},
        )
        apply_chart_layout(fig, height=500, x_title="Itens mapeados", y_title="")
        fig.update_layout(legend_title_text="Cobertura")
        fig.update_xaxes(tickformat="~s", showline=True, linecolor=EXECUTIVE_COLORS["grid"])
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Cobertura x profundidade")
        fig = px.scatter(
            filtered,
            x="category_depth",
            y="catalog_coverage_score",
            size="total_items_in_this_category",
            color="coverage_label",
            color_discrete_map=COVERAGE_COLORS,
            hover_name="category_name",
            hover_data={
                "category_id": True,
                "domain_count": True,
                "total_items_in_this_category": ":,",
                "coverage_label": False,
            },
        )
        apply_chart_layout(fig, height=500, x_title="Profundidade", y_title="Score de cobertura")
        fig.update_layout(legend_title_text="Cobertura")
        fig.update_traces(marker={"opacity": 0.92, "line": {"width": 1, "color": "#0b111a"}})
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        filtered[
            [
                "category_id",
                "category_name",
                "domain_count",
                "total_items_in_this_category",
                "catalog_coverage_score",
                "coverage_label",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_opportunities(ml_scores: pd.DataFrame) -> None:
    render_kpi_grid(
        {
            "Maior score": round(float(ml_scores["opportunity_score"].max()), 2),
            "Score medio": round(float(ml_scores["opportunity_score"].mean()), 2),
            "Categorias avaliadas": len(ml_scores),
        }
    )
    top_scores = ml_scores.sort_values("opportunity_score", ascending=False).head(15)
    top_scores = top_scores.sort_values("opportunity_score")
    fig = px.bar(
        top_scores,
        x="opportunity_score",
        y="category_name",
        orientation="h",
        color="is_anomaly",
        text=top_scores["opportunity_score"].round(1),
        color_discrete_map=ANOMALY_COLORS,
        hover_data={
            "category_name": False,
            "opportunity_rank": True,
            "anomaly_score": ":.2f",
            "anomaly_type": True,
        },
    )
    fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
    apply_chart_layout(fig, height=520, x_title="Opportunity Score", y_title="")
    fig.update_layout(legend_title_text="Anomalia")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        ml_scores[
            [
                "opportunity_rank",
                "category_id",
                "category_name",
                "opportunity_score",
                "anomaly_score",
                "anomaly_type",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_ml(metadata: dict, advanced_ml: dict, ml_scores: pd.DataFrame) -> None:
    st.subheader("Baseline")
    render_kpi_grid(
        {
            "Modelo": metadata["model_version"],
            "Linhas": metadata["metrics"]["output_rows"],
            "Anomalias": metadata["metrics"]["anomaly_count"],
        }
    )
    st.dataframe(pd.DataFrame({"features": metadata["features"]}), use_container_width=True, hide_index=True)

    st.subheader("Distribuicao dos scores")
    fig = px.histogram(
        ml_scores,
        x="opportunity_score",
        nbins=8,
        color="is_anomaly",
        color_discrete_map=ANOMALY_COLORS,
        labels={"is_anomaly": "Anomalia"},
    )
    apply_chart_layout(fig, height=360, x_title="Opportunity Score", y_title="Categorias")
    fig.update_layout(legend_title_text="Anomalia", bargap=0.05)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("ML avancado")
    readiness = advanced_ml["readiness"]
    st.dataframe(pd.DataFrame(readiness.values()), use_container_width=True, hide_index=True)


def apply_chart_layout(fig, height: int, x_title: str, y_title: str) -> None:
    fig.update_layout(
        height=height,
        margin={"l": 10, "r": 28, "t": 12, "b": 36},
        plot_bgcolor=EXECUTIVE_COLORS["surface"],
        paper_bgcolor=EXECUTIVE_COLORS["surface"],
        font={"family": "Arial", "size": 13, "color": EXECUTIVE_COLORS["text"]},
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"color": EXECUTIVE_COLORS["text"], "size": 12},
            "title": {"font": {"color": EXECUTIVE_COLORS["muted"]}},
        },
        hoverlabel={
            "bgcolor": EXECUTIVE_COLORS["surface_alt"],
            "bordercolor": EXECUTIVE_COLORS["grid"],
            "font_color": EXECUTIVE_COLORS["text"],
        },
    )
    fig.update_xaxes(
        gridcolor=EXECUTIVE_COLORS["grid"],
        zeroline=False,
        color=EXECUTIVE_COLORS["text"],
        title_font_color=EXECUTIVE_COLORS["primary"],
        tickfont={"color": EXECUTIVE_COLORS["muted"]},
        linecolor=EXECUTIVE_COLORS["grid"],
    )
    fig.update_yaxes(
        gridcolor=EXECUTIVE_COLORS["grid"],
        zeroline=False,
        color=EXECUTIVE_COLORS["text"],
        title_font_color=EXECUTIVE_COLORS["primary"],
        tickfont={"color": EXECUTIVE_COLORS["muted"]},
        linecolor=EXECUTIVE_COLORS["grid"],
    )


def format_pt_int(value: float) -> str:
    return f"{int(value):,}".replace(",", ".")


def format_compact(value: float) -> str:
    number = float(value)
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.1f}M".replace(".", ",")
    if abs(number) >= 1_000:
        return f"{number / 1_000:.0f} mil"
    return format_pt_int(number)


if __name__ == "__main__":
    main()
