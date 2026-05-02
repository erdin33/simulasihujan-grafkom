# ============================================================
#  river.py — Sungai mengalir dari kaki gunung menuju laut
#  Seperti gambar siklus air: aliran air biru dari gunung → laut
# ============================================================

import math
import numpy as np
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


# ================= TITIK-TITIK JALUR SUNGAI =================
def get_river_path():
    """
    Kembalikan list titik (x, z) jalur tengah sungai,
    dari kaki gunung (darat) menuju tepi laut (x=0).
    
    Koordinat sesuai terrain:
      - Darat : X > 0
      - Laut  : X < 0  (batas di X=0)
    """
    N = TERRAIN_SIZE
    S = TERRAIN_SCALE
    
    # Mulai dari kaki gunung (X negatif)
    x_start = -13.0
    z_start = -11.0
    
    # Akhir di bibir pantai (pasir/air)
    x_end = -4.0
    z_end = 2.0

    P0 = (-14.0, -11.0) # gunung
    P1 = (-10.0, 2.0)   # meliuk tajam ke arah depan (Z positif)
    P2 = (-6.0, -12.0)  # meliuk tajam kembali ke belakang (Z negatif)
    P3 = (-1.0, 3.0)    # bersambung jauh ke dalam laut

    # Interpolasi Bezier Cubic untuk S-Curve yang indah dan mengalir mulus
    path = []
    STEPS = 60
    for i in range(STEPS + 1):
        t = i / STEPS
        u = 1.0 - t
        # Rumus Cubic Bezier
        x = (u**3)*P0[0] + 3*(u**2)*t*P1[0] + 3*u*(t**2)*P2[0] + (t**3)*P3[0]
        z = (u**3)*P0[1] + 3*(u**2)*t*P1[1] + 3*u*(t**2)*P2[1] + (t**3)*P3[1]
        path.append((x, z))
    return path


# ================= GAMBAR SUNGAI =================
def draw_river():
    """
    Gambar sungai sebagai strip quad berwarna biru di atas terrain.
    Melayang perlahan mengikuti kemiringan daratan ke laut.
    """
    glDisable(GL_LIGHTING)

    path  = get_river_path()
    WIDTH = 0.85   # Setengah lebar sungai (unit world) lebih lebar

    # Warna sungai: gradien dari biru gelap (dalam) ke biru terang (pantai)
    COLOR_DEEP    = (0.15, 0.45, 0.80)
    COLOR_SHALLOW = (0.30, 0.65, 0.90)

    total = len(path)
    
    # ─── PRE-KALKULASI BANK KIRI DAN KANAN ───
    left_bank = []
    right_bank = []
    
    for i in range(total):
        x, z = path[i]
        
        # Arah tangen sungai
        if i < total - 1:
            nx_dir = path[i+1][0] - x
            nz_dir = path[i+1][1] - z
        else:
            nx_dir = x - path[i-1][0]
            nz_dir = z - path[i-1][1]
            
        length = math.sqrt(nx_dir**2 + nz_dir**2) + 1e-6
        nx = nz_dir / length
        nz = -nx_dir / length
        
        from terrain import get_world_y
        lx = x + nx * WIDTH
        lz = z + nz * WIDTH
        ly = get_world_y(lx, lz) + 0.04
        
        rx = x - nx * WIDTH
        rz = z - nz * WIDTH
        ry = get_world_y(rx, rz) + 0.04
        
        left_bank.append((lx, ly, lz))
        right_bank.append((rx, ry, rz))

    # ─── GAMBAR PERMUKAAN SUNGAI ───
    glBegin(GL_QUAD_STRIP)
    for i in range(total):
        t  = i / total
        r  = COLOR_DEEP[0] + (COLOR_SHALLOW[0] - COLOR_DEEP[0]) * t
        g  = COLOR_DEEP[1] + (COLOR_SHALLOW[1] - COLOR_DEEP[1]) * t
        b  = COLOR_DEEP[2] + (COLOR_SHALLOW[2] - COLOR_DEEP[2]) * t

        glColor3f(r, g, b)
        lx, ly, lz = left_bank[i]
        glVertex3f(lx, ly, lz)
        
        rx, ry, rz = right_bank[i]
        glVertex3f(rx, ry, rz)
    glEnd()

    # ─── Highlight tengah sungai (warna lebih terang) ───
    glBegin(GL_QUAD_STRIP)
    for i in range(total):
        x, z = path[i]
        t   = i / total
        r   = 0.40 + 0.15 * t
        g_v = 0.70 + 0.10 * t
        b   = 0.95

        # Normal sungai
        if i < total - 1:
            nx_dir = path[i+1][0] - x
            nz_dir = path[i+1][1] - z
        else:
            nx_dir = x - path[i-1][0]
            nz_dir = z - path[i-1][1]
            
        length = math.sqrt(nx_dir**2 + nz_dir**2) + 1e-6
        nx = nz_dir / length
        nz = -nx_dir / length

        from terrain import get_world_y
        ry = get_world_y(x, z) + 0.045
        glColor3f(r, g_v, b)
        
        # Gambar highlight mengikuti arah aliran sungai (tegak lurus)
        hl_w = WIDTH * 0.25
        glVertex3f(x + nx * hl_w, ry, z + nz * hl_w)
        glVertex3f(x - nx * hl_w, ry, z - nz * hl_w)
    glEnd()

    # ─── Batu-batu kecil di pinggir sungai ───
    _draw_river_rocks(path)


def _draw_river_rocks(path):
    """Gambar batu-batu kecil di beberapa titik sepanjang sungai."""
    glDisable(GL_LIGHTING)

    # Ambil beberapa titik secara berkala
    rock_indices = range(5, len(path) - 5, 10)

    from terrain import get_world_y
    for i in rock_indices:
        x, z = path[i]

        # Batu di kiri
        _draw_rock(x + 1.2, get_world_y(x + 1.2, z + 1.2), z + 1.2)
        # Batu di kanan
        _draw_rock(x - 1.1, get_world_y(x - 1.1, z - 1.1), z - 1.1)


def _draw_rock(rx, ry, rz):
    """Gambar 1 batu kecil (kubus gepeng)."""
    size = 0.12
    h    = 0.08
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
