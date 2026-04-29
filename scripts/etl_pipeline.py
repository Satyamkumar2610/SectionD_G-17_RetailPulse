"""
etl_pipeline.py — MediScope DVA Capstone Project
=================================================

A standalone Python script that replicates the full notebook pipeline:
  01_extraction  → loads raw CSVs, saves to data/processed/
  02_cleaning    → cleans & engineers features, saves clean_lab_master_v3.csv
  05_final_load  → produces Tableau-ready CSVs

Usage:
    python scripts/etl_pipeline.py [--root <project_root>]

If --root is not supplied the script assumes it is run from the project root.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def banner(msg: str) -> None:
    """Print a highlighted section banner."""
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print(f"{'=' * 60}")


def check_file(path: str) -> None:
    """Raise if a required file is missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Extraction
# ─────────────────────────────────────────────────────────────────────────────

FILE_MAP = {
    "patients":   "PATIENTS.csv",
    "admissions": "ADMISSIONS.csv",
    "labevents":  "LABEVENTS.csv",
    "labitems":   "D_LABITEMS.csv",
    "structured": "structured_medical_records.csv",
}


def stage_extraction(raw_dir: str, processed_dir: str) -> dict:
    """Load raw CSVs and save raw copies to data/processed/."""
    banner("Stage 1 — Extraction")

    dfs = {}
    for key, filename in FILE_MAP.items():
        path = os.path.join(raw_dir, filename)
        check_file(path)
        dfs[key] = pd.read_csv(path, low_memory=False)
        print(f"  Loaded {filename:<42}  shape={dfs[key].shape}")

    # Save raw copies to processed/
    save_map = {
        "patients_raw.csv":   dfs["patients"],
        "admissions_raw.csv": dfs["admissions"],
        "labevents_raw.csv":  dfs["labevents"],
        "labitems_raw.csv":   dfs["labitems"],
        "structured_raw.csv": dfs["structured"],
    }
    for fname, df in save_map.items():
        out = os.path.join(processed_dir, fname)
        df.to_csv(out, index=False)
        print(f"  Saved  → {os.path.relpath(out)}")

    print("\n✅  Extraction complete.")
    return dfs


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Cleaning & Feature Engineering
# ─────────────────────────────────────────────────────────────────────────────

VALUE_TO_NUM = {
    "NORMAL":     0,
    "TRACE":      0.5,
    "OCCASIONAL": 0.5,
    "1+":         1,
    "2+":         2,
    "3+":         3,
    "4+":         4,
}


def stage_cleaning(dfs: dict, processed_dir: str) -> pd.DataFrame:
    """Replicate the cleaning steps from 02_cleaning.ipynb."""
    banner("Stage 2 — Cleaning & Feature Engineering")

    patients   = dfs["patients"].copy()
    admissions = dfs["admissions"].copy()
    labevents  = dfs["labevents"].copy()
    labitems   = dfs["labitems"].copy()

    # ── Datetime parsing ────────────────────────────────────────────────────
    for col in ["admittime", "dischtime", "deathtime", "edregtime", "edouttime"]:
        admissions[col] = pd.to_datetime(admissions[col], errors="coerce")

    for col in ["dob", "dod", "dod_hosp", "dod_ssn"]:
        patients[col] = pd.to_datetime(patients[col], errors="coerce")

    labevents["charttime"] = pd.to_datetime(labevents["charttime"], errors="coerce")

    # ── LOS (length of stay in days) ────────────────────────────────────────
    admissions["los_days"] = (
        (admissions["dischtime"] - admissions["admittime"]).dt.total_seconds() / 86400
    ).round(2)

    # ── Abnormal flag ────────────────────────────────────────────────────────
    labevents["is_abnormal"] = labevents["flag"].notna().astype(int)

    # ── Join LabEvents ↔ D_LABITEMS ─────────────────────────────────────────
    lab_with_dict = labevents.merge(
        labitems[["itemid", "label", "category", "fluid", "loinc_code"]],
        on="itemid",
        how="left",
    )

    # ── Join with Admissions (LOS, admission_type) ───────────────────────────
    lab_with_adm = lab_with_dict.merge(
        admissions[["subject_id", "hadm_id", "los_days", "admission_type"]],
        on=["subject_id", "hadm_id"],
        how="left",
    )

    # ── Join with Patients (gender, dob) ─────────────────────────────────────
    lab_master = lab_with_adm.merge(
        patients[["subject_id", "gender", "dob"]],
        on="subject_id",
        how="left",
    )

    # ── Drop rows where 'value' is entirely missing ──────────────────────────
    # These 5 rows (out of 76,074) have no lab value recorded in the MIMIC
    # source itself. The original 02_cleaning.ipynb dropped them, making the
    # canonical dataset 76,069 rows — matching what Tableau was built on.
    # Keeping them with a -1 sentinel would skew min() / histogram statistics.
    before = len(lab_master)
    lab_master = lab_master.dropna(subset=["value"])
    dropped = before - len(lab_master)
    print(f"  Dropped {dropped} row(s) with null 'value' (no MIMIC source data)")

    # ── Impute valuenum from text value ──────────────────────────────────────
    for text_val, num_val in VALUE_TO_NUM.items():
        mask = lab_master["valuenum"].isna() & (
            lab_master["value"].astype(str).str.upper() == text_val.upper()
        )
        lab_master.loc[mask, "valuenum"] = num_val

    # Fill remaining nulls with sentinel -1
    lab_master["valuenum"] = lab_master["valuenum"].fillna(-1)

    print(f"  Master dataset shape : {lab_master.shape}")
    print(f"  Nulls in valuenum    : {lab_master['valuenum'].isna().sum()}")

    # ── Save ─────────────────────────────────────────────────────────────────
    out_path = os.path.join(processed_dir, "clean_lab_master_v3.csv")
    lab_master.to_csv(out_path, index=False)
    print(f"  Saved  → {os.path.relpath(out_path)}")

    print("\n✅  Cleaning complete.")
    return lab_master


