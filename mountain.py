# ============================================================
#  mountain.py — Gunung dengan puncak bersalju (low-poly style)
#  Seperti gambar siklus air: gunung besar di kiri terrain
# ============================================================

import numpy as np
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


def _triangle(ax, ay, az, bx, by, bz, cx, cy, cz, color):
    """Helper: gambar 1 segitiga dengan warna solid (flat shading)."""
    glColor3f(*color)
    glBegin(GL_TRIANGLES)
    glVertex3f(ax, ay, az)
    glVertex3f(bx, by, bz)
    glVertex3f(cx, cy, cz)
    glEnd()


def _quad(ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz, color):
    """Helper: gambar 1 quad (2 segitiga) dengan warna solid."""
    _triangle(ax, ay, az, bx, by, bz, cx, cy, cz, color)
    _triangle(ax, ay, az, cx, cy, cz, dx, dy, dz, color)


# ================= GUNUNG UTAMA =================
def draw_mountain():
    """
    Gambar gunung besar di sisi kiri-tengah terrain.
    Koordinat disesuaikan agar berada di atas terrain darat (X positif → kanan = darat).
    
    Layout terrain:
      - Laut : X dari min_pos s/d 0
      - Darat: X dari 0 s/d max_pos
    
    Gunung ditempatkan di kuadran darat (X positif, Z tengah).
    """
    glDisable(GL_LIGHTING)

    N = TERRAIN_SIZE
    S = TERRAIN_SCALE

    # ─── Titik puncak utama gunung ───
    # Letakkan gunung di 30% dari tepi kanan terrain
    cx = (N * 0.20) * S   # ~20% dari tengah ke kanan
    cz = 0.0              # Tengah Z
    base_y = 0.1          # Ketinggian tanah (sama dengan terrain)
    peak_y = 14.0         # Puncak gunung
    snow_y = 10.0         # Batas salju mulai

    radius = (N * 0.18) * S  # Radius kaki gunung

    # ─── Jumlah sisi low-poly ───
    SIDES = 8  # Semakin sedikit = makin kotak / low-poly

    import math
    angles = [2 * math.pi * k / SIDES for k in range(SIDES)]

    # Titik-titik kaki gunung (lingkaran)
    base_pts = [
        (cx + radius * math.cos(a), base_y, cz + radius * math.sin(a))
        for a in angles
    ]

    # Titik-titik tengah (bahu gunung, lebih kecil radiusnya)
    mid_radius = radius * 0.45
    mid_y      = (base_y + peak_y) * 0.55
    mid_pts = [
        (cx + mid_radius * math.cos(a), mid_y, cz + mid_radius * math.sin(a))
        for a in angles
    ]

    # ─── Warna zona gunung ───
    COLOR_ROCK_DARK  = (0.38, 0.35, 0.35)   # Batu gelap (bawah)
    COLOR_ROCK_MID   = (0.52, 0.50, 0.48)   # Batu sedang (tengah)
    COLOR_ROCK_LIGHT = (0.65, 0.63, 0.60)   # Batu terang (atas)
    COLOR_SNOW       = (0.93, 0.95, 0.98)   # Salju putih
    COLOR_SNOW_SHADE = (0.78, 0.82, 0.88)   # Salju bayangan

    # ─── BAGIAN BAWAH: kaki → bahu ───
    for k in range(SIDES):
        nk = (k + 1) % SIDES
        bA = base_pts[k]
        bB = base_pts[nk]
        mA = mid_pts[k]
        mB = mid_pts[nk]

        # Sisi bawah (gelap)
        shade = 0.85 + 0.15 * math.cos(angles[k])
        c = tuple(v * shade for v in COLOR_ROCK_DARK)
        _quad(
            bA[0], bA[1], bA[2],
            bB[0], bB[1], bB[2],
            mB[0], mB[1], mB[2],
            mA[0], mA[1], mA[2],
            c
        )

    # ─── BAGIAN TENGAH: bahu → puncak (zona batu + salju) ───
    peak = (cx, peak_y, cz)

    for k in range(SIDES):
        nk = (k + 1) % SIDES
        mA = mid_pts[k]
        mB = mid_pts[nk]

        # Cek apakah segmen ini di sisi "cerah" (menghadap kamera)
        angle_mid = (angles[k] + angles[nk]) / 2
        face_light = math.cos(angle_mid - math.pi * 0.25)  # bias ke arah kamera

        # Pilih warna berdasarkan ketinggian rata-rata dan arah cahaya
        avg_y = (mA[1] + mB[1] + peak[1]) / 3
        if avg_y > snow_y:
            base_color = COLOR_SNOW if face_light > 0 else COLOR_SNOW_SHADE
        elif avg_y > mid_y * 0.7:
            base_color = COLOR_ROCK_LIGHT
        else:
            base_color = COLOR_ROCK_MID

        shade = 0.75 + 0.25 * max(0, face_light)
        c = tuple(v * shade for v in base_color)

        _triangle(
            mA[0], mA[1], mA[2],
            mB[0], mB[1], mB[2],
            peak[0], peak[1], peak[2],
            c
        )

    # ─── TUTUP BAWAH (lantai gunung) agar tidak bolong ───
    glColor3f(0.30, 0.22, 0.12)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(cx, base_y - 0.05, cz)
    for pt in base_pts:
        glVertex3f(pt[0], pt[1] - 0.05, pt[2])
    glVertex3f(base_pts[0][0], base_pts[0][1] - 0.05, base_pts[0][2])
    glEnd()

    # ─── GUNUNG KECIL DI BELAKANG (gunung hijau kecil) ───
    _draw_small_hill(
        cx  = cx + radius * 0.9,
        cz  = cz + radius * 0.6,
        base_y = base_y,
        peak_y = 7.5,
        radius = radius * 0.55,
        sides  = 7,
        color_base = (0.25, 0.48, 0.22),   # Hijau gelap
        color_peak = (0.38, 0.60, 0.30),   # Hijau terang
    )

    _draw_small_hill(
        cx  = cx + radius * 0.7,
        cz  = cz - radius * 0.7,
        base_y = base_y,
        peak_y = 5.5,
        radius = radius * 0.40,
        sides  = 6,
        color_base = (0.22, 0.42, 0.20),
        color_peak = (0.35, 0.55, 0.28),
    )


