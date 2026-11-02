"""
Attrition risk model (logistic regression).

Reads employees from the SQL database, fits a model, checks it with cross-validation,
then writes a risk score for every employee back to the database (table: risk_scores).

Output: db/hr_analytics.db (new table risk_scores)
        outputs/model_odds_ratios.csv
        outputs/model_performance.csv
        outputs/watchlist_top25_active.csv
"""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "db" / "hr_analytics.db")
df = pd.read_sql_query("SELECT * FROM employees", con)

numeric = ["age", "monthly_income", "years_at_company", "years_since_last_promotion",
           "years_with_curr_manager", "distance_from_home", "job_satisfaction",
           "env_satisfaction", "work_life_balance", "job_involvement",
           "num_companies_worked", "stock_option_level", "training_times_last_year"]
# marital status is left out on purpose: it predicts well but is not a fair basis for HR action
categorical = ["overtime", "business_travel", "job_level", "department"]

X = df[numeric + categorical].copy()
X["job_level"] = X["job_level"].astype(str)    
y = df["attrition_flag"]

prep = ColumnTransformer([
    ("num", StandardScaler(), numeric),
    ("cat", OneHotEncoder(drop="first"), categorical),
])
model = Pipeline([
    ("prep", prep),
    ("clf", LogisticRegression(max_iter=2000, C=0.5, class_weight="balanced")),
])

# performance check: every score comes from a model that never saw that row
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_prob = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
auc = roc_auc_score(y, cv_prob)

# flag the top 20% highest scores and see how many real leavers that catches
cut = np.quantile(cv_prob, 0.80)
flagged = cv_prob >= cut
precision = precision_score(y, flagged)
recall = recall_score(y, flagged)
print(f"Cross-validated AUC: {auc:.3f}")
print(f"Top 20% flagged: catches {recall:.0%} of leavers, {precision:.0%} of those flagged did leave")

pd.DataFrame([
    {"metric": "Cross-validated AUC (5-fold)", "value": round(auc, 3)},
    {"metric": "Share of leavers caught in top 20% of scores", "value": round(recall, 3)},
    {"metric": "Share of flagged people who actually left", "value": round(precision, 3)},
    {"metric": "Base attrition rate", "value": round(y.mean(), 3)},
]).to_csv(ROOT / "outputs" / "model_performance.csv", index=False)

# fit on all data to read the coefficients and score everyone
model.fit(X, y)
names = model.named_steps["prep"].get_feature_names_out()
coefs = model.named_steps["clf"].coef_[0]
odds = (pd.DataFrame({"feature": names, "coefficient": coefs, "odds_ratio": np.exp(coefs)})
        .sort_values("odds_ratio", ascending=False))
odds["feature"] = odds["feature"].str.replace("num__", "", regex=False).str.replace("cat__", "", regex=False)
odds.round(3).to_csv(ROOT / "outputs" / "model_odds_ratios.csv", index=False)
print("\nStrongest risk factors (odds ratio > 1 raises risk):")
print(odds.head(8).round(2).to_string(index=False))

# use the cross-validated score for everyone so the scores are not flattered
scores = pd.DataFrame({
    "employee_id": df["employee_id"],
    "risk_score": cv_prob.round(4),
})
scores["risk_band"] = pd.cut(scores["risk_score"], [-0.01, 0.30, 0.60, 1.01],
                             labels=["Low", "Medium", "High"]).astype(str)
scores.to_sql("risk_scores", con, if_exists="replace", index=False)

# SQL join pulls the watchlist: current staff with the highest scores
watch = pd.read_sql_query("""
    SELECT e.employee_id, e.department, e.job_role, e.job_level, e.overtime,
           e.tenure_band, e.monthly_income, r.risk_score, r.risk_band
    FROM employees e
    JOIN risk_scores r ON r.employee_id = e.employee_id
    WHERE e.attrition = 'No'
    ORDER BY r.risk_score DESC
    LIMIT 25
""", con)
watch.to_csv(ROOT / "outputs" / "watchlist_top25_active.csv", index=False)

band = pd.read_sql_query("""
    SELECT r.risk_band, COUNT(*) AS headcount, SUM(e.attrition_flag) AS leavers,
           ROUND(100.0 * SUM(e.attrition_flag) / COUNT(*), 1) AS attrition_rate_pct
    FROM employees e JOIN risk_scores r ON r.employee_id = e.employee_id
    GROUP BY r.risk_band ORDER BY MIN(r.risk_score)
""", con)
band.to_csv(ROOT / "outputs" / "query_results" / "q13_risk_band_check.csv", index=False)
print("\nHow real attrition lines up with the risk bands:")
print(band.to_string(index=False))
con.close()