# ─────────────────────────────────────────────────────────────────────────────
# Stage 5 — Final Load & Tableau Export
# ─────────────────────────────────────────────────────────────────────────────

def stage_final_load(lab: pd.DataFrame, tableau_dir: str) -> None:
    """Produce Tableau-ready CSV exports."""
    banner("Stage 5 — Final Load & Tableau Prep")

    os.makedirs(tableau_dir, exist_ok=True)

    # ── Export 1: Patient-level summary ──────────────────────────────────────
    patient_summary = (
        lab.groupby(["subject_id", "gender", "admission_type"])
        .agg(
            total_tests    = ("itemid",     "count"),
            abnormal_tests = ("is_abnormal","sum"),
            avg_valuenum   = ("valuenum",   "mean"),
            avg_los_days   = ("los_days",   "mean"),
            unique_items   = ("itemid",     "nunique"),
        )
        .reset_index()
    )
    patient_summary["abnormal_rate"] = (
        patient_summary["abnormal_tests"] / patient_summary["total_tests"]
    ).round(4)

    # ── Export 2: Category breakdown ─────────────────────────────────────────
    category_breakdown = (
        lab.groupby(["category", "fluid"])
        .agg(
            test_count     = ("itemid",     "count"),
            abnormal_count = ("is_abnormal","sum"),
            mean_value     = ("valuenum",   "mean"),
            median_value   = ("valuenum",   "median"),
        )
        .reset_index()
    )
    category_breakdown["abnormal_rate"] = (
        category_breakdown["abnormal_count"] / category_breakdown["test_count"]
    ).round(4)

    # ── Export 3: Monthly trends ─────────────────────────────────────────────
    lab_ts = lab.copy()
    lab_ts["charttime"] = pd.to_datetime(lab_ts["charttime"], errors="coerce")
    monthly_trends = (
        lab_ts.set_index("charttime")
        .resample("ME")
        .agg(
            test_count     = ("itemid",     "count"),
            abnormal_count = ("is_abnormal","sum"),
            avg_valuenum   = ("valuenum",   "mean"),
        )
        .reset_index()
    )
    monthly_trends["abnormal_rate"] = (
        monthly_trends["abnormal_count"]
        / monthly_trends["test_count"].replace(0, np.nan)
    ).round(4)

    # ── Export 4: Admission-type comparison ───────────────────────────────────
    admission_comparison = (
        lab.groupby("admission_type")
        .agg(
            patient_count  = ("subject_id", "nunique"),
            total_tests    = ("itemid",     "count"),
            abnormal_tests = ("is_abnormal","sum"),
            avg_los_days   = ("los_days",   "mean"),
            median_los     = ("los_days",   "median"),
        )
        .reset_index()
    )
    admission_comparison["abnormal_rate"] = (
        admission_comparison["abnormal_tests"] / admission_comparison["total_tests"]
    ).round(4)

    # ── Save all ──────────────────────────────────────────────────────────────
    exports = {
        "tableau_patient_summary.csv":      patient_summary,
        "tableau_category_breakdown.csv":   category_breakdown,
        "tableau_monthly_trends.csv":       monthly_trends,
        "tableau_admission_comparison.csv": admission_comparison,
    }

    for fname, df in exports.items():
        out = os.path.join(tableau_dir, fname)
        df.to_csv(out, index=False)
        print(f"  Saved  → {os.path.relpath(out)}")

    print("\n✅  Tableau exports complete.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="MediScope ETL Pipeline")
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    args = parser.parse_args()

    root          = os.path.abspath(args.root)
    raw_dir       = os.path.join(root, "data", "raw")
    processed_dir = os.path.join(root, "data", "processed")
    tableau_dir   = os.path.join(processed_dir, "tableau_exports")

    os.makedirs(processed_dir, exist_ok=True)

    print(f"Project root  : {root}")
    print(f"Raw data      : {raw_dir}")
    print(f"Processed data: {processed_dir}")

    # Run pipeline
    dfs        = stage_extraction(raw_dir, processed_dir)
    lab_master = stage_cleaning(dfs, processed_dir)
    stage_final_load(lab_master, tableau_dir)

    banner("Pipeline Complete ✅")
    print("All outputs written to data/processed/")
    print("Tableau exports in data/processed/tableau_exports/")


if __name__ == "__main__":
    main()
