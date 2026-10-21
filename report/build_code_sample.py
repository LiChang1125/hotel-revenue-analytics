from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = Path(__file__).with_name("Li_Chang_Python_Code_Sample.pdf")

NAVY = HexColor("#14253D")
BLUE = HexColor("#2E6F9E")
TEAL = HexColor("#388A82")
GOLD = HexColor("#D5A13C")
INK = HexColor("#1D2733")
MUTED = HexColor("#667482")
PALE = HexColor("#F2F5F7")
GRID = HexColor("#D8E0E6")
WHITE = colors.white


CODE = '''"""Core functions from a hotel revenue-management project."""
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def add_revenue_metrics(bookings: pd.DataFrame,
                        weekly_adr: pd.DataFrame) -> pd.DataFrame:
    """Wrangle bookings and calculate revenue and opportunity costs."""
    data = bookings.copy()
    data["ArrivalDate"] = pd.to_datetime(data["ArrivalDate"])
    data["ReservationStatusDate"] = pd.to_datetime(data["ReservationStatusDate"])
    data["Nights"] = data.StaysInWeekendNights + data.StaysInWeekNights
    data["RevenuebyStays"] = data.Nights * data.AverageDailyRate

    assigned_adr = weekly_adr.rename(
        columns={"ReservedRoom": "AssignedRoom", "ADR": "AssignedADR"})
    data = data.merge(assigned_adr,
                      on=["ArrivalWeekNumber", "AssignedRoom"], how="left")
    upgraded = ((data.ReservedRoom != data.AssignedRoom)
                & data.ReservationStatus.eq("Check-Out"))
    opportunity_cost = (data.AssignedADR - data.AverageDailyRate) * data.Nights
    data["RevenueLossbyUpgrade"] = np.where(
        upgraded, opportunity_cost.clip(lower=0), 0)

    days_before = (data.ArrivalDate - data.ReservationStatusDate).dt.days
    late_cancel = (data.ReservationStatus.eq("Canceled")
                   & days_before.between(0, 3))
    cancel_cost = data.AverageDailyRate * (data.Nights - 1).clip(lower=0)
    data["RevenueLossbyCancel"] = np.where(late_cancel, cancel_cost, 0)
    data["PotentialRevenue"] = (data.RevenuebyStays
                                - data.RevenueLossbyUpgrade
                                - data.RevenueLossbyCancel)
    return data


def fit_probability_model(data, features, target, seed=42):
    """Fit a Random Forest with an out-of-sample evaluation split."""
    x, y = data[features], data[target]
    categorical = x.select_dtypes(include=["object", "category"]).columns
    numeric = x.columns.difference(categorical)
    prep = ColumnTransformer([
        ("category", OneHotEncoder(handle_unknown="ignore"), categorical),
        ("numeric", "passthrough", numeric)])
    model = Pipeline([
        ("preprocessing", prep),
        ("classifier", RandomForestClassifier(
            n_estimators=400, min_samples_leaf=3,
            class_weight="balanced_subsample", random_state=seed, n_jobs=-1))])
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=.20, stratify=y, random_state=seed)
    model.fit(x_train, y_train)
    return model, model.score(x_test, y_test)


def backtest_premiums(data, upgrade_premium, cancel_premium):
    """Apply refundable premiums and test the paired revenue improvement."""
    tested = data.copy()
    upgrade_recovery = (upgrade_premium * tested.Nights).clip(
        upper=tested.RevenueLossbyUpgrade)
    cancel_recovery = (cancel_premium * tested.Nights).clip(
        upper=tested.RevenueLossbyCancel)
    tested["RevenueWithBothStrategies"] = (
        tested.PotentialRevenue + upgrade_recovery + cancel_recovery)
    test = ttest_rel(tested.RevenueWithBothStrategies,
                     tested.PotentialRevenue, alternative="greater")
    return tested, {"revenue": tested.RevenueWithBothStrategies.sum(),
                    "t_statistic": test.statistic, "p_value": test.pvalue}
'''


