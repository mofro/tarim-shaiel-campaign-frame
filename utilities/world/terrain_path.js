"use strict";
/*
 * Terrain path worker (#312): least-cost walk between two stops across AWS
 * terrarium elevation tiles. The Map Workshop embeds this file as text and runs
 * it from a Blob URL (generate_map_workshop.py), so it must stay self-contained.
 *
 * Elevation comes from the U.S. Geological Survey (SRTM, GMTED2010 and other
 * public-domain sources) via the AWS Terrain Tiles bucket.
 *
 * Cost of a step is its length divided by a relative Tobler factor, so flat
 * ground costs its length and a climb costs more. Steps steeper than the mode's
 * max slope are impassable. Rivers and lakes are not obstacles, and existing
 * roads are not used: this follows the ground, nothing else.
 *
 * The pure functions below are exercised from Node (tests/test_terrain_path.py)
 * by evaluating this file in a vm context, so keep browser-only code at the
 * bottom behind the importScripts check.
 */

var TILE = 256;
var SQRT2 = Math.SQRT2;
var MIN_MARGIN_PX = 16;
var FETCH_POOL = 8;
var EARTH_CIRC_M = 40075016.686;

function terr(code, message) {
  var e = new Error(message);
  e.code = code;
  return e;
}

// --- Web Mercator pixel space ------------------------------------------------

function worldPx(z) { return TILE * Math.pow(2, z); }

function lngToPx(lng, z) { return (lng + 180) / 360 * worldPx(z); }

function latToPx(lat, z) {
  var s = Math.sin(lat * Math.PI / 180);
  s = Math.max(-0.9999, Math.min(0.9999, s));
  return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * worldPx(z);
}

function pxToLng(x, z) { return x / worldPx(z) * 360 - 180; }

function pxToLat(y, z) {
  var n = Math.PI - 2 * Math.PI * y / worldPx(z);
  return 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
}

function metresPerPx(lat, z) {
  return EARTH_CIRC_M * Math.cos(lat * Math.PI / 180) / worldPx(z);
}

// Relative Tobler hiking factor: 1 on the flat, best on a gentle downhill.
function toblerFactor(slope, k, off) {
  return Math.exp(-k * (Math.abs(slope + off) - off));
}

// Terrarium pixel -> metres above sea level.
function terrariumMetres(r, g, b) { return r * 256 + g + b / 256 - 32768; }

// --- Grid selection ----------------------------------------------------------

/*
 * Pick the search window: stops plus a margin, at the finest zoom whose grid
 * fits `targetCells` (default `maxCells`). Falls back to minZoom while that still
 * fits `maxCells`, else null (the leg is too large to route).
 */
function planGrid(from, to, cfg) {
  var target = cfg.targetCells || cfg.maxCells;
  var fallback = null;
  for (var z = cfg.maxZoom; z >= cfg.minZoom; z--) {
    var ax = lngToPx(from[0], z), ay = latToPx(from[1], z);
    var bx = lngToPx(to[0], z), by = latToPx(to[1], z);
    var span = Math.max(Math.abs(ax - bx), Math.abs(ay - by));
    var m = Math.ceil(cfg.marginFrac * span) + MIN_MARGIN_PX;
    var last = worldPx(z) - 1;
    var x0 = Math.max(0, Math.floor(Math.min(ax, bx)) - m);
    var x1 = Math.min(last, Math.floor(Math.max(ax, bx)) + m);
    var y0 = Math.max(0, Math.floor(Math.min(ay, by)) - m);
    var y1 = Math.min(last, Math.floor(Math.max(ay, by)) + m);
    var w = x1 - x0 + 1, h = y1 - y0 + 1;
    var g = { z: z, x0: x0, y0: y0, w: w, h: h, cells: w * h };
    if (g.cells <= target) return g;
    if (z === cfg.minZoom && g.cells <= cfg.maxCells) fallback = g;
  }
  return fallback;
}

// --- Elevation ---------------------------------------------------------------

/*
 * Fill a Float32Array(w*h) with metres for the grid. `provider(z, tx, ty, stats)`
 * resolves to a Float32Array(256*256); it is called through a small pool.
 */
