"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, c, d, b, o, g = R["source"], R["cats"], R["dist"], R["border"], R["ocean"], R["gbr"]
N = lambda v: f"{round(v):,}"
readme = f"""# Named after somewhere else: places named after other places

A map and analysis of the {N(s['n'])} settlements that Wikidata records as "named after" (P138) another geographical place, each joined by a great circle to its namesake: what places are named after, how far the names travelled, which countries gave and received names, the "New X" places, and the Old World names of the United States. It also shows, honestly, how uneven Wikidata's coverage of name origins is.

Interactive page: {PAGE}
Paper: {DOI_URL}
Blog post: {BLOG}

## Headline results

- Links: {N(s['n'])} links from {N(s['places'])} places to {N(s['namesakes'])} namesakes, after removing {N(s['excluded_links'])} of {N(s['links_raw'])} raw links ({s['excl_pct']:.0f}%), mostly US census urban areas.
- What: {c['Settlement']['pct']:.0f}% of links are to another settlement, {c['River']['pct']:.0f}% to rivers, {c['Mountain or hill']['pct']:.0f}% to mountains and hills, {c['Region or country']['pct']:.0f}% to regions and countries, {c['Other']['pct']:.0f}% to other features (lakes, coasts, buildings, streets, parks).
- How far: median {d['median']:.1f} km; {d['under10_pct']:.0f}% within 10 km, {d['over1000_pct']:.0f}% over 1,000 km. The distances are bimodal: neighbours, or across an ocean ({o['pct']:.1f}% of links, median {N(o['km_med'])} km). The longest: {R['longest'][0]['place']} ({R['longest'][0]['pc']}) from {R['longest'][0]['namesake']}, {N(R['longest'][0]['km'])} km.
- Who named whom: {b['pct']:.0f}% of links cross a border. The United Kingdom gave {R['giving'][0]['n']} ({R['giving'][0]['pct']:.0f}%), {g['four_pct']:.0f}% of them to the United States ({g['usa']}), Australia ({g['aus']}), Canada ({g['can']}) and New Zealand ({g['nzl']}).
- Most borrowed: Prague ({R['top'][0]['n']} places, mostly Czech suburbs called Pražské Předměstí), Amsterdam ({R['top'][1]['n']}, {R['top'][1]['abroad']} abroad), Moscow ({R['top'][3]['n']}).
- New X: {R['new']['n']} places, {R['new']['under30_pct']:.0f}% within 30 km of the original; {R['new']['ocean']} crossed an ocean.
- United States: {R['us']['n']} links; {R['us']['old']} to places outside the Americas, led by Minnesota ({R['us_top_state']['n']}, mostly townships).
- Coverage: the United States, Germany, Australia and the Netherlands hold {R['cov']['top4_pct']:.0f}% of links; Latin America {R['iberia']['latam_places_pct']:.1f}%. Spain and Portugal gave only {R['iberia']['latam']} names to Latin America in the file. This is a map of Wikidata's coverage as much as of naming.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/named_after_links.csv` | All {N(s['n'])} links: place and namesake Wikidata ids, names, coordinates, countries, US state, population, inception year, namesake category, distance, border and ocean flags, landmasses, "New" word. |
| `data/top_namesakes.csv` | The 20 most borrowed namesakes and their places. |
| `data/country_flows.csv` | Country-to-country counts of links that cross a border. |
| `data/links_by_country.csv` | Links per place country, share and per million people (coverage). |
| `data/us_states_old_world.csv` | US places named after places outside the Americas, by state. |
| `data/exclusions.csv` | Every exclusion rule with counts and examples. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/world.json`, `data/countries.json`, `data/cities.json`, `data/oceans.json` | Page data and outlines. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Query (QLever, Wikidata, {s['fetched']}): items that are a human settlement (Q486972 or subclass) with "named after" (P138) a geographic location (Q2221906 or subclass), both with coordinates and English labels; countries, population and inception of the place; classes of the namesake. {N(s['rows'])} rows collapse to {N(s['links_raw'])} links.
- Not settlements: removed by label (census and statistical areas, megalopolises, regions and counties, concentration and prison camps, stations and bases, parks and ski resorts), plus self-links and administrative twins (same name, under 30 km). See `data/exclusions.csv`.
- Namesake category: from Wikidata classes, read from the namesakes that carry them (`code/common.py`); {s['cat_class_pct']:.0f}% sorted by a listed class, the rest by name cues or as "other".
- Distance: great circle between Wikidata coordinates (rivers, regions and ranges are single points, so rough). Border: Wikidata country (P17) matched to Natural Earth. Ocean: ends on different landmasses (Americas; Africa, Europe and Asia; Australia and neighbours; Antarctica; remote islands).
- Caveats: Wikidata statements are crowd-sourced and mostly unreferenced; coverage is very uneven; places named after people are outside the study.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, scipy, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Steps 01 to 03 read `raw/` (not published); from 04 onwards only `data/` is needed. Intermediates go to `/dev/shm/namedafter/work` (set `NATMP` to change).

```
python3 code/01_clean.py        # collapse rows, exclusions, namesake categories
python3 code/02_geo.py          # outlines, countries, landmasses, US states
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Wikidata contributors, Wikidata, queried with QLever ({QLEVER}) in {s['fetched']}. CC0.
- Wikipedia, "Toponymy" and "Place names considered unusual" (CC BY-SA 4.0), read for context only; no text reproduced.
- Natural Earth countries, land, admin 1 states and populated places (https://www.naturalearthdata.com/). Public domain.

## Citation

Hotham, T. (2026) Named after somewhere else: places named after other places in Wikidata. Zenodo. {DOI_URL}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The place and name data are
derived from Wikidata, which is CC0. Context was read from Wikipedia
(CC BY-SA 4.0); no Wikipedia text is reproduced. Natural Earth is public
domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] I mapped {N(s['n'])} places named after other places. Most names come from a river or the town next door, but {o['pct']:.0f}% crossed an ocean, and Britain gave away more names than anywhere else

## Body

Wikidata records, for some settlements, what they are "named after". I took every settlement named after another geographical place and drew a great circle from the namesake to the place. Only {c['Settlement']['pct']:.0f}% are named after another settlement; the rest after rivers ({c['River']['pct']:.0f}%), hills, lakes, bays, castles and streets. Half the links are shorter than {d["median"]:.1f} km, yet {d['over1000_pct']:.0f}% are more than 1,000 km away: names either stay at home or cross an ocean. Of the names that crossed a border, {R['giving'][0]['pct']:.0f}% came from the UK, {g['four_pct']:.0f}% of those to the US, Australia, Canada and New Zealand. The longest: {R['longest'][0]['place']}, New Zealand, from {R['longest'][0]['namesake']}, {N(R['longest'][0]['km'])} km. The most borrowed: Prague ({R['top'][0]['n']}, mostly Czech suburbs) and Amsterdam ({R['top'][1]['n']}). Big caveat: this maps Wikidata's coverage as much as history. Four countries hold {R['cov']['top4_pct']:.0f}% of the links, and Spanish names in Latin America are almost missing. Interactive map (click any line to see the whole family of a name, search, filters): {PAGE}

## Source comment

Source: Wikidata (CC0), "named after" (P138) for human settlements, queried with QLever in {s['fetched']}; US census urban areas, camps, stations and other non-settlements removed ({N(s['excluded_links'])} of {N(s['links_raw'])} links). Outlines: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: {DOI_URL}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
