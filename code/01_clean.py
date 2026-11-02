"""Read the Wikidata query result (raw/wd_named_after.tsv), collapse the repeated rows to one record per place, per
namesake and per link, drop the places that are not settlements in the ordinary sense, and sort every namesake into a
category from its Wikidata classes.

Rows. The query returns one row for every combination of multiple values: a namesake with three classes and a place
with two populations give six rows for one link. Here:
  * a place (?p) keeps its first coordinate pair in the file, its largest population (P1082) and its earliest
    inception (P571); its countries (P17) are all kept and resolved in 02_geo.py;
  * a namesake (?s) keeps its first coordinate pair, all its countries and the set of its classes (?stype);
  * a link is one (place, namesake) pair. A place named after two things (Boston, Massachusetts, after both Boston in
    Lincolnshire and Lincolnshire) has two links.
Places left out (EXCLUDE_P in common.py) are matched on the English label: census and statistical areas (in Wikidata
these are named after their main town, so they would double count it), megalopolises and conurbations, regions and
counties, camps that were never homes, stations and bases, parks and ski areas. Links from a place to itself, and
'administrative twins' (a place with the same name as a settlement or region namesake less than SAME_KM away, such as a
town and the municipality of the same name), are also dropped. Every exclusion is counted in work/checks.json.
Namesake category: Settlement if any class is in SETTLE, else Region or country (REGION), else River (RIVER), else
Mountain or hill (MOUNTAIN); a namesake with none of the listed classes is sorted by its name (CUE), then counted as a
settlement if it appears in the file as a settlement itself, and otherwise as Other (lakes, islands, castles, streets,
estates, bays and the rest)."""
import numpy as np, pandas as pd, collections
from common import *

D0 = pd.read_csv(f"{RAW}/wd_named_after.tsv", sep="\t", dtype=str, keep_default_na=False, quoting=3)
D0.columns = [c.lstrip("?") for c in D0.columns]
assert list(D0.columns) == ["p", "pLabel", "pc", "pco", "ppop", "pinc", "s", "sLabel", "sc", "sco", "stype"], D0.columns
chk = {"rows": len(D0)}
D = D0.copy()
qid = lambda s: s.str.extract(r"entity/(Q\d+)>", expand=False).fillna("")
lab = lambda s: s.str.replace(r'"@en$', "", regex=True).str.replace(r'^"', "", regex=True).str.replace(r'\\"', '"', regex=False)
for c in ("p", "pco", "s", "sco", "stype"):
    D[c] = qid(D[c])
D["pl"], D["sl"] = lab(D.pLabel), lab(D.sLabel)
for c, k in (("pc", "p"), ("sc", "s")):
    xy = D[c].str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)")
    D[k + "lon"], D[k + "lat"] = pd.to_numeric(xy[0]), pd.to_numeric(xy[1])
assert D.p.ne("").all() and D.s.ne("").all()
chk["rows_unknown_coord"] = int((D.plat.isna() | D.slat.isna()).sum())   # Wikidata "unknown value" coordinates; other values are used
assert D.pl.ne("").all() and D.sl.ne("").all()
D["pop"] = pd.to_numeric(D.ppop, errors="coerce")
D["inc"] = pd.to_numeric(D.pinc.str.extract(r"^(-?\d{1,4})-", expand=False), errors="coerce")
chk.update(places_raw=int(D.p.nunique()), namesakes_raw=int(D.s.nunique()), links_raw=int(D[["p", "s"]].drop_duplicates().shape[0]),
           classes_raw=int(D.stype.nunique()), place_multi_coord=int((D.groupby("p").pc.nunique() > 1).sum()),
           namesake_multi_coord=int((D.groupby("s").sc.nunique() > 1).sum()))

# ---------- one record per place ----------
gp = D.groupby("p", sort=False)
P = pd.DataFrame({"label": gp.pl.first(), "lon": gp.plon.first(), "lat": gp.plat.first(), "pop": gp["pop"].max(), "inc": gp.inc.min(),
                  "p17": gp.pco.agg(lambda s: [x for x in dict.fromkeys(s) if x])})
gs = D.groupby("s", sort=False)
S = pd.DataFrame({"label": gs.sl.first(), "lon": gs.slon.first(), "lat": gs.slat.first(),
                  "p17": gs.sco.agg(lambda s: [x for x in dict.fromkeys(s) if x]), "types": gs.stype.agg(lambda s: sorted(set(x for x in s if x)))})