async function buildElevation(grid, provider, stats, onProgress) {
  var tx0 = Math.floor(grid.x0 / TILE), tx1 = Math.floor((grid.x0 + grid.w - 1) / TILE);
  var ty0 = Math.floor(grid.y0 / TILE), ty1 = Math.floor((grid.y0 + grid.h - 1) / TILE);
  var jobs = [];
  for (var ty = ty0; ty <= ty1; ty++) for (var tx = tx0; tx <= tx1; tx++) jobs.push([tx, ty]);

  var elev = new Float32Array(grid.w * grid.h);
  var next = 0, done = 0, failed = false;

  async function lane() {
    while (!failed) {
      var i = next++;
      if (i >= jobs.length) return;
      var tx = jobs[i][0], ty = jobs[i][1];
      var data;
      try {
        data = await provider(grid.z, tx, ty, stats);
      } catch (e) {
        failed = true;
        throw e;
      }
      // overlap of this tile with the grid, in global pixels
      var gx0 = Math.max(grid.x0, tx * TILE), gx1 = Math.min(grid.x0 + grid.w - 1, tx * TILE + TILE - 1);
      var gy0 = Math.max(grid.y0, ty * TILE), gy1 = Math.min(grid.y0 + grid.h - 1, ty * TILE + TILE - 1);
      for (var y = gy0; y <= gy1; y++) {
        var src = (y - ty * TILE) * TILE + (gx0 - tx * TILE);
        elev.set(data.subarray(src, src + (gx1 - gx0 + 1)), (y - grid.y0) * grid.w + (gx0 - grid.x0));
      }
      done++;
      onProgress({ type: "progress", phase: "tiles", done: done, total: jobs.length });
    }
  }

  var lanes = [];
  for (var n = 0; n < Math.min(FETCH_POOL, jobs.length); n++) lanes.push(lane());
  await Promise.all(lanes);
  return elev;
}

// --- Search ------------------------------------------------------------------

function MinHeap() {
  this.n = 0;
  this.cap = 1 << 16;
  this.f = new Float64Array(this.cap);
  this.v = new Int32Array(this.cap);
}

MinHeap.prototype.push = function (f, v) {
  if (this.n === this.cap) {
    var nf = new Float64Array(this.cap * 2), nv = new Int32Array(this.cap * 2);
    nf.set(this.f); nv.set(this.v);
    this.f = nf; this.v = nv; this.cap *= 2;
  }
  var F = this.f, V = this.v, i = this.n++;
  while (i > 0) {
    var p = (i - 1) >> 1;
    if (F[p] <= f) break;
    F[i] = F[p]; V[i] = V[p]; i = p;
  }
  F[i] = f; V[i] = v;
};

MinHeap.prototype.pop = function () {
  var F = this.f, V = this.v, top = V[0];
  var n = --this.n;
  if (n > 0) {
    var f = F[n], v = V[n], i = 0;
    for (;;) {
      var l = 2 * i + 1;
      if (l >= n) break;
      var r = l + 1, c = (r < n && F[r] < F[l]) ? r : l;
      if (F[c] >= f) break;
      F[i] = F[c]; V[i] = V[c]; i = c;
    }
    F[i] = f; V[i] = v;
  }
  return top;
};

// Metres per pixel for every row of the grid (Mercator stretches with latitude).
function rowScale(grid) {
  var out = new Float64Array(grid.h);
  for (var j = 0; j < grid.h; j++) out[j] = metresPerPx(pxToLat(grid.y0 + j + 0.5, grid.z), grid.z);
  return out;
}

var DX = [-1, 0, 1, -1, 1, -1, 0, 1];
var DY = [-1, -1, -1, 0, 0, 1, 1, 1];
var DIAG = [SQRT2, 1, SQRT2, 1, 1, SQRT2, 1, SQRT2];

/*
 * 8-neighbour A* from cell (sx,sy) to (gx,gy). Returns an Int32Array of cell
 * indexes start..goal, or null when no passable route exists. A step costs
 * length / toblerFactor(slope); |slope| > maxSlope is impassable.
 */
function astar(elev, w, h, rows, sx, sy, gx, gy, maxSlope, k, off, onProgress) {
  var N = w * h;
  var start = sy * w + sx, goal = gy * w + gx;
  if (start === goal) return new Int32Array([start]);

  var g = new Float32Array(N).fill(Infinity);
  var parent = new Int32Array(N).fill(-1);
  var closed = new Uint8Array(N);
  var heap = new MinHeap();

  var mppMin = Infinity;
  for (var j = 0; j < h; j++) if (rows[j] < mppMin) mppMin = rows[j];
  var fmax = Math.exp(k * off);

  function hOf(x, y) {
    var dx = Math.abs(x - gx), dy = Math.abs(y - gy);
    return mppMin * (Math.max(dx, dy) + (SQRT2 - 1) * Math.min(dx, dy)) / fmax;
  }

  g[start] = 0;
  heap.push(hOf(sx, sy), start);
  var expanded = 0;

  while (heap.n > 0) {
    var v = heap.pop();
    if (closed[v]) continue;
    closed[v] = 1;
    if (v === goal) {
      var rev = [];
      for (var c = goal; c !== -1; c = parent[c]) rev.push(c);
      return Int32Array.from(rev.reverse());
    }
    if ((++expanded & 0xFFFF) === 0) {
      onProgress({ type: "progress", phase: "search", done: expanded, total: N });
    }
    var vy = (v / w) | 0, vx = v - vy * w;
    var ev = elev[v], gv = g[v];
    for (var d = 0; d < 8; d++) {
      var nx = vx + DX[d], ny = vy + DY[d];
      if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
      var n = ny * w + nx;
      if (closed[n]) continue;
      var dist = (rows[vy] + rows[ny]) * 0.5 * DIAG[d];
      var slope = (elev[n] - ev) / dist;
      if (slope > maxSlope || slope < -maxSlope) continue;
      var ng = gv + dist / Math.exp(-k * (Math.abs(slope + off) - off));
      if (ng < g[n]) {
        g[n] = ng;
        parent[n] = v;
        heap.push(ng + hOf(nx, ny), n);
      }
    }
  }
  return null;
}

