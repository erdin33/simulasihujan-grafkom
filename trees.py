# ============================================================
#  trees.py — Pohon-pohon hijau di terrain darat
#  Seperti gambar siklus air: pohon hijau di lereng & dataran
# ============================================================

import math
import random
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


# ================= POSISI POHON =================
def _generate_tree_positions(seed=42):
    """
    Hasilkan list posisi pohon (x, z) di atas terrain darat.
    Terrain darat berada di X > 0.
    """
    rng = random.Random(seed)
    N   = TERRAIN_SIZE
    S   = TERRAIN_SCALE

    positions = []

    # Pohon di dataran rendah (dekat pantai, X kecil)
    for _ in range(12):
        x = rng.uniform(S * 0.5, N * S * 0.18)
        z = rng.uniform(-(N / 2 - 1) * S, (N / 2 - 1) * S)
        scale = rng.uniform(0.7, 1.1)
        positions.append((x, 0.1, z, scale, 'lowland'))

    # Pohon di lereng gunung (X tengah)
    for _ in range(10):
        x = rng.uniform(N * S * 0.10, N * S * 0.20)
        z = rng.uniform(-(N / 2 - 2) * S, (N / 2 - 2) * S)
        scale = rng.uniform(0.8, 1.3)
        positions.append((x, 0.1, z, scale, 'slope'))

    # Pohon besar di sekitar kaki gunung
    for _ in range(6):
        x = rng.uniform(N * S * 0.12, N * S * 0.25)
        z = rng.uniform(-S * 3, S * 3)
        scale = rng.uniform(1.0, 1.5)
        positions.append((x, 0.1, z, scale, 'mountain_base'))

    return positions


# Pra-komputasi posisi (hanya 1x saat modul di-import)
_TREE_POSITIONS = _generate_tree_positions()


# ================= GAMBAR SEMUA POHON =================
def draw_trees():
    """Gambar semua pohon di terrain darat."""
    glDisable(GL_LIGHTING)

    for (x, y, z, scale, tree_type) in _TREE_POSITIONS:
        if tree_type == 'lowland':
            _draw_round_tree(x, y, z, scale)
        elif tree_type == 'slope':
            _draw_pine_tree(x, y, z, scale)
        else:  # mountain_base
            _draw_round_tree(x, y, z, scale * 0.9)
            # Tambah pine kecil di sebelahnya
            _draw_pine_tree(x + scale * 0.8, y, z + scale * 0.5, scale * 0.7)


# ================= POHON BULAT (POHON TROPIS) =================
def _draw_round_tree(cx, base_y, cz, scale=1.0):
    """
    Pohon dengan mahkota bulat/oval — gaya low-poly.
    Seperti pohon hijau rimbun di gambar siklus air.
    """
    trunk_h   = 0.8  * scale
    trunk_r   = 0.10 * scale
    crown_r   = 0.75 * scale
    crown_y   = base_y + trunk_h + crown_r * 0.5

    # ─── BATANG (silinder low-poly 6 sisi) ───
    SIDES = 6
    glColor3f(0.38, 0.24, 0.12)   # Cokelat kayu
    glBegin(GL_QUAD_STRIP)
    for k in range(SIDES + 1):
        angle = 2 * math.pi * k / SIDES
        px = cx + trunk_r * math.cos(angle)
        pz = cz + trunk_r * math.sin(angle)
        glVertex3f(px, base_y,         pz)
        glVertex3f(px, base_y + trunk_h, pz)
    glEnd()

    # ─── MAHKOTA (sphere low-poly = icosahedron kasar) ───
    # Implementasi: stack × slices sederhana
    STACKS = 5
    SLICES = 7

    # Warna mahkota: lebih gelap di bawah, lebih terang di atas
    def crown_color(stack_idx):
        t = stack_idx / STACKS
        r = 0.15 + 0.10 * t
        g = 0.42 + 0.18 * t
        b = 0.12 + 0.05 * t
        return (r, g, b)

    for s in range(STACKS):
        phi0 = math.pi * s / STACKS - math.pi / 2
        phi1 = math.pi * (s + 1) / STACKS - math.pi / 2

        c0 = crown_color(s)
        c1 = crown_color(s + 1)

        glBegin(GL_QUADS)
        for sl in range(SLICES):
            theta0 = 2 * math.pi * sl / SLICES
            theta1 = 2 * math.pi * (sl + 1) / SLICES

            # 4 titik quad
            def pt(phi, theta):
                return (
                    cx + crown_r * math.cos(phi) * math.cos(theta),
                    crown_y + crown_r * math.sin(phi),
                    cz + crown_r * math.cos(phi) * math.sin(theta),
                )

            A = pt(phi0, theta0)
            B = pt(phi0, theta1)
            C = pt(phi1, theta1)
            D = pt(phi1, theta0)

            glColor3f(*c0)
            glVertex3f(*A)
            glVertex3f(*B)
            glColor3f(*c1)
            glVertex3f(*C)
            glVertex3f(*D)
        glEnd()


