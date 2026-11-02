"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, and Natural Earth outlines in an Equal Earth projection centred on 10 E (the seam runs
down the Pacific at 170 W, so the Atlantic and the routes to Australia stay whole). Reads only data/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, box
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1D2128", "#636A72", "#E2DED3", "#DDD8CC", "#E8EEF1"
HOT, INK = "#C8322B", "#1F3A6B"

LON0 = 10
EE = Transformer.from_crs(4326, f"+proj=eqearth +lon_0={LON0} +datum=WGS84 +units=m", always_xy=True)
SEAM = LON0 - 180   # -170


def wrap(lon):
    """Longitude shifted into (SEAM, SEAM + 360)."""
    return (np.asarray(lon, float) - SEAM) % 360 + SEAM


def proj(lon, lat):
    lo = wrap(lon); lo = np.where(lo > 180, lo - 360, lo)
    return EE.transform(lo, np.asarray(lat, float))


W = jload(f"{DATA}/world.json")
SHAPES = []
for f in W["features"]:
    g = shape(f["geometry"]).buffer(0)
    for half in (box(-180, -90, SEAM - 1e-3, 90), box(SEAM + 1e-3, -90, 180, 90)):
        q = g.intersection(half)
        if q.is_empty: continue
        for poly in (q.geoms if hasattr(q, "geoms") else [q]):
            if poly.geom_type != "Polygon": continue
            xy = np.array(poly.exterior.coords)
            x, y = EE.transform(xy[:, 0], np.clip(xy[:, 1], -89.5, 89.5))
            SHAPES.append((f["properties"]["iso"], np.column_stack([x, y])))
WORLD_EXT = (-17.0e6, 17.0e6, -8.75e6, 8.7e6)


def world(ax, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1, skip_ata=True):
    for iso, p in SHAPES:
        if skip_ata and iso == "ATA":
            continue
        ax.add_patch(MPoly(p, closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, SEAM + 1e-6), lat); xr, yr = EE.transform(np.full_like(lat, SEAM - 1e-6), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def arc_xy(lon0, lat0, lon1, lat1):
    """Projected great-circle pieces from (lon0, lat0) to (lon1, lat1), cut where they cross the seam."""
    pts = np.array(gc_points(lon0, lat0, lon1, lat1))
    lo = wrap(pts[:, 0]); cut = np.where(np.abs(np.diff(lo)) > 180)[0] + 1
    out = []
    for seg in np.split(np.column_stack([lo, pts[:, 1]]), cut):
        if len(seg) < 2: continue
        x, y = EE.transform(np.where(seg[:, 0] > 180, seg[:, 0] - 360, seg[:, 0]), seg[:, 1]); out.append((x, y))
    return out


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def site():
    S = jload(f"{DATA}/site.json")
    P = [dict(zip(["name", "lon", "lat", "iso", "state", "pop", "q"], r)) for r in S["places"]]
    N = [dict(zip(["name", "lon", "lat", "iso", "c", "g", "q"], r)) for r in S["names"]]
    L = [dict(zip(["p", "s", "km", "b", "o"], r)) for r in S["links"]]
    return P, N, L
