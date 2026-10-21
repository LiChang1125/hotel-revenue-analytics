# Hotel Revenue Analytics

A portfolio edition of the **Gold Medal Analysis Team** submission to the 4th
Business Analytics Competition (2024), Round 2. The project uses booking-level
data from Global Hotels and Resorts (GHR) to estimate losses from free room
upgrades and last-minute cancellations, then back-tests two refundable-premium
strategies designed to hedge those losses.

## Business question

How can a hotel use information available before check-in to reduce revenue
leakage without simply increasing room rates?

The team modeled:

1. the probability of assignment to each room type;
2. the probability of a cancellation within three days of arrival;
3. the expected loss associated with each outcome; and
4. the revenue impact of charging contingently refundable premiums.

## Results from the submitted analysis

| Outcome | Baseline | With strategy | Change |
|---|---:|---:|---:|
| Loss from free upgrades | €637,988 | €170,090 | −73.34% |
| Loss from last-minute cancellations | €1,190,536 | €279,872 | −76.49% |
| Potential revenue, upgrade strategy | €26,083,973 | €26,551,871 | +1.79% |
| Potential revenue, cancellation strategy | €26,083,973 | €26,994,636 | +3.49% |
| Potential revenue, both strategies | €26,083,973 | €27,462,534 | **+5.28%** |

The original report also recorded one-sided hypothesis tests for all five
comparisons. The exact values are available in
[`results/project_summary.csv`](results/project_summary.csv).

![Weekly revenue decomposition](assets/figures/revenue_decomposition.png)

## Repository structure

```text
hotel-revenue-analytics/
├── src/hotel_revenue_analytics.py     # cleaned, reusable analysis functions
├── notebooks/                         # original workflow, outputs stripped
├── assets/figures/                    # selected figures from the submission
├── results/project_summary.csv        # reported business outcomes
├── report/                            # two-page programming supplement
└── AUTHORS.md                         # transparent team attribution
```

## Methods demonstrated

- CSV/Excel ingestion and explicit date/type handling
- feature engineering for revenue, opportunity cost, and cancellation loss
- categorical preprocessing and Random Forest probability models
- expected-loss pricing for refundable premiums
- historical back-testing and paired statistical testing
- weekly revenue aggregation and visualization

The cleaned module improves reproducibility by separating feature engineering,
modeling, premium calculation, back-testing, and plotting into reusable
functions. The original notebooks are retained for provenance.

## Reproducing the workflow

```bash
python -m venv .venv
python -m pip install -r requirements.txt
jupyter lab
```

Place the competition files in a local `data/` directory and update notebook
paths accordingly. The original dataset and large intermediate spreadsheets are
not redistributed here; `data/` is excluded from version control.

## Important limitations

- This was a team competition project; see [`AUTHORS.md`](AUTHORS.md).
- Reported figures come from the submitted 2024 analysis and are not claims
  about current hotel operations.
- The original notebooks evaluated several models on their training data. The
  cleaned module uses a stratified holdout split to make model assessment more
  defensible, so newly reproduced model metrics may differ from the submission.
- The premium strategies are analytical proposals, not evidence from a live
  randomized business experiment.

