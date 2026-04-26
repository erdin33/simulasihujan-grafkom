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

        # Bikin daratan datar di ketinggian sedikit di atas air (biar tidak tenggelam)
        # Ketinggian air laut kita ada di 0.0, jadi kita taruh pasir di 0.1
        height = np.full((N, N), 0.1, dtype=np.float32)

        # ================= NOISE (TEKSTUR PASIR) =================
        # Kita beri sedikit gelombang agar tidak terlalu rata seperti lantai
        rng = np.random.default_rng(seed=7)
        height += rng.uniform(-0.05, 0.05, (N, N))

        self.height = height

        # ================= BUILD MESH (LOW POLY STYLE) =================
        verts  = []
        colors = []

        for i in range(N - 1):
            for j in range(N - 1):
                xA, zA, yA = (j - N/2)*S,     (i - N/2)*S,     float(height[i][j])
                xB, zB, yB = (j + 1 - N/2)*S, (i - N/2)*S,     float(height[i][j+1])
                xC, zC, yC = (j - N/2)*S,     (i + 1 - N/2)*S, float(height[i+1][j])
                xD, zD, yD = (j + 1 - N/2)*S, (i + 1 - N/2)*S, float(height[i+1][j+1])

                # SEGITIGA 1
                y_avg1 = (yA + yC + yB) / 3.0       
                c1 = self._color(y_avg1)
                
                verts.extend([[xA, yA, zA], [xC, yC, zC], [xB, yB, zB]])
                colors.extend([c1, c1, c1])         

                # SEGITIGA 2
                y_avg2 = (yB + yC + yD) / 3.0
                c2 = self._color(y_avg2)
                
                verts.extend([[xB, yB, zB], [xC, yC, zC], [xD, yD, zD]])
                colors.extend([c2, c2, c2])

        self.vertices = np.array(verts,  dtype=np.float32)
        self.colors   = np.array(colors, dtype=np.float32)

    # ================= WARNA =================
    @staticmethod
    def _color(y):
        # Karena kita ingin semuanya pasir, abaikan Y dan selalu return warna pasir
        return [0.85, 0.75, 0.50, 1.0]  # Warna Pasir

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
        
    # (Biarkan draw_base dan get_sea_spawn_positions di bawah ini tetap seperti aslinya)
        
    # ================= FONDASI & SPAWN UAP ... (biarkan sisanya utuh) =================

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