/*
 * Length, Tobler cost and steepest step of a cell path, all in double precision.
 * `costM` is the sum of length/factor, in metres: the reference the tests compare
 * the browser result against the Python model with.
 */
function pathStats(path, elev, w, rows, k, off) {
  var lenM = 0, costM = 0, steepest = 0;
  for (var i = 0; i + 1 < path.length; i++) {
    var a = path[i], b = path[i + 1];
    var ay = (a / w) | 0, by = (b / w) | 0;
    var ax = a - ay * w, bx = b - by * w;
    var dist = (rows[ay] + rows[by]) * 0.5 * ((ax !== bx && ay !== by) ? SQRT2 : 1);
    var slope = (elev[b] - elev[a]) / dist;
    lenM += dist;
    costM += dist / toblerFactor(slope, k, off);
    if (Math.abs(slope) > steepest) steepest = Math.abs(slope);
  }
  return { lenM: lenM, costM: costM, steepest: steepest };
}

// Douglas-Peucker over flat [x0,y0,x1,y1,...]; returns the kept point indexes.
function simplifyIdx(pts, tol) {
  var n = pts.length / 2;
  if (n <= 2) { var all = []; for (var q = 0; q < n; q++) all.push(q); return all; }
  var keep = new Uint8Array(n);
  keep[0] = 1; keep[n - 1] = 1;
  var stack = [0, n - 1];
  while (stack.length) {
    var hi = stack.pop(), lo = stack.pop();
    var ax = pts[2 * lo], ay = pts[2 * lo + 1], bx = pts[2 * hi], by = pts[2 * hi + 1];
    var dx = bx - ax, dy = by - ay, len2 = dx * dx + dy * dy;
    var worst = -1, at = -1;
    for (var i = lo + 1; i < hi; i++) {
      var px = pts[2 * i], py = pts[2 * i + 1], dd;
      if (len2 === 0) {
        dd = Math.hypot(px - ax, py - ay);
      } else {
        var t = ((px - ax) * dx + (py - ay) * dy) / len2;
        t = Math.max(0, Math.min(1, t));
        dd = Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
      }
      if (dd > worst) { worst = dd; at = i; }
    }
    if (worst > tol) {
      keep[at] = 1;
      stack.push(lo, at, at, hi);
    }
  }
  var out = [];
  for (var j = 0; j < n; j++) if (keep[j]) out.push(j);
  return out;
}

// --- One leg -----------------------------------------------------------------

/*
 * req = { id, from:[lng,lat], to:[lng,lat], maxSlope, cfg }. `provider` supplies
 * elevation tiles; `post` receives progress messages. Resolves to
 * { coords, costKm, zoom, cells, ... } or rejects with an Error carrying `code`
 * (toolarge | nopath | network | internal).
 */
