"""
Load, validate and clean the raw HR file.

Input : data/raw/IBM_HR_Attrition.csv
Output: data/clean/employees_clean.csv
        outputs/data_quality_report.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "IBM_HR_Attrition.csv"
CLEAN = ROOT / "data" / "clean" / "employees_clean.csv"
REPORT = ROOT / "outputs" / "data_quality_report.csv"

# utf-8-sig strips the hidden BOM character at the start of this file
df = pd.read_csv(RAW, encoding="utf-8-sig")
print(f"Rows: {len(df):,}   Columns: {df.shape[1]}")

# validation checks
checks = []

def check(name, passed, detail=""):
    checks.append({"check": name, "result": "PASS" if passed else "FAIL", "detail": detail})

check("No missing values", df.isna().sum().sum() == 0,
      f"{df.isna().sum().sum()} missing cells")
check("No fully duplicated rows", df.duplicated().sum() == 0,
      f"{df.duplicated().sum()} duplicates")
check("EmployeeNumber is unique", df["EmployeeNumber"].is_unique)
check("Attrition only Yes/No", set(df["Attrition"].unique()) <= {"Yes", "No"})
check("Age between 18 and 65", df["Age"].between(18, 65).all(),
      f"min {df['Age'].min()}, max {df['Age'].max()}")
check("Monthly income above zero", (df["MonthlyIncome"] > 0).all())
check("Years at company <= total working years",
      (df["YearsAtCompany"] <= df["TotalWorkingYears"]).all(),
      f"{(df['YearsAtCompany'] > df['TotalWorkingYears']).sum()} rows break the rule")
check("Years in role <= years at company",
      (df["YearsInCurrentRole"] <= df["YearsAtCompany"]).all())
check("Rating scales sit inside 1-4",
      df[["JobSatisfaction", "EnvironmentSatisfaction", "WorkLifeBalance",
          "RelationshipSatisfaction", "JobInvolvement"]].stack().between(1, 4).all())

# columns that hold one value for every row carry no information
constant_cols = [c for c in df.columns if df[c].nunique() == 1]
checks.append({"check": "Constant columns (no information)",
               "result": "NOTE" if constant_cols else "PASS",
               "detail": "dropped: " + ", ".join(constant_cols)})

pd.DataFrame(checks).to_csv(REPORT, index=False)
print(pd.DataFrame(checks).to_string(index=False))

# data cleaning
df = df.drop(columns=constant_cols)

df = df.rename(columns={
    "EmployeeNumber": "employee_id", "Age": "age", "Attrition": "attrition",
    "BusinessTravel": "business_travel", "Department": "department",
    "DistanceFromHome": "distance_from_home", "Education": "education",
    "EducationField": "education_field", "EnvironmentSatisfaction": "env_satisfaction",
    "Gender": "gender", "JobInvolvement": "job_involvement", "JobLevel": "job_level",
    "JobRole": "job_role", "JobSatisfaction": "job_satisfaction",
    "MaritalStatus": "marital_status", "MonthlyIncome": "monthly_income",
    "NumCompaniesWorked": "num_companies_worked", "OverTime": "overtime",
    "PercentSalaryHike": "percent_salary_hike", "PerformanceRating": "performance_rating",
    "RelationshipSatisfaction": "relationship_satisfaction",
    "StockOptionLevel": "stock_option_level", "TotalWorkingYears": "total_working_years",
    "TrainingTimesLastYear": "training_times_last_year", "WorkLifeBalance": "work_life_balance",
    "YearsAtCompany": "years_at_company", "YearsInCurrentRole": "years_in_current_role",
    "YearsSinceLastPromotion": "years_since_last_promotion",
    "YearsWithCurrManager": "years_with_curr_manager",
})

# drop pay rates as they are nor neccessary in this analysis
df = df.drop(columns=["DailyRate", "HourlyRate", "MonthlyRate"])

df["business_travel"] = df["business_travel"].replace(
    {"Non-Travel": "No travel", "Travel_Rarely": "Rarely", "Travel_Frequently": "Frequently"})

# derived fields
df["attrition_flag"] = (df["attrition"] == "Yes").astype(int)
df["overtime_flag"] = (df["overtime"] == "Yes").astype(int)

df["age_band"] = pd.cut(df["age"], [17, 25, 35, 45, 70],
                        labels=["18-25", "26-35", "36-45", "46+"]).astype(str)
df["tenure_band"] = pd.cut(df["years_at_company"], [-1, 1, 3, 5, 10, 100],
                           labels=["0-1 yrs", "2-3 yrs", "4-5 yrs", "6-10 yrs", "10+ yrs"]).astype(str)
df["promotion_gap_band"] = pd.cut(df["years_since_last_promotion"], [-1, 0, 2, 5, 100],
                                  labels=["Promoted this year", "1-2 yrs", "3-5 yrs", "6+ yrs"]).astype(str)
df["commute_band"] = pd.cut(df["distance_from_home"], [0, 5, 15, 100],
                            labels=["0-5 km", "6-15 km", "16+ km"]).astype(str)

CLEAN.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(CLEAN, index=False)
print(f"\nSaved {len(df):,} rows and {df.shape[1]} columns to {CLEAN.name}")
print(f"Overall attrition rate: {df['attrition_flag'].mean():.1%}")
