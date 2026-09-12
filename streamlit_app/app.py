import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app.components.kpis import render_kpi_grid
from streamlit_app.data import (
    load_advanced_ml_metadata,
    load_category_metrics,
    load_marketplace_overview,
    load_ml_metadata,
    load_ml_scores,
    load_public_query_metrics,
)

EXECUTIVE_COLORS = {
    "primary": "#1f4e79",
    "secondary": "#2a9d8f",
    "accent": "#f4a261",
    "risk": "#c1121f",
    "muted": "#6b7280",
    "grid": "#e5e7eb",
}
COVERAGE_COLORS = {
    "high_coverage": "#1f4e79",
    "medium_coverage": "#2a9d8f",
    "low_coverage": "#c1121f",
}
ANOMALY_COLORS = {False: "#1f4e79", True: "#c1121f"}

st.set_page_config(
    page_title="Mercado Intelligence AI",
    page_icon="MI",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def cached_data():
    return {
        "categories": load_category_metrics(),
        "overview": load_marketplace_overview(),
        "ml_scores": load_ml_scores(),
        "query_metrics": load_public_query_metrics(),
        "ml_metadata": load_ml_metadata(),
        "advanced_ml": load_advanced_ml_metadata(),
    }


def main() -> None:
    data = cached_data()
    categories = data["categories"]
    overview = data["overview"]
    ml_scores = data["ml_scores"]

    apply_executive_theme()
    st.title("Mercado Intelligence AI")

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
        .block-container {padding-top: 1.4rem;}
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetricLabel"] p {
            color: #475569;
            font-size: 0.86rem;
        }
        div[data-testid="stMetricValue"] {
            color: #111827;
            font-size: 1.85rem;
            font-weight: 650;
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
            color_continuous_scale=["#dbeafe", EXECUTIVE_COLORS["primary"]],
            hover_data={
                "search_query": False,
                "total_items_in_categories": ":,",
                "category_count": True,
                "domain_count": True,
                "avg_catalog_coverage_score": ":.2f",
            },
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
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
    coverage_filter = st.multiselect(
        "Coverage band",
        sorted(categories["coverage_band"].dropna().unique()),
        default=sorted(categories["coverage_band"].dropna().unique()),
    )
    filtered = categories[categories["coverage_band"].isin(coverage_filter)]

    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.subheader("Top categorias por itens")
        top_categories = filtered.nlargest(15, "total_items_in_this_category").sort_values(
            "total_items_in_this_category"
        )
        fig = px.bar(
            top_categories,
            x="total_items_in_this_category",
            y="category_name",
            orientation="h",
            color="coverage_band",
            text=top_categories["total_items_in_this_category"].map(format_compact),
            color_discrete_map=COVERAGE_COLORS,
            hover_data={
                "category_name": False,
                "category_id": True,
                "domain_count": True,
                "catalog_coverage_score": ":.2f",
                "total_items_in_this_category": ":,",
            },
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        apply_chart_layout(fig, height=520, x_title="Itens", y_title="")
        fig.update_layout(legend_title_text="Cobertura")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Cobertura x profundidade")
        fig = px.scatter(
            filtered,
            x="category_depth",
            y="catalog_coverage_score",
            size="total_items_in_this_category",
            color="coverage_band",
            color_discrete_map=COVERAGE_COLORS,
            hover_name="category_name",
            hover_data={
                "category_id": True,
                "domain_count": True,
                "total_items_in_this_category": ":,",
                "coverage_band": False,
            },
        )
        apply_chart_layout(fig, height=520, x_title="Profundidade", y_title="Coverage score")
        fig.update_layout(legend_title_text="Cobertura")
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        filtered[
            [
                "category_id",
                "category_name",
                "domain_count",
                "total_items_in_this_category",
                "catalog_coverage_score",
                "coverage_band",
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
    fig.update_traces(textposition="outside", cliponaxis=False)
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
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font={"family": "Arial", "size": 13, "color": "#334155"},
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    fig.update_xaxes(gridcolor=EXECUTIVE_COLORS["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=EXECUTIVE_COLORS["grid"], zeroline=False)


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
