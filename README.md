# Named after somewhere else: places named after other places

A map and analysis of the 3,981 settlements that Wikidata records as "named after" (P138) another geographical place, each joined by a great circle to its namesake: what places are named after, how far the names travelled, which countries gave and received names, the "New X" places, and the Old World names of the United States. It also shows, honestly, how uneven Wikidata's coverage of name origins is.

Interactive page: https://maps.tristanhotham.com/named-after/
Paper: https://doi.org/10.5281/zenodo.23878606
Blog post: https://blog.tristanhotham.com/2026/10/31/named-after/

## Headline results

- Links: 3,981 links from 3,837 places to 3,551 namesakes, after removing 3,684 of 7,666 raw links (48%), mostly US census urban areas.
- What: 37% of links are to another settlement, 14% to rivers, 7% to mountains and hills, 6% to regions and countries, 35% to other features (lakes, coasts, buildings, streets, parks).
- How far: median 4.4 km; 58% within 10 km, 22% over 1,000 km. The distances are bimodal: neighbours, or across an ocean (14.2% of links, median 7,620 km). The longest: Lansdowne (New Zealand) from Lansdown, 19,071 km.
- Who named whom: 22% of links cross a border. The United Kingdom gave 259 (29%), 96% of them to the United States (102), Australia (102), Canada (31) and New Zealand (13).
- Most borrowed: Prague (13 places, mostly Czech suburbs called Pražské Předměstí), Amsterdam (10, 8 abroad), Moscow (8).
- New X: 75 places, 55% within 30 km of the original; 18 crossed an ocean.
- United States: 998 links; 316 to places outside the Americas, led by Minnesota (45, mostly townships).
- Coverage: the United States, Germany, Australia and the Netherlands hold 54% of links; Latin America 2.2%. Spain and Portugal gave only 6 names to Latin America in the file. This is a map of Wikidata's coverage as much as of naming.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `data/named_after_links.csv` | All 3,981 links: place and namesake Wikidata ids, names, coordinates, countries, US state, population, inception year, namesake category, distance, border and ocean flags, landmasses, "New" word. |
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

- Query (QLever, Wikidata, 2026): items that are a human settlement (Q486972 or subclass) with "named after" (P138) a geographic location (Q2221906 or subclass), both with coordinates and English labels; countries, population and inception of the place; classes of the namesake. 23,818 rows collapse to 7,666 links.
- Not settlements: removed by label (census and statistical areas, megalopolises, regions and counties, concentration and prison camps, stations and bases, parks and ski resorts), plus self-links and administrative twins (same name, under 30 km). See `data/exclusions.csv`.
- Namesake category: from Wikidata classes, read from the namesakes that carry them (`code/common.py`); 78% sorted by a listed class, the rest by name cues or as "other".
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

- Wikidata contributors, Wikidata, queried with QLever (https://qlever.cs.uni-freiburg.de/wikidata) in 2026. CC0.
- Wikipedia, "Toponymy" and "Place names considered unusual" (CC BY-SA 4.0), read for context only; no text reproduced.
- Natural Earth countries, land, admin 1 states and populated places (https://www.naturalearthdata.com/). Public domain.

## Citation

Hotham, T. (2026) Named after somewhere else: places named after other places in Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23878606

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
