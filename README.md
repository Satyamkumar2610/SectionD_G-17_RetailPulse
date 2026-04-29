# MediScope: Transforming Raw Patient Datasets into Actionable Healthcare Insights

> **Sector:** Healthcare Technology & Analytics  
> **Team:** G-17 · Section D · Newton School of Technology  
> **Faculty Mentor:** Archit Raj

[![Tableau Dashboard](https://img.shields.io/badge/Tableau-Dashboard-blue?logo=tableau)](https://public.tableau.com/app/profile/sambhav.kumar2781/viz/dv_p7/Dashboard1)
[![GitHub](https://img.shields.io/badge/GitHub-SectionD_G--17_MediScope-black?logo=github)](https://github.com/Satyamkumar2610/SectionD_G-17_MediScope)

---

## 📌 Problem Statement

Hospitals generate enormous volumes of laboratory data every day, yet this data often remains siloed in raw, unstructured databases — inaccessible to the clinical teams and administrators who need it most. Without a systematic data pipeline, critical signals such as abnormal lab trends, high-risk patient clusters, and drivers of prolonged hospital stays go undetected until they become emergencies.

**MediScope addresses three core questions:**

1. **Who is at risk?** — Are there patient subgroups (by gender, admission type, or lab profile) that consistently show higher rates of abnormal results?
2. **What drives long stays?** — Is the length of hospital stay meaningfully different across admission types, and can this be quantified with statistical confidence?
3. **Where are the critical cases?** — Can unsupervised machine learning identify distinct patient risk clusters from raw lab data alone?

The goal is to transform a de-identified subset of the MIMIC-III clinical database into a clean, analysis-ready dataset, derive statistically validated insights, and surface those insights through an interactive Tableau dashboard — turning raw clinical data into a decision-support tool for hospital administrators and clinical teams.

---

## 📊 Interactive Dashboard

🔗 **[View the MediScope Tableau Dashboard](https://public.tableau.com/app/profile/sambhav.kumar2781/viz/dv_p7/Dashboard1)**

The dashboard presents a 6-slide narrative arc:

| Slide | Title | Key Visual |
|---|---|---|
| 1 | The Scope | KPI tiles — 76,069 tests · 100 patients · 39% abnormal |
| 2 | Who is most at risk? | Stacked bar — Abnormal rate by Gender |
| 3 | What drives long stays? | Box plot — LOS by Admission Type |
| 4 | Where are the critical cases? | Scatter — KMeans patient clusters |
| 5 | Is it getting better? | Line chart — Monthly abnormal rate trend |
| 6 | What should we do? | Summary of recommendations |

---

## 🗄️ Dataset

**Source:** [MIMIC-III Clinical Database](https://physionet.org/content/mimiciii/) — a de-identified subset of ICU patient records from Beth Israel Deaconess Medical Center.

| File | Description | Rows | Columns |
|---|---|---|---|
| `PATIENTS.csv` | Patient demographics | 100 | 8 |
| `ADMISSIONS.csv` | Hospital admission records | 129 | 19 |
| `LABEVENTS.csv` | Laboratory test results | 76,074 | 9 |
| `D_LABITEMS.csv` | Lab test code dictionary | 753 | 6 |
| `structured_medical_records.csv` | Pre-structured patient records | 408 | 5 |

**Canonical cleaned dataset:** `data/processed/clean_lab_master_v3.csv`
- **76,069 rows × 18 columns** (5 null-value rows dropped from raw)
- Joins all 5 source tables via `subject_id`, `hadm_id`, `itemid`

---

## 🔑 Key Findings

### Dataset Overview
| Metric | Value |
|---|---|
| Total lab records (cleaned) | **76,069** |
| Unique patients | **100** |
| Unique admissions | **129** |
| Abnormal lab results | **29,736 (39.1%)** |
| Delta-flagged results | **227 (0.3%)** |
| Unique lab test types | **439** |
| Lab categories | **6** (Chemistry, Hematology, Blood Gas, Urine, etc.) |

### Statistical Results

#### 1. Gender vs Abnormal Results — Chi-Square Test
> **p < 0.0001** — Statistically significant

Female and male patients do not show the same rate of abnormal lab results. Gender is a significant predictor of test abnormality, suggesting that **gender-stratified clinical reference ranges** should be considered.

#### 2. Length of Stay by Admission Type — Independent T-Test
> **p < 0.0001** — Statistically significant

| Admission Type | Patients | Avg LOS (days) | Abnormal Rate |
|---|---|---|---|
| Emergency | 91 | **28.8** | 39.6% |
| Elective | 8 | **21.2** | 38.6% |
| Urgent | 2 | **6.3** | 26.9% |

Emergency admissions result in a **36% longer hospital stay** than Elective admissions — a clinically and operationally significant difference.

#### 3. Gender vs Lab Values — Independent T-Test
> **p = 0.886** — Not statistically significant

While the *type* of abnormal results differs by gender, the raw numeric lab values (`valuenum`) do not differ significantly between male and female patients.

#### 4. Patient Risk Clusters — KMeans (k=3)
| Cluster | Records | Profile |
|---|---|---|
| 0 | 6,412 | Moderate lab values, extended stay |
| 1 | 52,643 | Standard lab values, typical stay |
| 2 | 14 | **Extreme lab values** — highest-risk group |

Cluster 2 represents fewer than **0.02% of records** but contains patients with extreme lab values across prolonged stays — the primary target for early clinical intervention.

---

## 🏗️ Project Pipeline

```
data/raw/          →  01_extraction.ipynb   →  Inspect & validate
                   →  02_cleaning.ipynb     →  data/processed/clean_lab_master_v3.csv
                   →  03_eda.ipynb          →  Exploratory visualisations
                   →  04_statistical_analysis.ipynb  →  Hypothesis tests & clustering
                   →  05_final_load_prep.ipynb       →  data/processed/tableau_exports/
                   →  Tableau Dashboard              →  Interactive storytelling
```

### Running the Full Pipeline (Automated)

```bash
# From the project root
python scripts/etl_pipeline.py --root .
```

This runs Stages 1 (Extraction), 2 (Cleaning), and 5 (Tableau export) end-to-end and produces all files in `data/processed/`.

---

## 📁 Repository Structure

```
SectionD_G-17_MediScope/
│
├── data/
│   ├── raw/                          # Original MIMIC-III source CSVs (read-only)
│   │   ├── PATIENTS.csv
│   │   ├── ADMISSIONS.csv
│   │   ├── LABEVENTS.csv
│   │   ├── D_LABITEMS.csv
│   │   └── structured_medical_records.csv
│   │
│   └── processed/                    # Cleaned & aggregated outputs
│       ├── clean_lab_master_v3.csv   # Canonical dataset (76,069 × 18)
│       └── tableau_exports/
│           ├── tableau_patient_summary.csv
│           ├── tableau_category_breakdown.csv
│           ├── tableau_monthly_trends.csv
│           └── tableau_admission_comparison.csv
│
├── notebooks/
│   ├── 01_extraction.ipynb           # Load & validate raw data
│   ├── 02_cleaning.ipynb             # Clean, engineer features, join tables
│   ├── 03_eda.ipynb                  # Exploratory data analysis
│   ├── 04_statistical_analysis.ipynb # T-tests, Chi-square, KMeans clustering
│   └── 05_final_load_prep.ipynb      # Produce Tableau-ready exports
│
├── scripts/
│   └── etl_pipeline.py              # Standalone end-to-end ETL script
│
├── docs/
│   └── data_dictionary.md           # Column definitions for all tables
│
├── reports/
│   ├── project_report.pdf
│   └── presentation.pdf
│
└── tableau/
    └── dashboard_links.md           # Tableau Public dashboard links
```

---

## ⚙️ Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.x |
| Data Manipulation | pandas, numpy |
| Statistical Analysis | scipy.stats, statsmodels |
| Machine Learning | scikit-learn (KMeans, StandardScaler, LinearRegression) |
| Visualisation (code) | matplotlib, seaborn |
| Visualisation (dashboard) | Tableau Public |
| Version Control | Git / GitHub |
| Notebooks | Jupyter / Google Colab |

---

## 📦 Data Dictionary (Key Columns — `clean_lab_master_v3.csv`)

| Column | Type | Description |
|---|---|---|
| `subject_id` | int | Unique patient identifier |
| `hadm_id` | float | Hospital admission identifier (null = outpatient lab) |
| `itemid` | int | Lab test code (links to D_LABITEMS) |
| `charttime` | datetime | Timestamp of lab result |
| `value` | str | Raw lab result value (text) |
| `valuenum` | float | Numeric lab result; `-1` = sentinel for unmappable text |
| `valueuom` | str | Unit of measurement (e.g. `mEq/L`, `mg/dL`) |
| `flag` | str | `abnormal` / `delta` / null (null = normal) |
| `is_abnormal` | int | Binary flag: 1 if `flag` is not null, else 0 |
| `label` | str | Human-readable test name (from D_LABITEMS) |
| `category` | str | Lab category (Chemistry, Hematology, Blood Gas, …) |
| `fluid` | str | Specimen type (Blood, Urine, Cerebrospinal Fluid, …) |
| `loinc_code` | str | LOINC standard code for the lab test |
| `los_days` | float | Length of stay in days (derived from admittime/dischtime) |
| `admission_type` | str | EMERGENCY / ELECTIVE / URGENT |
| `gender` | str | Patient gender (M / F) |
| `dob` | datetime | Patient date of birth |

---

## 👥 Team

**Team ID:** G-17 · Section D  
**Institute:** Newton School of Technology  
**Faculty Mentor:** Archit Raj

| Name | Role |
|---|---|
| **Satyam** | Project Lead & Data Engineer |
| **Sambhav** | Statistical Analyst |
| **Shagun** | Visualization Specialist |
| **Yash** | Documentation Lead |
| **Harsh** | Research & Quality Assurance |

---

## 📜 Data Ethics & Privacy

This project uses the **MIMIC-III** database, which is de-identified in accordance with HIPAA Safe Harbor requirements. All dates have been shifted by a random offset per patient to prevent re-identification. No real patient names, addresses, or direct identifiers are present in any dataset in this repository.

Access to the full MIMIC-III database requires completion of the CITI "Data or Specimens Only Research" training and credentialed access via PhysioNet.

---

*MediScope · G-17 · Section D · Newton School of Technology · 2025–26*