def _draw_small_hill(cx, cz, base_y, peak_y, radius, sides, color_base, color_peak):
    """Gambar bukit kecil hijau (variasi gunung kecil)."""
    import math
    angles  = [2 * math.pi * k / sides for k in range(sides)]
    base_pts = [
        (cx + radius * math.cos(a), base_y, cz + radius * math.sin(a))
        for a in angles
    ]
    peak = (cx, peak_y, cz)

    glDisable(GL_LIGHTING)

    for k in range(sides):
        nk = (k + 1) % sides
        bA = base_pts[k]
        bB = base_pts[nk]

        face_light = math.cos((angles[k] + angles[nk]) / 2 - math.pi * 0.2)
        t = (peak_y - base_y) / (peak_y - base_y + 0.001)  # selalu 1 di puncak

        r = color_base[0] + (color_peak[0] - color_base[0]) * t
        g = color_base[1] + (color_peak[1] - color_base[1]) * t
        b_val = color_base[2] + (color_peak[2] - color_base[2]) * t

        shade = 0.80 + 0.20 * max(0, face_light)
        c = (r * shade, g * shade, b_val * shade)

        _triangle(
            bA[0], bA[1], bA[2],
            bB[0], bB[1], bB[2],
            peak[0], peak[1], peak[2],
            c
        )

    # Tutup bawah
    glColor3f(0.28, 0.20, 0.10)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(cx, base_y - 0.05, cz)
    for pt in base_pts:
        glVertex3f(pt[0], pt[1] - 0.05, pt[2])
    glVertex3f(base_pts[0][0], base_pts[0][1] - 0.05, base_pts[0][2])
    glEnd()