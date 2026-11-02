"""r/dataisbeautiful collage for named-after: 2400 x 3200 px, light background. Numbers from data/results.json.
No labels sit on the map itself (the lines cover the oceans): every label is on the paper around the panels, so none
can fall on land or on the data, and no leader lines are needed."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

R = jload(f"{DATA}/results.json")
P, N, L = site()
GC = [c for _, c in GROUPS]; CC = [c for _, c in CATS]
BGc = "#F7F5F0"; SEAc = "#E9EEF1"; LANDc = "#E3DED2"
s, d, o, g = R["source"], R["dist"], R["ocean"], R["gbr"]

fig = plt.figure(figsize=(12, 16), dpi=200, facecolor=BGc)
fig.text(.045, .985, "Named after somewhere else", fontproperties=DISP, fontsize=44, color=FG, va="top")
fig.text(.045, .940, f"{s['n']:,} places that Wikidata says are named after another place, each joined to its namesake by a great\n"
         f"circle. Most names come from the river or the town next door; {o['pct']:.0f}% crossed an ocean, and the United\n"
         f"Kingdom gave {R['giving'][0]['pct']:.0f}% of all the names that went abroad.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.3)

# ---- map (no labels on it)
ax = fig.add_axes([.03, .566, .94, .30])
outline(ax, fc=SEAc, ec="#C9CDD0", lw=.8); world(ax, lw=.3, land=LANDc, ec=BGc)
for i in sorted(range(len(L)), key=lambda i: L[i]["km"]):
    l = L[i]; n, p = N[l["s"]], P[l["p"]]
    for x, y in arc_xy(n["lon"], n["lat"], p["lon"], p["lat"]):
        ax.plot(x, y, color=GC[n["g"]], lw=.45, alpha=.42, zorder=3, solid_capstyle="round")
x, y = proj([p["lon"] for p in P], [p["lat"] for p in P]); ax.scatter(x, y, s=1.0, c=FG, lw=0, alpha=.55, zorder=5)

# ---- legend under the map, on paper
LP = SERP.copy(); LP.set_size(11.5)
fig.text(.045, .552, "Each line runs from the namesake to the place named after it, coloured by where the name came from. Dots: the places.", fontsize=9.4, color=MUT, va="top")
fig.legend(handles=[Line2D([], [], color=c, lw=3, label=gg) for gg, c in GROUPS], loc="upper left", bbox_to_anchor=(.035, .542), ncol=4, frameon=False, prop=LP,
           handlelength=1.6, handletextpad=.5, columnspacing=1.3, labelspacing=.45)

# ---- numbers row
ln = [n for n in N if n["name"] == R["longest"][0]["namesake"]][0]
assert -3 < ln["lon"] < -2 and 51 < ln["lat"] < 52   # Lansdown, near Bath, England
nums = [(f"{d['median']:.1f} km", INK, "median distance from\nnamesake to place"),
        (f"{R['cats']['Settlement']['pct']:.0f}%", HOT, "named after another\nsettlement; the rest\nafter rivers, hills, lakes"),
        (f"{o['pct']:.0f}%", GC[0], "crossed an ocean,\nmedian " + f"{o['km_med']:,} km"),
        (f"{R['longest'][0]['km']:,} km", FG, f"the longest: {R['longest'][0]['place']},\nNew Zealand, from\n{R['longest'][0]['namesake']}, England")]
for i, (big, col, sm) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, .468, big, fontproperties=SERB, fontsize=30, color=col, va="top")
    fig.text(xx, .432, sm, family=MONO, fontsize=10, color=FG, va="top", linespacing=1.25)

# ---- panel: distances
H = R["dist_hist"]
a = fig.add_axes([.07, .195, .40, .125]); a.set_facecolor(BGc); base = np.zeros(len(H))
for k, c in enumerate(CN):
    v = np.array([h[c] for h in H]); a.bar(range(len(H)), v, bottom=base, color=CC[k], width=.84); base += v
lab = lambda v: f"{v // 1000}k" if v >= 1000 else str(v)
a.set_xticks(np.arange(len(H) + 1) - .5); a.set_xticklabels([lab(h["a"]) for h in H] + ["21k"], fontsize=8.5)
a.set_xlim(-.6, len(H) - .4); a.set_yticks([0, 500, 1000]); a.tick_params(axis="y", labelsize=8.5); spines(a)
fig.text(.045, .352, "Names stay at home, or cross an ocean", family=MONO, fontsize=12, color=FG, fontweight="medium", va="bottom")
fig.text(.045, .338, "links by distance, km (stretched scale)", family=MONO, fontsize=9.5, color=MUT, va="bottom")
fig.legend(handles=[Patch(color=c, label=n.lower()) for n, c in CATS], loc="upper left", bbox_to_anchor=(.035, .172), ncol=5, frameon=False, prop=LP, handlelength=1, columnspacing=1)

# ---- panel: flows
F = R["flows"][:10]
a = fig.add_axes([.72, .175, .23, .15]); a.set_facecolor(BGc); yy = np.arange(len(F))[::-1]
a.barh(yy, [f["n"] for f in F], color=[GC[GN.index(group_of(f["fi"]))] for f in F], height=.66)
for y_, f in zip(yy, F): a.text(f["n"] + 2, y_, str(f["n"]), va="center", fontsize=9)
sh = lambda t: t.replace("United Kingdom", "UK").replace("United States", "US").replace("New Zealand", "NZ")
a.set_yticks(yy); a.set_yticklabels([f"{sh(f['from'])} to {sh(f['to'])}" for f in F], fontsize=9.5); a.tick_params(axis="y", length=0)
a.set_xticks([]); a.set_xlim(0, 130); spines(a); a.spines["bottom"].set_visible(False)
fig.text(.535, .352, "Who named whom", family=MONO, fontsize=12, color=FG, fontweight="medium", va="bottom")
fig.text(.535, .338, "names that crossed a border, biggest flows", family=MONO, fontsize=9.5, color=MUT, va="bottom")

# ---- famous pairs (text on paper)
ex = R["ex"]
pairs = [("Boston, Massachusetts", "Boston, Lincolnshire", ex["boston"]["km"]), ("Perth, Australia", "Perth, Scotland", ex["perth"]["km"]),
         ("Brooklyn, New York", "Breukelen, Netherlands", ex["brooklyn"]["km"]), ("Melbourne, Florida", "Melbourne, Australia", ex["melbourne_fl"]["km"]),
         ("Paris, Kiribati", "Paris, France", ex["kiri_paris"]["km"]), ("Nueva Palmira, Uruguay", "Palmyra, Syria", ex["palmira"]["km"]),
         ("New Delhi", "Delhi", ex["delhi"]["km"])]
fig.text(.045, .132, "Borrowed names", family=MONO, fontsize=12, color=FG, fontweight="medium", va="bottom")
for k, (a_, b_, km) in enumerate(pairs):
    yk = .118 - k * .012
    fig.text(.045, yk, a_, family=MONO, fontsize=9.2, color=FG, va="center")
    fig.text(.24, yk, "after " + b_, family=MONO, fontsize=9.2, color=MUT, va="center")
    fig.text(.545, yk, f"{km:,} km", family=MONO, fontsize=9.2, color=FG, va="center", ha="right")
T = R["top"][:6]
fig.text(.6, .132, "Most borrowed namesakes", family=MONO, fontsize=12, color=FG, fontweight="medium", va="bottom")
for k, t in enumerate(T):
    yk = .118 - k * .012
    fig.text(.6, yk, f"{t['name']} ({t['country']})", family=MONO, fontsize=9.2, color=FG, va="center")
    fig.text(.955, yk, f"{t['n']} places", family=MONO, fontsize=9.2, color=FG, va="center", ha="right")
fig.text(.6, .118 - 6 * .012, f"Prague's are mostly Czech suburbs", family=MONO, fontsize=9, color=MUT, va="center")

fig.text(.045, .006, f"Data: Wikidata \"named after\" (P138), CC0, via QLever, {s['fetched']}; census areas, camps and stations removed. Coverage is uneven:\n"
         f"four countries hold {R['cov']['top4_pct']:.0f}% of links. Outlines: Natural Earth. Interactive map: maps.tristanhotham.com/named-after", fontsize=8.6, color=MUT, va="bottom", linespacing=1.35)
out = os.path.join(ROOT, "reddit", "places_named_after_other_places.png")
fig.savefig(out, dpi=200, facecolor=BGc)
from PIL import Image
assert Image.open(out).size == (2400, 3200), Image.open(out).size
print("collage", out)
