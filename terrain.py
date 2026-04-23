# ============================================================
#  terrain.py — FINAL (Flat Ocean + Curved Coast + Mountain)
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

    # --- SOLUSI Z-FIGHTING (MICRO-OFFSET) ---
    eps = -0.0002  # Epsilon: geser 0.02 unit ke luar
    s_min_x = min_pos - eps
    s_min_z = min_pos - eps
    s_max_z = max_pos + eps
    s_base_y = base_y - eps
    # ----------------------------------------

    glDisable(GL_LIGHTING)

    # 1. PERMUKAAN ATAS AIR (Gunakan variabel 's_' yang sudah digeser)
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
    # Ini dibiarkan 0.0 karena posisinya tenggelam di "dalam" tanah
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

        height = np.zeros((N, N), dtype=np.float32)

        # ================= GUNUNG DI KANAN =================
        for i in range(N):
            for j in range(N):

                x = (j - N/2) / (N/2)
                z = (i - N/2) / (N/2)

                cx = 0.6
                cz = 0.0

                d = math.sqrt((x - cx)**2 + (z - cz)**2)

                mountain = max(0.0, 1.0 - d * 1.3)
                mountain = mountain ** 1.8 * 4.0

                hill = math.sin(3*x) * math.sin(3*z) * 0.3

                height[i][j] = mountain + hill

        # ================= SMOOTH PANTAI =================
        for i in range(N):
            for j in range(N):

                x = (j - N/2) / (N/2)
                z = (i - N/2) / (N/2)

                cx = 0.6
                cz = 0.0

                d = math.sqrt((x - cx)**2 + (z - cz)**2)

                if 0.5 < d < 0.6:
                    height[i][j] *= 0.85

        # ================= NOISE =================
        rng = np.random.default_rng(seed=7)
        height += rng.uniform(-0.08, 0.08, (N, N))

        self.height = height

        # ================= BUILD MESH =================
        verts  = []
        colors = []

        for i in range(N):
            for j in range(N):

                x = (j - N / 2) * S
                y = float(height[i][j])
                z = (i - N / 2) * S

                verts.append([x, y, z])
                colors.append(self._color(y))

        idxs = []
        for i in range(N - 1):
            for j in range(N - 1):
                a = i * N + j
                idxs += [a, a + 1, a + N,
                         a + 1, a + N + 1, a + N]

        self.vertices = np.array(verts,  dtype=np.float32)
        self.colors   = np.array(colors, dtype=np.float32)
        self.indices  = np.array(idxs,   dtype=np.uint32)

    # ================= WARNA =================
    @staticmethod
    def _color(y):

        if y < 0.0:
            return [0.85, 0.75, 0.50, 1.0]  # pantai (tidak ada laut di sini lagi)
        elif y < 1.5:
            return [0.45, 0.85, 0.35, 1.0]
        elif y < 3.0:
            return [0.25, 0.60, 0.20, 1.0]
        elif y < 4.5:
            return [0.50, 0.45, 0.40, 1.0]
        else:
            return [0.95, 0.95, 1.00, 1.0]

    # ================= DRAW =================
    def draw(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glColorPointer(4, GL_FLOAT, 0, self.colors)

        glDrawElements(GL_TRIANGLES, len(self.indices),
                       GL_UNSIGNED_INT, self.indices)

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        self.draw_base()

    # ================= FONDASI & DINDING (SKIRTING) =================
    def draw_base(self):
        N = self.N
        S = TERRAIN_SCALE
        base_y = -3.0  # Kedalaman fondasi pulau
        
        # Hitung batas koordinat X dan Z paling ujung
        min_pos = (0 - N / 2) * S
        max_pos = (N - 1 - N / 2) * S
        
        glDisable(GL_LIGHTING)

        # 1. GAMBAR LANTAI DASAR (WARNA ABU-ABU GELAP)
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(min_pos, base_y, max_pos)
        glVertex3f(max_pos, base_y, max_pos)
        glVertex3f(max_pos, base_y, min_pos)
        glVertex3f(min_pos, base_y, min_pos)
        glEnd()

        # 2. GAMBAR DINDING / TEBING TANAH (WARNA COKELAT)
        glColor3f(0.35, 0.25, 0.15) 
        glBegin(GL_QUADS)

        # Sisi Belakang (Z = min_pos)
        for j in range(N - 1):
            x1 = (j - N / 2) * S
            x2 = (j + 1 - N / 2) * S
            z = min_pos
            y1 = float(self.height[0][j])
            y2 = float(self.height[0][j+1])
            glVertex3f(x1, base_y, z)
            glVertex3f(x2, base_y, z)
            glVertex3f(x2, y2, z)
            glVertex3f(x1, y1, z)

        # Sisi Depan (Z = max_pos)
        for j in range(N - 1):
            x1 = (j - N / 2) * S
            x2 = (j + 1 - N / 2) * S
            z = max_pos
            y1 = float(self.height[N-1][j])
            y2 = float(self.height[N-1][j+1])
            glVertex3f(x1, y1, z)
            glVertex3f(x2, y2, z)
            glVertex3f(x2, base_y, z)
            glVertex3f(x1, base_y, z)

        # Sisi Kiri (X = min_pos)
        for i in range(N - 1):
            z1 = (i - N / 2) * S
            z2 = (i + 1 - N / 2) * S
            x = min_pos
            y1 = float(self.height[i][0])
            y2 = float(self.height[i+1][0])
            glVertex3f(x, y1, z1)
            glVertex3f(x, base_y, z1)
            glVertex3f(x, base_y, z2)
            glVertex3f(x, y2, z2)

        # Sisi Kanan (X = max_pos)
        for i in range(N - 1):
            z1 = (i - N / 2) * S
            z2 = (i + 1 - N / 2) * S
            x = max_pos
            y1 = float(self.height[i][N-1])
            y2 = float(self.height[i+1][N-1])
            glVertex3f(x, base_y, z1)
            glVertex3f(x, y1, z1)
            glVertex3f(x, y2, z2)
            glVertex3f(x, base_y, z2)

        glEnd()

    # ================= SPAWN UAP =================
    def get_sea_spawn_positions(self, n=10):
        # ambil posisi dekat laut (x kiri)
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