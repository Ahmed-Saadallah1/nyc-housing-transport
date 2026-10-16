"""Build the small, pre-aggregated tables used by the website.

Input  (written by the notebook, Section 4-6): data/processed/collisions_clean.parquet,
                                               data/processed/housing_clean.parquet,
                                               data/processed/buildings_exposure.parquet,
                                               data/processed/zip_year_panel.parquet
Output (committed to the repository):          app/data/*.parquet and app/data/*.csv (a few MB in total)

Run from the repository root:  python app/prepare_data.py
"""
import os

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

PROCESSED = os.path.join("data", "processed")
OUT = os.path.join("app", "data")
EARTH_RADIUS_M = 6_371_000
BUFFER_M = 250
FULL_YEARS = list(range(2014, 2026))
os.makedirs(OUT, exist_ok=True)

collisions = pd.read_parquet(os.path.join(PROCESSED, "collisions_clean.parquet"))
buildings = pd.read_parquet(os.path.join(PROCESSED, "buildings_exposure.parquet"))
housing = pd.read_parquet(os.path.join(PROCESSED, "housing_clean.parquet"))
zip_panel = pd.read_parquet(os.path.join(PROCESSED, "zip_year_panel.parquet"))
residential_zips = set(zip_panel["zip_code"])

crashes = collisions[collisions["crash_year"].isin(FULL_YEARS)].copy()
crashes["motorist_casualties"] = crashes["number_of_motorist_injured"] + crashes["number_of_motorist_killed"]
crashes["all_casualties"] = crashes["number_of_persons_injured"] + crashes["number_of_persons_killed"]


# ---- Distance from each crash to the nearest new-construction and preservation building ----
def nearest_distance(points, targets):
    tree = BallTree(np.radians(targets[["latitude", "longitude"]].to_numpy()), metric="haversine")
    distance, _ = tree.query(np.radians(points[["latitude", "longitude"]].to_numpy()), k=1)
    return distance[:, 0] * EARTH_RADIUS_M


located = crashes["latitude"].notna()
for ctype, column in [("New Construction", "near_new_construction"), ("Preservation", "near_preservation")]:
    crashes[column] = False
    crashes.loc[located, column] = nearest_distance(
        crashes[located], buildings[buildings["construction_type"] == ctype]) <= BUFFER_M
crashes["located"] = located

MEASURES = {"crashes": ("collision_id", "size"),
            "pedestrian_casualties": ("pedestrian_casualties", "sum"),
            "cyclist_casualties": ("cyclist_casualties", "sum"),
            "motorist_casualties": ("motorist_casualties", "sum"),
            "all_casualties": ("all_casualties", "sum")}

# ---- 1. Crash cube: borough x year x weekday x hour x near-flags x severity ----
crashes["weekday"] = crashes["crash_date"].dt.dayofweek  # 0 = Monday
crash_cube = (crashes.assign(borough=crashes["borough"].fillna("Unknown"))
              .groupby(["borough", "crash_year", "weekday", "crash_hour", "time_unknown", "located",
                        "near_new_construction", "near_preservation", "severity"], observed=True)
              .agg(**MEASURES).reset_index().rename(columns={"crash_year": "year"}))

# ---- 2. ZIP x year x severity crash table (residential ZIP codes, as in the notebook) ----
zip_crashes = (crashes[crashes["zip_code"].isin(residential_zips)]
               .groupby(["zip_code", "crash_year", "severity"]).agg(**MEASURES).reset_index()
               .rename(columns={"crash_year": "year"}))

# ---- 3. ZIP x year housing table + ZIP attributes ----
zip_housing = zip_panel[["zip_code", "year", "borough", "affordable_units_completed",
                         "new_construction_units_completed", "deeply_affordable_units_completed",
                         "buildings_completed"]].copy()
zip_housing["preservation_units_completed"] = (zip_housing["affordable_units_completed"]
                                               - zip_housing["new_construction_units_completed"])
zip_centres = (collisions.dropna(subset=["zip_code", "latitude"]).groupby("zip_code")[["latitude", "longitude"]]
               .median().reset_index())
zip_centres = zip_centres[zip_centres["zip_code"].isin(residential_zips)]

# ---- 4. Buildings (one row per mappable building) ----
building_cols = ["building_id", "latitude", "longitude", "borough", "zip_code", "construction_type",
                 "affordable_units", "deeply_affordable_units", "completion_year", "crashes_per_year",
                 "pedestrian_casualties_per_year", "cyclist_casualties_per_year", "persons_injured_per_year"]
buildings_out = buildings[building_cols].copy()

# ---- 5. Housing by borough x completion year x type (includes confidential records, which have no location) ----
housing_years = (housing[housing["completion_year"].isin(FULL_YEARS)]
                 .groupby(["borough", "completion_year", "reporting_construction_type"])
                 .agg(buildings=("project_id", "size"), affordable_units=("all_counted_units", "sum"),
                      deeply_affordable_units=("deeply_affordable_units", "sum"))
                 .reset_index().rename(columns={"completion_year": "year",
                                                "reporting_construction_type": "construction_type"}))
housing_years["year"] = housing_years["year"].astype(int)

outputs = {"crash_cube": crash_cube, "zip_crashes": zip_crashes, "zip_housing": zip_housing,
           "zip_centres": zip_centres, "buildings": buildings_out, "housing_years": housing_years}
for name, table in outputs.items():
    path = os.path.join(OUT, f"{name}.parquet")
    table.to_parquet(path, index=False)
    table.to_csv(path.replace(".parquet", ".csv"), index=False)  # CSV copy for hosts without pyarrow
    print(f"{name:<14} {len(table):>8,} rows  {os.path.getsize(path) / 1e6:6.2f} MB")

# Reconciliation with the notebook: totals must match
assert crash_cube["crashes"].sum() == len(crashes)
assert zip_crashes["crashes"].sum() == zip_panel["crashes"].sum()
assert zip_housing["affordable_units_completed"].sum() == zip_panel["affordable_units_completed"].sum()
print("Reconciliation checks passed.")
