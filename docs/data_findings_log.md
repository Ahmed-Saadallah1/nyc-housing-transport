# Data Findings Log (observations to address in EDA / cleaning)

## Snapshot (downloaded 2026-10-14)
- Housing (hg8x-zxpr): 9,551 rows x 41 columns (full dataset, no filter)
- Collisions (h9gi-nx95): full dataset 2,269,187 rows; since 2014-01-01: 1,964,900 rows (86.6%) x 29 columns
- Completeness check passed for both (downloaded rows == server count)

## Housing observations (from head())
- One row per building; a project can have multiple buildings (e.g., project 72449 has 3+ rows) -> count buildings vs projects separately
- project_completion_date NaN for recently started projects (start 2026-06-30) -> meaningful missing (in-progress), keep
- bin = 4000000 -> NYC "million BIN" placeholder (1000000/2000000/3000000/4000000/5000000) = no BIN assigned -> hidden missing
- Dates stored as text "YYYY-MM-DDT00:00:00.000" -> convert
- postcode/bbl/bin as text (by design)

## Collisions observations (from head())
- API field names off_street_name / cross_street_name are SWAPPED vs content:
  off_street_name holds cross streets (e.g., ROCKAWAY BOULEVARD); cross_street_name holds off-street addresses (e.g., "745 MANHATTAN AVENUE")
  (metadata: fieldName off_street_name has display name "CROSS STREET NAME", cross_street_name has display "OFF STREET NAME") -> rename
- Rows with no borough/zip/coords (e.g., ALEXANDER HAMILTON BRIDGE) -> unlocatable
- Rows with coords but no borough/zip -> recoverable via spatial lookup
- Multiple internal spaces in street text ("745       MANHATTAN AVENUE") -> normalize whitespace
- Inconsistent case in vehicle types (AMBULANCE / Van / Bus) -> standardize
- "Unspecified" in contributing factors -> hidden missing
- location column redundant with latitude/longitude -> drop with justification
- crash_time format "H:MM" without leading zero; check midnight 0:00 over-representation (possible default/unknown time)
- Rows are ordered by :id, not chronologically

## Full profile (run on the attached snapshot, pandas 2.2.3)
### Housing
- 5,928 projects; 7,478 distinct building_ids; 0 fully duplicated rows; 0 duplicate (project_id, building_id)
- Dates: project_start 2014-01-03 -> 2026-06-30; project_completion 2014-01-03 -> 2026-08-11 (19.0% missing); building_completion 2014-01-03 -> 2026-08-21 (17.4% missing)
- 1,949 rows "CONFIDENTIAL": house_number/street_name = "----" (hidden missing), no building_id/bin/bbl/postcode/coords; community_board present
- 9 non-confidential rows missing coords/postcode (e.g., ARVERNE EAST) -> 1,958 rows missing lat/lon/postcode/census tract/NTA (20.5%)
- 482 "million BIN" placeholders
- Unit columns: NaN never co-occurs with explicit '0' -> NaN means 0 units; income-band sum == all_counted_units for 100% of rows
- all_counted_units missing 29 rows; total_units no zeros, max 1,320; sum 445,588
- latitude_internal missing 86 rows where latitude present
- Borough: Brooklyn 3,649 / Bronx 2,630 / Manhattan 1,485 / Queens 1,342 / Staten Island 445
- New Construction 4,766 vs Preservation 4,785
### Collisions
- Dates 2014-01-01 -> 2026-06-11 (2026 is partial: 36,424 rows) ; 2020 sharp drop (COVID) 231k(2018)->113k(2020)
- borough missing 31.6% (620,645), zip missing 31.6% (620,931), lat/lon missing 9.9% (193,919)
- 7,590 rows at (0,0); 7,740 rows with coords outside NYC bbox (incl the (0,0))
- 20 zip codes made of blank spaces -> hidden missing
- 1,590 rows duplicated on every column except collision_id
- number_of_persons_injured missing 18; number_of_persons_killed missing 8,913; sub-columns (ped/cyc/mot) complete -> can recompute
- vehicle_type_code1: 1,905 distinct values (messy); contributing_factor_vehicle_1: 66 values
- Midnight 0:00 = 1.25% (24,529), comparable to peak 16:00 (25,920) -> mild over-representation, check
- off_street_name (42.1% missing) holds cross streets; cross_street_name (79.7% missing, 265,710 unique) holds addresses -> swap confirmed
- on_street_name has trailing spaces (e.g., '111 STREET        ') -> strip

## EDA findings (Section 3)
- 24,529 crashes at exactly 0:00 vs ~757 per other minute of hour 0 (32x) -> placeholder time
- persons_injured total 673,772 > ped+cyc+mot 662,808; killed 3,183 vs 3,131 -> totals include other persons; check in cleaning
- Confidential housing records: median 1 unit (single homes); non-confidential NC median 24, P median 18
- IQR flags 1,171 buildings > 108 units: real large developments, keep
- 150 non-(0,0) points outside NYC (lon as low as -201)
- Borough preview: Bronx 27.7% units vs 16.8% ped casualties; Queens 14.2% vs 24.4%

## CORRECTION (data dictionary)
- total_units = affordable + market-rate; all_counted_units = affordable only (320,946 of 445,588 = 72.0%; 2,752 mixed-income buildings)
- Affordable units by borough: Bronx 106,661 (33.2%), Brooklyn 90,784 (28.3%), Manhattan 74,338 (23.2%), Queens 42,952 (13.4%), SI 6,211 (1.9%)
- Unit columns perfectly consistent: income sum == bedroom sum == rental+ownership == all_counted for all 9,522 rows; 29 rows all_counted missing with no breakdown
- Housing dates: start>project completion 5 rows; start>building completion 20 rows; 166 rows building completed but project not
- 123 building_ids appear in 2 projects (re-financed/phased); 121 same type
- Collisions: duplicates 1,590 = same date/minute/location/vehicles/injuries, different id -> double-entered; drop keeping lowest id
- persons_killed missing 8,877 in 2026 alone (publisher stopped filling) -> impute from sum of parts; totals<parts: 227 injured, 6 killed
- factor junk numeric codes ('1','35','36','37','52','70','80') and spelling variants (Illnes, Cell Phone (hand-Held), Drugs (Illegal), Reaction to Other Uninvolved Vehicle)
- ZIP: 235 values; invalid 10803 (Westchester), 12345; 463,458 crashes have valid coords but no zip; 157,493 no coords & no zip
- KNN (10% holdout): zip k=1 99.56%, k=5 99.44%, k=15 99.03%; borough k=5 99.9%

## Step 4 results
- Collisions: 1,964,900 -> 1,963,310 rows (1,590 duplicates removed); 34 columns saved
- ZIP missing 620,290 -> 157,223 (8.0%) via kNN (k=1, 99.58% holdout); borough 619,982 -> 157,192 (k=5, 99.90%)
- Invalid coords -> NaN: 7,589 (0,0) + 150 outside; casualty totals fixed: injured 18 filled + 223 raised; killed 8,908 filled + 6 raised
- Severity: PDO 1,462,605 / Injury 497,630 / Fatal 3,075; time_unknown 24,521; partial year 2026 36,410
- 17 crashes with 20+ injured: 12 involve a bus
- Housing: 49 columns saved; 106,309 empty unit cells -> 0; all consistency checks 100%; Marble Hill 5 rows ZIP 10463 borough Manhattan (correct)
- Completed 7,898 / In progress 1,653; 21 rows start after completion (flagged); 247 rows in multi-project buildings
