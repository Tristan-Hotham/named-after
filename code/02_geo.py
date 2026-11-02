"""Geography. A light world outline file for the page and figures (Natural Earth 1:50m), country names, label
positions, populations and giving region; city and ocean labels; and, for every place and namesake, its country, its
landmass, and for places in the United States its state.

Country. Wikidata's own country (P17), matched to Natural Earth by Natural Earth's Wikidata id. Where Wikidata gives
several countries, the one whose outline contains the point; where it gives none that Natural Earth knows (historical
states such as the Soviet Union or the Ottoman Empire, or disputed entries), the country whose outline contains the
point, or failing that the nearest outline within 100 km (points on the coast or in the sea).
Landmass. The Natural Earth 1:50m land polygon that holds the point (or the nearest one). The four giant polygons are
the Americas, Africa with Europe and Asia, Australia and Antarctica; every other island is joined to the nearest of
these if it lies within 2,500 km (Britain and Japan to Eurasia, Newfoundland and Cuba to the Americas, New Zealand to
Australia), and otherwise counted as a remote ocean island (Hawaii, most of the Pacific islands). A link 'crosses an
ocean' when its two ends are on different landmasses."""
import numpy as np, pandas as pd, collections
from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree
from shapely.ops import transform as stransform
from pyproj import Transformer
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND", "SOL": "SOM"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, meta, polys, wd = [], {}, [], {}
for f in W50["features"]:
    p = f["properties"]; iso = FIX.get(iso_of(p), iso_of(p))
    g = shape(f["geometry"]); polys.append((iso, g))
    if p.get("WIKIDATAID"): wd[p["WIKIDATAID"]] = iso
    gs = g.simplify(0.04, preserve_topology=True)
    if gs.is_empty:
        continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
    if iso not in meta:
        nm = (p.get("NAME_EN") or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
        meta[iso] = {"name": nm, "lx": round(p["LABEL_X"], 2), "ly": round(p["LABEL_Y"], 2), "pop": float(p.get("POP_EST") or 0), "group": group_of(iso)}
meta.get("CYP", {}).update(name="Cyprus")
for k, v in {"GBR": "United Kingdom", "CZE": "Czechia", "MKD": "North Macedonia", "COD": "DR Congo", "BIH": "Bosnia and Herzegovina"}.items():
    if k in meta: meta[k]["name"] = v
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave(meta, f"{DATA}/countries.json")
CT = STRtree([g for _, g in polys]); CISO = [i for i, _ in polys]

P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in P["features"]:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 300000 or p.get("adm0cap") == 1:
        cities.append({"name": re.sub(r"\s+", " ", p["name"]), "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")

# ocean and sea labels (my positions, on open water)
OL = [("PACIFIC OCEAN", -150, 25, 1), ("PACIFIC OCEAN", -125, -28, 1), ("ATLANTIC OCEAN", -40, 30, 1), ("ATLANTIC OCEAN", -15, -25, 1), ("INDIAN OCEAN", 78, -18, 1),
      ("SOUTHERN OCEAN", 60, -58, 1), ("Mediterranean Sea", 17, 35, 2), ("Caribbean Sea", -76, 15, 2), ("Gulf of Mexico", -90, 25.5, 2), ("North Sea", 3.5, 56, 2),
      ("Baltic Sea", 19.5, 57.5, 2), ("Tasman Sea", 161, -38, 2), ("Hudson Bay", -85.5, 60, 2), ("Bay of Biscay", -5.5, 45.3, 2), ("Black Sea", 34.5, 43.3, 2)]
jsave([{"name": n, "lon": lo, "lat": la, "rank": r} for n, lo, la, r in OL], f"{DATA}/oceans.json")

# ---------- country of each place and namesake ----------
how = collections.Counter()


def pip(lon, lat):
    pt = Point(lon, lat)
    for k in CT.query(pt, predicate="intersects"):
        return CISO[k]
    k = CT.nearest(pt)
    if polys[k][1].distance(pt) * 111 * max(.2, np.cos(np.radians(lat))) <= 100:
        return CISO[k]
    return ""


def country(row, kind):
    isos = [wd[q] for q in row.p17 if q in wd]
    isos = list(dict.fromkeys(isos))
    if len(isos) == 1: how[kind + ": Wikidata country"] += 1; return isos[0]
    here = pip(row.lon, row.lat)
    if len(isos) > 1:
        how[kind + ": several, chose by position"] += 1
        return here if here in isos else isos[0]
    how[kind + (": by position" if here else ": none")] += 1
    return here


PL = pd.read_pickle(f"{WORK}/places.pkl"); SN = pd.read_pickle(f"{WORK}/namesakes.pkl")
PL["iso"] = [country(r, "place") for r in PL.itertuples()]
SN["iso"] = [country(r, "namesake") for r in SN.itertuples()]
PL["pip"] = [pip(r.lon, r.lat) for r in PL.itertuples()]
SN["pip"] = [pip(r.lon, r.lat) for r in SN.itertuples()]

# ---------- landmass ----------
EE = Transformer.from_crs(4326, 8857, always_xy=True)
LAND = [shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]
LANDm = [stransform(EE.transform, g) for g in LAND]
order = np.argsort([-g.area for g in LANDm])[:4]
GIANT = {}
for k in order:
    c = LAND[k].representative_point()
    nm = ("Antarctica" if c.y < -60 else "Australia and neighbours" if c.x > 110 and c.y < 0 else "The Americas" if c.x < -30 else "Africa, Europe and Asia")
    GIANT[k] = nm
assert sorted(GIANT.values()) == ["Africa, Europe and Asia", "Antarctica", "Australia and neighbours", "The Americas"], GIANT
LT = STRtree(LAND)
poly_mass = {}


def mass_of_poly(k):
    if k in poly_mass: return poly_mass[k]
    if k in GIANT: poly_mass[k] = GIANT[k]; return GIANT[k]
    d = {GIANT[g]: LANDm[k].distance(LANDm[g]) for g in GIANT}
    nm, dist = min(d.items(), key=lambda kv: kv[1])
    poly_mass[k] = nm if dist <= 2.5e6 else "Remote ocean islands"
    return poly_mass[k]


def landmass(lon, lat):
    pt = Point(lon, lat)
    hit = list(LT.query(pt, predicate="intersects"))
    k = hit[0] if hit else int(LT.nearest(pt))
    return mass_of_poly(int(k))


PL["mass"] = [landmass(r.lon, r.lat) for r in PL.itertuples()]
SN["mass"] = [landmass(r.lon, r.lat) for r in SN.itertuples()]

# ---------- US state for places in the United States ----------
A1 = [f for f in jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"] if f["properties"]["adm0_a3"] == "USA"]
ST = STRtree([shape(f["geometry"]) for f in A1]); SNAME = [f["properties"]["name"] for f in A1]
SPOS = {f["properties"]["name"]: (f["properties"]["longitude"], f["properties"]["latitude"]) for f in A1}


def state(lon, lat):
    pt = Point(lon, lat)
    for k in ST.query(pt, predicate="intersects"):
        return SNAME[k]
    k = int(ST.nearest(pt))
    return SNAME[k] if ST.geometries[k].distance(pt) < 0.5 else ""


PL["state"] = [state(r.lon, r.lat) if r.iso == "USA" else "" for r in PL.itertuples()]
jsave({k: [round(v[0], 2), round(v[1], 2)] for k, v in SPOS.items()}, f"{WORK}/state_pos.json")
PL.to_pickle(f"{WORK}/places.pkl"); SN.to_pickle(f"{WORK}/namesakes.pkl")
chk = jload(f"{WORK}/checks.json")
chk["country_how"] = dict(how)
chk["place_p17_vs_position_agree_pct"] = round(100 * float(((PL.iso == PL.pip) | (PL.pip == "")).mean()), 1)
chk["namesake_p17_vs_position_agree_pct"] = round(100 * float(((SN.iso == SN.pip) | (SN.pip == "")).mean()), 1)
chk["no_country"] = {"places": int((PL.iso == "").sum()), "namesakes": int((SN.iso == "").sum()), "namesake_examples": list(SN[SN.iso == ""].label[:12])}
chk["us_no_state"] = int(((PL.iso == "USA") & (PL.state == "")).sum())
chk["mass_places"] = PL.mass.value_counts().to_dict(); chk["mass_namesakes"] = SN.mass.value_counts().to_dict()
jsave(chk, f"{WORK}/checks.json", indent=1)
print("countries", len(meta), "cities", len(cities), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")
print(dict(how)); print(chk["no_country"], "us no state", chk["us_no_state"]); print(chk["mass_places"]); print(chk["mass_namesakes"])
print("agree", chk["place_p17_vs_position_agree_pct"], chk["namesake_p17_vs_position_agree_pct"])
