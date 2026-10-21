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

## Repository structure

```text
hotel-revenue-analytics/
├── src/hotel_revenue_analytics.py     # cleaned, reusable analysis functions
├── notebooks/                         # compact and original executed notebooks
│   └── original_with_outputs/         # original project notebooks and outputs
├── data/
│   ├── preparation/                   # source and cleaned booking data
│   └── analysis/                      # ADR and loss-matrix inputs
├── outputs/
│   ├── upgrade/                       # upgrade model, probabilities, and figures
│   ├── cancellation/                  # cancellation model, probabilities, and figures
│   └── revenue/                       # revenue visualizations
├── requirements.txt                   # reproducible Python environment
├── README.md                          # project and method documentation
└── AUTHORS.md                         # transparent team attribution
```

The six original project bundles—Data Preparation, Data Analysis, Python,
Upgrade, Cancel, and Revenue—are preserved in the folders above. Application
documents remain outside this repository.

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

The original competition files are available under `data/`. The notebooks in
`notebooks/original_with_outputs/` preserve the executed project workflow;
the smaller notebooks directly under `notebooks/` have outputs removed for
faster browsing. Some original notebook paths may need to be changed to the
repository-relative locations shown above before re-running the full analysis.

## Important limitations

- This was a team competition project; see [`AUTHORS.md`](AUTHORS.md).
- Reported figures come from the submitted 2024 analysis and are not claims
  about current hotel operations.
- The original notebooks evaluated several models on their training data. The
  cleaned module uses a stratified holdout split to make model assessment more
  defensible, so newly reproduced model metrics may differ from the submission.
- The premium strategies are analytical proposals, not evidence from a live
  randomized business experiment.