async function routeLeg(req, provider, post) {
  var t0 = Date.now(), cfg = req.cfg;
  var grid = planGrid(req.from, req.to, cfg);
  if (!grid) {
    throw terr("toolarge", "Leg too long for terrain routing: even at zoom " + cfg.minZoom +
      " the search area exceeds " + cfg.maxCells.toLocaleString("en-US") + " cells");
  }
  var stats = { net: 0, cache: 0 };
  var elev = await buildElevation(grid, provider, stats, post);
  var rows = rowScale(grid);

  var sx = Math.floor(lngToPx(req.from[0], grid.z)) - grid.x0;
  var sy = Math.floor(latToPx(req.from[1], grid.z)) - grid.y0;
  var gx = Math.floor(lngToPx(req.to[0], grid.z)) - grid.x0;
  var gy = Math.floor(latToPx(req.to[1], grid.z)) - grid.y0;

  var path = astar(elev, grid.w, grid.h, rows, sx, sy, gx, gy,
                   req.maxSlope, cfg.toblerK, cfg.toblerOffset, post);
  if (!path) {
    throw terr("nopath", "No route found within the slope limit (" + req.maxSlope + " rise/run)");
  }
  var st = pathStats(path, elev, grid.w, rows, cfg.toblerK, cfg.toblerOffset);

  // Cell centres in pixel space, thinned so the saved line stays small.
  var pts = new Float64Array(path.length * 2);
  for (var i = 0; i < path.length; i++) {
    var cy = (path[i] / grid.w) | 0, cx = path[i] - cy * grid.w;
    pts[2 * i] = grid.x0 + cx + 0.5;
    pts[2 * i + 1] = grid.y0 + cy + 0.5;
  }
  var keep = simplifyIdx(pts, 0.6);
  var coords = keep.map(function (ix) {
    return [+pxToLng(pts[2 * ix], grid.z).toFixed(6), +pxToLat(pts[2 * ix + 1], grid.z).toFixed(6)];
  });
  coords[0] = [req.from[0], req.from[1]];
  coords[coords.length - 1] = [req.to[0], req.to[1]];

  return {
    coords: coords,
    costKm: st.costM / 1000,
    pathKm: st.lenM / 1000,
    steepest: st.steepest,
    zoom: grid.z,
    cells: grid.cells,
    tilesNet: stats.net,
    tilesCache: stats.cache,
    ms: Date.now() - t0
  };
}

// --- Browser worker ----------------------------------------------------------

var _tileDb = null;

function openTileDb() {
  if (_tileDb) return _tileDb;
  // The cache is optional: if the open errors, is blocked, or is still pending after
  // two seconds (a queued deleteDatabase from another tab does that), route without it.
  _tileDb = new Promise(function (resolve) {
    var timer = setTimeout(function () { resolve(null); }, 2000);
    function done(db) { clearTimeout(timer); resolve(db); }
    try {
      var r = indexedDB.open("hh-terrain-tiles", 1);
      r.onupgradeneeded = function () { r.result.createObjectStore("tiles"); };
      r.onsuccess = function () { done(r.result); };
      r.onerror = r.onblocked = function () { done(null); };
    } catch (e) {
      done(null);
    }
  });
  return _tileDb;
}

async function tileGet(key) {
  var db = await openTileDb();
  if (!db) return null;
  return new Promise(function (resolve) {
    try {
      var q = db.transaction("tiles", "readonly").objectStore("tiles").get(key);
      q.onsuccess = function () { resolve(q.result || null); };
      q.onerror = function () { resolve(null); };
    } catch (e) {
      resolve(null);
    }
  });
}

async function tilePut(key, buf) {
  var db = await openTileDb();
  if (!db) return;
  return new Promise(function (resolve) {
    try {
      var tx = db.transaction("tiles", "readwrite");
      tx.objectStore("tiles").put(buf, key);
      tx.oncomplete = tx.onerror = tx.onabort = function () { resolve(); };
    } catch (e) {
      resolve();
    }
  });
}

async function decodeTile(buf) {
  var bmp = await createImageBitmap(new Blob([buf], { type: "image/png" }),
                                    { colorSpaceConversion: "none", premultiplyAlpha: "none" });
  var cv = new OffscreenCanvas(TILE, TILE);
  var ctx = cv.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(bmp, 0, 0);
  bmp.close();
  var d = ctx.getImageData(0, 0, TILE, TILE).data;
  var out = new Float32Array(TILE * TILE);
  for (var i = 0; i < out.length; i++) out[i] = terrariumMetres(d[4 * i], d[4 * i + 1], d[4 * i + 2]);
  return out;
}

var _tileUrl = "";

async function fetchTile(z, x, y, stats) {
  var key = z + "/" + x + "/" + y;
  var buf = await tileGet(key);
  if (buf) {
    stats.cache++;
  } else {
    var resp;
    try {
      resp = await fetch(_tileUrl.replace("{z}", z).replace("{x}", x).replace("{y}", y));
    } catch (e) {
      throw terr("network", "Could not reach the elevation tile server");
    }
    if (!resp.ok) throw terr("network", "Elevation tile " + key + " returned HTTP " + resp.status);
    buf = await resp.arrayBuffer();
    stats.net++;
    await tilePut(key, buf);
  }
  return decodeTile(buf);
}

if (typeof importScripts === "function") {
  self.onmessage = function (ev) {
    var m = ev.data;
    if (!m || m.type !== "route") return;
    _tileUrl = m.cfg.tileUrl;
    function post(p) { p.id = m.id; self.postMessage(p); }
    routeLeg(m, fetchTile, post).then(function (res) {
      res.type = "result";
      post(res);
    }, function (err) {
      post({ type: "error", code: err.code || "internal", message: err.message || String(err) });
    });
  };
}
