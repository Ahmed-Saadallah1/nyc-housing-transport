# Homes on Dangerous Streets?
### Linking NYC Affordable Housing Production to Motor Vehicle Collisions

Data Engineering and Visualization — Winter Semester 2026 — Project Milestone 1
German International University, Faculty of Informatics and Computer Science

**Question:** Where do NYC affordable-housing production and recorded pedestrian harm overlap, and how do recorded crashes compare around sites and administrative completion dates?

| | Link |
|---|---|
| Website (deployed) | [Homes on Dangerous Streets?](https://nyc-housing-transport.vercel.app/) |
| Notebook | [`notebooks/Milestone1_Housing_Collisions.ipynb`](notebooks/Milestone1_Housing_Collisions.ipynb) |
| Housing dataset | [Affordable Housing Production by Building (`hg8x-zxpr`)](https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr) |
| Transportation dataset | [Motor Vehicle Collisions – Crashes (`h9gi-nx95`)](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95) |

## Findings and scope

* Higher-production ZIP codes had higher pedestrian casualties per reported crash in the notebook comparison.
  Production includes new construction and preservation; casualties count people, not the percentage of crashes.
* Within-ZIP comparisons found a positive near-site pedestrian-involvement difference in most eligible ZIPs.
* New-construction sites had higher historical nearby recorded crash counts than preservation sites. This does not
  measure street busyness or traffic volume.
* Upper-quartile production and pedestrian casualties per crash provide a descriptive shortlist for further HPD/DOT review.
* Completion-window and next-year-growth comparisons do not establish causal effects or validated predictive performance.

The spatial inventory is retrospective: sites may be unfinished or completed after a crash. Only housing records with
known affordable counts enter unit/site analyses; unknown totals remain missing in the cleaned source. Overlapping
buffers, estimated ZIPs, reporting changes and missing locations limit inference. Population, occupancy, residents’
travel modes and pedestrian/traffic exposure are not measured. Exact results and snapshot hashes are in the executed
notebook; website tables must be regenerated from those outputs.

## Repository structure

```
nyc-housing-transport/
├── notebooks/
│   └── Milestone1_Housing_Collisions.ipynb   # EDA, cleaning, integration, 12 research questions, story
├── app/
│   ├── app.py              # Dash website (filters, search, Generate Report, 5 charts, story)
│   ├── prepare_data.py     # builds app/data/ (CSV) from the notebook's cleaned outputs
│   ├── data/               # small pre-aggregated CSV tables used by the website
│   ├── assets/style.css    # website styling
│   └── requirements.txt    # website dependencies (pinned)
├── data/
│   ├── raw/                # raw API snapshots (created by the notebook; not committed)
│   └── processed/          # cleaned and integrated tables (created by the notebook; not committed)
├── docs/
│   ├── prompt_log.md       # every prompt used, as required by the project description
│   └── data_findings_log.md
├── wsgi.py                 # Flask entry point for Vercel
├── pyproject.toml          # Vercel website dependencies and Python version
├── vercel.json             # Vercel framework and function configuration
├── .vercelignore           # excludes notebooks and large source data from deployment
├── requirements.txt        # notebook dependencies
└── README.md
```

## Setup

### 1. Run the notebook (Google Colab — recommended)
1. Open [colab.research.google.com](https://colab.research.google.com) → **File → Upload notebook** →
   `notebooks/Milestone1_Housing_Collisions.ipynb`.
2. **Runtime → Run all.** Allow Google Drive access when asked.
3. The first run downloads housing and crashes since 2014 from NYC Open Data into
   `My Drive/nyc-housing-transport/data/raw`. Later runs reuse these Parquet snapshots. Keep the cache and share
   the exact files explicitly with teammates; separate MyDrive folders do not automatically share data.
   Runtime and memory depend on the snapshot and Colab allocation; a large download can take several minutes.
4. The cleaned and integrated tables are written to `My Drive/nyc-housing-transport/data/processed`.

### 2. Run locally (optional)
```bash
python3.13 -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/Milestone1_Housing_Collisions.ipynb
```

The notebook locates the cloned repository from its working directory or a parent directory and writes to the
repository's `data/`. Cached files without retrieval sidecars are explicitly labelled as having an unknown retrieval
timestamp; file modification time is not substituted. SHA-256 fingerprints and validation time are always reported.
New downloads record request parameters and retrieval time. Do not delete a working cache merely to rerun a correction.

### 3. Run the website locally
```bash
pip install -r app/requirements.txt
python app/app.py                 # open http://127.0.0.1:8050
```
The website reads only the small CSV tables in `app/data/`. To rebuild them after re-running the notebook, download the
four Parquet files from `My Drive/nyc-housing-transport/data/processed` into the repository's `data/processed/`
folder and run (requires `scikit-learn`):
```bash
python app/prepare_data.py
```

## Website

| Requirement | Implementation |
|---|---|
| Multiple dropdown filters | Borough, Year, Housing type (housing category), Who was hurt (road-user category), Crash severity |
| Search mode | Free text such as `Brooklyn 2022 new buildings` sets the dropdowns automatically (filters not mentioned go back to their defaults) |
| "Generate Report" button | Applies relevant filters; trend/production highlight the selected year. Housing-only metrics ignore crash filters; building hovers are explicitly fixed historical averages |
| Variety of interactive charts | Map, scatter plot, line chart, heatmap, bar chart — all with hover, zoom and legend toggling |
| Relationship between the two domains | The map overlays affordable buildings on ZIP-code crash harm; the scatter plot relates affordable units to people hurt per crash |
| Story section | The question, findings, limitations and benefit for NYC |

## Deployment (Vercel Hobby)

The repository is configured to run the existing Dash website through its Flask server on Vercel.
The notebook is not executed during deployment. The website reads the committed CSV tables in `app/data/`.

1. Push the reviewed changes to GitHub, then import your GitHub fork in Vercel.
2. Select your personal **Hobby** plan, not a Pro trial or paid team.
3. Use these project settings:

   | Setting | Value |
   |---|---|
   | Root Directory | Repository root (`./`), not `app` |
   | Framework Preset | Flask |
   | Build Command | Leave unset; do not run the notebook or data preparation |
   | Install Command | Leave unset; Vercel reads `pyproject.toml` |
   | Output Directory | Leave unset |
   | Environment Variables | None required |

4. Select **Deploy**. `pyproject.toml` selects Python 3.13 and `wsgi:app`, which exports Dash's Flask server.
   `.vercelignore` excludes the notebook and raw/processed data from the upload.
5. Open the generated `https://<project>.vercel.app` URL. Test every dropdown, the search
   `Brooklyn 2022 new buildings`, **Generate Report**, chart hover/zoom, and a sparse selection on desktop and phone.
   Check Vercel runtime logs if a page or callback fails.
6. Keep the website link at the top of this README current.
   Verify that a signed-out visitor can open the production site without Vercel authentication.

No API keys, database, custom domain, notebook runtime, or payment method is needed by the application.
If signup requests a payment method, stop and check that you selected Hobby; do not activate a paid plan.
Hobby usage limits apply. After connecting GitHub, pushes to the configured production branch trigger redeployment.

The root `pyproject.toml` declares only Vercel runtime dependencies. Keep using `requirements.txt` for notebook
execution and `app/requirements.txt` for the existing local website setup. Vercel serves the Dash component bundles
and `app/assets/style.css` through the Flask application.

References: [Flask on Vercel](https://vercel.com/docs/frameworks/backend/flask),
[Python version](https://vercel.com/docs/functions/runtimes/python/python-version),
[Hobby plan](https://vercel.com/docs/plans/hobby).

## Member contributions

| Member | ID | Research questions & visualizations | Data cleaning | Integration | Website | Other |
|---|---|---|---|---|---|---|
| Ahmed Saadallah | 16008325 | RQ1 (scatter), RQ2 (box plot) | Housing hidden missing values & formats (H1) | Integration design (2.5) | Search mode; deployment | Dataset selection & overview, coordination |
| Ismail Ahmed Mohamed | 16002979 | RQ3 (histogram), RQ4 (grouped bar) | Casualty consistency & outliers (C6) | 250 m spatial join, before/after windows (5.2) | "Generate Report" button and report callbacks | Statistical tests |
| Ziad Elshayeb | 16002080 | RQ5 (diverging heatmap), RQ6 (diverging bar) | Collisions structure, formats & categories (C1 – C3) | Crash distance to nearest building (5.3) | Time-pattern heatmap | Collisions EDA (3.1) |
| Renad Osama | 16001737 | RQ7 (line chart), RQ8 (scatter) | Housing unit counts & dates (H2 – H3) | ZIP × year aggregation (5.1) | Trend charts and story section | Data story (Section 9) |
| Yassin Amr | 16005309 | RQ9 (grouped bar), RQ10 (bubble map) | Duplicates, coordinates, time flags (C4, C5, C7) | ZIP/borough recovery with k-NN (C8) | Interactive map | Visual style |
| Yassin Elazab | 16006124 | RQ11 (box + strip plot), RQ12 (scatter) | Housing duplicates & domain checks (H4) | Post-integration cleaning & validation (6 – 7) | Dropdown filters and page layout | Housing EDA (3.2), README |

## AI use

Claude was used for initial planning, drafting and writing. Codex was used for corrective review, implementation and local verification. Documented prompts are
listed in [`docs/prompt_log.md`](docs/prompt_log.md) and in Section 11 of the notebook.
