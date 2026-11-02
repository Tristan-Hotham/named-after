"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json).

Definitions:
  * link: one (place, namesake) pair kept by 01_clean.py; 'daughters' of a namesake = the distinct places named after it;
  * distance: great-circle distance between Wikidata's coordinates for the place and for the namesake (for a river, a
    region or a mountain range that is a single point Wikidata picked, often a mouth, a source or a centre, so those
    distances are rough);
  * crossing a border: the namesake's country differs from the place's country (02_geo.py);
  * crossing an ocean: the two lie on different landmasses (02_geo.py);
  * a 'New X': the place's English name starts with a word for new (New, Nuevo, Nueva, Nova, Novo, Novi, Neu, Nieuw,
    Nouveau, Nouvelle, Nowy, Ny...), or a prefix (Neu-, Nieuw-, Novo-), and the rest of the name matches the
    namesake's name (a similarity of at least 0.6 between the first word and any word of the namesake's name, after
    dropping 'Old', 'Canton of' and articles), and the namesake is not itself a 'New' name."""
import numpy as np, pandas as pd, difflib, collections
from common import *

P = pd.read_pickle(f"{WORK}/places.pkl"); S = pd.read_pickle(f"{WORK}/namesakes.pkl"); L = pd.read_pickle(f"{WORK}/links.pkl").reset_index(drop=True)
CHK = jload(f"{WORK}/checks.json"); CM = jload(f"{DATA}/countries.json")
cname = lambda i: CM[i]["name"] if i in CM else ("no country" if not i else i)
CONT = {"Europe", "Americas", "Africa", "Asia", "Oceania"}
sname = lambda s: "a continent" if S.loc[s, "label"] in CONT else cname(S.loc[s, "iso"])
pc = lambda a, b: round(100 * a / b, 2) if b else None
L["pl"], L["sl"] = L.p.map(P.label), L.s.map(S.label)
L["piso"], L["siso"] = L.p.map(P.iso), L.s.map(S.iso)
L["pg"], L["sg"] = L.piso.map(group_of), L.siso.map(group_of)
L["state"] = L.p.map(P.state)
L["border"] = (L.piso != L.siso).astype(int)
L["ocean"] = (L.p.map(P.mass) != L.s.map(S.mass)).astype(int)
L["pop"], L["inc"] = L.p.map(P["pop"]), L.p.map(P.inc)
L["okind"] = L.s.map(S.okind)
N = len(L)
R = {}

# ---------- source ----------
ex = [{"what": k, "links": v["links"], "places": v["places"], "examples": v.get("examples", [])[:5]} for k, v in CHK["excluded"].items()]
R["source"] = {"rows": CHK["rows"], "links_raw": CHK["links_raw"], "places_raw": CHK["places_raw"], "namesakes_raw": CHK["namesakes_raw"],
               "classes_raw": CHK["classes_raw"], "excluded": ex, "excluded_links": sum(e["links"] for e in ex),
               "excluded_stat_links": ex[1]["links"], "excluded_stat_places": ex[1]["places"],
               "n": N, "places": int(L.p.nunique()), "namesakes": int(L.s.nunique()),
               "places_two": int((L.groupby("p").size() > 1).sum()),
               "countries_p": int(L.piso.nunique()), "countries_s": int(L.siso[L.siso != ""].nunique()),
               "with_pop": int(P.loc[L.p.unique(), "pop"].notna().sum()), "with_inc": int(P.loc[L.p.unique(), "inc"].notna().sum()),
               "cat_by_class": CHK["category_how"].get("class", 0), "cat_by_cue": CHK["category_how"].get("name cue", 0),
               "cat_by_self": CHK["category_how"].get("is a settlement in the file", 0), "cat_other": CHK["category_how"].get("other", 0),
               "fetched": FETCHED, "unknown_coord_rows": CHK["rows_unknown_coord"], "country_how": CHK["country_how"],
               "p17_agree_pct": CHK["place_p17_vs_position_agree_pct"], "checks": CHK}
src = R["source"]
src["excl_pct"] = pc(src["excluded_links"], src["links_raw"]); src["stat_pct"] = pc(src["excluded_stat_links"], src["links_raw"])
src["cat_class_pct"] = pc(src["cat_by_class"], src["cat_by_class"] + src["cat_by_cue"] + src["cat_by_self"] + src["cat_other"])
assert N == len(L[["p", "s"]].drop_duplicates()) and src["links_raw"] == 7666 and N > 3500

# ---------- what the namesakes are ----------
cats = []
for c in CN:
    a = L[L.cat == c]
    cats.append({"cat": c, "n": len(a), "pct": pc(len(a), N), "namesakes": int(a.s.nunique()), "km_med": round(float(a.km.median()), 1),
                 "km_q75": round(float(a.km.quantile(.75)), 1), "border": int(a.border.sum()), "border_pct": pc(a.border.sum(), len(a)),
                 "ocean": int(a.ocean.sum()), "ocean_pct": pc(a.ocean.sum(), len(a)), "under10_pct": pc((a.km < 10).sum(), len(a))})
R["cats_list"] = cats; R["cats"] = {c["cat"]: c for c in cats}
ok = L[L.cat == "Other"].okind.value_counts()
R["other_kinds"] = [{"kind": k, "n": int(v), "pct_all": pc(v, N)} for k, v in ok.items()]
OK = {r["kind"]: r for r in R["other_kinds"]}
R["lakes"] = OK["Lakes, reservoirs and seas"]["n"]
R["natural_pct"] = pc(R["cats"]["River"]["n"] + R["cats"]["Mountain or hill"]["n"] + R["lakes"] + OK["Bays, islands, capes and beaches"]["n"] + OK["Parks, forests, valleys and plains"]["n"], N)

# ---------- distance ----------
km = L.km
R["dist"] = {"median": round(float(km.median()), 1), "q25": round(float(km.quantile(.25)), 1), "q75": round(float(km.quantile(.75)), 1),
             "under10_pct": pc((km < 10).sum(), N), "under50_pct": pc((km < 50).sum(), N), "over1000": int((km >= 1000).sum()),
             "over1000_pct": pc((km >= 1000).sum(), N), "over5000": int((km >= 5000).sum()), "over10000": int((km >= 10000).sum()),
             "border_med": round(float(L[L.border == 1].km.median())), "domestic_med": round(float(L[L.border == 0].km.median()), 1),
             "settle_med": round(float(L[L.cat == "Settlement"].km.median()), 1)}
BINS = [0, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 21000]
hist = []
for a, b in zip(BINS[:-1], BINS[1:]):
    m = (km >= a) & (km < b)
    hist.append({"a": a, "b": b, **{c: int((m & (L.cat == c)).sum()) for c in CN}, "n": int(m.sum())})
R["dist_hist"] = hist
far = L.sort_values("km", ascending=False)
R["longest"] = [{"place": r.pl, "pc": cname(r.piso), "namesake": r.sl, "sc": cname(r.siso), "km": round(r.km), "cat": r.cat, "pi": r.p, "si": r.s} for r in far.head(15).itertuples()]
R["longest_nzl"] = int((far.head(15).piso == "NZL").sum())
assert R["longest"][0]["km"] > 19000 and R["longest"][0]["pc"] == "New Zealand"

# ---------- crossing a border and an ocean ----------
B = L[L.border == 1]
R["border"] = {"n": len(B), "pct": pc(len(B), N), "settle": int((B.cat == "Settlement").sum()), "settle_pct": pc((B.cat == "Settlement").sum(), len(B)),
               "ocean_of_border": int(B.ocean.sum()), "ocean_of_border_pct": pc(B.ocean.sum(), len(B))}
O = L[L.ocean == 1]
R["ocean"] = {"n": len(O), "pct": pc(len(O), N), "settle": int((O.cat == "Settlement").sum()), "settle_pct": pc((O.cat == "Settlement").sum(), len(O)),
              "domestic": int((O.border == 0).sum()), "km_med": round(float(O.km.median())),
              "of_settle_pct": pc(((L.cat == "Settlement") & (L.ocean == 1)).sum(), (L.cat == "Settlement").sum())}
gv = B[B.siso != ""].siso.value_counts(); rc = B.piso.value_counts()
R["giving"] = [{"iso": i, "country": cname(i), "n": int(v), "pct": pc(v, len(B)), "to": int(B[B.siso == i].piso.nunique())} for i, v in gv.head(15).items()]
R["receiving"] = [{"iso": i, "country": cname(i), "n": int(v), "pct": pc(v, len(B)), "from": int(B[B.piso == i].siso.nunique())} for i, v in rc.head(15).items()]
fl = B[B.siso != ""].groupby(["siso", "piso"]).size().sort_values(ascending=False)
R["flows"] = [{"from": cname(a), "to": cname(b), "fi": a, "ti": b, "n": int(v)} for (a, b), v in fl.head(25).items()]
FL = {(f["fi"], f["ti"]): f["n"] for f in R["flows"]}
gb = B[B.siso == "GBR"]
R["gbr"] = {"n": len(gb), "pct": pc(len(gb), len(B)), "usa": FL[("GBR", "USA")], "aus": FL[("GBR", "AUS")], "can": FL[("GBR", "CAN")], "nzl": FL[("GBR", "NZL")],
            "four": int(gb.piso.isin(["USA", "AUS", "CAN", "NZL"]).sum())}
R["gbr"]["four_pct"] = pc(R["gbr"]["four"], len(gb))
R["gbr"]["ireland"] = int(((B.siso == "IRL") & B.piso.isin(["USA", "AUS", "CAN", "NZL"])).sum())
LAT = ["MEX", "GTM", "BLZ", "HND", "SLV", "NIC", "CRI", "PAN", "CUB", "HTI", "DOM", "PRI", "COL", "VEN", "ECU", "PER", "BOL", "BRA", "PRY", "URY", "ARG", "CHL"]
ib = B[B.siso.isin(["ESP", "PRT"])]
R["iberia"] = {"n": len(ib), "latam": int(ib.piso.isin(LAT).sum()), "phl": int((ib.piso == "PHL").sum()), "usa": int((ib.piso == "USA").sum()),
               "latam_places": int(L.piso.isin(LAT).sum()), "latam_places_pct": pc(L.piso.isin(LAT).sum(), N),
               "bra_from_eu": int(((B.piso == "BRA") & B.sg.isin(["Germany and central Europe", "Italy and Greece", "France and the Low Countries", "Britain and Ireland"])).sum())}
R["dutch"] = {"n": int((B.siso == "NLD").sum()), "usa": int(((B.siso == "NLD") & (B.piso == "USA")).sum()),
              "examples": [f"{r.pl} ({cname(r.piso)})" for r in B[(B.siso == "NLD")].sort_values("km", ascending=False).head(8).itertuples()]}
R["greece"] = {"tur_grc": FL.get(("TUR", "GRC"), 0), "examples": [r.pl for r in B[(B.siso == "TUR") & (B.piso == "GRC")].itertuples()][:8]}
REV = B[B.sg.isin(["North America", "Latin America"]) & ~B.pg.isin(["North America", "Latin America"])]
R["reverse"] = {"n": len(REV), "examples": [f"{r.pl} ({cname(r.piso)}) after {r.sl}" for r in REV.itertuples()][:12]}
# region flows for the chord diagram (links that cross a border)
M = pd.crosstab(B[B.siso != ""].sg, B[B.siso != ""].pg).reindex(index=GN, columns=GN, fill_value=0)
R["region_matrix"] = M.values.tolist()
R["region_give"] = {g: int(M.loc[g].sum()) for g in GN}; R["region_get"] = {g: int(M[g].sum()) for g in GN}
R["eur_to_new"] = int(M.loc[GN[:6], ["North America", "Latin America", "Asia and Oceania"]].values.sum())
R["eur_to_new_pct"] = pc(R["eur_to_new"], int(M.values.sum()))
assert R["giving"][0]["iso"] == "GBR" and {R["flows"][0]["ti"], R["flows"][1]["ti"]} == {"USA", "AUS"}

# ---------- the most borrowed names ----------
d = L.groupby("s").agg(n=("p", "nunique"), km=("km", "median"), mx=("km", "max"), nb=("border", "sum")).sort_values(["n", "mx"], ascending=False)
top = []
for s, r in d.head(20).iterrows():
    kids = L[L.s == s]
    top.append({"si": s, "name": S.loc[s, "label"], "country": sname(s), "cat": S.loc[s, "cat"], "n": int(r.n), "abroad": int(r.nb),
                "km_med": round(float(r.km)), "km_max": round(float(r.mx)),
                "kids": [f"{k.pl}{', ' + k.state if k.state else ''} ({cname(k.piso)})" for k in kids.sort_values("km").itertuples()]})
R["top"] = top
R["top_abroad"] = []
dab = B.groupby("s").p.nunique().sort_values(ascending=False)
for s, n in dab.head(15).items():
    R["top_abroad"].append({"si": s, "name": S.loc[s, "label"], "country": sname(s), "cat": S.loc[s, "cat"], "n": int(n),
                            "where": sorted(set(cname(i) for i in B[B.s == s].piso))})
T = {t["name"]: t for t in top}
R["max_daughters"] = top[0]["n"]
R["one_daughter_pct"] = pc((d.n == 1).sum(), len(d))
R["prague"] = {"n": T["Prague"]["n"], "cz": int((L[L.s == top[0]["si"]].piso == "CZE").sum()), "us": int((L[L.s == top[0]["si"]].piso == "USA").sum())}
assert top[0]["name"] == "Prague" and top[1]["name"] == "Amsterdam"

# ---------- New X ----------
STOP = {"old", "canton", "of", "de", "la", "le", "el", "the", "het", "den", "der", "die", "das", "l", "les", "los", "las", "city", "province", "duchy", "municipality"}


def is_new(pl, sl):
    m = NEW_RE.match(pl) or NEW_PREFIX.match(pl)
    if not m or NEW_RE.match(sl) or NEW_PREFIX.match(sl): return None
    rest = [w for w in norm(m.group(2)).split() if w not in STOP]
    sw = [w for w in norm(sl).split() if w not in STOP and len(w) >= 3]
    if not rest or not sw: return None
    best = max(difflib.SequenceMatcher(None, rest[0], w).ratio() for w in sw)
    pre = any(w[:4] == rest[0][:4] for w in sw) if len(rest[0]) >= 4 else False
    return m.group(1) if (best >= .6 or pre) else None


L["new"] = [is_new(a, b) or "" for a, b in zip(L.pl, L.sl)]
NW = L[L.new != ""]
R["new"] = {"n": len(NW), "places": int(NW.p.nunique()), "border": int(NW.border.sum()), "ocean": int(NW.ocean.sum()),
            "km_med": round(float(NW.km.median()), 1), "under30": int((NW.km < 30).sum()), "egypt": int((NW.piso == "EGY").sum()),
            "nld": int((NW.piso == "NLD").sum()), "deu": int((NW.piso == "DEU").sum()), "usa": int((NW.piso == "USA").sum()),
            "words": NW.new.map(lambda w: "Neu" if w.lower().startswith("neu") else "Nieuw" if w.lower().startswith("nieuw") else w).value_counts().to_dict(),
            "rows": [{"place": r.pl, "pc": cname(r.piso), "namesake": r.sl, "sc": cname(r.siso), "km": round(r.km, 1), "pi": r.p, "si": r.s, "state": r.state}
                     for r in NW.sort_values("km", ascending=False).itertuples()]}
R["new"]["under30_pct"] = pc(R["new"]["under30"], len(NW))
nn = {r["place"] for r in R["new"]["rows"]}
assert "New Delhi" in nn and "New Amsterdam" in nn and "Neutral Bay" not in nn and "New Haven" not in nn and "Nye Beach" not in nn
ND = [r for r in R["new"]["rows"] if r["place"] == "New Delhi"][0]
R["new"]["delhi_km"] = ND["km"]

# ---------- the United States ----------
US = L[L.piso == "USA"]; UA = US[US.border == 1]
OLD = UA[~UA.sg.isin(["North America", "Latin America"])]
R["us"] = {"n": len(US), "pct": pc(len(US), N), "abroad": len(UA), "abroad_pct": pc(len(UA), len(US)), "old": len(OLD),
           "old_settle": int((OLD.cat == "Settlement").sum()), "townships": int(US.pl.str.contains("Township").sum()),
           "states_with": int(OLD.state.replace("", np.nan).dropna().nunique()), "gbr": int((UA.siso == "GBR").sum()),
           "gbr_pct": pc((UA.siso == "GBR").sum(), len(UA)), "deu": int((UA.siso == "DEU").sum()), "nld": int((UA.siso == "NLD").sum()),
           "mn_townships": int(((US.state == "Minnesota") & US.pl.str.contains("Township")).sum()), "mn": int((US.state == "Minnesota").sum())}
R["us"]["townships_pct"] = pc(R["us"]["townships"], len(US))
st = OLD[OLD.state != ""].groupby("state")
R["us_states"] = sorted([{"state": k, "n": len(g), "settle": int((g.cat == "Settlement").sum()), "townships": int(g.pl.str.contains("Township").sum()),
                          "list": [f"{r.pl} ({r.sl}, {cname(r.siso)})" for r in g.sort_values("pl").itertuples()]} for k, g in st], key=lambda x: (-x["n"], x["state"]))
R["us_top_state"] = R["us_states"][0]
on = OLD.groupby("s").p.nunique().sort_values(ascending=False)
R["us_old_names"] = [{"si": s, "name": S.loc[s, "label"], "country": cname(S.loc[s, "iso"]), "n": int(n),
                      "states": sorted(set(x for x in OLD[OLD.s == s].state if x))} for s, n in on.head(15).items()]
R["us_old_countries"] = [{"country": cname(i), "n": int(v)} for i, v in OLD.siso.value_counts().head(12).items()]
CLASSIC = OLD[OLD.sl.isin(["Athens", "Rome", "Sparta", "Troy", "Carthage", "Utica", "Ithaca", "Syracuse", "Palmyra", "Corinth", "Memphis", "Thebes", "Babylon", "Troy", "Smyrna", "Alexandria", "Antioch", "Delphi", "Marathon", "Olympia", "Macedonia", "Euclid", "Attica", "Arcadia"])]
R["us"]["classical"] = len(CLASSIC); R["us"]["classical_names"] = sorted(set(CLASSIC.sl))
BIB = OLD[OLD.siso.isin(["ISR", "PSE", "LBN", "JOR", "SYR", "EGY", "IRQ"])]
R["us"]["biblical"] = len(BIB); R["us"]["biblical_names"] = sorted(set(BIB.sl))
assert R["us_states"][0]["state"] == "Minnesota"

# ---------- coverage ----------
cov = []
for i, v in L.piso.value_counts().items():
    popm = CM.get(i, {}).get("pop", 0) / 1e6
    cov.append({"iso": i, "country": cname(i), "n": int(v), "pct": pc(v, N), "per_m": round(v / popm, 2) if popm >= .5 else None, "popm": round(popm, 1)})
R["coverage"] = cov
CV = {c["iso"]: c for c in cov}
R["cov"] = {"n_countries": len(cov), "top4": sum(CV[i]["n"] for i in ("USA", "DEU", "AUS", "NLD")), "usa": CV["USA"]["n"], "deu": CV["DEU"]["n"], "aus": CV["AUS"]["n"],
            "nld": CV["NLD"]["n"], "gbr": CV["GBR"]["n"], "chn": CV.get("CHN", {"n": 0})["n"], "ind": CV.get("IND", {"n": 0})["n"], "bra": CV.get("BRA", {"n": 0})["n"],
            "mex": CV.get("MEX", {"n": 0})["n"], "nga": CV.get("NGA", {"n": 0})["n"],
            "nld_per_m": CV["NLD"]["per_m"], "ind_per_m": CV["IND"]["per_m"] if "IND" in CV else 0, "aus_per_m": CV["AUS"]["per_m"], "usa_per_m": CV["USA"]["per_m"],
            "africa": int(L.piso.map(lambda i: i in ISO_GROUP and ISO_GROUP[i] == "Middle East and Africa" and i not in ("TUR", "SYR", "LBN", "ISR", "PSE", "JOR", "IRQ", "IRN", "SAU", "YEM", "OMN", "ARE", "QAT", "BHR", "KWT")).sum()),
            "latam": R["iberia"]["latam_places"]}
R["cov"]["top4_pct"] = pc(R["cov"]["top4"], N)
R["cov"]["nld_vs_ind"] = round((CV["NLD"]["n"] / CM["NLD"]["pop"]) / (CV["IND"]["n"] / CM["IND"]["pop"]), -1)
R["cov"]["ind_per_100m"] = round(CV["IND"]["n"] / CM["IND"]["pop"] * 1e8, 1)
R["cov"]["zero_countries"] = sum(1 for k, v in CM.items() if v["pop"] >= 1e6 and k not in CV)
R["cov"]["countries_1m"] = sum(1 for k, v in CM.items() if v["pop"] >= 1e6)

# ---------- largest places named after somewhere else ----------
lg = L[L["pop"].notna()].sort_values("pop", ascending=False).drop_duplicates("p")
R["largest"] = [{"place": r.pl, "pc": cname(r.piso), "pop": int(r.pop), "namesake": r.sl, "cat": r.cat, "km": round(r.km, 1), "pi": r.p, "si": r.s} for r in lg.head(15).itertuples()]
lgb = L[L["pop"].notna() & (L.border == 1)].sort_values("pop", ascending=False).drop_duplicates("p")
R["largest_abroad"] = [{"place": r.pl, "pc": cname(r.piso), "pop": int(r.pop), "namesake": r.sl, "sc": cname(r.siso), "km": round(r.km), "pi": r.p, "si": r.s} for r in lgb.head(12).itertuples()]

# ---------- when the far-named places were founded (Wikidata inception, where given) ----------
FI = L[(L.border == 1) & L.inc.notna() & (L.inc >= 1500)]
dec = FI.groupby((FI.inc // 25 * 25).astype(int)).size()
R["founded"] = {"n": len(FI), "of": len(B), "pct": pc(len(FI), len(B)), "median": int(FI.inc.median()), "q25": int(FI.inc.quantile(.25)), "q75": int(FI.inc.quantile(.75)),
                "bins": [[int(k), int(v)] for k, v in dec.items()], "peak": int(dec.idxmax()), "peak_n": int(dec.max()),
                "c19_pct": pc(((FI.inc >= 1800) & (FI.inc < 1900)).sum(), len(FI))}

# ---------- named stories (checked) ----------
def link(pl, sl, piso=None, state=None):
    m = L[(L.pl == pl) & (L.sl == sl) & ((L.piso == piso) if piso else True) & ((L.state == state) if state else True)]
    assert len(m) >= 1, (pl, sl)
    r = m.iloc[0]
    return {"place": pl, "namesake": sl, "km": round(r.km), "pc": cname(r.piso), "sc": cname(r.siso), "pop": None if np.isnan(r["pop"]) else int(r["pop"]), "state": r.state, "pi": r.p, "si": r.s}


R["ex"] = {"boston": link("Boston", "Boston", "USA", "Massachusetts"), "boston_lincs": link("Boston", "Lincolnshire", "USA", "Massachusetts"),
           "boston_in": link("Boston", "Boston", "USA", "Indiana"), "perth": link("Perth", "Perth", "AUS"), "brooklyn": link("Brooklyn", "Breukelen"),
           "melbourne_fl": link("Melbourne", "Melbourne", "USA"), "kiri_paris": link("Paris", "Paris", "KIR"), "kiri_poland": link("Poland", "Poland", "KIR"),
           "delhi": link("New Delhi", "Delhi"), "newam": link("New Amsterdam", "Amsterdam", "USA"), "london_on": link("London", "London", "CAN"),
           "launceston": link("Launceston", "Launceston", "AUS"), "kitchener": link("Kitchener", "Berlin", "CAN"), "mexico": link("Mexico City", "Tenochtitlan"),
           "nova_roma": link("Nova Roma", "Rome"), "palmira": link("Nueva Palmira", "Palmyra"), "hamburgo": link("Novo Hamburgo", "Hamburg"), "madrid": link("New Madrid", "Madrid"),
           "calgary": link("Calgary", "Calgary"), "odesa": link("Odesa", "Odessos"), "smyrni": link("Nea Smyrni", "Smyrna") if ((L.pl == "Nea Smyrni") & (L.sl == "Smyrna")).any() else None}
assert R["ex"]["boston"]["sc"] == "United Kingdom" and R["ex"]["boston_in"]["namesake"] == "Boston" and R["ex"]["boston_in"]["sc"] == "United States"
R["absent"] = {k: bool(((L.pl == k) & (L.piso == i)).any()) for k, i in (("New York City", "USA"), ("New York", "USA"), ("New Orleans", "USA"), ("Sydney", "AUS"), ("York", "GBR"))}
assert not any(R["absent"].values())

# ---------- Wikipedia (context only) ----------
WP = jload(f"{RAW}/wiki_pages.json")
R["wiki"] = {"revid_toponymy": WP["Toponymy"]["revid"], "revid_unusual": WP["Place names considered unusual"]["revid"],
             "list_missing": "error" in WP["List of places named after other places"]}
R["meta"] = {"page": PAGE, "repo": REPO, "slug": SLUG, "qlever": QLEVER}

# ---------- clean data out ----------
out = L.copy()
out["place_qid"], out["namesake_qid"] = out.p, out.s
out["place_lon"], out["place_lat"] = out.p.map(P.lon), out.p.map(P.lat)
out["namesake_lon"], out["namesake_lat"] = out.s.map(S.lon), out.s.map(S.lat)
out["place_country"], out["namesake_country"] = out.piso.map(cname), out.siso.map(cname)
out["place_landmass"], out["namesake_landmass"] = out.p.map(P.mass), out.s.map(S.mass)
out["namesake_region"] = out.sg; out["km"] = out.km.round(1)
cols = ["place_qid", "pl", "place_lon", "place_lat", "piso", "place_country", "state", "pop", "inc", "namesake_qid", "sl", "namesake_lon", "namesake_lat", "siso",
        "namesake_country", "namesake_region", "cat", "okind", "km", "border", "ocean", "place_landmass", "namesake_landmass", "new"]
out[cols].rename(columns={"pl": "place", "piso": "place_iso3", "state": "us_state", "pop": "population", "inc": "inception_year", "sl": "namesake", "siso": "namesake_iso3",
                          "cat": "namesake_category", "okind": "other_kind", "km": "distance_km", "border": "crosses_border", "ocean": "crosses_ocean",
                          "new": "new_word"}).to_csv(f"{DATA}/named_after_links.csv", index=False)
pd.DataFrame([{**{k: v for k, v in t.items() if k not in ("kids",)}, "daughters": "; ".join(t["kids"])} for t in top]).to_csv(f"{DATA}/top_namesakes.csv", index=False)
pd.DataFrame(fl.reset_index().rename(columns={"siso": "from_iso3", "piso": "to_iso3", 0: "links"})).assign(
    from_country=lambda x: x.from_iso3.map(cname), to_country=lambda x: x.to_iso3.map(cname)).to_csv(f"{DATA}/country_flows.csv", index=False)
pd.DataFrame(cov).to_csv(f"{DATA}/links_by_country.csv", index=False)
pd.DataFrame([{k: v for k, v in r.items() if k != "list"} | {"places": "; ".join(r["list"])} for r in R["us_states"]]).to_csv(f"{DATA}/us_states_old_world.csv", index=False)
pd.DataFrame([{k: v for k, v in e.items() if k != "examples"} | {"examples": "; ".join(e["examples"])} for e in ex]).to_csv(f"{DATA}/exclusions.csv", index=False)

# ---------- page data ----------
PI = {p: i for i, p in enumerate(L.p.unique())}; SI = {s: i for i, s in enumerate(L.s.unique())}
GI = {g: i for i, g in enumerate(GN)}; CI = {c: i for i, c in enumerate(CN)}
site = {"groups": GROUPS, "cats": CATS,
        "places": [[P.loc[p, "label"], round(float(P.loc[p, "lon"]), 4), round(float(P.loc[p, "lat"]), 4), P.loc[p, "iso"], P.loc[p, "state"],
                    None if np.isnan(P.loc[p, "pop"]) else int(P.loc[p, "pop"]), p] for p in PI],
        "names": [[S.loc[s, "label"], round(float(S.loc[s, "lon"]), 4), round(float(S.loc[s, "lat"]), 4), S.loc[s, "iso"], CI[S.loc[s, "cat"]], GI[group_of(S.loc[s, "iso"])], s] for s in SI],
        "links": [[PI[r.p], SI[r.s], round(r.km, 1), int(r.border), int(r.ocean)] for r in L.itertuples()],
        "cname": {i: v["name"] for i, v in CM.items()}, "cpos": {i: [v["lx"], v["ly"], v["pop"]] for i, v in CM.items() if v["pop"] > 2e5}}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "results.json", "named_after_links.csv")})
print("N", N, R["dist"], "\nborder", R["border"], "\nocean", R["ocean"])
print("cats", [(c["cat"], c["n"], c["pct"], c["km_med"]) for c in cats]); print(R["other_kinds"])
print("giving", [(g["country"], g["n"]) for g in R["giving"][:10]]); print("receiving", [(g["country"], g["n"]) for g in R["receiving"][:10]])
print("flows", [(f["from"], f["to"], f["n"]) for f in R["flows"][:14]])
print("top", [(t["name"], t["country"], t["n"]) for t in top[:15]]); print("top abroad", [(t["name"], t["n"], t["where"]) for t in R["top_abroad"][:10]])
print("new", {k: v for k, v in R["new"].items() if k != "rows"}); print("us", R["us"]); print([(s["state"], s["n"]) for s in R["us_states"][:10]])
print("us old names", [(t["name"], t["n"]) for t in R["us_old_names"][:10]]); print("cov", R["cov"]); print("gbr", R["gbr"], "iberia", R["iberia"])
print("founded", {k: v for k, v in R["founded"].items() if k != "bins"}); print("reverse", R["reverse"]); print("greece", R["greece"])
print("largest abroad", [(x["place"], x["pc"], x["pop"], x["namesake"], x["sc"]) for x in R["largest_abroad"]]); print(R["ex"])
