# HR Attrition Analytics: Python, SQL and Excel

A business intelligence case study on employee attrition. It cleans and validates HR data in Python,
answers business questions in SQL, scores attrition risk with a logistic regression model, and presents
the results in an Excel dashboard with a costed retention business case.

## The business question
Where are we losing people, what does it cost, and which retention measures are worth piloting?

## Data
IBM HR Analytics Employee Attrition & Performance dataset (1,470 employees, 35 fields). It is a public
dataset created by IBM data scientists and shared on Kaggle. It is fictional, so this project shows a
method and does not describe any real company.

## Main findings
- 237 of 1,470 employees left (16.1%). Estimated replacement cost is about USD 6.8m at 50% of annual salary (an assumption).
- Employees working overtime left at 30.5% against 10.4% for those who do not. Level 1 staff on overtime left at 52.6%.
- Employees with one year of service or less left at 34.9%, against 18.4% at two to three years.
- The risk model reaches a cross-validated AUC of 0.83. Flagging the top 20% of scores catches 62% of leavers.
- A pilot of overtime relief and first-year support breaks even if it closes about 8% of the attrition gap (placeholder costs).

## How the pieces fit
| Step | Script | Tool | Output |
|---|---|---|---|
| 1 | scripts/01_clean_validate.py | Python | data/clean/employees_clean.csv, data quality report |
| 2 | scripts/02_build_database.py + sql/*.sql | SQL (SQLite) | db/hr_analytics.db, 12 query result files |
| 3 | scripts/03_risk_model.py | Python (scikit-learn) | risk scores table, odds ratios, watchlist |
| 4 | scripts/04_report_charts.py | Python (matplotlib) | charts for the management report |

## Run it
```
pip install -r requirements.txt
python scripts/01_clean_validate.py
python scripts/02_build_database.py
python scripts/03_risk_model.py
python scripts/04_report_charts.py
```
Download the raw file first (see data/raw/README.txt).

## Limits
One snapshot, so results show association and not cause. Programme costs and the replacement-cost share
are assumptions. Marital status and gender were left out of the model on purpose.
