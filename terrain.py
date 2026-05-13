import math
import random
import numpy as np
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE, SEA_LIMIT, TERRAIN_OFFSET_X


# ================= RIVER PATH CACHE =================
_cached_river_path    = None
_cached_river_arr     = None   # (M, 2) float32 — untuk operasi NumPy

def _ensure_river_cache():
    global _cached_river_path, _cached_river_arr
    if _cached_river_path is None:
        from river import get_river_path
        _cached_river_path = get_river_path()
        _cached_river_arr  = np.array(_cached_river_path, dtype=np.float32)


# ================= get_world_y (scalar — dipakai river.py, trees.py, dll.) =================
def get_world_y(x, z):
    """Elevasi daratan di titik (x, z). API scalar tetap tersedia."""
    _ensure_river_cache()
    # x = x - TERRAIN_OFFSET_X

    # 1. Base slope
    if x > 3.0:
        base_h = -1.45
    elif x > -6.0:
        t_lin  = (3.0 - x) / 9.0
        base_h = -1.5 + 1.6 * (1.0 - math.cos(t_lin * math.pi)) / 2.0
    else:
        base_h = 0.1

    # 2. Bukit
    hill1 = 1.8 * math.sin(x * 0.3) * math.sin(z * 0.3)
    hill2 = 1.0 * math.sin(x * 0.7 + 2.0) * math.cos(z * 0.5 - 1.0)
    hill_h = max(0.0, hill1 + hill2)
    
    # Buat bukit yang di sebelah kanan (mendekati area tengah/sungai) jadi jauh lebih tinggi
    # X berjalan dari -15 (kiri jauh) ke 0 (tengah). Semakin besar X, bukit makin tinggi.
    right_boost = 1.0 + max(0.0, (x + 15.0) / 8.0) * 2.2
    hill_h *= right_boost
    
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
        
    # 4. Hilangkan bukit di area depan (termasuk pasir) agar rata, tapi biarkan bukit kanan tetap menjulang
    if x > -5.0:
        hill_h = 0.0
    elif x > -10.0:
        t_taper = (-5.0 - x) / 5.0
        hill_h *= t_taper
        
    # 5. Taper ujung dunia (pinggiran luar kotak) agar bukit tidak terpotong tebing lurus
    # Ujung kiri (X mendekati -15)
    if x < -12.0:
        t_edge_x = max(0.0, min(1.0, (x - (-15.0)) / 3.0)) # 0 di ujung -15, 1 di -12
        hill_h *= t_edge_x
        
    # Ujung depan/belakang (Z mendekati -15 dan +15)
    abs_z = abs(z)
    if abs_z > 12.0:
        t_edge_z = max(0.0, min(1.0, (15.0 - abs_z) / 3.0)) # 0 di ujung 15, 1 di 12
        hill_h *= t_edge_z
        
    return base_h + hill_h


# ================= get_world_y VECTORIZED (internal) =================
def _get_world_y_grid(X, Z):
    """
    Hitung elevasi untuk seluruh grid sekaligus.
    X, Z : 2-D ndarray shape (N, N), dtype float32.
    Return : Y shape (N, N), float32.
    """
    _ensure_river_cache()
    ra = _cached_river_arr   # (M, 2)

    # 1. Base slope — vectorized dengan np.where
    base_h = np.where(
        X > 3.0,
        -1.45,
        np.where(
            X > -6.0,
            -1.5 + 1.6 * (1.0 - np.cos((3.0 - X) / 9.0 * math.pi)) / 2.0,
            0.1,
        )
    ).astype(np.float32)

    # 2. Bukit
    hill1  = 1.8 * np.sin(X * 0.3) * np.sin(Z * 0.3)
    hill2  = 1.0 * np.sin(X * 0.7 + 2.0) * np.cos(Z * 0.5 - 1.0)
    hill_h = np.maximum(0.0, hill1 + hill2).astype(np.float32)

    # 3. Lembah sungai — jarak minimum ke semua titik river sekaligus
    #    Broadcast: (N, N, 1) vs (M,) → min over axis M
    rx = ra[:, 0]   # (M,)
    rz = ra[:, 1]   # (M,)
    # Hitung jarak kuadrat: shape (N, N, M) — bisa besar, pakai loop tipis per chunk
    # Untuk N=120, M~30 → 120*120*30 float = ~1.7 MB, aman.
    dx   = X[:, :, None] - rx[None, None, :]   # (N,N,M)
    dz_  = Z[:, :, None] - rz[None, None, :]
    d    = np.sqrt(np.min(dx*dx + dz_*dz_, axis=2))   # (N,N)

    valley_radius = 4.0
    tv = d / valley_radius
    tv = np.clip(tv, 0.0, 1.0)
    tv = tv * tv * (3.0 - 2.0 * tv)          # smoothstep
    # Hanya terapkan di dalam radius
    hill_h = np.where(d < valley_radius, hill_h * tv, hill_h)

    # 4. Taper area depan
    hill_h = np.where(X > -9.0, 0.0, hill_h)
    taper  = np.clip((-9.0 - X) / 3.0, 0.0, 1.0)
    hill_h = np.where((X > -12.0) & (X <= -9.0), hill_h * taper, hill_h)

    return (base_h + hill_h).astype(np.float32)


