# ============================================================
#  terrain.py — Terrain datar hijau + laut biru
#  Update: terrain darat berwarna hijau (bukan pasir)
#          agar cocok dengan gambar siklus air
# ============================================================

import math
import random
import numpy as np
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


# ================= LAUT (BALOK AIR / AKUARIUM) =================
def draw_sea():
    N = TERRAIN_SIZE
    S = TERRAIN_SCALE
    base_y = -3.0  
    
    min_pos = (0 - N / 2) * S
    max_pos = (N - 1 - N / 2) * S

    eps = -0.0002
    s_min_x = min_pos - eps
    s_min_z = min_pos - eps
    s_max_z = max_pos + eps
    s_base_y = base_y - eps

    glDisable(GL_LIGHTING)

    # 1. PERMUKAAN ATAS AIR
    glColor3f(0.1, 0.4, 0.85)
    glBegin(GL_QUADS)
    glVertex3f(s_min_x, 0.0, s_min_z) 
    glVertex3f(0.0,     0.0, s_min_z) 
    glVertex3f(0.0,     0.0, s_max_z) 
    glVertex3f(s_min_x, 0.0, s_max_z) 
    glEnd()

    # 2. DINDING BALOK AIR
    glColor3f(0.05, 0.25, 0.65)
    glBegin(GL_QUADS)
    
    # Dinding Kiri (X terluar)
    glVertex3f(s_min_x, 0.0,      s_min_z)
    glVertex3f(s_min_x, 0.0,      s_max_z)
    glVertex3f(s_min_x, s_base_y, s_max_z)
    glVertex3f(s_min_x, s_base_y, s_min_z)

    # Dinding Depan (Z terluar depan)
    glVertex3f(s_min_x, 0.0,      s_max_z)
    glVertex3f(0.0,     0.0,      s_max_z)
    glVertex3f(0.0,     s_base_y, s_max_z)
    glVertex3f(s_min_x, s_base_y, s_max_z)

    # Dinding Belakang (Z terluar belakang)
    glVertex3f(s_min_x, 0.0,      s_min_z)
    glVertex3f(s_min_x, s_base_y, s_min_z)
    glVertex3f(0.0,     s_base_y, s_min_z)
    glVertex3f(0.0,     0.0,      s_min_z)

    # Dinding Kanan (Batas tengah dengan tanah)
    glVertex3f(0.0, 0.0,      s_max_z)
    glVertex3f(0.0, 0.0,      s_min_z)
    glVertex3f(0.0, s_base_y, s_min_z)
    glVertex3f(0.0, s_base_y, s_max_z)
    
    glEnd()


