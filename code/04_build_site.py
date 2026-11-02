"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, ocean labels, cities) is embedded. Facts stated in words
are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before </body>.
10.5281/zenodo.23878606, https://doi.org/10.5281/zenodo.23878606 and https://blog.tristanhotham.com/2026/10/31/named-after/ stay as placeholders for the publisher. Needs only data/ (not raw/)."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
T = {t["name"]: t for t in R["top"]}
NEWR = {r["place"]: r for r in R["new"]["rows"]}
links = __import__("pandas").read_csv(f"{DATA}/named_after_links.csv", keep_default_na=False)

# facts stated in words (page, blog, paper, collage)
c = R["cats"]
assert c["Mountain or hill"]["km_med"] < c["River"]["km_med"] < c["Settlement"]["km_med"] < c["Region or country"]["km_med"]
assert c["Settlement"]["pct"] < 40 and R["natural_pct"] > 30
H = R["dist_hist"]
assert H[0]["n"] == max(h["n"] for h in H) and H[8]["n"] > H[7]["n"] > 0 and H[8]["n"] > H[6]["n"] and H[5]["n"] < H[8]["n"]        # two humps, a dip between
assert R["longest_nzl"] >= 10 and R["longest"][0]["km"] < 20015
assert [t["name"] for t in R["top"][:5]] == ["Prague", "Amsterdam", "Anatolia", "Moscow", "Europe"]
pr = [k for k in T["Prague"]["kids"] if "edm" in k.lower()]
assert len(pr) > R["prague"]["cz"] / 2                                                   # "most of them ... Pražské Předměstí"
assert R["top_abroad"][0]["name"] == "Amsterdam"
mk = T["Moscow"]["kids"]
assert sum(("Mosk" in k or "Mask" in k or "Moscow city" in k) and "Netherlands" not in k for k in mk) >= 4 and sum("Netherlands" in k for k in mk) == 2
for nm in ("Berlin", "Paris", "Bristol", "Windsor", "Athens", "Bethlehem"):
    assert 4 <= T[nm]["n"] <= 6 and T[nm]["abroad"] >= T[nm]["n"] - 1, nm
assert R["one_daughter_pct"] > 80
assert [g["iso"] for g in R["giving"][:4]] == ["GBR", "DEU", "NLD", "FRA"] and [g["iso"] for g in R["receiving"][:3]] == ["USA", "AUS", "CAN"]
nl_us = set(links[(links.namesake_iso3 == "NLD") & (links.place_iso3 == "USA")].place)
assert {"Brooklyn", "New Amsterdam", "New Utrecht"} <= nl_us
assert R["greece"]["tur_grc"] >= 10 and {"Nea Smyrni", "Nea Vyssa"} <= set(R["greece"]["examples"])
assert any("Amerikamura" in e for e in R["reverse"]["examples"]) and any("Sherbrooke (Australia)" in e for e in R["reverse"]["examples"])
assert R["iberia"]["latam"] < 10 and R["iberia"]["latam_places_pct"] < 3
for nm in ("Neu-Ulm", "New Delhi", "New Cairo", "New Aswan City"):
    assert NEWR[nm]["km"] < 30, nm
for nm in ("New Amsterdam", "New Madrid", "New Bremen", "New Glarus", "Novo Hamburgo", "Nova Friburgo", "Nueva Palmira"):
    assert links[(links.place == nm) & (links.new_word != "")].crosses_ocean.max() == 1, nm
assert R["new"]["under30_pct"] > 50
assert {"Athens", "Rome", "Sparta", "Ithaca", "Syracuse", "Antioch", "Smyrna", "Palmyra", "Memphis"} == set(R["us"]["classical_names"])
assert {"Bethlehem", "Hebron", "Lebanon", "Moab", "Mount Carmel"} <= set(R["us"]["biblical_names"])
mn = [s for s in R["us_states"] if s["state"] == "Minnesota"][0]["list"]
for nm in ("Belgium Township", "Russia Township", "Malmo Township", "Christiania Township (Oslo"):
    assert any(x.startswith(nm) for x in mn), nm
assert 20 < R["us"]["pct"] < 30                                                          # "a quarter of the whole file"
assert 1500 < R["cov"]["nld_vs_ind"] < 2500                                              # "about 2,000 times"
assert R["ex"]["perth"]["sc"] == "United Kingdom" and R["ex"]["boston"]["sc"] == "United Kingdom" and R["ex"]["kiri_paris"]["sc"] == "France"
assert R["founded"]["c19_pct"] > 50 and 1800 <= R["founded"]["median"] < 1900
assert R["source"]["excluded_stat_links"] / R["source"]["excluded_links"] > .8              # "above all"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23878606", "https://doi.org/10.5281/zenodo.23878606", "https://blog.tristanhotham.com/2026/10/31/named-after/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    RS = {k: v for k, v in R.items() if k not in ("source",)}
    RS["source"] = {k: v for k, v in R["source"].items() if k != "checks"}
    html = html.replace("/*RESULTS*/", J(RS)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*OCEANS*/", J(jload(f"{DATA}/oceans.json")))
    html = html.replace("/*CITIES*/", J([c for c in jload(f"{DATA}/cities.json") if c["pop"] >= 4e5]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
