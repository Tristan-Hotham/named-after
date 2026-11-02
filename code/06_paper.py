"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23878606 placeholder.
Needs only data/ and the figures."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Named_After_Somewhere_Else"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
H = R["dist_hist"]
assert max(H[5]["n"], H[6]["n"], H[7]["n"]) < H[8]["n"] and min(H[5]["n"], H[6]["n"], H[7]["n"]) < H[3]["n"]           # "a trough between about 100 and 3,000 km"
assert set(R["top_abroad"][0]["where"]) == {"Canada", "Guyana", "South Africa", "Suriname", "United States"}
assert R["top"][1]["abroad"] == 8 and R["eur_to_new_pct"] > 50


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{tex(e['what'])} & {e['places']:,} & {e['links']:,}\\\\\n" for e in R["source"]["excluded"])
TE = ("\\begin{table}[tbp]\\centering\\small\\caption{Links removed from the raw query result, in the order the rules are applied.}\\label{tab:excl}"
      "\\begin{tabular}{p{10.5cm}rr}\\toprule Rule & Places & Links\\\\\\midrule\n" + rows +
      f"\\midrule All removed & & {R['source']['excluded_links']:,}\\\\ Kept & {R['source']['places']:,} & {R['source']['n']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{tex(c['cat'])} & {c['n']:,} & {c['pct']:.1f}\\% & {c['namesakes']:,} & {c['km_med']:,.1f} & {c['under10_pct']:.0f}\\% & {c['border_pct']:.0f}\\% & {c['ocean_pct']:.0f}\\%\\\\\n" for c in R["cats_list"])
TC = ("\\begin{table}[tbp]\\centering\\small\\setlength{\\tabcolsep}{4pt}\\caption{Links by the kind of namesake: count, share, distinct namesakes, median distance (km), and the shares within 10 km, crossing a border and crossing an ocean.}\\label{tab:cats}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Namesake & Links & Share & Namesakes & Median km & $<$10 km & Border & Ocean\\\\\\midrule\n" + rows +
      f"\\midrule All & {R['source']['n']:,} & 100\\% & {R['source']['namesakes']:,} & {R['dist']['median']:.1f} & {R['dist']['under10_pct']:.0f}\\% & {R['border']['pct']:.0f}\\% & {R['ocean']['pct']:.0f}\\%\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{tex(f['from'])} & {tex(f['to'])} & {f['n']}\\\\\n" for f in R["flows"][:20])
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{The twenty largest country-to-country flows of names (links crossing a border).}\\label{tab:flows}"
      "\\begin{tabular}{llr}\\toprule From (namesake) & To (place) & Links\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = fill(t, R, f=lambda v, f: tfmt(v, f or "raw"))
for k, v in (("EXCL", TE), ("CATS", TC), ("FLOWS", TF)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in txt
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