# ================= LAUT =================
# Pre-compute Z coords for wave segments (constant)
_WAVE_SEGMENTS = 40
_SEA_Z_COORDS  = None   # computed once on first draw_sea() call

def draw_sea(time=0.0):
    """Laut animasi — wave X di-compute tiap frame (wajib), tapi Z statis."""
    global _SEA_Z_COORDS
    _ensure_river_cache()

    N = TERRAIN_SIZE
    S = TERRAIN_SCALE
    base_y  = -3.0
    min_pos = (0 - N / 2) * S
    max_pos = (N - 1 - N / 2) * S

    if _SEA_Z_COORDS is None:
        _SEA_Z_COORDS = np.linspace(min_pos, max_pos, _WAVE_SEGMENTS + 1, dtype=np.float32)

    zc = _SEA_Z_COORDS
    # Animasi gelombang — vectorized
    sea_border_x = (SEA_LIMIT * N - N / 2) * S 
    wave_x = (-4.2
                + 0.15 * np.sin(time * 2.0 + zc * 1.2)
                + 0.075 * np.sin(time * 1.5 - zc * 0.8)).astype(np.float32)

    # Elevasi terrain di sepanjang bibir pantai (vectorized)
    x_cyan  = wave_x + 0.5
    # get_world_y per-element — pakai vectorized versi 1-D
    ra      = _cached_river_arr
    def _y_strip(xs, zs):
        """Hitung elevasi untuk array 1-D xs, zs."""
        base_h = np.where(
            xs > 3.0, -1.45,
            np.where(xs > -6.0,
                     -1.5 + 1.6 * (1.0 - np.cos((3.0 - xs) / 9.0 * math.pi)) / 2.0,
                     0.1)
        ).astype(np.float32)
        hill1  = 1.8 * np.sin(xs * 0.3) * np.sin(zs * 0.3)
        hill2  = 1.0 * np.sin(xs * 0.7 + 2.0) * np.cos(zs * 0.5 - 1.0)
        hill_h = np.maximum(0.0, hill1 + hill2).astype(np.float32)
        dx = xs[:, None] - ra[:, 0][None, :]
        dz = zs[:, None] - ra[:, 1][None, :]
        d  = np.sqrt(np.min(dx*dx + dz*dz, axis=1))
        tv = np.clip(d / 4.0, 0.0, 1.0)
        tv = tv * tv * (3.0 - 2.0 * tv)
        hill_h = np.where(d < 4.0, hill_h * tv, hill_h)
        hill_h = np.where(xs > -9.0, 0.0, hill_h)
        taper  = np.clip((-9.0 - xs) / 3.0, 0.0, 1.0)
        hill_h = np.where((xs > -12.0) & (xs <= -9.0), hill_h * taper, hill_h)
        return base_h + hill_h

    y_foam  = np.full_like(zc, 0.05)
    y_cyan  = np.full_like(zc, 0.0)

    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(0.125, 0.125)
    
    # 1. LAUT DALAM
    glBegin(GL_QUAD_STRIP)
    for i in range(_WAVE_SEGMENTS + 1):
        glColor4f(0.15, 0.80, 0.90, 0.85)
        glVertex3f(float(x_cyan[i]), float(y_cyan[i]), float(zc[i]))
        glColor4f(0.05, 0.45, 0.85, 0.95)
        glVertex3f(max_pos, 0.0, float(zc[i]))
    glEnd()

    # 2. BUIH OMBAK
    glBegin(GL_QUAD_STRIP)
    for i in range(_WAVE_SEGMENTS + 1):
        glColor4f(1.0, 1.0, 1.0, 0.9)
        glVertex3f(float(wave_x[i]), float(y_foam[i]), float(zc[i]))
        glColor4f(0.15, 0.80, 0.90, 0.85)
        glVertex3f(float(x_cyan[i]), float(y_cyan[i]), float(zc[i]))
    glEnd()

    # 3. DINDING BALOK AIR
    glColor4f(0.05, 0.25, 0.65, 0.90)
    wf = float(wave_x[-1]); wb = float(wave_x[0])
    yf = float(y_foam[-1]);  yb = float(y_foam[0])

    glBegin(GL_QUADS)
    # Kanan
    glVertex3f(max_pos, 0.0,    max_pos); glVertex3f(max_pos, 0.0,    min_pos)
    glVertex3f(max_pos, base_y, min_pos); glVertex3f(max_pos, base_y, max_pos)
    # Depan
    glVertex3f(wf, yf, max_pos); glVertex3f(max_pos, 0.0,    max_pos)
    glVertex3f(max_pos, base_y, max_pos); glVertex3f(wf, base_y, max_pos)
    # Belakang
    glVertex3f(max_pos, 0.0,    min_pos); glVertex3f(wb, yb, min_pos)
    glVertex3f(wb, base_y, min_pos);      glVertex3f(max_pos, base_y, min_pos)
    glEnd()

    glDisable(GL_POLYGON_OFFSET_FILL)
    glDisable(GL_BLEND)


