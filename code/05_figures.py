"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; lines from data/site.json."""
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
P, N, L = site()
GC = [c for _, c in GROUPS]
CC = [c for _, c in CATS]


def both(fig, name, blog=True):
    w = fig.get_size_inches()[0]
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=1800 / w, facecolor=fig.get_facecolor())
    plt.close(fig)


def arcs(ax, sel=None, lw=.35, alpha=.35, z=3):
    order = sorted(range(len(L)), key=lambda i: L[i]["km"])
    for i in order:
        l = L[i]
        if sel and not sel(l): continue
        n, p = N[l["s"]], P[l["p"]]
        for x, y in arc_xy(n["lon"], n["lat"], p["lon"], p["lat"]):
            ax.plot(x, y, color=GC[n["g"]], lw=lw, alpha=alpha, zorder=z, solid_capstyle="round")


def dots(ax, s=1.2, z=5):
    x, y = proj([p["lon"] for p in P], [p["lat"] for p in P]); ax.scatter(x, y, s=s, c=FG, lw=0, alpha=.55, zorder=z)


# ---------- world map of every line ----------
fig = plt.figure(figsize=(12, 6.7), facecolor=BG); ax = fig.add_axes([0, .1, 1, .82])
outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG); arcs(ax); dots(ax)
fig.text(.02, .955, f"{R['source']['n']:,} places named after another place, each joined to its namesake by a great circle, coloured by where the name came from", fontsize=10.5, color=FG)
fig.legend(handles=[Line2D([], [], color=c, lw=2.5, label=g) for g, c in GROUPS], loc="lower center", ncol=5, frameon=False, fontsize=9, bbox_to_anchor=(.5, 0))
both(fig, "map")

# ---------- lines that cross an ocean ----------
fig = plt.figure(figsize=(12, 6.7), facecolor=BG); ax = fig.add_axes([0, .1, 1, .82])
outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG); arcs(ax, sel=lambda l: l["o"] == 1, lw=.6, alpha=.55)
fig.text(.02, .955, f"The {R['ocean']['n']:,} names that crossed an ocean, coloured by where they came from", fontsize=10.5, color=FG)
fig.legend(handles=[Line2D([], [], color=c, lw=2.5, label=g) for g, c in GROUPS], loc="lower center", ncol=5, frameon=False, fontsize=9, bbox_to_anchor=(.5, 0))
both(fig, "ocean_map")

# ---------- what they are named after, and how far ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.4), facecolor=BG, gridspec_kw={"width_ratios": [1, 1.35]}); fig.subplots_adjust(left=.15, right=.98, wspace=.32, top=.86, bottom=.17)
C = R["cats_list"]
a1.set_facecolor(BG); y = np.arange(len(C))[::-1]
a1.barh(y, [c["n"] for c in C], color=CC, height=.62)
for yy, c in zip(y, C): a1.text(c["n"] + 30, yy, f"{c['n']:,}\nmedian {c['km_med']:,.0f} km" if c["km_med"] >= 10 else f"{c['n']:,}\nmedian {c['km_med']:.1f} km", va="center", fontsize=9, linespacing=1.15)
a1.set_yticks(y); a1.set_yticklabels([c["cat"].replace("Region or country", "Region or\ncountry").replace("Mountain or hill", "Mountain\nor hill") for c in C], fontsize=10)
a1.set_xticks([]); a1.set_xlim(0, 2300); spines(a1); a1.spines["bottom"].set_visible(False); a1.tick_params(axis="y", length=0)
a1.set_title("Named after a...", loc="left", fontsize=12, color=FG)
H = R["dist_hist"]; a2.set_facecolor(BG); base = np.zeros(len(H))
for k, c in enumerate(CN):
    v = np.array([h[c] for h in H]); a2.bar(range(len(H)), v, bottom=base, color=CC[k], width=.84, label=c.lower()); base += v
