# ============================================================
#  river.py — Sungai mengalir dari kaki gunung menuju laut
#  Seperti gambar siklus air: aliran air biru dari gunung → laut
# ============================================================

import math
import numpy as np
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


# ================= TITIK-TITIK JALUR SUNGAI =================
def _get_river_path():
    """
    Kembalikan list titik (x, z) jalur tengah sungai,
    dari kaki gunung (darat) menuju tepi laut (x=0).
    
    Koordinat sesuai terrain:
      - Darat : X > 0
      - Laut  : X < 0  (batas di X=0)
    """
    N = TERRAIN_SIZE
    S = TERRAIN_SCALE
    
    # Mulai dari kaki gunung
    x_start = (N * 0.15) * S
    z_start = 0.0
    
    # Akhir di bibir pantai (dekat X=0)
    x_end = 0.2
    z_end = 0.0

    # Buat jalur berliku (kurva Bezier sederhana manual)
    # Titik kontrol untuk tikungan sungai
    ctrl_pts = [
        (x_start,             z_start),           # mulai kaki gunung
        (x_start * 0.75,      z_start + S * 1.5), # belok kanan
        (x_start * 0.50,      z_start + S * 0.5), # lurus sedikit
        (x_start * 0.30,      z_start - S * 1.0), # belok kiri
        (x_start * 0.15,      z_start + S * 0.3), # mendekati pantai
        (x_end,               z_end),             # bibir pantai
    ]

    # Interpolasi titik-titik antara ctrl_pts (linear)
    path = []
    STEPS = 40
    for seg in range(len(ctrl_pts) - 1):
        x0, z0 = ctrl_pts[seg]
        x1, z1 = ctrl_pts[seg + 1]
        for t_step in range(STEPS):
            t = t_step / STEPS
            path.append((
                x0 + (x1 - x0) * t,
                z0 + (z1 - z0) * t
            ))
    path.append(ctrl_pts[-1])
    return path


# ================= GAMBAR SUNGAI =================
def draw_river():
    """
    Gambar sungai sebagai strip quad berwarna biru di atas terrain.
    Sedikit melayang (y = 0.12) agar tidak Z-fighting dengan tanah.
    """
    glDisable(GL_LIGHTING)

    path  = _get_river_path()
    WIDTH = 0.35   # Setengah lebar sungai (unit world)
    y_river = 0.13 # Sedikit di atas permukaan tanah (0.1)

    # Warna sungai: gradien dari biru gelap (dalam) ke biru terang (pantai)
    COLOR_DEEP    = (0.15, 0.45, 0.80)
    COLOR_SHALLOW = (0.30, 0.65, 0.90)

    total = len(path)

    glBegin(GL_QUADS)
    for i in range(total - 1):
        x0, z0 = path[i]
        x1, z1 = path[i + 1]

        # Arah tegak lurus jalur sungai
        dx = x1 - x0
        dz = z1 - z0
        length = math.sqrt(dx * dx + dz * dz) + 1e-6
        nx =  dz / length  # normal X (tegak lurus)
        nz = -dx / length  # normal Z

        # Gradien warna berdasarkan posisi (0=hulu, 1=hilir)
        t  = i / total
        r  = COLOR_DEEP[0] + (COLOR_SHALLOW[0] - COLOR_DEEP[0]) * t
        g  = COLOR_DEEP[1] + (COLOR_SHALLOW[1] - COLOR_DEEP[1]) * t
        b  = COLOR_DEEP[2] + (COLOR_SHALLOW[2] - COLOR_DEEP[2]) * t

        t2 = (i + 1) / total
        r2 = COLOR_DEEP[0] + (COLOR_SHALLOW[0] - COLOR_DEEP[0]) * t2
        g2 = COLOR_DEEP[1] + (COLOR_SHALLOW[1] - COLOR_DEEP[1]) * t2
        b2 = COLOR_DEEP[2] + (COLOR_SHALLOW[2] - COLOR_DEEP[2]) * t2

        # 4 sudut quad
        glColor3f(r, g, b)
        glVertex3f(x0 + nx * WIDTH, y_river, z0 + nz * WIDTH)
        glVertex3f(x0 - nx * WIDTH, y_river, z0 - nz * WIDTH)

        glColor3f(r2, g2, b2)
        glVertex3f(x1 - nx * WIDTH, y_river, z1 - nz * WIDTH)
        glVertex3f(x1 + nx * WIDTH, y_river, z1 + nz * WIDTH)
    glEnd()

    # ─── Highlight tengah sungai (warna lebih terang) ───
    glBegin(GL_QUAD_STRIP)
    for i, (x, z) in enumerate(path):
        t   = i / total
        r   = 0.40 + 0.15 * t
        g_v = 0.70 + 0.10 * t
        b   = 0.95

        glColor3f(r, g_v, b)
        glVertex3f(x, y_river + 0.002, z + 0.08)
        glVertex3f(x, y_river + 0.002, z - 0.08)
    glEnd()

    # ─── Batu-batu kecil di pinggir sungai ───
    _draw_river_rocks(path)


