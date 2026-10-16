"""Homes on Dangerous Streets? — interactive website (Dash).

Explore how NYC's affordable-housing production (HPD) relates to motor-vehicle crashes (NYPD), 2014-2025.
Data: pre-aggregated tables in app/data/, built by app/prepare_data.py from the notebook's cleaned outputs.

Run locally:  python app/app.py            (then open http://127.0.0.1:8050)
Production:   PythonAnywhere WSGI (deploy/pythonanywhere_wsgi.py) or gunicorn app.app:server (render.yaml)
"""
import os
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

# --------------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TEXT_COLUMNS = {"zip_code": str, "building_id": str}  # identifiers stay text when read from CSV


def load(name):
    # Read a website table: Parquet when pyarrow is installed (Render / local), otherwise the CSV copy
    # (PythonAnywhere free accounts, where installing pyarrow does not fit in the disk quota).
    parquet_path = os.path.join(DATA_DIR, f"{name}.parquet")
    try:
        return pd.read_parquet(parquet_path)
    except ImportError:
        return pd.read_csv(os.path.join(DATA_DIR, f"{name}.csv"), dtype=TEXT_COLUMNS)


CRASH_CUBE = load("crash_cube")
ZIP_CRASHES = load("zip_crashes")
ZIP_HOUSING = load("zip_housing")
ZIP_CENTRES = load("zip_centres")
BUILDINGS = load("buildings")
HOUSING_YEARS = load("housing_years")
ZIP_BOROUGH = ZIP_HOUSING.drop_duplicates("zip_code").set_index("zip_code")["borough"]

YEARS = list(range(2014, 2026))
BOROUGHS = ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Colours shared with the notebook (colour-blind-checked order)
HOUSING_BLUE, CRASH_RED, GREY, INK, MUTED = "#2a78d6", "#e34948", "#b9bcb6", "#1d2329", "#5b6168"
TYPE_COLORS = {"New Construction": "#2a78d6", "Preservation": "#eb6834"}
BOROUGH_COLORS = dict(zip(["Brooklyn", "Bronx", "Manhattan", "Queens", "Staten Island"],
                          ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))

ROAD_USERS = {  # dropdown value -> (cube column, label used in text)
    "all": ("all_casualties", "people"),
    "pedestrians": ("pedestrian_casualties", "pedestrians"),
    "cyclists": ("cyclist_casualties", "cyclists"),
    "motorists": ("motorist_casualties", "motorists"),
}
MAP_STYLE = os.environ.get("MAP_STYLE", "carto-positron")  # base map tiles (needs internet in the browser)
SEVERITY = {"all": None, "injury": ["Injury", "Fatal"], "fatal": ["Fatal"]}
DEFAULT_FILTERS = {"borough": "all", "year": "all", "construction": "all", "road_user": "pedestrians",
                   "severity": "all"}

# --------------------------------------------------------------------------------------
# Search: free text -> filter values
# --------------------------------------------------------------------------------------
SEARCH_TERMS = [  # (regex, filter, value) - checked in order, first match per filter wins
    (r"\bstaten\s*island\b|\bsi\b", "borough", "Staten Island"),
    (r"\bbronx\b", "borough", "Bronx"),
    (r"\bbrooklyn\b|\bbk\b", "borough", "Brooklyn"),
    (r"\bmanhattan\b|\bmn\b", "borough", "Manhattan"),
    (r"\bqueens\b|\bqn\b", "borough", "Queens"),
    (r"\bnew\s*(construction|buildings?|builds?)\b|\bnew\b", "construction", "New Construction"),
    (r"\bpreserv\w*\b", "construction", "Preservation"),
    (r"\bpedestrians?\b|\bwalk\w*\b|\bon foot\b", "road_user", "pedestrians"),
    (r"\bcyclists?\b|\bbikes?\b|\bbicycl\w*\b|\be-?bikes?\b", "road_user", "cyclists"),
    (r"\bmotorists?\b|\bdrivers?\b|\bcars?\b", "road_user", "motorists"),
    (r"\bfatal\w*\b|\bdeadly\b|\bdeaths?\b|\bkilled\b", "severity", "fatal"),
    (r"\binjur\w*\b", "severity", "injury"),
]