RESULTS = [
    ("Upgrade loss", "€637,988", "€170,090", "-73.34%", "8.39e-287"),
    ("Cancellation loss", "€1,190,536", "€279,872", "-76.49%", "9.04e-267"),
    ("Upgrade strategy revenue", "€26,083,973", "€26,551,871", "+1.79%", "3.04e-06"),
    ("Cancellation strategy revenue", "€26,083,973", "€26,994,636", "+3.49%", "1.30e-18"),
    ("Combined-strategy revenue", "€26,083,973", "€27,462,534", "+5.28%", "1.00e-40"),
]


def header(canvas: Canvas, page: int, section: str) -> None:
    width, height = letter
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - .58 * inch, width, .58 * inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(.55 * inch, height - .35 * inch, "PYTHON PROGRAMMING SAMPLE")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - .55 * inch, height - .34 * inch,
                           f"Li Chang  |  {section}  |  {page} / 2")


def footer(canvas: Canvas) -> None:
    width, _ = letter
    canvas.setStrokeColor(GRID)
    canvas.line(.55 * inch, .43 * inch, width - .55 * inch, .43 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 6.7)
    canvas.drawString(.55 * inch, .25 * inch,
                      "Gold Medal Analysis Team • 2024 Business Analytics Competition")
    canvas.drawRightString(width - .55 * inch, .25 * inch,
                           "Python • pandas • scikit-learn • SciPy • Matplotlib")


def draw_code_page(canvas: Canvas) -> None:
    width, height = letter
    header(canvas, 1, "CODE")
    x, y = .55 * inch, height - .82 * inch
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawString(x, y, "Hotel Revenue Analytics")
    y -= .22 * inch
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8.2)
    canvas.drawString(x, y, "Selected code: feature engineering, probability modeling, and back-testing.")
    y -= .20 * inch
    bottom, top = .55 * inch, y
    canvas.setFillColor(PALE)
    canvas.roundRect(x, bottom, width - 1.10 * inch, top - bottom, 6, fill=1, stroke=0)
    lines = CODE.rstrip().splitlines()
    code_x, code_y = x + .14 * inch, top - .15 * inch
    font_size, leading = 5.65, 6.42
    for number, line in enumerate(lines, 1):
        line_y = code_y - (number - 1) * leading
        canvas.setFont("Courier", font_size)
        canvas.setFillColor(BLUE)
        canvas.drawRightString(code_x + .23 * inch, line_y, f"{number:>2}")
        canvas.setStrokeColor(GRID)
        canvas.line(code_x + .29 * inch, line_y - 1,
                    code_x + .29 * inch, line_y + leading - 1)
        canvas.setFillColor(TEAL if line.lstrip().startswith("#") else INK)
        canvas.drawString(code_x + .37 * inch, line_y, line)
    footer(canvas)


def draw_table(canvas: Canvas, x: float, y: float, width: float) -> float:
    columns = [("OUTCOME", .29), ("BASELINE", .18), ("STRATEGY", .18),
               ("CHANGE", .14), ("P-VALUE", .21)]
    row_h = .31 * inch
    canvas.setFillColor(NAVY)
    canvas.roundRect(x, y - row_h, width, row_h, 4, fill=1, stroke=0)
    cx = x
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 6.8)
    for label, fraction in columns:
        canvas.drawCentredString(cx + width * fraction / 2, y - .20 * inch, label)
        cx += width * fraction
    y -= row_h
    for index, row in enumerate(RESULTS):
        canvas.setFillColor(WHITE if index % 2 == 0 else PALE)
        canvas.rect(x, y - row_h, width, row_h, fill=1, stroke=0)
        cx = x
        for cell_index, ((_, fraction), value) in enumerate(zip(columns, row)):
            canvas.setFillColor(BLUE if cell_index == 3 else INK)
            canvas.setFont("Helvetica-Bold" if cell_index in (0, 3) else "Helvetica", 6.8)
            canvas.drawCentredString(cx + width * fraction / 2, y - .20 * inch, value)
            cx += width * fraction
        y -= row_h
    return y


