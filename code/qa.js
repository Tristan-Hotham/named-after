// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server PORT; set PORT).
// MapLibre comes from a local npm copy (the CDN is not reachable from the build container); fonts are blocked here,
// so the screenshots show the Natural Earth base map with system fonts. NOML=1 blocks MapLibre too, to check that the
// page falls back to its own canvas map.
const { chromium } = require("playwright");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
const fs = require("fs");
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  const sizes = process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]];
  for (const [nm, vw, vh] of sizes) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/googleapis|gstatic/, r => r.abort());
    if (process.env.NOML) await p.route(/maplibre-gl/, r => r.abort());
    else {
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    }
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + process.env.PORT + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(3500);
    const tag = process.env.NOML ? "noml_" : "";
    await p.screenshot({ path: `qa/${tag}${nm}_top.png` });
    const idle = () => p.evaluate(() => new Promise(r => { if (typeof map === "undefined" || !map || !map.loaded) return r(); let done = false; const fin = () => { if (!done) { done = true; r(); } }; map.once("idle", fin); map.triggerRepaint(); setTimeout(fin, 30000); }));
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(500); if (!process.env.NOML && /atlas|map/.test(sel)) await idle(); await p.locator(sel).screenshot({ path: `qa/${tag}${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    await p.click('#showRow [data-m="ocean"]'); await p.waitForTimeout(800); await shot("#atlas", "map_ocean");
    await p.click('#showRow [data-m="all"]');
    await p.click('#tryRow .btn:nth-child(2)'); await p.waitForTimeout(2500); await shot("#atlas", "try_boston");
    await p.click('#tryRow .btn:nth-child(5)'); await p.waitForTimeout(2500); await shot("#atlas", "try_amsterdam");
    await p.fill("#q", "Athens"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_athens");
    await p.click(".back").catch(() => {});
    await p.click("#groupRow .btn:nth-child(2)"); await p.waitForTimeout(800); await shot("#atlas", "group_britain"); await p.click("#groupRow .btn:nth-child(1)").catch(() => {});
    await p.click("#groupRow .btn:nth-child(2)"); await p.waitForTimeout(300);
    await p.click(".lyrBtn"); await p.waitForTimeout(300); await p.locator('.lyrPanel [data-k="cities"]').check(); await p.locator('.lyrPanel input[value="cat"]').check(); await p.waitForTimeout(600); await shot("#map", "layers_panel");
    await p.locator('.lyrPanel input[value="group"]').check(); await p.click(".lyrBtn");
    if (!process.env.NOML) {
      const nf = await p.evaluate(() => [map.queryRenderedFeatures({ layers: ["arcs"] }).length, map.queryRenderedFeatures({ layers: ["nm"] }).length]); console.log(nm, "arcs and rings rendered:", nf);
      // click a namesake ring for its family
      await p.evaluate(() => map.jumpTo({ center: [-1, 52], zoom: 4 })); await p.waitForTimeout(1200);
      const hit = await p.evaluate(() => { const f = map.queryRenderedFeatures({ layers: ["nm"] }); if (!f.length) return null; const c = f.sort((a, b) => b.properties.k - a.properties.k)[0]; const xy = map.project(c.geometry.coordinates); const r = map.getContainer().getBoundingClientRect(); return [r.left + xy.x, r.top + xy.y]; });
      if (hit) { await p.mouse.click(hit[0], hit[1]); await p.waitForTimeout(2500); await shot("#atlas", "click_ring"); } else errs.push(nm + ": no rings rendered");
    } else {
      const box = await p.locator("#map canvas.fb").boundingBox(); if (!box) errs.push(nm + ": no fallback canvas");
    }
    for (const c of ["catChart", "distChart", "longTable", "topChart", "giveChart", "chordChart", "newTable", "usChart", "covChart", "foundChart"]) await shot("#" + c, c);
    if (nm === "phone" && !process.env.NOML) {
      await p.click("#theme"); await p.waitForTimeout(1200); await shot("#atlas", "dark_map"); await shot("#chordChart", "dark_chord");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
      await p.click(".mfs-btn"); await p.waitForTimeout(600);
    }
    if (process.env.NOML) { await p.locator("#atlas").scrollIntoViewIfNeeded(); const fs_ = await p.locator(".mfs-btn").count(); console.log(nm, "fallback full-screen buttons:", fs_); }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