for i, h in enumerate(H): a2.text(i, h["n"] + 15, f"{h['n']:,}", ha="center", fontsize=8.5)
lab = lambda a: f"{a // 1000}k" if a >= 1000 else str(a)
a2.set_xticks(np.arange(len(H) + 1) - .5); a2.set_xticklabels([lab(h["a"]) for h in H] + ["21k"], fontsize=9)
a2.set_xlim(-.6, len(H) - .4); spines(a2); a2.set_title("Distance to the namesake, km (stretched scale)", loc="left", fontsize=12, color=FG)
a2.legend(loc="upper center", frameon=False, fontsize=9, ncol=1, bbox_to_anchor=(.55, 1))
both(fig, "types")

# ---------- most borrowed ----------
T = R["top"][:15]
fig = plt.figure(figsize=(12, 6), facecolor=BG); ax = fig.add_axes([.19, .08, .62, .82]); ax.set_facecolor(BG)
y = np.arange(len(T))[::-1]
ax.barh(y, [t["n"] for t in T], color=[CC[CN.index(t["cat"])] for t in T], height=.66)
ax.barh(y, [t["abroad"] for t in T], color="#000000", alpha=.3, height=.66)
for yy, t in zip(y, T):
    ax.text(t["n"] + .15, yy, f"{t['n']}", va="center", fontsize=10)
    ax.text(14.6, yy, t["country"], va="center", fontsize=9.5, color=MUT)
ax.set_yticks(y); ax.set_yticklabels([t["name"] for t in T], fontsize=10.5); ax.tick_params(axis="y", length=0); ax.set_xticks([]); ax.set_xlim(0, 14.4)
spines(ax); ax.spines["bottom"].set_visible(False)
fig.text(.19, .935, "Places named after each namesake; the darker part of each bar is in another country", fontsize=10.5, color=FG)
fig.legend(handles=[Patch(color=c, label=n.lower()) for n, c in CATS], loc="lower right", frameon=False, fontsize=9, bbox_to_anchor=(.76, .08))
both(fig, "top")

# ---------- flows between countries ----------
F = R["flows"][:16]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 6.2), facecolor=BG, gridspec_kw={"width_ratios": [1, 1.25]}); fig.subplots_adjust(left=.12, right=.98, wspace=.62, top=.88, bottom=.05)
G = R["giving"][:12]; y = np.arange(len(G))[::-1]
a1.set_facecolor(BG); a1.barh(y, [g["n"] for g in G], color=HOT, height=.62)
for yy, g in zip(y, G): a1.text(g["n"] + 4, yy, f"{g['n']}", va="center", fontsize=9.5)
a1.set_yticks(y); a1.set_yticklabels([g["country"] for g in G], fontsize=10); a1.set_xticks([]); a1.set_xlim(0, 300); spines(a1); a1.spines["bottom"].set_visible(False); a1.tick_params(axis="y", length=0)
a1.set_title("Names given abroad, by country", loc="left", fontsize=12)
y = np.arange(len(F))[::-1]
a2.set_facecolor(BG); a2.barh(y, [f["n"] for f in F], color=[GC[GN.index(group_of(f["fi"]))] for f in F], height=.62)
for yy, f in zip(y, F): a2.text(f["n"] + 1.5, yy, f"{f['n']}", va="center", fontsize=9.5)
sh = lambda s: s.replace("United Kingdom", "UK").replace("United States", "US")
a2.set_yticks(y); a2.set_yticklabels([f"{sh(f['from'])} to {sh(f['to'])}" for f in F], fontsize=10); a2.set_xticks([]); a2.set_xlim(0, 120); spines(a2); a2.spines["bottom"].set_visible(False); a2.tick_params(axis="y", length=0)
a2.set_title("The biggest flows", loc="left", fontsize=12)
both(fig, "flows")