def parse_search(text):
    # Turn a free-text query into filter values; returns (filters found, words not understood).
    query = (text or "").lower()
    found = {}
    year = re.search(r"\b(20(1[4-9]|2[0-5]))\b", query)
    if year:
        found["year"] = int(year.group(1))
        query = query.replace(year.group(1), " ")
    for pattern, key, value in SEARCH_TERMS:
        match = re.search(pattern, query)
        if match and key not in found:
            found[key] = value
            query = query[:match.start()] + " " + query[match.end():]
    leftover = [w for w in re.findall(r"[a-z0-9-]+", query)
                if w not in {"in", "the", "and", "of", "for", "at", "near", "crashes", "crash", "housing",
                             "affordable", "homes", "units", "all", "show", "me", "to", "from"}]
    return found, leftover


# --------------------------------------------------------------------------------------
# Filtering helpers
# --------------------------------------------------------------------------------------
def near_column(construction):
    # Which "near affordable housing" flag to use for the chosen construction type
    if construction == "New Construction":
        return CRASH_CUBE["near_new_construction"]
    if construction == "Preservation":
        return CRASH_CUBE["near_preservation"]
    return CRASH_CUBE["near_new_construction"] | CRASH_CUBE["near_preservation"]


def filter_cube(f, use_year=True):
    cube = CRASH_CUBE.assign(near=near_column(f["construction"]))
    if f["borough"] != "all":
        cube = cube[cube["borough"] == f["borough"]]
    if use_year and f["year"] != "all":
        cube = cube[cube["year"] == int(f["year"])]
    if SEVERITY[f["severity"]]:
        cube = cube[cube["severity"].isin(SEVERITY[f["severity"]])]
    return cube


def filter_buildings(f):
    b = BUILDINGS
    if f["borough"] != "all":
        b = b[b["borough"] == f["borough"]]
    if f["construction"] != "all":
        b = b[b["construction_type"] == f["construction"]]
    if f["year"] != "all":
        b = b[b["completion_year"] == int(f["year"])]
    return b


def zip_table(f):
    # One row per ZIP: crashes and casualties (selected filters) + affordable units completed
    measure = ROAD_USERS[f["road_user"]][0]
    crashes = ZIP_CRASHES
    housing = ZIP_HOUSING
    if f["year"] != "all":
        crashes = crashes[crashes["year"] == int(f["year"])]
        housing = housing[housing["year"] == int(f["year"])]
    if SEVERITY[f["severity"]]:
        crashes = crashes[crashes["severity"].isin(SEVERITY[f["severity"]])]
    units_col = {"all": "affordable_units_completed", "New Construction": "new_construction_units_completed",
                 "Preservation": "preservation_units_completed"}[f["construction"]]
    table = (crashes.groupby("zip_code")[["crashes", measure]].sum()
             .join(housing.groupby("zip_code")[units_col].sum().rename("units"), how="outer").fillna(0)
             .join(ZIP_BOROUGH).join(ZIP_CENTRES.set_index("zip_code")).reset_index())
    if f["borough"] != "all":
        table = table[table["borough"] == f["borough"]]
    table["rate"] = np.where(table["crashes"] > 0, 100 * table[measure] / table["crashes"].clip(lower=1), np.nan)
    return table


# --------------------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------------------
FONT = "Public Sans, Helvetica, Arial, sans-serif"


def base_layout(fig, height=420, **overrides):
    # Shared look for every chart; `overrides` replace the defaults (e.g. legend or margins of the map)
    layout = {"template": "plotly_white", "height": height, "font": {"family": FONT, "size": 13, "color": INK},
              "margin": {"l": 56, "r": 16, "t": 16, "b": 48}, "hoverlabel": {"font_family": FONT},
              "legend": {"orientation": "h", "y": -0.18, "x": 0}}
    layout.update(overrides)
    fig.update_layout(**layout)
    return fig


def empty_figure(message, height=420):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font={"size": 15, "color": MUTED})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return base_layout(fig, height)