# ================= POHON PINUS (POHON LERENG) =================
def _draw_pine_tree(cx, base_y, cz, scale=1.0):
    """
    Pohon pinus / cemara dengan 3 lapis kerucut — gaya low-poly.
    Cocok untuk pohon di lereng dan sekitar gunung.
    """
    trunk_h = 0.6  * scale
    trunk_r = 0.08 * scale

    # ─── BATANG ───
    SIDES = 5
    glColor3f(0.32, 0.20, 0.10)
    glBegin(GL_QUAD_STRIP)
    for k in range(SIDES + 1):
        angle = 2 * math.pi * k / SIDES
        px = cx + trunk_r * math.cos(angle)
        pz = cz + trunk_r * math.sin(angle)
        glVertex3f(px, base_y,           pz)
        glVertex3f(px, base_y + trunk_h, pz)
    glEnd()

    # ─── 3 LAPIS KERUCUT (dari bawah ke atas, makin kecil) ───
    layers = [
        # (y_base, radius, height, color)
        (base_y + trunk_h * 0.5, 0.70 * scale, 1.00 * scale, (0.18, 0.42, 0.18)),
        (base_y + trunk_h * 0.5 + 0.55 * scale, 0.50 * scale, 0.80 * scale, (0.22, 0.50, 0.22)),
        (base_y + trunk_h * 0.5 + 1.05 * scale, 0.32 * scale, 0.65 * scale, (0.28, 0.58, 0.25)),
    ]

    CONE_SIDES = 7
    for (ly, lr, lh, lc) in layers:
        peak_y = ly + lh
        angles  = [2 * math.pi * k / CONE_SIDES for k in range(CONE_SIDES)]
        base_pts = [
            (cx + lr * math.cos(a), ly, cz + lr * math.sin(a))
            for a in angles
        ]

        glBegin(GL_TRIANGLES)
        for k in range(CONE_SIDES):
            nk = (k + 1) % CONE_SIDES
            bA = base_pts[k]
            bB = base_pts[nk]

            # Shading sederhana berdasarkan arah
            face_light = math.cos((angles[k] + angles[nk]) / 2 - math.pi * 0.3)
            shade = 0.75 + 0.25 * max(0, face_light)
            glColor3f(lc[0] * shade, lc[1] * shade, lc[2] * shade)

            glVertex3f(bA[0], bA[1], bA[2])
            glVertex3f(bB[0], bB[1], bB[2])
            glVertex3f(cx, peak_y, cz)
        glEnd()

        # Tutup bawah kerucut
        glColor3f(lc[0] * 0.6, lc[1] * 0.6, lc[2] * 0.6)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(cx, ly - 0.02, cz)
        for pt in base_pts:
            glVertex3f(pt[0], pt[1] - 0.02, pt[2])
        glVertex3f(base_pts[0][0], base_pts[0][1] - 0.02, base_pts[0][2])
        glEnd()


# ================= SEMAK-SEMAK KECIL =================
def draw_bushes():
    """
    Gambar semak-semak kecil sebagai variasi vegetasi.
    Ditempatkan di sela-sela pohon.
    """
    glDisable(GL_LIGHTING)

    rng = random.Random(99)
    N   = TERRAIN_SIZE
    S   = TERRAIN_SCALE

    for _ in range(15):
        x = rng.uniform(S * 0.3, N * S * 0.22)
        z = rng.uniform(-(N / 2 - 1) * S, (N / 2 - 1) * S)
        scale = rng.uniform(0.25, 0.50)

        # Semak = sphere kecil tanpa batang
        crown_r = 0.45 * scale
        crown_y = 0.1 + crown_r * 0.8

        STACKS = 3
        SLICES = 6

        for s in range(STACKS):
            phi0 = math.pi * s / STACKS - math.pi / 2
            phi1 = math.pi * (s + 1) / STACKS - math.pi / 2

            t0 = s / STACKS
            t1 = (s + 1) / STACKS
            c0 = (0.20 + 0.08 * t0, 0.45 + 0.12 * t0, 0.16 + 0.06 * t0)
            c1 = (0.20 + 0.08 * t1, 0.45 + 0.12 * t1, 0.16 + 0.06 * t1)

            glBegin(GL_QUADS)
            for sl in range(SLICES):
                theta0 = 2 * math.pi * sl / SLICES
                theta1 = 2 * math.pi * (sl + 1) / SLICES

                def pt(phi, theta):
                    return (
                        x + crown_r * math.cos(phi) * math.cos(theta),
                        crown_y + crown_r * math.sin(phi),
                        z + crown_r * math.cos(phi) * math.sin(theta),
                    )

                A = pt(phi0, theta0)
                B = pt(phi0, theta1)
                C = pt(phi1, theta1)
                D = pt(phi1, theta0)

                glColor3f(*c0)
                glVertex3f(*A)
                glVertex3f(*B)
                glColor3f(*c1)
                glVertex3f(*C)
                glVertex3f(*D)
            glEnd()