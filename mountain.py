# ============================================================
#  mountain.py — IMPROVED: mirip gambar siklus air
#  Fitur: kerucut tajam, banyak layer, batu abu2, salju tebal
# ============================================================

import math
import random
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


def _triangle(a, b, c, color):
    glColor3f(*color)
    glBegin(GL_TRIANGLES)
    glVertex3f(*a)
    glVertex3f(*b)
    glVertex3f(*c)
    glEnd()


def _quad(a, b, c, d, color):
    _triangle(a, b, c, color)
    _triangle(a, c, d, color)


def _lerp_color(c1, c2, t):
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t,
    )


def draw_mountain():
    glDisable(GL_LIGHTING)

    N = TERRAIN_SIZE
    S = TERRAIN_SCALE

    # ── posisi & ukuran ──────────────────────────────────────
    cx = (N * 0.2) * S
    cz = 0.0

    base_y   = 0.1
    peak_y   = 15.0          # lebih tinggi → lebih dramatis
    radius   = (N * 0.20) * S

    SIDES = 24               # lebih halus

    angles = [2 * math.pi * k / SIDES for k in range(SIDES)]

    # ── profil gunung: kerucut curam (mirip gambar) ───────────
    # Kita pakai kurva kuadratik: radius mengecil cepat ke atas
    # layer: 0=base … 6=peak
    LAYERS = 6
    layer_t = [i / LAYERS for i in range(LAYERS + 1)]   # 0.0 … 1.0

    # radius mengikuti (1-t)^1.6  → lereng curam di atas
    layer_r = [radius * ((1 - t) ** 1.6) for t in layer_t]

    # tinggi mengikuti t  (linear cukup)
    layer_y = [base_y + (peak_y - base_y) * t for t in layer_t]

    # ── warna per layer (gelap bawah → terang tengah → putih atas) ──
    ROCK_BASE  = (0.30, 0.28, 0.27)   # batu gelap
    ROCK_MID   = (0.52, 0.50, 0.48)   # batu terang
    ROCK_UPPER = (0.68, 0.66, 0.64)   # batu abu cerah
    SNOW_LINE  = (0.90, 0.90, 0.92)   # salju tipis
    SNOW_PEAK  = (0.97, 0.97, 1.00)   # salju murni

    def layer_color(i):
        # i = indeks layer bawah (0..LAYERS-1)
        t = i / (LAYERS - 1)
        if t < 0.35:
            return _lerp_color(ROCK_BASE, ROCK_MID, t / 0.35)
        elif t < 0.65:
            return _lerp_color(ROCK_MID, ROCK_UPPER, (t - 0.35) / 0.30)
        elif t < 0.85:
            return _lerp_color(ROCK_UPPER, SNOW_LINE, (t - 0.65) / 0.20)
        else:
            return _lerp_color(SNOW_LINE, SNOW_PEAK, (t - 0.85) / 0.15)

    # ── generate titik tiap layer ─────────────────────────────
    # Tambah noise kecil supaya kelihatan berbatu, bukan sempurna
    rng = random.Random(42)   # seed tetap → shape konsisten

    def make_ring(r, y, noise_amp=0.0):
        pts = []
        for a in angles:
            nr = r + rng.uniform(-noise_amp, noise_amp) * r
            ny = y + rng.uniform(-noise_amp, noise_amp) * (peak_y * 0.04)
            pts.append((cx + nr * math.cos(a), ny, cz + nr * math.sin(a)))
        return pts

    rings = []
    for i, (r, y) in enumerate(zip(layer_r, layer_y)):
        amp = 0.08 if i < LAYERS else 0.0   # layer atas lebih halus
        rings.append(make_ring(r, y, noise_amp=amp))

    peak = (cx, peak_y, cz)

    # ── gambar tiap band layer ────────────────────────────────
    for i in range(LAYERS):
        bot = rings[i]
        top = rings[i + 1]
        col = layer_color(i)

        # variasi warna ringan tiap facet (simulasi batu)
        for k in range(SIDES):
            nk = (k + 1) % SIDES
            # sedikit variasi terang/gelap per segmen
            v = rng.uniform(-0.04, 0.04)
            fc = (
                min(1.0, max(0.0, col[0] + v)),
                min(1.0, max(0.0, col[1] + v)),
                min(1.0, max(0.0, col[2] + v)),
            )
            _quad(bot[k], bot[nk], top[nk], top[k], fc)

    # ── cap puncak (salju tebal) ──────────────────────────────
    top_ring = rings[LAYERS]
    for k in range(SIDES):
        nk = (k + 1) % SIDES
        _triangle(top_ring[k], top_ring[nk], peak, SNOW_PEAK)

    # ── salju di bagian upper (overlay putih di lereng atas) ──
    # Gambar patch salju transparan di beberapa segmen atas
    SNOW_THRESH = 4   # layer teratas ke-4 ke atas
    for i in range(LAYERS - SNOW_THRESH, LAYERS):
        bot = rings[i]
        top = rings[i + 1]
        t_ratio = (i - (LAYERS - SNOW_THRESH)) / SNOW_THRESH
        # hanya sebagian segmen (sisi depan / random) punya salju
        for k in range(SIDES):
            nk = (k + 1) % SIDES
            # gambar patch salju di ~40% facet secara acak (seed konsisten)
            if rng.random() < 0.45 + t_ratio * 0.35:
                snow_col = _lerp_color(SNOW_LINE, SNOW_PEAK, t_ratio)
                # sedikit transparan → geser warna ke abu agar blend
                blend = 0.55 + t_ratio * 0.35
                sc = (
                    snow_col[0] * blend + 0.5 * (1 - blend),
                    snow_col[1] * blend + 0.5 * (1 - blend),
                    snow_col[2] * blend + 0.5 * (1 - blend),
                )
                _quad(bot[k], bot[nk], top[nk], top[k], sc)

    # ── tutup dasar (tanah coklat gelap) ─────────────────────
    glColor3f(0.25, 0.18, 0.10)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(cx, base_y - 0.05, cz)
    for pt in rings[0]:
        glVertex3f(pt[0], pt[1] - 0.05, pt[2])
    glVertex3f(rings[0][0][0], rings[0][0][1] - 0.05, rings[0][0][2])
    glEnd()