def draw_bar_chart(canvas: Canvas, x: float, y: float, width: float, height: float) -> None:
    drawing = Drawing(width, height)
    chart = HorizontalBarChart()
    chart.x, chart.y = 128, 24
    chart.width, chart.height = width - 154, height - 38
    chart.data = [[73.34, 76.49, 1.79, 3.49, 5.28]]
    chart.categoryAxis.categoryNames = [
        "Upgrade loss reduced", "Cancel loss reduced", "Upgrade revenue gain",
        "Cancel revenue gain", "Combined revenue gain"]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin, chart.valueAxis.valueMax = 0, 80
    chart.valueAxis.valueStep = 20
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.visibleGrid = 1
    chart.valueAxis.gridStrokeColor = GRID
    chart.bars[0].fillColor = BLUE
    chart.bars[0].strokeColor = BLUE
    drawing.add(chart)
    drawing.add(String(chart.x + chart.width / 2, 4, "Absolute percentage change",
                       textAnchor="middle", fontName="Helvetica", fontSize=7,
                       fillColor=MUTED))
    drawing.drawOn(canvas, x, y)


def draw_output_page(canvas: Canvas) -> None:
    width, height = letter
    header(canvas, 2, "OUTPUT")
    x, y = .55 * inch, height - .82 * inch
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawString(x, y, "Back-test Results & Business Impact")
    y -= .30 * inch

    cards = [("89,634", "CLEAN BOOKINGS"), ("28", "MODEL FEATURES"),
             ("2", "RANDOM FORESTS"), ("+5.28%", "COMBINED REVENUE")]
    gap = .10 * inch
    card_w = (width - 1.10 * inch - 3 * gap) / 4
    for index, (value, label) in enumerate(cards):
        left = x + index * (card_w + gap)
        canvas.setFillColor(NAVY if index < 3 else BLUE)
        canvas.roundRect(left, y - .73 * inch, card_w, .73 * inch, 5, fill=1, stroke=0)
        canvas.setFillColor(GOLD if index < 3 else WHITE)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawCentredString(left + card_w / 2, y - .31 * inch, value)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 5.8)
        canvas.drawCentredString(left + card_w / 2, y - .56 * inch, label)
    y -= .98 * inch

    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 10.5)
    canvas.drawString(x, y, "Reported project outcomes")
    y -= .10 * inch
    y = draw_table(canvas, x, y, width - 1.10 * inch)
    y -= .24 * inch

    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 10.5)
    canvas.drawString(x, y, "Effect sizes from historical back-testing")
    y -= 2.45 * inch
    draw_bar_chart(canvas, x, y, width - 1.10 * inch, 2.22 * inch)
    y -= .18 * inch

    note_h = 1.15 * inch
    canvas.setFillColor(PALE)
    canvas.roundRect(x, y - note_h, width - 1.10 * inch, note_h, 6, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(x + .16 * inch, y - .22 * inch, "INTERPRETATION")
    style = ParagraphStyle("note", fontName="Helvetica", fontSize=8.0,
                           leading=10.5, textColor=INK, alignment=TA_LEFT)
    text = ("The models convert booking-level probabilities into expected-loss premiums. "
            "Historical back-tests indicate that the upgrade and cancellation strategies reduce "
            "their respective losses by 73.34% and 76.49%; together they raise potential revenue "
            "from €26.08M to €27.46M. These are results from the submitted team project, not a "
            "live randomized experiment.")
    paragraph = Paragraph(escape(text), style)
    _, paragraph_h = paragraph.wrap(width - 1.42 * inch, .8 * inch)
    paragraph.drawOn(canvas, x + .16 * inch, y - .34 * inch - paragraph_h)
    footer(canvas)


def main() -> None:
    canvas = Canvas(str(PDF_PATH), pagesize=letter)
    canvas.setTitle("Li Chang - Hotel Revenue Analytics Python Sample")
    canvas.setAuthor("Li Chang")
    canvas.setSubject("Graduate application programming supplement")
    draw_code_page(canvas)
    canvas.showPage()
    draw_output_page(canvas)
    canvas.showPage()
    canvas.save()
    print(PDF_PATH)


if __name__ == "__main__":
    main()