# ================= TERRAIN CLASS =================
class Terrain:

    def __init__(self):
        N = TERRAIN_SIZE
        S = TERRAIN_SCALE
        self.N = N

        # ── Buat grid koordinat dunia sekaligus ──
        j_idx = np.arange(N, dtype=np.float32)
        i_idx = np.arange(N, dtype=np.float32)
        J, I  = np.meshgrid(j_idx, i_idx)          # (N, N)
        X_grid = (J - N / 2) * S                   # world X
        Z_grid = (I - N / 2) * S                   # world Z

        # ── Elevasi seluruh grid sekaligus (vectorized) ──
        rng    = np.random.default_rng(seed=7)
        noise  = np.where(X_grid > -4.0,
                          rng.uniform(-0.005, 0.005, (N, N)),
                          rng.uniform(-0.03,  0.03,  (N, N))).astype(np.float32)
        height = _get_world_y_grid(X_grid, Z_grid) + noise
        self.height = height

        # ── Koordinat 4 sudut tiap quad (vectorized) ──
        # A=top-left B=top-right C=bot-left D=bot-right  (i,j index)
        xA = X_grid[:N-1, :N-1]; zA = Z_grid[:N-1, :N-1]; yA = height[:N-1, :N-1]
        xB = X_grid[:N-1, 1:N ]; zB = Z_grid[:N-1, 1:N ]; yB = height[:N-1, 1:N ]
        xC = X_grid[1:N,  :N-1]; zC = Z_grid[1:N,  :N-1]; yC = height[1:N,  :N-1]
        xD = X_grid[1:N,  1:N ]; zD = Z_grid[1:N,  1:N ]; yD = height[1:N,  1:N ]

        # World center X/Z untuk pewarnaan
        xW = (xA + xB + xC + xD) / 4.0
        zW = (zA + zB + zC + zD) / 4.0

        # ── Warna per quad (vectorized) ──
        boundary_offset = 1.2 * np.sin(zW * 0.4) + 0.6 * np.sin(zW * 0.9)
        sand_edge  = -3.0 + boundary_offset
        grass_edge = -6.5 + boundary_offset

        # Zona pasir
        is_sand  = xW > sand_edge
        # Zona transisi
        is_trans = (~is_sand) & (xW > grass_edge)
        # Zona hijau (sisanya)

        t_lin    = np.clip((sand_edge - xW) / np.maximum(sand_edge - grass_edge, 1e-6), 0.0, 1.0)
        t_smooth = (1.0 - np.cos(t_lin * math.pi)) / 2.0

        # Rata-rata Y untuk shading hijau
        y_avg1 = (yA + yC + yB) / 3.0
        y_avg2 = (yB + yC + yD) / 3.0
        shade1 = np.clip(0.88 + 0.12 * (y_avg1 - 0.07) / 0.06, 0.80, 1.0)
        shade2 = np.clip(0.88 + 0.12 * (y_avg2 - 0.07) / 0.06, 0.80, 1.0)

        def _make_color_arr(shade, is_s, is_t, t_sm):
            r = np.where(is_s, 0.96,
                np.where(is_t, 0.96 + (0.35 - 0.96) * t_sm, 0.35 * shade))
            g = np.where(is_s, 0.83,
                np.where(is_t, 0.83 + (0.58 - 0.83) * t_sm, 0.58 * shade))
            b = np.where(is_s, 0.45,
                np.where(is_t, 0.45 + (0.22 - 0.45) * t_sm, 0.22 * shade))
            a = np.ones_like(r)
            return np.stack([r, g, b, a], axis=-1).astype(np.float32)

        c1 = _make_color_arr(shade1, is_sand, is_trans, t_smooth)   # (N-1,N-1,4)
        c2 = _make_color_arr(shade2, is_sand, is_trans, t_smooth)

        # ── Susun vertex & color arrays untuk GL_TRIANGLES ──
        # Tiap quad → 2 segitiga × 3 vertex = 6 vertex
        M = (N - 1) * (N - 1)

        # Segitiga 1: A, C, B
        t1_v = np.stack([
            np.stack([xA, yA, zA], axis=-1),
            np.stack([xC, yC, zC], axis=-1),
            np.stack([xB, yB, zB], axis=-1),
        ], axis=2)                                   # (N-1,N-1,3,3)

        # Segitiga 2: B, C, D
        t2_v = np.stack([
            np.stack([xB, yB, zB], axis=-1),
            np.stack([xC, yC, zC], axis=-1),
            np.stack([xD, yD, zD], axis=-1),
        ], axis=2)

        # Interleave: [t1_v0, t1_v1, t1_v2, t2_v0, t2_v1, t2_v2] per quad
        all_v = np.concatenate([t1_v, t2_v], axis=2)  # (N-1,N-1,6,3)
        self.vertices = all_v.reshape(-1, 3).astype(np.float32)

        # Warna: tiap segitiga pakai warna seragam → repeat c1/c2 ×3 vertex
        c1_rep = np.repeat(c1[:, :, None, :], 3, axis=2)   # (N-1,N-1,3,4)
        c2_rep = np.repeat(c2[:, :, None, :], 3, axis=2)
        all_c  = np.concatenate([c1_rep, c2_rep], axis=2)  # (N-1,N-1,6,4)
        self.colors = all_c.reshape(-1, 4).astype(np.float32)

        # ── Bake dinding/fondasi ke Display List ──
        self._base_list = self._build_base_list()

    # ================= DRAW =================
    def draw(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glColorPointer(4,  GL_FLOAT, 0, self.colors)
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices))
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        glCallList(self._base_list)

    # ================= FONDASI & DINDING (baked) =================
    def _build_base_list(self):
        N      = self.N
        S      = TERRAIN_SCALE
        base_y = -3.0
        min_pos = (0 - N / 2) * S
        max_pos = (N - 1 - N / 2) * S
        height  = self.height

        dl = glGenLists(1)
        glNewList(dl, GL_COMPILE)
        glDisable(GL_LIGHTING)

        # Lantai dasar
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(min_pos, base_y, max_pos); glVertex3f(max_pos, base_y, max_pos)
        glVertex3f(max_pos, base_y, min_pos); glVertex3f(min_pos, base_y, min_pos)
        glEnd()

        # Dinding tebing
        glColor3f(0.35, 0.25, 0.15)
        glBegin(GL_QUADS)
        # Depan (z = min_pos)
        for j in range(N - 1):
            x1 = (j     - N / 2) * S;  x2 = (j + 1 - N / 2) * S
            y1 = float(height[0][j]);   y2 = float(height[0][j+1])
            glVertex3f(x1, base_y, min_pos); glVertex3f(x2, base_y, min_pos)
            glVertex3f(x2, y2,     min_pos); glVertex3f(x1, y1,     min_pos)
        # Belakang (z = max_pos)
        for j in range(N - 1):
            x1 = (j     - N / 2) * S;  x2 = (j + 1 - N / 2) * S
            y1 = float(height[N-1][j]); y2 = float(height[N-1][j+1])
            glVertex3f(x1, y1, max_pos); glVertex3f(x2, y2,     max_pos)
            glVertex3f(x2, base_y, max_pos); glVertex3f(x1, base_y, max_pos)
        # Kiri (x = min_pos)
        for i in range(N - 1):
            z1 = (i     - N / 2) * S;  z2 = (i + 1 - N / 2) * S
            y1 = float(height[i][0]);   y2 = float(height[i+1][0])
            glVertex3f(min_pos, y1, z1); glVertex3f(min_pos, base_y, z1)
            glVertex3f(min_pos, base_y, z2); glVertex3f(min_pos, y2, z2)
        # Kanan (x = max_pos)
        for i in range(N - 1):
            z1 = (i     - N / 2) * S;  z2 = (i + 1 - N / 2) * S
            y1 = float(height[i][N-1]); y2 = float(height[i+1][N-1])
            glVertex3f(max_pos, base_y, z1); glVertex3f(max_pos, y1,     z1)
            glVertex3f(max_pos, y2,     z2); glVertex3f(max_pos, base_y, z2)
        glEnd()

        glEndList()
        return dl

    # ================= SPAWN UAP =================
    def get_sea_spawn_positions(self, n=10):
        N = self.N
        S = TERRAIN_SCALE
        positions = []
        tries = 0
        while len(positions) < n and tries < 600:
            i = random.randint(0, N - 1)
            j = random.randint(int(N * 0.7), N - 1)
            x = (j - N / 2) * S
            z = (i - N / 2) * S
            positions.append((x, 0.0, z))
            tries += 1
        return positions