# ---------- US states ----------
U = R["us_states"][:18]
fig = plt.figure(figsize=(12, 6), facecolor=BG); ax = fig.add_axes([.17, .06, .5, .82]); ax.set_facecolor(BG)
y = np.arange(len(U))[::-1]
ax.barh(y, [u["n"] for u in U], color=INK, height=.64, label="other places")
ax.barh(y, [u["townships"] for u in U], color="#0B1426", height=.64, label="townships")
for yy, u in zip(y, U): ax.text(u["n"] + .5, yy, f"{u['n']}", va="center", fontsize=9.5)
ax.set_yticks(y); ax.set_yticklabels([u["state"] for u in U], fontsize=10); ax.tick_params(axis="y", length=0); ax.set_xticks([]); ax.set_xlim(0, 50); spines(ax); ax.spines["bottom"].set_visible(False)
ax.legend(loc="lower right", frameon=False, fontsize=9.5)
fig.text(.17, .935, f"US places named after places outside the Americas, by state ({R['us']['old']} in all)", fontsize=10.5, color=FG)
on = R["us_old_names"][:12]
fig.text(.71, .86, "Most used Old World names", fontsize=11, color=FG, fontweight="medium")
for k, o in enumerate(on):
    fig.text(.71, .815 - k * .055, f"{o['name']} ({o['country']})", fontsize=9.5, color=FG)
    fig.text(.97, .815 - k * .055, f"{o['n']}", fontsize=9.5, color=FG, ha="right")
both(fig, "us")

# ---------- coverage ----------
CV = R["coverage"][:20]
fig = plt.figure(figsize=(12, 6), facecolor=BG); ax = fig.add_axes([.17, .06, .6, .82]); ax.set_facecolor(BG)
y = np.arange(len(CV))[::-1]
ax.barh(y, [c["n"] for c in CV], color=[HOT if c["iso"] in ("USA", "DEU", "AUS", "NLD") else "#8C8478" for c in CV], height=.64)
for yy, c in zip(y, CV):
    ax.text(c["n"] + 8, yy, f"{c['n']:,}", va="center", fontsize=9.5)
    ax.text(1240, yy, f"{c['per_m']:.2f}" if c["per_m"] < .1 else f"{c['per_m']:.1f}", va="center", ha="right", fontsize=9.5, color=MUT)
ax.text(1240, len(CV) - .2, "per million\npeople", ha="right", va="bottom", fontsize=9, color=MUT)
ax.set_yticks(y); ax.set_yticklabels([c["country"] for c in CV], fontsize=10); ax.tick_params(axis="y", length=0); ax.set_xticks([]); ax.set_xlim(0, 1100); spines(ax); ax.spines["bottom"].set_visible(False)
ax.set_clip_on(False)
fig.text(.17, .935, f"Links by the place's country: four countries hold {R['cov']['top4_pct']:.0f}% of the file", fontsize=10.5, color=FG)
both(fig, "coverage")

# ---------- founding years (paper only) ----------
B = R["founded"]["bins"]
fig = plt.figure(figsize=(11, 4), facecolor=BG); ax = fig.add_axes([.07, .14, .9, .76]); ax.set_facecolor(BG)
ax.bar([b[0] + 12.5 for b in B], [b[1] for b in B], width=23, color=HOT)
ax.set_xlim(1500, 2025); spines(ax); ax.set_ylabel("places"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.set_title(f"Founding year (Wikidata inception) of places named after somewhere in another country, {R['founded']['n']} of {R['founded']['of']}", loc="left", fontsize=10.5)
both(fig, "founded", blog=False)

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.41, .1, .58, .8]); outline(ax, fc=SEA, ec="#C9CDD0", lw=.6); world(ax, lw=.2, ec=BG)
arcs(ax, lw=.45, alpha=.45); dots(ax, s=.8)
fig.text(.04, .88, "Named", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.04, .73, "after", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.04, .58, "somewhere", fontproperties=DISP, fontsize=54, color=HOT, va="top")
fig.text(.04, .43, "else", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.04, .26, f"{R['source']['n']:,} places named after another\nplace, and how far the names travelled.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.35)
fig.text(.04, .05, "maps.tristanhotham.com/named-after", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