class Terrain:

    def __init__(self):
        N = TERRAIN_SIZE
        S = TERRAIN_SCALE
        self.N = N

        # Terrain darat: datar di y=0.1, sedikit noise agar natural
        height = np.full((N, N), 0.1, dtype=np.float32)

        rng = np.random.default_rng(seed=7)
        # Noise lebih kecil agar tetap flat (tapi tidak rata seperti lantai)
        height += rng.uniform(-0.03, 0.04, (N, N))

        self.height = height

        # ================= BUILD MESH =================
        verts  = []
        colors = []

        for i in range(N - 1):
            for j in range(N - 1):
                xA = (j     - N / 2) * S;  zA = (i     - N / 2) * S;  yA = float(height[i  ][j  ])
                xB = (j + 1 - N / 2) * S;  zB = (i     - N / 2) * S;  yB = float(height[i  ][j+1])
                xC = (j     - N / 2) * S;  zC = (i + 1 - N / 2) * S;  yC = float(height[i+1][j  ])
                xD = (j + 1 - N / 2) * S;  zD = (i + 1 - N / 2) * S;  yD = float(height[i+1][j+1])

                # x world dari titik ini (rata-rata)
                x_world = (xA + xB + xC + xD) / 4.0

                # SEGITIGA 1
                y_avg1 = (yA + yC + yB) / 3.0       
                c1 = self._color(y_avg1, x_world)
                verts.extend([[xA, yA, zA], [xC, yC, zC], [xB, yB, zB]])
                colors.extend([c1, c1, c1])

                # SEGITIGA 2
                y_avg2 = (yB + yC + yD) / 3.0
                c2 = self._color(y_avg2, x_world)
                verts.extend([[xB, yB, zB], [xC, yC, zC], [xD, yD, zD]])
                colors.extend([c2, c2, c2])

        self.vertices = np.array(verts,  dtype=np.float32)
        self.colors   = np.array(colors, dtype=np.float32)

    # ================= WARNA =================
    @staticmethod
    def _color(y, x_world):
        """
        Warna terrain berdasarkan posisi:
        - Dekat pantai (x kecil): warna pasir / kuning
        - Dataran:                hijau terang
        - Agak jauh:              hijau sedang
        """
        N = TERRAIN_SIZE
        S = TERRAIN_SCALE

        # x_world: 0 = pantai, (N/2)*S = tepi kanan
        x_frac = x_world / ((N / 2) * S)  # 0..1

        if x_frac < 0.08:
            # Zona pantai / pasir
            return [0.85, 0.78, 0.52, 1.0]
        elif x_frac < 0.18:
            # Transisi pasir → rumput
            t = (x_frac - 0.08) / 0.10
            r = 0.85 + (0.45 - 0.85) * t
            g = 0.78 + (0.65 - 0.78) * t
            b = 0.52 + (0.25 - 0.52) * t
            return [r, g, b, 1.0]
        else:
            # Zona darat: hijau (variasi sedikit berdasarkan y)
            shade = 0.88 + 0.12 * (y - 0.07) / 0.06
            shade = max(0.80, min(1.0, shade))
            return [0.28 * shade, 0.58 * shade, 0.22 * shade, 1.0]

    # ================= DRAW =================
    def draw(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glColorPointer(4, GL_FLOAT, 0, self.colors)

        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices))

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        self.draw_base()

    # ================= FONDASI & DINDING (SKIRTING) =================
    def draw_base(self):
        N = self.N
        S = TERRAIN_SCALE
        base_y = -3.0
        
        min_pos = (0 - N / 2) * S
        max_pos = (N - 1 - N / 2) * S
        
        glDisable(GL_LIGHTING)

        # Lantai dasar
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(min_pos, base_y, max_pos)
        glVertex3f(max_pos, base_y, max_pos)
        glVertex3f(max_pos, base_y, min_pos)
        glVertex3f(min_pos, base_y, min_pos)
        glEnd()

        # Dinding / tebing tanah (cokelat)
        glColor3f(0.35, 0.25, 0.15) 
        glBegin(GL_QUADS)

        for j in range(N - 1):
            x1 = (j - N / 2) * S
            x2 = (j + 1 - N / 2) * S
            z  = min_pos
            y1 = float(self.height[0][j])
            y2 = float(self.height[0][j+1])
            glVertex3f(x1, base_y, z); glVertex3f(x2, base_y, z)
            glVertex3f(x2, y2,     z); glVertex3f(x1, y1,     z)

        for j in range(N - 1):
            x1 = (j - N / 2) * S
            x2 = (j + 1 - N / 2) * S
            z  = max_pos
            y1 = float(self.height[N-1][j])
            y2 = float(self.height[N-1][j+1])
            glVertex3f(x1, y1, z); glVertex3f(x2, y2,     z)
            glVertex3f(x2, base_y, z); glVertex3f(x1, base_y, z)

        for i in range(N - 1):
            z1 = (i - N / 2) * S
            z2 = (i + 1 - N / 2) * S
            x  = min_pos
            y1 = float(self.height[i][0])
            y2 = float(self.height[i+1][0])
            glVertex3f(x, y1, z1); glVertex3f(x, base_y, z1)
            glVertex3f(x, base_y, z2); glVertex3f(x, y2, z2)

        for i in range(N - 1):
            z1 = (i - N / 2) * S
            z2 = (i + 1 - N / 2) * S
            x  = max_pos
            y1 = float(self.height[i][N-1])
            y2 = float(self.height[i+1][N-1])
            glVertex3f(x, base_y, z1); glVertex3f(x, y1,     z1)
            glVertex3f(x, y2,     z2); glVertex3f(x, base_y, z2)

        glEnd()

    # ================= SPAWN UAP =================
    def get_sea_spawn_positions(self, n=10):
        N  = self.N
        S  = TERRAIN_SCALE
        positions = []
        tries = 0
        while len(positions) < n and tries < 600:
            i = random.randint(0, N - 1)
            j = random.randint(0, int(N * 0.3))
            x = (j - N / 2) * S
            z = (i - N / 2) * S
            y = 0.0
            positions.append((x, y, z))
            tries += 1
        return positions