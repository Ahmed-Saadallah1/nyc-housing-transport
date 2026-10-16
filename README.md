# Homes on Dangerous Streets?
### Linking NYC Affordable Housing Production to Motor Vehicle Collisions

Data Engineering and Visualization — Winter Semester 2026 — Project Milestone 1
German International University, Faculty of Informatics and Computer Science

**Question:** Are New York's newest affordable homes — especially those for the lowest-income households — being built
on the city's most dangerous streets, and does street safety around them change once residents move in?

| | Link |
|---|---|
| Website (deployed) | **`<paste the website link here, e.g. https://USERNAME.pythonanywhere.com>`** |
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
│   ├── app.py              # Dash website (filters, search, Generate Report, 5 charts, story)
│   ├── prepare_data.py     # builds app/data/ (Parquet + CSV) from the notebook's cleaned outputs
│   ├── data/               # small pre-aggregated tables used by the website: .parquet and .csv copies
│   ├── assets/style.css    # website styling
│   └── requirements.txt    # website dependencies (pinned)
├── data/
│   ├── raw/                # raw API snapshots (created by the notebook; not committed)
│   └── processed/          # cleaned and integrated tables (created by the notebook; not committed)
├── docs/
│   ├── prompt_log.md       # every prompt used, as required by the project description
│   └── data_findings_log.md
├── deploy/
│   ├── pythonanywhere_wsgi.py          # WSGI entry point for PythonAnywhere
│   └── requirements-pythonanywhere.txt # packages to install on PythonAnywhere
├── render.yaml             # alternative: Render deployment blueprint
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
The website reads only the small tables in `app/data/`: the Parquet files when `pyarrow` is installed, otherwise the
identical CSV copies (this is what PythonAnywhere uses). To rebuild them after re-running the notebook, download the
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
| "Generate Report" button | Rebuilds every chart and summary number from the selected filters; a hint appears when the filters change |
| Variety of interactive charts | Map, scatter plot, line chart, heatmap, bar chart — all with hover, zoom and legend toggling |
| Relationship between the two domains | The map overlays affordable buildings on ZIP-code crash harm; the scatter plot relates affordable units to people hurt per crash |
| Story section | The question, findings, limitations and benefit for NYC |

## Deployment (PythonAnywhere, free account)

The website is hosted on [PythonAnywhere](https://www.pythonanywhere.com). A free account allows one web app at
`https://USERNAME.pythonanywhere.com`, which stays awake (no cold start for visitors). The app needs no `pyarrow` there:
it reads the CSV copies in `app/data/`.

**1. Create the account.** Sign up for a free *Beginner* account. The username becomes the address of the website.

**2. Get the code and install the packages.** Open **Consoles → Bash** and run:
```bash
git clone --depth 1 https://github.com/Ahmed-Saadallah1/nyc-housing-transport.git
cd nyc-housing-transport
pip3.13 install --user --no-cache-dir -r deploy/requirements-pythonanywhere.txt
```
(`--no-cache-dir` keeps the download cache out of the 512 MB disk quota.)

**3. Create the web app.** Open the **Web** tab → **Add a new web app** → **Next** → **Manual configuration** (not
"Flask") → **Python 3.13** → **Next**.

**4. Point it at the Dash app.** On the Web tab, open the **WSGI configuration file** link, delete everything in it,
paste the contents of [`deploy/pythonanywhere_wsgi.py`](deploy/pythonanywhere_wsgi.py), replace `YOUR_USERNAME` with
your PythonAnywhere username, and **Save**.

**5. Go live.** Back on the Web tab, select **Reload**, then open `https://USERNAME.pythonanywhere.com`.

**6. Test** the live site: change every dropdown, try the search box (e.g. `Brooklyn 2022 new buildings`), select
**Generate Report**, hover and zoom the charts, and open it on a phone.

**Keep it online for grading.** Free web apps switch off after one month unless renewed. On the Web tab, select
**"Run until 1 month from today"** on the submission day (9 November 2026) so the site stays up while it is graded.

**Troubleshooting.** If the page shows an error, open the **Error log** link on the Web tab. The most common cause is
a wrong path or username in the WSGI file.

**Updating the site.** After pushing changes to GitHub: in the Bash console run `cd ~/nyc-housing-transport && git pull`,
then select **Reload** on the Web tab.

### Alternative: Render
`render.yaml` deploys the same app on [Render](https://render.com) (**New → Blueprint** → select this repository). The
free plan sleeps after 15 minutes without visits, so the first page load can take about a minute.

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

An AI assistant (Claude, by Anthropic) was used for planning, code drafting, verification and writing. All prompts are
listed in [`docs/prompt_log.md`](docs/prompt_log.md) and in Section 11 of the notebook.