def _draw_river_rocks(path):
    """Gambar batu-batu kecil di beberapa titik sepanjang sungai."""
    glDisable(GL_LIGHTING)

    # Ambil beberapa titik secara berkala
    rock_indices = range(5, len(path) - 5, 8)

    for i in rock_indices:
        x, z = path[i]

        # Batu di kiri
        _draw_rock(x + 0.5, 0.14, z + 0.55)
        # Batu di kanan
        _draw_rock(x - 0.4, 0.14, z - 0.45)


def _draw_rock(rx, ry, rz):
    """Gambar 1 batu kecil (kubus gepeng)."""
    size = 0.18
    h    = 0.10
    glColor3f(0.42, 0.40, 0.38)
    glBegin(GL_QUADS)
    # Atas
    glVertex3f(rx - size, ry + h, rz - size)
    glVertex3f(rx + size, ry + h, rz - size)
    glVertex3f(rx + size, ry + h, rz + size)
    glVertex3f(rx - size, ry + h, rz + size)
    # Depan
    glColor3f(0.32, 0.30, 0.28)
    glVertex3f(rx - size, ry,     rz + size)
    glVertex3f(rx + size, ry,     rz + size)
    glVertex3f(rx + size, ry + h, rz + size)
    glVertex3f(rx - size, ry + h, rz + size)
    glEnd()


# ================= ALIRAN BAWAH TANAH =================
def draw_underground_flow():
    """
    Visualisasi aliran bawah tanah (arrow biru di bawah terrain),
    dari darat menuju laut — sesuai label 'Air hujan kembali ke lautan'.
    Digambar di bawah terrain base (y < -3.0).
    """
    glDisable(GL_LIGHTING)

    N = TERRAIN_SIZE
    S = TERRAIN_SCALE

    y_underground = -2.5   # Di dalam fondasi, di atas lantai dasar (-3.0)

    # Beberapa jalur aliran bawah tanah (garis horizontal dari darat → laut)
    for z_offset in [-S * 1.5, 0.0, S * 1.5]:
        x_start = (N * 0.35) * S
        x_end   = -S * 0.5   # Mendekati laut

        # Gambar sebagai strip tipis berwarna biru transparan
        glColor3f(0.20, 0.55, 0.85)
        glBegin(GL_QUADS)
        glVertex3f(x_end,   y_underground,        z_offset - 0.15)
        glVertex3f(x_start, y_underground,        z_offset - 0.15)
        glVertex3f(x_start, y_underground + 0.08, z_offset - 0.15)
        glVertex3f(x_end,   y_underground + 0.08, z_offset - 0.15)
        glEnd()

        # Panah di ujung kiri (menuju laut)
        ax = x_end
        az = z_offset
        glColor3f(0.10, 0.40, 0.75)
        glBegin(GL_TRIANGLES)
        glVertex3f(ax - 0.4, y_underground + 0.04, az)
        glVertex3f(ax + 0.1, y_underground + 0.04, az - 0.25)
        glVertex3f(ax + 0.1, y_underground + 0.04, az + 0.25)
        glEnd()