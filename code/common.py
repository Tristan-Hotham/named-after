"""Shared paths, groupings and helpers for the named-after project.

Raw inputs (read by 01 and 02 only, never modified; raw/ is not needed once data/ is built):
  raw/wd_named_after.tsv   Wikidata (CC0), query run on QLever: every ?p that is an instance of human settlement
      (Q486972) or a subclass, with "named after" (P138) ?s, where ?s is an instance of geographic location (Q2221906)
      or a subclass; both with coordinates (P625); English labels; countries (P17) of both; and the population (P1082)
      and inception (P571) of ?p where Wikidata has them; ?stype is each instance-of (P31) class of ?s. Rows repeat for
      every combination of multiple values (several classes, countries, coordinates or populations).
  raw/wiki_pages.json      English Wikipedia pages (CC BY-SA 4.0) with revision ids: "Toponymy" and "Place names
      considered unusual" (context only; a third title asked for, "List of places named after other places", does not
      exist and came back as an error).
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_50m_land.geojson,
      ne_10m_admin_1_states_provinces.geojson, ne_10m_populated_places_simple.geojson   Natural Earth, public domain.

Wikidata class ids (instance of, P31) are not labelled in the query result. The tables below give the classes I read
from the data (the namesakes that carry each class, printed by 01_clean.py in work/class_examples.txt) and from
Wikidata's own class names. They cover the classes carried by most namesakes; namesakes whose classes are all
unlisted are sorted by cues in their name, then as settlements if Wikidata elsewhere in the file treats them as
settlements, and otherwise counted as 'other'.
"""
import json, gzip, os, re, unicodedata, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("NA_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("NA_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("NA_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("NATMP", "/dev/shm/namedafter"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "named-after"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23878606"                # filled in by the publisher
DOI_URL = "https://doi.org/10.5281/zenodo.23878606"        # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/named-after/"          # filled in by the publisher
QLEVER = "https://qlever.cs.uni-freiburg.de/wikidata"
FETCHED = "2026"               # query run in 2026; year only in public copy
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
R_EARTH = 6371.0088

# ---------- namesake categories, from the namesake's Wikidata classes ----------
CATS = [("Settlement", "#C8322B"), ("River", "#2763A6"), ("Region or country", "#7B57A8"), ("Mountain or hill", "#7A5C3E"), ("Other", "#8C8478")]
CN = [c for c, _ in CATS]; CCOL = dict(CATS)

SETTLE = set("""Q1093829 Q62049 Q1549591 Q498162 Q532 Q15127012 Q515 Q486972 Q3957 Q17343829 Q1852859 Q253019 Q132680629
Q76514543 Q263639 Q1115575 Q777120 Q123705 Q13218357 Q63440326 Q13218391 Q751708 Q2039348 Q15221373 Q484170 Q55237813
Q15063611 Q15303838 Q1077097 Q15661340 Q108569710 Q902814 Q21010817 Q18511725 Q1187811 Q7897276 Q51929311 Q2264924
Q42744322 Q125767932 Q1266818 Q148837 Q200250 Q5084 Q141162078 Q21518270 Q2755753 Q747074 Q13539802 Q1484611 Q23019040
Q2154459 Q5153359 Q3301053 Q7841907 Q15978299 Q8452914 Q108178728 Q7819319 Q174844 Q106071004 Q188509 Q1357964
Q108569739 Q707813 Q22674925 Q15221242 Q134626 Q15221370 Q12031379 Q19730508 Q110071194 Q2785216 Q2074737 Q110071217
Q15411644 Q110266204 Q2974552 Q253030 Q15221310 Q7930989 Q3184121 Q1134686 Q7543008 Q18663566 Q75135432 Q1493533 Q70208
Q3257686 Q27554677 Q350895 Q139961091 Q54935504 Q925381 Q133442 Q494721 Q21507948 Q208511 Q582706 Q456876 Q125778656
Q21672098 Q2202509 Q4286337 Q1074523 Q257391 Q138010797 Q856076 Q12813115 Q42961155 Q5327369 Q11271835 Q1749269
Q65589340 Q11422368 Q15284 Q15273785 Q493522 Q17376095 Q130261443 Q28203007 Q5119 Q7930614 Q2989398 Q14762300 Q22865
Q262166 Q2514025 Q2616791 Q3558970 Q4174776 Q1529096 Q5770918 Q17201685 Q17468533 Q1501046 Q2983893 Q12404340
Q116457956 Q252916 Q15219655 Q17198620 Q61708053 Q20968646 Q19658107 Q79423884 Q12104567 Q2276925 Q56436498""".split())
RIVER = set("Q4022 Q47521 Q355304 Q573344 Q4366834 Q63565252 Q159675 Q1437299".split())
REGION = set("""Q82794 Q3502482 Q1620908 Q6256 Q3624078 Q35657 Q209495 Q36784 Q3024240 Q860290 Q51576574 Q107390 Q10864048
Q11828004 Q1221156 Q180673 Q769603 Q7275 Q15239622 Q154547 Q161243 Q20181813 Q3455524 Q5107 Q6465 Q83057 Q1289426
Q134390 Q1122846""".split())
MOUNTAIN = set("Q8502 Q54050 Q46831 Q169358 Q1595289 Q111177881 Q3393392 Q8072 Q207326 Q1437459 Q212057".split())
# classes that say nothing about the kind of place (tourist destination, financial centre...): ignored when sorting
NEUTRAL = set("Q1200957 Q1066984 Q748198 Q56061 Q2221906 Q15642541 Q15893266 Q1048835 Q19953632".split())
# kinds of 'Other' namesake, for the breakdown only (first match wins)
OTHER_KIND = [("Lakes, reservoirs and seas", "Q23397 Q131681 Q104093746 Q188025 Q187223 Q211302 Q5926864 Q1973404 Q15324 Q11566792", r"\b(lake|loch|lough|lac|see|järvi|reservoir|pond|sea|lagoon)\b"),
              ("Bays, islands, capes and beaches", "Q39594 Q23442 Q40080 Q24529780 Q34763 Q17018380 Q185113 Q1402592 Q44782 Q7900097 Q28060923 Q31615 Q191992 Q37901 Q45776", r"\b(bay|island|isle|cape|point|beach|harbou?r|cove|peninsula|head|sound)\b"),
              ("Castles, forts, churches, stations and other buildings", "Q23413 Q55488 Q845945 Q82117 Q1785071 Q33506 Q92026 Q751876 Q2066754 Q17715832 Q2451577 Q134917286 Q1516079 Q245016 Q1147171 Q57831 Q56242215 Q22808404 Q11670533 Q44613 Q39614 Q615810 Q19563580 Q1195705 Q11606300 Q18543139 Q16970 Q16560 Q1497375 Q175288 Q135160342 Q11482300 Q135022904 Q11390939 Q16823155 Q928830 Q695850 Q12292478 Q4663385", r"\b(castle|fort|palace|church|abbey|shrine|temple|station|manor|hall|house|mill|mine|gate|tower|burg|schloss)\b"),
              ("Streets and squares", "Q79007 Q174782 Q34442 Q7543083 Q54114", r"\b(street|road|avenue|square|straße|strasse|platz|lane|way|boulevard|drive)\b"),
              ("Parks, forests, valleys and plains", "Q22698 Q39816 Q4421 Q22746 Q150784 Q473972 Q160091 Q10594991", r"\b(park|forest|wood|valley|plain|prairie|canyon|glen|meadow)\b")]
# name cues for namesakes with no listed class
CUE = [("River", r"\b(river|creek|brook|stream|rio|río|rivière|fluss|bach|beck|burn|run|nahal|wadi|joki|ree)\b"),
       ("Mountain or hill", r"\b(mount|mountain|mountains|mt|hill|hills|peak|mont|monte|berg|ben|sierra|range|volcano|pic|pico|cerro|vrch|gora|dağ|dagi)\b|^(ben|mount|mont|monte|pic|cerro) "),
       ("Region or country", r"\b(county|province|region|shire|state|kingdom|empire|duchy|land|oblast|prefecture|canton|department|territory|republic)\b|shire$")]

# ---------- places (?p) left out: not settlements in the ordinary sense ----------
# patterns on the English label (case-insensitive); each is reported with its count in results.source.excluded
EXCLUDE_P = [
    ("Census and statistical areas (urban, metropolitan, micropolitan, combined statistical areas)", r"urban area\b|urbanized area|metropolitan|micropolitan|statistical area|urban cluster|\bmsa$|\w–\w"),
    ("Megalopolises, conurbations, agglomerations and 'Greater' areas", r"megalopolis|conurbation|agglomeration|^greater |\bbay area\b|\bmetro\b|metroplex|capital area|^keihanshin$|^las vegas valley$"),
    ("Regions, counties, provinces and new areas", r"\b(region|county|province|prefecture|oblast|governorate|new area|district council)\b"),
    ("Camps that were not homes (concentration, extermination, prison, internment, DP and military camps)", r"concentration camp|extermination camp|prison camp|internment camp|\bdp camp|transit camp|labou?r camp|military camp|\bpow camp|subcamp|außenlager"),
    ("Stations, airports, bases and ranger posts", r"ranger station|entrance station|railway station|train station|\bstation$|\bstazione\b|\bestación\b|airport|air base|air force base|naval base|military base|\bbase$"),
    ("Parks, resorts, ski areas and industrial estates", r"national park|ski area|snow park|ski resort|industrial park|industrial estate|business park|industrial area|theme park|amusement park"),
]
SAME_KM = 30   # a place with the same name as a settlement or region namesake less than this far away is an administrative twin

# ---------- giving regions (where the namesake is), for colours ----------
GROUPS = [("Britain and Ireland", "#C8322B"), ("France and the Low Countries", "#2F5FA7"), ("Germany and central Europe", "#E0A11B"),
          ("Spain and Portugal", "#D46A8C"), ("Italy and Greece", "#2E9A8C"), ("Eastern Europe and Russia", "#7B57A8"),
          ("Middle East and Africa", "#9C6B30"), ("Asia and Oceania", "#3B8F4E"), ("North America", "#3B3B3B"),
          ("Latin America", "#E06A2B")]
GN = [g for g, _ in GROUPS]; GCOL = dict(GROUPS)
ISO_GROUP = {}
for g, isos in (("Britain and Ireland", "GBR IRL IMN JEY GGY"),
                ("France and the Low Countries", "FRA BEL NLD LUX MCO"),
                ("Germany and central Europe", "DEU AUT CHE LIE CZE SVK HUN POL SVN DNK NOR SWE FIN ISL FRO ALA GRL"),
                ("Spain and Portugal", "ESP PRT AND GIB"),
                ("Italy and Greece", "ITA GRC MLT SMR VAT CYP CYN HRV"),
                ("Eastern Europe and Russia", "RUS UKR BLR MDA ROU BGR SRB MNE BIH MKD ALB KOS EST LVA LTU GEO ARM AZE KAZ"),
                ("Middle East and Africa", "TUR SYR LBN ISR PSE JOR IRQ IRN SAU YEM OMN ARE QAT BHR KWT EGY LBY TUN DZA MAR ESH SDN SSD ETH ERI DJI SOM SOL KEN UGA TZA RWA BDI COD COG GAB CMR CAF TCD NGA NER MLI BFA SEN GMB GIN GNB SLE LBR CIV GHA TGO BEN MRT AGO ZMB ZWE MWI MOZ BWA NAM ZAF LSO SWZ MDG MUS SYC COM CPV STP GNQ SHN"),
                ("North America", "USA CAN BMU SPM"),
                ("Latin America", "MEX GTM BLZ HND SLV NIC CRI PAN CUB HTI DOM JAM PRI BHS TTO BRB GRD LCA VCT ATG KNA DMA ABW CUW SXM MAF BLM VGB VIR CYM TCA AIA MSR COL VEN GUY SUR ECU PER BOL BRA PRY URY ARG CHL FLK SGS")):
    for i in isos.split():
        ISO_GROUP[i] = g
# anything not listed (the rest of Asia, Oceania, Antarctica) is "Asia and Oceania"
def group_of(iso):
    return ISO_GROUP.get(iso, "Asia and Oceania")


# the words that make a "New X"
NEW_RE = re.compile(r"^(New|Nuevo|Nueva|Nuevas|Nuevos|Nova|Novo|Novi|Nove|Nová|Nové|Novy|Novyi|Novyy|Novaya|Novoye|Nowy|Nowa|Nowe|Neu|Neue|Neuer|Nieuw|Nieuwe|Nouveau|Nouvelle|Nouvel|Ny|Nya|Nye|Uusi)\b[\s-]*(.+)$")
NEW_PREFIX = re.compile(r"^(Neu|Nieuw|Novo|Nova|Novi|Nowo)-?(.+)$")


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


def fill(text, R, f=fmt):
    """Replace {{path|format}} tokens with numbers from R, leaving the publisher's tokens (10.5281/zenodo.23878606, https://doi.org/10.5281/zenodo.23878606,
    https://blog.tristanhotham.com/2026/10/31/named-after/), image tokens ({{IMG|...}}) and table tokens ({{TABLE_...}}) alone."""
    return re.sub(r"\{\{(?!IMG\||DOI\}\}|DOI_URL\}\}|BLOG_URL\}\}|TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: f(get(R, m.group(1)), m.group(3)), text)


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return R_EARTH * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


def gc_points(lon1, lat1, lon2, lat2, n=None):
    """Points along the great circle from (lon1, lat1) to (lon2, lat2), longitudes unwrapped (continuous)."""
    import numpy as np
    d = float(gc_km(lat1, lon1, lat2, lon2))
    if n is None:
        n = max(2, min(64, int(d / 150) + 2))
    if d < 1:
        return [[lon1, lat1], [lon2, lat2]]
    p1, l1, p2, l2 = map(math.radians, (lat1, lon1, lat2, lon2))
    a = np.array([math.cos(p1) * math.cos(l1), math.cos(p1) * math.sin(l1), math.sin(p1)])
    b = np.array([math.cos(p2) * math.cos(l2), math.cos(p2) * math.sin(l2), math.sin(p2)])
    om = math.acos(max(-1, min(1, float(a @ b))))
    out, prev = [], None
    for t in np.linspace(0, 1, n):
        v = (math.sin((1 - t) * om) * a + math.sin(t * om) * b) / math.sin(om)
        lat = math.degrees(math.asin(max(-1, min(1, v[2])))); lon = math.degrees(math.atan2(v[1], v[0]))
        if prev is not None:
            while lon - prev > 180: lon -= 360
            while lon - prev < -180: lon += 360
        prev = lon; out.append([round(lon, 3), round(lat, 3)])
    return out
