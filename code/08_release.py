"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23878606, https://doi.org/10.5281/zenodo.23878606 and https://blog.tristanhotham.com/2026/10/31/named-after/ stay as placeholders for the publisher. Needs only data/, code/, the figures and
the paper PDF: raw/ is not used and is not packed."""
import json as _json, shutil, zipfile, importlib.util
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Named_After_Somewhere_Else"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
G = R["giving"]
assert 4.5 < G[0]["n"] / G[1]["n"] < 5.5                                                  # "five times as many as Germany"
US = {s["state"]: s for s in R["us_states"]}
assert (US["Indiana"]["n"], US["New York"]["n"], US["Massachusetts"]["n"], US["Utah"]["n"]) == (24, 24, 20, 18)
assert US["Minnesota"]["townships"] > US["Minnesota"]["n"] / 2                             # "most are townships"
assert [t["n"] for t in R["top"][2:5]] == [8, 8, 8]
assert [f["ti"] for f in R["flows"][3:6]] == ["USA"] * 3 and [f["fi"] for f in R["flows"][3:6]] == ["DEU", "NLD", "ITA"]
assert [o["name"] for o in R["us_old_names"][:4]] == ["Germany", "Athens", "Bristol", "Amsterdam"]
ams = [k for k in R["top"][1]["kids"]]
assert any("New York" in k for k in ams) and any("Missouri" in k for k in ams) and any("South Africa" in k for k in ams) and any("Canada" in k for k in ams)
assert [r["iso"] for r in R["coverage"][:4]] == ["USA", "DEU", "AUS", "NLD"] and R["coverage"][4]["iso"] == "CAN"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23878606"}, set(re.findall(r"\{\{[^|}]+\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s = R["source"]
meta = {"title": "Named after somewhere else: mapping the places named after other places",
        "slug": "named-after",
        "excerpt": f"I mapped the {s['n']:,} settlements Wikidata says are named after another place. Most names come from a river or the town next door, but {R['ocean']['pct']:.0f}% crossed an ocean, and Britain gave away more names than anywhere else.",
        "seo_description": f"A map of {s['n']:,} places named after other places: rivers, hills and towns next door, and the British names that crossed the oceans.",
        "tags": ["place names", "toponymy", "maps", "data visualisation", "Wikidata", "migration", "history", "geography"],
        "header_alt": f"Title card reading 'Named after somewhere else' in black and red on pale paper, beside a world map criss-crossed by thin coloured great circles: a red bundle from Britain to the eastern United States and another to Australia and New Zealand. Text: {s['n']:,} places named after another place, and how far the names travelled."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/named-after_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"named-after/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"named-after/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "named-after/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("``", "\u201c").replace("''", "\u201d")
zmeta = {"title": "Named After Somewhere Else: Places Named After Other Places in Wikidata",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Place and name data: Wikidata (CC0).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["toponymy", "place names", "transfer names", "Wikidata", "migration", "colonial settlement", "great circles", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
