"""
Charts for the management report (PNG files).
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
Q = ROOT / "outputs" / "query_results"
OUT = ROOT / "outputs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

GREEN, RED, GREY = "#2E6B4F", "#C0504D", "#9AA5A0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})

def label_bars(ax, bars, fmt="{:.1f}%"):
    for b in bars:
        ax.annotate(fmt.format(b.get_height()), (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=9, xytext=(0, 2), textcoords="offset points")

# overtime by job level
d = pd.read_csv(Q / "q05_overtime_by_job_level.csv")
piv = d.pivot(index="job_level", columns="overtime", values="attrition_rate_pct")
fig, ax = plt.subplots(figsize=(7, 3.6))
x = range(len(piv))
w = 0.38
b1 = ax.bar([i - w / 2 for i in x], piv["Yes"], w, color=RED, label="Works overtime")
b2 = ax.bar([i + w / 2 for i in x], piv["No"], w, color=GREEN, label="No overtime")
label_bars(ax, b1); label_bars(ax, b2)
ax.set_xticks(list(x)); ax.set_xticklabels([f"Level {i}" for i in piv.index])
ax.set_ylabel("Attrition rate (%)"); ax.legend(frameon=False)
ax.set_title("Overtime and attrition, by job level", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT / "chart1_overtime_by_level.png", dpi=200); plt.close(fig)

# tenure
d = pd.read_csv(Q / "q06_attrition_by_tenure.csv")
fig, ax = plt.subplots(figsize=(7, 3.2))
cols = [RED] + [GREEN] * (len(d) - 1)
bars = ax.bar(d["tenure_band"], d["attrition_rate_pct"], color=cols)
label_bars(ax, bars)
ax.set_ylabel("Attrition rate (%)")
ax.set_title("Attrition falls steadily with length of service", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT / "chart2_tenure.png", dpi=200); plt.close(fig)

# job role
d = pd.read_csv(Q / "q03_attrition_by_job_role.csv").sort_values("attrition_rate_pct")
fig, ax = plt.subplots(figsize=(7, 3.9))
avg = 16.1
cols = [RED if v > avg else GREEN for v in d["attrition_rate_pct"]]
bars = ax.barh(d["job_role"], d["attrition_rate_pct"], color=cols)
for b, n in zip(bars, d["leavers"]):
    ax.annotate(f"{b.get_width():.1f}%  ({n} left)", (b.get_width(), b.get_y() + b.get_height() / 2),
                va="center", fontsize=8.5, xytext=(3, 0), textcoords="offset points")
ax.axvline(avg, color=GREY, linestyle="--", linewidth=1)
ax.text(avg + 0.6, 1.5, "company average 16.1%", color="#595959", fontsize=8.5)
ax.set_xlim(0, 50); ax.set_xlabel("Attrition rate (%)")
ax.set_title("Attrition by job role", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT / "chart3_job_role.png", dpi=200); plt.close(fig)

# risk bands
d = pd.read_csv(Q / "q13_risk_band_check.csv")
d["risk_band"] = pd.Categorical(d["risk_band"], ["Low", "Medium", "High"], ordered=True)
d = d.sort_values("risk_band")
fig, ax = plt.subplots(figsize=(7, 3.0))
bars = ax.bar(d["risk_band"].astype(str), d["attrition_rate_pct"], color=[GREEN, GREY, RED])
label_bars(ax, bars)
ax.set_ylabel("Actual attrition rate (%)")
ax.set_title("Model risk band vs what actually happened", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(OUT / "chart4_risk_bands.png", dpi=200); plt.close(fig)
print("Charts saved to outputs/charts/")
