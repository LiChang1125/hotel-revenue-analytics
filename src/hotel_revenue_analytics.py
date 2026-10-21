"""Core analytics from the 2024 GHR revenue-management competition project.

The original work was completed in notebooks.  This module keeps the same
business logic in reusable, testable functions for a portfolio-ready release.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


@dataclass(frozen=True)
class BacktestResult:
    baseline_revenue: float
    upgrade_strategy_revenue: float
    cancellation_strategy_revenue: float
    combined_strategy_revenue: float
    upgrade_loss_reduction: float
    cancellation_loss_reduction: float
    paired_t_statistic: float
    paired_p_value: float


def add_revenue_metrics(bookings: pd.DataFrame, weekly_adr: pd.DataFrame) -> pd.DataFrame:
    """Wrangle booking records and calculate the three revenue components."""
    data = bookings.copy()
    data["ArrivalDate"] = pd.to_datetime(data["ArrivalDate"])
    data["ReservationStatusDate"] = pd.to_datetime(data["ReservationStatusDate"])
    data["Nights"] = data["StaysInWeekendNights"] + data["StaysInWeekNights"]
    data["RevenuebyStays"] = data["Nights"] * data["AverageDailyRate"]

    assigned_adr = weekly_adr.rename(columns={"ReservedRoom": "AssignedRoom", "ADR": "AssignedADR"})
    data = data.merge(assigned_adr, on=["ArrivalWeekNumber", "AssignedRoom"], how="left")
    upgraded = (data["ReservedRoom"] != data["AssignedRoom"]) & data["ReservationStatus"].eq("Check-Out")
    opportunity_cost = (data["AssignedADR"] - data["AverageDailyRate"]) * data["Nights"]
    data["RevenueLossbyUpgrade"] = np.where(upgraded, opportunity_cost.clip(lower=0), 0)

    days_before_arrival = (data["ArrivalDate"] - data["ReservationStatusDate"]).dt.days
    last_minute = data["ReservationStatus"].eq("Canceled") & days_before_arrival.between(0, 3)
    cancellation_cost = data["AverageDailyRate"] * (data["Nights"] - 1).clip(lower=0)
    data["RevenueLossbyCancel"] = np.where(last_minute, cancellation_cost, 0)
    data["PotentialRevenue"] = (
        data["RevenuebyStays"] - data["RevenueLossbyUpgrade"] - data["RevenueLossbyCancel"]
    )
    return data


def fit_probability_model(
    data: pd.DataFrame,
    features: list[str],
    target: str,
    random_state: int = 42,
) -> tuple[Pipeline, dict]:
    """Fit an out-of-sample Random Forest probability model and report metrics."""
    x, y = data[features], data[target]
    categorical = x.select_dtypes(include=["object", "category"]).columns.tolist()
    numeric = [column for column in features if column not in categorical]
    preprocessing = ColumnTransformer(
        [("category", OneHotEncoder(handle_unknown="ignore"), categorical),
         ("numeric", "passthrough", numeric)]
    )
    model = Pipeline([
        ("preprocessing", preprocessing),
        ("classifier", RandomForestClassifier(
            n_estimators=400, min_samples_leaf=3, class_weight="balanced_subsample",
            random_state=random_state, n_jobs=-1,
        )),
    ])
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.20, stratify=y, random_state=random_state
    )
    model.fit(x_train, y_train)
    report = classification_report(y_test, model.predict(x_test), output_dict=True)
    return model, report


def calculate_upgrade_premium(
    assignment_probabilities: np.ndarray,
    upgrade_loss_matrix: np.ndarray,
    nights: pd.Series,
) -> pd.Series:
    """Convert predicted room-assignment probabilities into a nightly premium."""
    expected_loss = np.einsum("ij,ij->i", assignment_probabilities, upgrade_loss_matrix)
    return pd.Series(expected_loss / nights.replace(0, np.nan)).fillna(0).clip(lower=0)


def calculate_cancellation_premium(
    cancellation_probability: np.ndarray,
    bookings: pd.DataFrame,
) -> pd.Series:
    """Price the expected last-minute cancellation loss per booked night."""
    nights = bookings["Nights"]
    loss_if_cancelled = (nights - 1).clip(lower=0) * bookings["AverageDailyRate"]
    expected_loss = cancellation_probability * loss_if_cancelled
    return (expected_loss / nights.replace(0, np.nan)).fillna(0).clip(lower=0)


def backtest_premiums(
    data: pd.DataFrame,
    upgrade_premium: pd.Series,
    cancellation_premium: pd.Series,
) -> tuple[pd.DataFrame, BacktestResult]:
    """Back-test the two refundable premiums on historical bookings."""
    tested = data.copy()
    upgrade_recovery = (upgrade_premium * tested["Nights"]).clip(
        upper=tested["RevenueLossbyUpgrade"]
    )
    cancellation_recovery = (cancellation_premium * tested["Nights"]).clip(
        upper=tested["RevenueLossbyCancel"]
    )
    tested["RevenueWithUpgradeStrategy"] = tested["PotentialRevenue"] + upgrade_recovery
    tested["RevenueWithCancellationStrategy"] = tested["PotentialRevenue"] + cancellation_recovery
    tested["RevenueWithBothStrategies"] = (
        tested["PotentialRevenue"] + upgrade_recovery + cancellation_recovery
    )
    test = ttest_rel(tested["RevenueWithBothStrategies"], tested["PotentialRevenue"], alternative="greater")
    result = BacktestResult(
        baseline_revenue=tested["PotentialRevenue"].sum(),
        upgrade_strategy_revenue=tested["RevenueWithUpgradeStrategy"].sum(),
        cancellation_strategy_revenue=tested["RevenueWithCancellationStrategy"].sum(),
        combined_strategy_revenue=tested["RevenueWithBothStrategies"].sum(),
        upgrade_loss_reduction=float(upgrade_recovery.sum()),
        cancellation_loss_reduction=float(cancellation_recovery.sum()),
        paired_t_statistic=float(test.statistic),
        paired_p_value=float(test.pvalue),
    )
    return tested, result


def plot_weekly_revenue(data: pd.DataFrame, output_path: str) -> None:
    """Visualize weekly baseline revenue and losses."""
    weekly = data.groupby("ArrivalWeekNumber", observed=True)[
        ["RevenueLossbyUpgrade", "RevenueLossbyCancel", "PotentialRevenue"]
    ].sum()
    ax = weekly.div(1_000).plot.area(figsize=(12, 4), alpha=0.65)
    ax.set(title="Weekly revenue decomposition", xlabel="Arrival week", ylabel="EUR thousands")
    ax.spines[["top", "right"]].set_visible(False)
    ax.figure.tight_layout()
    ax.figure.savefig(output_path, dpi=180, transparent=True)