def map_figure(f):
    zips = zip_table(f)
    zips = zips[(zips["crashes"] >= 20) & zips["latitude"].notna()]
    who = ROAD_USERS[f["road_user"]][1]
    buildings = filter_buildings(f)
    fig = go.Figure()
    fig.add_trace(go.Scattermap(
        lat=zips["latitude"], lon=zips["longitude"], mode="markers", name="ZIP code (crash rate)",
        marker={"size": 26, "color": zips["rate"], "colorscale": "Reds", "opacity": 0.7,
                "colorbar": {"title": {"text": f"{who.capitalize()} hurt<br>per 100 crashes", "side": "right"},
                             "thickness": 12, "len": 0.75}},
        text=zips["zip_code"], customdata=np.c_[zips["crashes"], zips["units"]],
        hovertemplate=("<b>ZIP %{text}</b><br>%{marker.color:.1f} " + who + " hurt per 100 crashes"
                       "<br>%{customdata[0]:,.0f} crashes<br>%{customdata[1]:,.0f} affordable units completed"
                       "<extra></extra>")))
    if len(buildings):
        fig.add_trace(go.Scattermap(
            lat=buildings["latitude"], lon=buildings["longitude"], mode="markers", name="Affordable building",
            marker={"size": np.clip(np.sqrt(buildings["affordable_units"].clip(lower=1)) * 0.7, 3, 11),
                    "color": HOUSING_BLUE, "opacity": 0.55},
            text=buildings["construction_type"],
            customdata=np.c_[buildings["affordable_units"], buildings["completion_year"].astype("float"),
                             buildings["pedestrian_casualties_per_year"]],
            hovertemplate=("<b>%{text}</b><br>%{customdata[0]:,.0f} affordable units"
                           "<br>completed %{customdata[1]:.0f}"
                           "<br>%{customdata[2]:.1f} pedestrians hurt per year within 250 m<extra></extra>")))
    centre = ({"lat": zips["latitude"].mean(), "lon": zips["longitude"].mean()} if f["borough"] != "all" and len(zips)
              else {"lat": 40.71, "lon": -73.93})
    fig.update_layout(map={"style": MAP_STYLE, "center": centre, "zoom": 10.4 if f["borough"] != "all" else 9.4})
    return base_layout(fig, 520, legend={"orientation": "h", "y": 1.02, "x": 0, "bgcolor": "rgba(255,255,255,0.8)"},
                       margin={"l": 0, "r": 0, "t": 0, "b": 0})


def scatter_figure(f):
    zips = zip_table(f)
    zips = zips[zips["crashes"] >= 20]
    if len(zips) < 3:
        return empty_figure("Too few ZIP codes with 20+ crashes for this selection")
    who = ROAD_USERS[f["road_user"]][1]
    fig = go.Figure()
    for borough in BOROUGHS:
        part = zips[zips["borough"] == borough]
        if len(part):
            fig.add_trace(go.Scatter(
                x=part["units"] + 1, y=part["rate"], mode="markers", name=borough, text=part["zip_code"],
                marker={"size": 9, "color": BOROUGH_COLORS[borough], "line": {"width": 1, "color": "white"}},
                customdata=part["units"],
                hovertemplate="<b>ZIP %{text}</b><br>%{customdata:,.0f} affordable units"
                              "<br>%{y:.1f} " + who + " hurt per 100 crashes<extra></extra>"))
    rho = zips["units"].rank().corr(zips["rate"].rank())
    rho_text = f"{rho:.2f}" if pd.notna(rho) else "not defined (no variation for this selection)"
    fig.update_xaxes(type="log", title="Affordable units completed (log scale)",
                     tickvals=[1, 11, 101, 1001, 10001], ticktext=["0", "10", "100", "1,000", "10,000"])
    fig.update_yaxes(title=f"{who.capitalize()} hurt per 100 crashes", rangemode="tozero")
    fig.add_annotation(text=f"Spearman rank correlation: {rho_text} ({len(zips)} ZIP codes)", xref="paper",
                       yref="paper", x=0, y=1.06, showarrow=False, xanchor="left", font={"color": MUTED, "size": 12})
    return base_layout(fig)


def trend_figure(f):
    cube = filter_cube(f, use_year=False)
    cube = cube[cube["located"]]
    measure, who = ROAD_USERS[f["road_user"]]
    yearly = cube.groupby(["year", "near"])[["crashes", measure]].sum().reset_index()
    yearly["rate"] = 100 * yearly[measure] / yearly["crashes"].clip(lower=1)
    fig = go.Figure()
    for near, name, color in [(True, "Within 250 m of affordable housing", CRASH_RED),
                              (False, "Farther than 250 m", GREY)]:
        part = yearly[yearly["near"] == near]
        fig.add_trace(go.Scatter(x=part["year"], y=part["rate"], mode="lines+markers", name=name,
                                 line={"color": color, "width": 2.5}, marker={"size": 7},
                                 hovertemplate="%{x}: %{y:.1f} " + who + " hurt per 100 crashes<extra>"
                                               + name + "</extra>"))
    if f["year"] != "all":
        fig.add_vrect(x0=int(f["year"]) - 0.5, x1=int(f["year"]) + 0.5, fillcolor=HOUSING_BLUE, opacity=0.08,
                      line_width=0)
    fig.add_vline(x=2020, line_dash="dot", line_color=MUTED)
    fig.add_annotation(x=2020, y=1, yref="paper", text="COVID-19", showarrow=False, xanchor="left",
                       font={"color": MUTED, "size": 11})
    fig.update_xaxes(dtick=1, title=None)
    fig.update_yaxes(title=f"{who.capitalize()} hurt per 100 crashes", rangemode="tozero")
    return base_layout(fig)


