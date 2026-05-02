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


_cached_river_path = None

def get_world_y(x, z):
    """Fungsi global untuk mendapatkan elevasi daratan di titik (x, z), lengkap dengan bukit dan lembah."""
    global _cached_river_path
    if _cached_river_path is None:
        from river import get_river_path
        _cached_river_path = get_river_path()
        
    # 1. Base slope (kemiringan dasar menuju pantai)
    if x > 3.0:
        base_h = -1.45
    elif x > -6.0:
        t_linier = (3.0 - x) / 9.0
        t_smooth = (1.0 - math.cos(t_linier * math.pi)) / 2.0
        base_h = -1.5 + 1.6 * t_smooth
    else:
        base_h = 0.1
        
    # 2. Perbukitan (Hills) menggunakan gelombang sinus/kosinus
    hill1 = 1.8 * math.sin(x * 0.3) * math.sin(z * 0.3)
    hill2 = 1.0 * math.sin(x * 0.7 + 2.0) * math.cos(z * 0.5 - 1.0)
    hill_h = max(0.0, hill1 + hill2)
    
    # 3. Lembah Sungai (Ratakan bukit yang dekat dengan sungai)
    min_d2 = 999.0
    for rx, rz in _cached_river_path:
        d2 = (rx - x)**2 + (rz - z)**2
        if d2 < min_d2:
            min_d2 = d2
    d = math.sqrt(min_d2)
    
    valley_radius = 4.0
    if d < valley_radius:
        t_valley = d / valley_radius
        t_valley = t_valley * t_valley * (3.0 - 2.0 * t_valley) # Smooth S-Curve
        hill_h *= t_valley
        
    # 4. Hilangkan bukit di area depan (termasuk pasir dan padang rumput depan) agar rata
    if x > -9.0:
        hill_h = 0.0
    elif x > -12.0:
        t_taper = (-9.0 - x) / 3.0
        hill_h *= t_taper
        
    return base_h + hill_h


# ================= LAUT (BALOK AIR / AKUARIUM) =================
def draw_sea(time=0.0):
    """Menggambar laut di sisi kanan dengan animasi gelombang ombak di bibir pantai"""
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

    s_max_x = max_pos + eps

    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    WAVE_SEGMENTS = 40
    dz = (s_max_z - s_min_z) / WAVE_SEGMENTS
    
    # 1. LAUT DALAM (Cyan -> Biru Tua)
    glBegin(GL_QUAD_STRIP)
    for i in range(WAVE_SEGMENTS + 1):
        z_curr = s_min_z + i * dz
        wave_x = -4.2 + 0.6 * math.sin(time * 2.0 + z_curr * 1.2) + 0.3 * math.sin(time * 1.5 - z_curr * 0.8)
        
        x_cyan = wave_x + 0.5
        y_cyan = max(0.0, get_world_y(x_cyan, z_curr) + 0.02)
        
        glColor4f(0.15, 0.80, 0.90, 0.85) # Cyan terang
        glVertex3f(x_cyan, y_cyan, z_curr)
        
        glColor4f(0.05, 0.45, 0.85, 0.95) # Biru laut dalam
        glVertex3f(s_max_x, 0.0, z_curr)
    glEnd()

    # 2. BUIH OMBAK (Putih -> Cyan)
    glBegin(GL_QUAD_STRIP)
    for i in range(WAVE_SEGMENTS + 1):
        z_curr = s_min_z + i * dz
        wave_x = -4.2 + 0.6 * math.sin(time * 2.0 + z_curr * 1.2) + 0.3 * math.sin(time * 1.5 - z_curr * 0.8)
        
        x_foam = wave_x
        y_foam = get_world_y(x_foam, z_curr) + 0.04
        
        x_cyan = wave_x + 0.5
        y_cyan = max(0.0, get_world_y(x_cyan, z_curr) + 0.02)
        
        glColor4f(1.0, 1.0, 1.0, 0.9) # Buih putih
        glVertex3f(x_foam, y_foam, z_curr)
        
        glColor4f(0.15, 0.80, 0.90, 0.85) # Cyan terang
        glVertex3f(x_cyan, y_cyan, z_curr)
    glEnd()

    # 3. DINDING BALOK AIR
    glColor4f(0.05, 0.25, 0.65, 0.90)
    
    # Dinding Kanan, Depan, Belakang
    glBegin(GL_QUADS)
    
    # Dinding Kanan (X terluar)
    glVertex3f(s_max_x, 0.0,      s_max_z)
    glVertex3f(s_max_x, 0.0,      s_min_z)
    glVertex3f(s_max_x, s_base_y, s_min_z)
    glVertex3f(s_max_x, s_base_y, s_max_z)

    # Dinding Depan (Z terluar depan)
    wave_x_front = -4.2 + 0.6 * math.sin(time * 2.0 + s_max_z * 1.2) + 0.3 * math.sin(time * 1.5 - s_max_z * 0.8)
    glVertex3f(wave_x_front, get_world_y(wave_x_front, s_max_z)+0.04, s_max_z)
    glVertex3f(s_max_x,      0.0,      s_max_z)
    glVertex3f(s_max_x,      s_base_y, s_max_z)
    glVertex3f(wave_x_front, s_base_y, s_max_z)

    # Dinding Belakang (Z terluar belakang)
    wave_x_back = -4.2 + 0.6 * math.sin(time * 2.0 + s_min_z * 1.2) + 0.3 * math.sin(time * 1.5 - s_min_z * 0.8)
    glVertex3f(s_max_x,     0.0,      s_min_z)
    glVertex3f(wave_x_back, get_world_y(wave_x_back, s_min_z)+0.04, s_min_z)
    glVertex3f(wave_x_back, s_base_y, s_min_z)
    glVertex3f(s_max_x,     s_base_y, s_min_z)
    glEnd()

    glDisable(GL_BLEND)


