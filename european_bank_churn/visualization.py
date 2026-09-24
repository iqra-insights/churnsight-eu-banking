"""Plotly chart builders kept separate from the Streamlit interface."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Shared brand palette — matches the dashboard's dark theme and the project's
# presentation deck, so every chart, card, and slide feels like one product.
BRAND_BG = "#0B0E14"
BRAND_GRID = "#2A2E38"
BRAND_TEXT = "#F5F6F8"
BRAND_MUTED = "#9CA3AF"
BRAND_FONT = "Segoe UI, Calibri, sans-serif"


def _apply_brand_layout(figure: go.Figure, title: str) -> go.Figure:
    """Apply the shared dark, transparent styling used across every chart."""
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": BRAND_FONT, "color": BRAND_TEXT, "size": 13},
        title={"text": f"<b>{title}</b>", "font": {"size": 16, "color": BRAND_TEXT}},
        margin={"t": 56, "b": 40, "l": 50, "r": 24},
        hoverlabel={"bgcolor": "#171B23", "font_size": 12, "font_family": BRAND_FONT},
    )
    figure.update_xaxes(showgrid=False, linecolor=BRAND_GRID, tickfont={"color": BRAND_MUTED})
    figure.update_yaxes(
        gridcolor=BRAND_GRID, zerolinecolor=BRAND_GRID, tickfont={"color": BRAND_MUTED}
    )
    return figure


def churn_bar(summary: pd.DataFrame, dimension: str, title: str) -> go.Figure:
    """Build a segment churn-rate bar chart with customer counts in tooltips."""
    chart_data = summary.copy()
    chart_data[dimension] = chart_data[dimension].astype(str)
    figure = px.bar(
        chart_data,
        x=dimension,
        y="ChurnRate",
        color="ChurnRate",
        color_continuous_scale=["#FFF3E8", "#FF6B6B", "#8B1A1A"],
        text=chart_data["ChurnRate"].map(lambda value: f"{value:.1%}"),
        hover_data={"Customers": ":,", "Churners": ":,", "ChurnContribution": ":.1%"},
        title=title,
    )
    figure.update_traces(
        textposition="outside",
        textfont={"color": BRAND_TEXT, "size": 12},
        marker_line_width=0,
    )
    figure.update_yaxes(tickformat=".0%", title="Churn rate")
    upper_bound = max(0.05, float(chart_data["ChurnRate"].max()) * 1.18)
    figure.update_layout(coloraxis_showscale=False, yaxis_range=[0, upper_bound])
    return _apply_brand_layout(figure, title)


def geography_age_heatmap(matrix: pd.DataFrame) -> go.Figure:
    """Build a geography-by-age churn-rate heatmap."""
    labels = matrix.map(lambda value: "" if pd.isna(value) else f"{value:.1%}")
    figure = go.Figure(
        data=go.Heatmap(
            z=matrix.to_numpy(),
            x=matrix.columns.astype(str),
            y=matrix.index.astype(str),
            text=labels.to_numpy(),
            texttemplate="%{text}",
            colorscale=[[0, "#171B23"], [0.5, "#FF6B6B"], [1, "#8B1A1A"]],
            colorbar={"title": "Churn rate", "tickformat": ".0%"},
            hovertemplate="Geography=%{y}<br>Age=%{x}<br>Churn=%{z:.1%}<extra></extra>",
        )
    )
    figure.update_layout(
        title="Geography × age interaction",
        xaxis_title="Age group",
        yaxis_title="Geography",
    )
    return _apply_brand_layout(figure, "Geography × age interaction")


def confusion_matrix_figure(matrix) -> go.Figure:
    """Build a labeled binary-classification confusion matrix."""
    figure = px.imshow(
        matrix,
        text_auto=True,
        labels={"x": "Predicted", "y": "Actual", "color": "Customers"},
        x=["Retained", "Churned"],
        y=["Retained", "Churned"],
        title="Confusion matrix",
        color_continuous_scale=["#171B23", "#FF6B6B", "#8B1A1A"],
    )
    return _apply_brand_layout(figure, "Confusion matrix")


def feature_importance_figure(importances: pd.DataFrame) -> go.Figure:
    """Build a horizontal Random Forest feature-importance chart."""
    top_features = importances.head(15).sort_values("Importance")
    figure = px.bar(
        top_features,
        x="Importance",
        y="Feature",
        orientation="h",
        title="Random Forest feature importance",
        color_discrete_sequence=["#FF6B6B"],
    )
    return _apply_brand_layout(figure, "Random Forest feature importance")


def permutation_importance_figure(importances: pd.DataFrame) -> go.Figure:
    """Show holdout permutation importance using PR-AUC degradation."""
    top_features = importances.head(15).sort_values("ImportanceMean")
    figure = px.bar(
        top_features,
        x="ImportanceMean",
        y="Feature",
        error_x="ImportanceStd",
        orientation="h",
        title="Holdout permutation importance (PR-AUC decrease)",
        color_discrete_sequence=["#FF6B6B"],
    )
    figure.update_xaxes(title="Mean PR-AUC decrease when shuffled")
    return _apply_brand_layout(figure, "Holdout permutation importance (PR-AUC decrease)")


def logistic_coefficient_figure(coefficients: pd.DataFrame) -> go.Figure:
    """Show the strongest positive and negative logistic coefficients."""
    strongest = coefficients.head(15).sort_values("Coefficient")
    figure = px.bar(
        strongest,
        x="Coefficient",
        y="Feature",
        color="Direction",
        orientation="h",
        color_discrete_map={
            "Higher predicted churn": "#D62728",
            "Lower predicted churn": "#2CA02C",
        },
        title="Logistic Regression direction of association",
    )
    figure.update_xaxes(title="Standardized log-odds coefficient")
    return _apply_brand_layout(figure, "Logistic Regression direction of association")


def calibration_figure(curves: dict[str, pd.DataFrame]) -> go.Figure:
    """Compare predicted churn probability with observed churn frequency."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect calibration",
            line={"color": "#777777", "dash": "dash"},
        )
    )
    for model_name, table in curves.items():
        figure.add_trace(
            go.Scatter(
                x=table["MeanPredictedProbability"],
                y=table["ObservedChurnRate"],
                mode="lines+markers",
                name=model_name,
            )
        )
    figure.update_layout(
        title="Probability calibration on the holdout set",
        xaxis_title="Mean predicted churn probability",
        yaxis_title="Observed churn rate",
        xaxis={"tickformat": ".0%", "range": [0, 1]},
        yaxis={"tickformat": ".0%", "range": [0, 1]},
    )
    return _apply_brand_layout(figure, "Probability calibration on the holdout set")


def salary_balance_scatter(df: pd.DataFrame) -> go.Figure:
    """Compare salary and balance while making churn and geography visible."""
    chart_data = df.copy()
    chart_data["Churn status"] = chart_data["Exited"].map(
        {0: "Retained", 1: "Churned"}
    )
    figure = px.scatter(
        chart_data,
        x="EstimatedSalary",
        y="Balance",
        color="Churn status",
        symbol="Geography",
        opacity=0.55,
        color_discrete_map={"Retained": "#8AB4F8", "Churned": "#FF6B6B"},
        hover_data={
            "CustomerId": True,
            "Age": True,
            "NumOfProducts": True,
            "EstimatedSalary": ":,.2f",
            "Balance": ":,.2f",
        },
        title="Salary and balance profile by churn status",
    )
    figure.update_xaxes(title="Estimated salary")
    figure.update_yaxes(title="Account balance")
    return _apply_brand_layout(figure, "Salary and balance profile by churn status")