def heatmap_figure(f):
    cube = filter_cube(f)
    cube = cube[cube["located"] & cube["near"] & ~cube["time_unknown"]]
    measure, who = ROAD_USERS[f["road_user"]]
    grid = (cube.groupby(["weekday", "crash_hour"])[measure].sum()
            .unstack(fill_value=0).reindex(index=range(7), columns=range(24), fill_value=0))
    total = grid.to_numpy().sum()
    if total == 0:
        return empty_figure(f"No {who} hurt near affordable housing for this selection")
    share = 100 * grid / total
    fig = go.Figure(go.Heatmap(
        z=share.to_numpy(), x=list(range(24)), y=WEEKDAYS, colorscale="Blues", customdata=grid.to_numpy(),
        colorbar={"title": {"text": "% of total", "side": "right"}, "thickness": 12},
        hovertemplate="%{y} %{x}:00<br>%{z:.2f}% of " + who + " hurt (%{customdata:,} people)<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Hour of day", dtick=2)
    return base_layout(fig)


def production_figure(f):
    h = HOUSING_YEARS
    if f["borough"] != "all":
        h = h[h["borough"] == f["borough"]]
    yearly = h.groupby(["year", "construction_type"])["affordable_units"].sum().unstack(fill_value=0) \
              .reindex(YEARS, fill_value=0)
    fig = go.Figure()
    for ctype in ["New Construction", "Preservation"]:
        if f["construction"] in ("all", ctype) and ctype in yearly:
            opacity = [1 if f["year"] in ("all", str(y), y) else 0.35 for y in yearly.index]
            fig.add_trace(go.Bar(x=yearly.index, y=yearly[ctype], name=ctype, marker_color=TYPE_COLORS[ctype],
                                 marker_opacity=opacity,
                                 hovertemplate="%{x}: %{y:,} affordable units<extra>" + ctype + "</extra>"))
    fig.update_layout(barmode="group", bargap=0.25)
    fig.update_xaxes(dtick=1, title="Year of completion")
    fig.update_yaxes(title="Affordable units completed", tickformat=",")
    return base_layout(fig)


def kpis(f):
    cube = filter_cube(f)
    measure, who = ROAD_USERS[f["road_user"]]
    located = cube[cube["located"]]
    near_share = located.loc[located["near"], measure].sum() / max(located[measure].sum(), 1)
    h = HOUSING_YEARS
    if f["borough"] != "all":
        h = h[h["borough"] == f["borough"]]
    if f["year"] != "all":
        h = h[h["year"] == int(f["year"])]
    if f["construction"] != "all":
        h = h[h["construction_type"] == f["construction"]]
    return [
        (f"{cube['crashes'].sum():,}", "crashes"),
        (f"{cube[measure].sum():,}", f"{who} injured or killed"),
        (f"{near_share:.0%}", f"of {who} hurt were within 250 m of affordable housing"),
        (f"{h['affordable_units'].sum():,}", "affordable units completed"),
    ]


def describe(f):
    parts = [f["borough"] if f["borough"] != "all" else "All boroughs",
             str(f["year"]) if f["year"] != "all" else "2014 – 2025",
             {"all": "all affordable housing", "New Construction": "new construction",
              "Preservation": "preservation"}[f["construction"]],
             {"all": "all people", "pedestrians": "pedestrians", "cyclists": "cyclists",
              "motorists": "motorists"}[f["road_user"]],
             {"all": "all crashes", "injury": "injury or fatal crashes", "fatal": "fatal crashes"}[f["severity"]]]
    return "Report for " + ", ".join(parts)


# --------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------
def dropdown(id_, label, options, value):
    return html.Div(className="filter", children=[
        html.Label(label, htmlFor=id_),
        dcc.Dropdown(id=id_, options=options, value=value, clearable=False, searchable=False)])


def card(title, subtitle, graph_id, wide=False):
    return html.Section(className="card wide" if wide else "card", children=[
        html.H3(title), html.P(subtitle, className="card-sub"),
        dcc.Loading(dcc.Graph(id=graph_id, config={"displaylogo": False, "scrollZoom": graph_id == "map"}),
                    type="dot", color=HOUSING_BLUE)])


app = Dash(__name__, title="Homes on Dangerous Streets?",
           external_stylesheets=["https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700"
                                 "&family=Public+Sans:wght@400;600;700&display=swap"])
server = app.server

app.layout = html.Div(className="page", children=[
    html.Header(className="masthead", children=[
        html.Div(className="sign", children=[
            html.Div("Homes on Dangerous Streets?", className="sign-name"),
            html.Div("Affordable housing and traffic crashes in New York City, 2014 – 2025", className="sign-sub")]),
        html.P(className="lede", children=[
            "Are New York's newest affordable homes being built on the streets where crashes hurt people most? "
            "Pick a borough, a year and who was hurt, then generate a report. ",
            html.A("Read the story", href="#story")]),
    ]),

    html.Section(className="controls", children=[
        html.Div(className="search", children=[
            html.Label("Search", htmlFor="search-text"),
            html.Div(className="search-row", children=[
                dcc.Input(id="search-text", type="text", debounce=False,
                          placeholder="e.g. Bronx 2022 new construction pedestrians"),
                html.Button("Apply search", id="search-button", className="secondary")]),
            html.P(id="search-feedback", className="hint")]),
        html.Div(className="filters", children=[
            dropdown("borough", "Borough", [{"label": "All boroughs", "value": "all"}]
                     + [{"label": b, "value": b} for b in BOROUGHS], "all"),
            dropdown("year", "Year", [{"label": "All years (2014 – 2025)", "value": "all"}]
                     + [{"label": str(y), "value": str(y)} for y in YEARS], "all"),
            dropdown("construction", "Housing type", [
                {"label": "All affordable housing", "value": "all"},
                {"label": "New construction", "value": "New Construction"},
                {"label": "Preservation", "value": "Preservation"}], "all"),
            dropdown("road_user", "Who was hurt", [
                {"label": "All people", "value": "all"}, {"label": "Pedestrians", "value": "pedestrians"},
                {"label": "Cyclists", "value": "cyclists"}, {"label": "Motorists", "value": "motorists"}],
                "pedestrians"),
            dropdown("severity", "Crash severity", [
                {"label": "All crashes", "value": "all"}, {"label": "Injury or fatal", "value": "injury"},
                {"label": "Fatal only", "value": "fatal"}], "all"),
            html.Button("Generate Report", id="generate", className="primary"),
        ]),
        html.P(id="stale-hint", className="hint"),
    ]),

    html.H2(id="report-title", className="report-title"),
    html.Div(id="kpis", className="kpis"),

    html.Div(className="grid", children=[
        card("Where homes and dangerous streets meet",
             "Red circles: ZIP codes, darker where crashes hurt the selected group more often. "
             "Blue dots: affordable buildings, sized by affordable units.", "map", wide=True),
        card("More affordable housing, more harm per crash?",
             "Each dot is a ZIP code: affordable units completed vs. people hurt per 100 crashes.", "scatter"),
        card("Near vs. far from affordable housing, year by year",
             "People hurt per 100 crashes, within 250 m of an affordable building vs. elsewhere.", "trend"),
        card("When people are hurt near affordable housing",
             "Share of the selected group hurt within 250 m, by weekday and hour (unknown times excluded).",
             "heatmap"),
        card("Affordable homes completed",
             "Affordable units by year of completion and housing type (the selected year is highlighted).",
             "production"),
    ]),

    html.Section(id="story", className="story", children=[
        html.H2("The story"),
        html.Div(className="story-grid", children=[
            html.Div([html.H3("The question"), html.P(
                "Households in deeply affordable homes are the least likely to own a car. If those homes sit on the "
                "streets where crashes most often hurt people on foot, the people with the fewest alternatives "
                "carry the most risk. We linked 9,551 HPD affordable-housing records with 1.96 million NYPD crash "
                "reports (2014 – 2025) by ZIP code and year, and by distance: every crash within 250 m of each of "
                "7,470 affordable buildings.")]),
            html.Div([html.H3("What we found"), html.Ul([
                html.Li("ZIP codes with the most new affordable housing have crashes that hurt pedestrians far more "
                        "often: 7.2 per 100 crashes in the top quarter vs. 4.3 in the bottom quarter."),
                html.Li("Even inside the same ZIP code, crashes within 250 m of an affordable building hurt a "
                        "pedestrian more often in 78% of ZIP codes."),
                html.Li("20 hotspot ZIP codes combine heavy affordable production with high pedestrian harm — "
                        "mostly in the Bronx, Harlem, the Lower East Side and central Brooklyn."),
                html.Li("New construction sits on busier streets than preservation — more than twice as busy in "
                        "Queens."),
                html.Li("Crashes around new buildings change at the same pace as the city after completion: the "
                        "issue is where homes are built, not what they do to the street."),
            ])]),
            html.Div([html.H3("What the data cannot tell us"), html.Ul([
                html.Li("These are associations, not causes: dense, walkable neighbourhoods have both more "
                        "affordable housing and more pedestrian crashes."),
                html.Li("Rates are per crash, not per resident — neither dataset includes population or traffic."),
                html.Li("Police reporting of minor crashes fell after 2020, so later years show more injury per "
                        "crash; 8% of crashes could not be located."),
            ])]),
            html.Div([html.H3("Why it matters for New York"), html.Ul([
                html.Li("NYC DOT / Vision Zero: prioritise the hotspot ZIP codes and the blocks around affordable "
                        "buildings — with night-time lighting and speed control, safe bus stops and protected "
                        "space for bikes."),
                html.Li("HPD and developers: add a street-safety review to site selection, so safety improvements "
                        "arrive together with the residents."),
                html.Li("Advocates: the need follows location, so safety funding should follow location too."),
            ])]),
        ]),
    ]),
    html.Footer(children=[
        "Data: NYC Open Data — ",
        html.A("Affordable Housing Production by Building",
               href="https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr"),
        " and ",
        html.A("Motor Vehicle Collisions – Crashes",
               href="https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95"),
        ". German International University — Data Engineering and Visualization, Winter 2026."]),

    dcc.Store(id="applied-filters"),
])

FILTER_IDS = ["borough", "year", "construction", "road_user", "severity"]


# --------------------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------------------
@app.callback(
    [Output(i, "value") for i in FILTER_IDS] + [Output("search-feedback", "children")],
    Input("search-button", "n_clicks"), Input("search-text", "n_submit"),
    State("search-text", "value"), prevent_initial_call=True)
def apply_search(_, __, text):
    # Search mode: parse the query and set the dropdowns; the report updates on "Generate Report"
    found, leftover = parse_search(text)
    if not found:
        return [no_update] * len(FILTER_IDS) + [
            "No filters recognised. Try a borough, a year (2014 – 2025), new construction or preservation, "
            "pedestrians / cyclists / motorists, injury or fatal."]
    # Filters not mentioned in the query go back to their defaults, so an earlier search does not linger
    values = [str(found[k]) if k == "year" and k in found else found.get(k, DEFAULT_FILTERS[k]) for k in FILTER_IDS]
    understood = ", ".join(f"{k.replace('_', ' ')} = {v}" for k, v in found.items())
    note = f" Ignored: {' '.join(leftover)}." if leftover else ""
    return values + [f"Filters set: {understood}.{note} Select Generate Report to update the charts."]


@app.callback(
    Output("report-title", "children"), Output("kpis", "children"),
    Output("map", "figure"), Output("scatter", "figure"), Output("trend", "figure"),
    Output("heatmap", "figure"), Output("production", "figure"), Output("applied-filters", "data"),
    Input("generate", "n_clicks"), [State(i, "value") for i in FILTER_IDS])
def generate_report(_, *values):
    # "Generate Report": rebuild every chart from the selected filters (also runs once on page load)
    f = dict(zip(FILTER_IDS, values))
    tiles = [html.Div(className="kpi", children=[html.Div(v, className="kpi-value"), html.Div(l, className="kpi-label")])
             for v, l in kpis(f)]
    return (describe(f), tiles, map_figure(f), scatter_figure(f), trend_figure(f), heatmap_figure(f),
            production_figure(f), f)


@app.callback(Output("stale-hint", "children"), [Input(i, "value") for i in FILTER_IDS],
              Input("applied-filters", "data"))
def stale_hint(*args):
    # Tell the user when the dropdowns no longer match the report on screen
    *values, applied = args
    if applied and dict(zip(FILTER_IDS, values)) != applied:
        return "Filters changed — select Generate Report to update the charts."
    return ""


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