class Terrain:

    def __init__(self):
        N = TERRAIN_SIZE
        S = TERRAIN_SCALE
        self.N = N

        rng = np.random.default_rng(seed=7)
        height = np.zeros((N, N), dtype=np.float32)
        
        for i in range(N):
            for j in range(N):
                x = (j - N / 2) * S
                z = (i - N / 2) * S
                
                noise_amp = 0.005 if x > -4.0 else 0.03
                height[i][j] = get_world_y(x, z) + rng.uniform(-noise_amp, noise_amp)

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
                z_world = (zA + zB + zC + zD) / 4.0

                # SEGITIGA 1
                y_avg1 = (yA + yC + yB) / 3.0       
                c1 = self._color(y_avg1, x_world, z_world)
                verts.extend([[xA, yA, zA], [xC, yC, zC], [xB, yB, zB]])
                colors.extend([c1, c1, c1])

                # SEGITIGA 2
                y_avg2 = (yB + yC + yD) / 3.0
                c2 = self._color(y_avg2, x_world, z_world)
                verts.extend([[xB, yB, zB], [xC, yC, zC], [xD, yD, zD]])
                colors.extend([c2, c2, c2])

        self.vertices = np.array(verts,  dtype=np.float32)
        self.colors   = np.array(colors, dtype=np.float32)

    # ================= WARNA =================
    @staticmethod
    def _color(y, x_world, z_world):
        """
        Warna terrain berdasarkan posisi:
        - Dekat pantai (x kecil): warna pasir / kuning
        - Dataran:                hijau terang
        - Agak jauh:              hijau sedang
        """
        N = TERRAIN_SIZE
        S = TERRAIN_SCALE
        
        boundary_offset = 1.2 * math.sin(z_world * 0.4) + 0.6 * math.sin(z_world * 0.9)
        sand_edge = -3.0 + boundary_offset
        grass_edge = -6.5 + boundary_offset

        if x_world > sand_edge:
            # Zona pantai / pasir / bawah laut (Keemasan cerah)
            return [0.96, 0.83, 0.45, 1.0]
        elif x_world > grass_edge:
            # Transisi pasir → rumput yang lebih halus (S-Curve)
            t_linier = (sand_edge - x_world) / (sand_edge - grass_edge)
            t_smooth = (1.0 - math.cos(t_linier * math.pi)) / 2.0
            
            r = 0.96 + (0.35 - 0.96) * t_smooth
            g = 0.83 + (0.58 - 0.83) * t_smooth
            b = 0.45 + (0.22 - 0.45) * t_smooth
            return [r, g, b, 1.0]
        else:
            # Zona darat: hijau (variasi sedikit berdasarkan y)
            shade = 0.88 + 0.12 * (y - 0.07) / 0.06
            shade = max(0.80, min(1.0, shade))
            return [0.35 * shade, 0.58 * shade, 0.22 * shade, 1.0]

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
            j = random.randint(int(N * 0.7), N - 1)
            x = (j - N / 2) * S
            z = (i - N / 2) * S
            y = 0.0
            positions.append((x, y, z))
            tries += 1
        return positions