# Homes on Dangerous Streets?
### Linking NYC Affordable Housing Production to Motor Vehicle Collisions

Data Engineering and Visualization — Winter Semester 2026 — Project Milestone 1
German International University, Faculty of Informatics and Computer Science

**Question:** Are New York's newest affordable homes — especially those for the lowest-income households — being built
on the city's most dangerous streets, and does street safety around them change once residents move in?

| | Link |
|---|---|
| Website (deployed) | **`<paste the Render URL here>`** |
| Notebook | [`notebooks/Milestone1_Housing_Collisions.ipynb`](notebooks/Milestone1_Housing_Collisions.ipynb) |
| Housing dataset | [Affordable Housing Production by Building (`hg8x-zxpr`)](https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr) |
| Transportation dataset | [Motor Vehicle Collisions – Crashes (`h9gi-nx95`)](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95) |

## Key findings

* ZIP codes with the most new affordable housing have crashes that hurt pedestrians far more often (7.2 vs 4.3 per 100
  crashes, top vs bottom quarter; Spearman ρ ≈ 0.45).
* Even inside the same ZIP code, crashes within 250 m of an affordable building hurt a pedestrian more often in 78% of
  ZIP codes (Wilcoxon p < 0.001).
* 20 hotspot ZIP codes combine heavy affordable production with high pedestrian harm (mostly the Bronx, Harlem, the
  Lower East Side and central Brooklyn).
* Crashes around newly completed buildings change at the same pace as the city: the issue is *where* homes are built.
* These are associations, not causes; rates are per crash because neither dataset contains population.

## Repository structure

```
nyc-housing-transport/
├── notebooks/
│   └── Milestone1_Housing_Collisions.ipynb   # EDA, cleaning, integration, 12 research questions, story
├── app/
│   ├── app.py              # Dash website (filters, search, Generate report, 5 charts, story)
│   ├── prepare_data.py     # builds app/data/*.parquet from the notebook's cleaned outputs
│   ├── data/               # small pre-aggregated tables used by the website (< 1 MB, committed)
│   ├── assets/style.css    # website styling
│   └── requirements.txt    # website dependencies (pinned)
├── data/
│   ├── raw/                # raw API snapshots (created by the notebook; not committed)
│   └── processed/          # cleaned and integrated tables (created by the notebook; not committed)
├── docs/
│   ├── prompt_log.md       # every prompt used, as required by the project description
│   └── data_findings_log.md
├── render.yaml             # Render deployment blueprint
├── requirements.txt        # notebook dependencies
└── README.md
```

## Setup

### 1. Run the notebook (Google Colab — recommended)
1. Open [colab.research.google.com](https://colab.research.google.com) → **File → Upload notebook** →
   `notebooks/Milestone1_Housing_Collisions.ipynb`.
2. **Runtime → Run all.** Allow Google Drive access when asked.
3. The first run downloads the data from the NYC Open Data API (≈ 10 minutes for 1.96 M crashes) and stores it in
   `My Drive/nyc-housing-transport/data/raw`; later runs load the saved snapshot in seconds. The whole notebook then
   runs in about 5 minutes and needs about 5 GB of memory (the free Colab tier is enough).
4. The cleaned and integrated tables are written to `My Drive/nyc-housing-transport/data/processed`.

### 2. Run locally (optional)
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebooks/Milestone1_Housing_Collisions.ipynb   # outside Colab, data is stored in ./data
```

### 3. Run the website locally
```bash
pip install -r app/requirements.txt
python app/app.py                 # open http://127.0.0.1:8050
```
The website reads only the small tables in `app/data/`. To rebuild them after re-running the notebook, download the
four Parquet files from `My Drive/nyc-housing-transport/data/processed` into the repository's `data/processed/`
folder and run (requires `scikit-learn`):
```bash
python app/prepare_data.py
```

## Website

| Requirement | Implementation |
|---|---|
| Multiple dropdown filters | Borough, Year, Housing type (housing category), Who was hurt (road-user category), Crash severity |
| Search mode | Free text such as `Bronx 2022 new construction pedestrians` sets the dropdowns automatically |
| "Generate report" button | Rebuilds every chart and summary number from the selected filters; a hint appears when the filters change |
| Variety of interactive charts | Map, scatter plot, line chart, heatmap, bar chart — all with hover, zoom and legend toggling |
| Relationship between the two domains | The map overlays affordable buildings on ZIP-code crash harm; the scatter plot relates affordable units to people hurt per crash |
| Story section | The question, findings, limitations and benefit for NYC |

## Deployment (Render, free tier)

1. Push this repository to GitHub.
2. On [render.com](https://render.com), sign in with GitHub → **New → Blueprint** → select the repository.
   Render reads `render.yaml` and creates the web service:
   * build: `pip install -r app/requirements.txt`
   * start: `gunicorn app.app:server --workers 1 --threads 4 --timeout 120`
   * Python 3.13.1
3. Wait for the build to finish (≈ 3 minutes) and open the URL Render shows (`https://<name>.onrender.com`).
4. Test: change the filters, use the search box, select **Generate report**, hover and zoom the charts.

The free tier sleeps after 15 minutes without visits; the first request after that takes about 30 – 60 seconds.
The website uses about 300 MB of memory (limit: 512 MB).

## Member contributions

| Member | ID | Research questions & visualizations | Data cleaning | Integration | Website | Other |
|---|---|---|---|---|---|---|
| Ahmed Saadallah | 16008325 | RQ1 (scatter), RQ2 (box plot) | Housing hidden missing values & formats (H1) | Integration design (2.5) | Search mode; deployment | Dataset selection & overview, coordination |
| Ismail Ahmed Mohamed | 16002979 | RQ3 (histogram), RQ4 (grouped bar) | Casualty consistency & outliers (C6) | 250 m spatial join, before/after windows (5.2) | "Generate report" button and report callbacks | Statistical tests |
| Ziad Elshayeb | 16002080 | RQ5 (diverging heatmap), RQ6 (diverging bar) | Collisions structure, formats & categories (C1 – C3) | Crash distance to nearest building (5.3) | Time-pattern heatmap | Collisions EDA (3.1) |
| Renad Osama | 16001737 | RQ7 (line chart), RQ8 (scatter) | Housing unit counts & dates (H2 – H3) | ZIP × year aggregation (5.1) | Trend charts and story section | Data story (Section 9) |
| Yassin Amr | 16005309 | RQ9 (grouped bar), RQ10 (bubble map) | Duplicates, coordinates, time flags (C4, C5, C7) | ZIP/borough recovery with k-NN (C8) | Interactive map | Visual style |
| Yassin Elazab | 16006124 | RQ11 (box + strip plot), RQ12 (scatter) | Housing duplicates & domain checks (H4) | Post-integration cleaning & validation (6 – 7) | Dropdown filters and page layout | Housing EDA (3.2), README |

## AI use

An AI assistant (Claude, by Anthropic) was used for planning, code drafting, verification and writing. All prompts are
listed in [`docs/prompt_log.md`](docs/prompt_log.md) and in Section 11 of the notebook.