nop, nos = P.lat.isna(), S.lat.isna()
chk["places_no_coord"], chk["namesakes_no_coord"] = int(nop.sum()), int(nos.sum())
P, S = P[~nop], S[~nos]

# ---------- class examples (to read the classes; see common.py) ----------
u = D.drop_duplicates(["s", "stype"])
with open(f"{WORK}/class_examples.txt", "w", encoding="utf-8") as f:
    for q, g in u.groupby("stype"):
        f.write(f"{q}\t{len(g)}\t{', '.join(g.sl.head(8))}\n")

# ---------- namesake categories ----------
p_ids = set(P.index)
how = collections.Counter()


def category(row):
    t = set(row.types) - NEUTRAL
    if t & SETTLE: how["class"] += 1; return "Settlement"
    if t & REGION: how["class"] += 1; return "Region or country"
    if t & RIVER: how["class"] += 1; return "River"
    if t & MOUNTAIN: how["class"] += 1; return "Mountain or hill"
    nm = row.label.lower()
    for c, pat in CUE:
        if re.search(pat, nm): how["name cue"] += 1; return c
    if row.Index in p_ids: how["is a settlement in the file"] += 1; return "Settlement"
    how["other"] += 1; return "Other"


S["cat"] = [category(r) for r in S.itertuples()]


def other_kind(row):
    if row.cat != "Other": return ""
    for k, qs, pat in OTHER_KIND:
        if set(row.types) & set(qs.split()): return k
    for k, qs, pat in OTHER_KIND:
        if re.search(pat, row.label.lower()): return k
    return "Other features"


S["okind"] = [other_kind(r) for r in S.itertuples()]
chk["category_how"] = dict(how)
chk["category_n"] = S.cat.value_counts().to_dict()

# ---------- links ----------
L = D[["p", "s"]].drop_duplicates().reset_index(drop=True)
L = L[L.p.isin(P.index) & L.s.isin(S.index)]
ex = collections.OrderedDict()
self_ = L.p == L.s
ex["Links from a place to itself"] = {"links": int(self_.sum()), "places": int(L[self_].p.nunique())}
L = L[~self_].copy()
L["pl"] = L.p.map(P.label)
keep = pd.Series(True, index=L.index)
for name, pat in EXCLUDE_P:
    m = keep & L.pl.str.contains("(?:" + pat + ")", case=False, regex=True)
    ex[name] = {"links": int(m.sum()), "places": int(L[m].p.nunique()), "examples": list(dict.fromkeys(L[m].pl))[:8]}
    keep &= ~m
L = L[keep].copy()
L["km"] = gc_km(L.p.map(P.lat).values, L.p.map(P.lon).values, L.s.map(S.lat).values, L.s.map(S.lon).values)
L["cat"] = L.s.map(S.cat)
twin = (L.pl.map(norm) == L.s.map(S.label).map(norm)) & L.cat.isin(["Settlement", "Region or country"]) & (L.km < SAME_KM)
ex["Administrative twins (same name, under 30 km)"] = {"links": int(twin.sum()), "places": int(L[twin].p.nunique()),
                                                        "examples": list(dict.fromkeys(L[twin].pl))[:8]}
L = L[~twin].copy()
chk["excluded"] = ex
chk["links"] = len(L); chk["places"] = int(L.p.nunique()); chk["namesakes"] = int(L.s.nunique())

# ---------- what is left, briefly ----------
P = P.loc[sorted(set(L.p), key=list(P.index).index)]
S = S.loc[sorted(set(L.s), key=list(S.index).index)]
P.to_pickle(f"{WORK}/places.pkl"); S.to_pickle(f"{WORK}/namesakes.pkl"); L.drop(columns=["pl"]).to_pickle(f"{WORK}/links.pkl")
jsave(chk, f"{WORK}/checks.json", indent=1)
print("rows", len(D0), "links raw", chk["links_raw"], "kept", len(L), "places", chk["places"], "namesakes", chk["namesakes"])
for k, v in ex.items():
    print(f"  {v['links']:5d} links {v['places']:5d} places  {k}  {v.get('examples', '')[:5] if v.get('examples') else ''}")
print("category by", dict(how)); print(L.cat.value_counts().to_dict())
