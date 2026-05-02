# ============================================================
#  sky_clouds.py — Langit gradient + Awan Low-Poly 3D (FIXED)
# ============================================================

import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *

from config import SKY_BOTTOM, SKY_TOP, CLOUD_HEIGHT


# ================================================================
#  HELPER
# ================================================================

def _normalize(v):
    mag = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if mag < 1e-9:
        return (0.0, 1.0, 0.0)
    return (v[0]/mag, v[1]/mag, v[2]/mag)


def _face_normal(v0, v1, v2):
    ax, ay, az = v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]
    bx, by, bz = v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]
    return _normalize((
        ay*bz - az*by,
        az*bx - ax*bz,
        ax*by - ay*bx,
    ))


# ================================================================
#  CLOUD MESH BUILDER
#
#  Strategi baru:
#  - Buat "blob" dari beberapa sphere low-poly yang overlapping
#    (seperti di gambar referensi: gumpalan-gumpalan bulat)
#  - Setiap sphere disubdivisi jadi icosphere sederhana
#  - Hasilnya solid, volumetrik, tidak gepeng/runcing
# ================================================================

def _make_icosphere(cx, cy, cz, rx, ry, rz, subdivisions=1, rng=None):
    """
    Buat icosphere ter-deformasi (ellipsoid low-poly).
    Kembalikan list segitiga [(v0,v1,v2), ...] dalam world space.
    """
    # Vertex awal icosahedron
    t = (1.0 + math.sqrt(5.0)) / 2.0
    base_verts = [
        (-1,  t,  0), ( 1,  t,  0), (-1, -t,  0), ( 1, -t,  0),
        ( 0, -1,  t), ( 0,  1,  t), ( 0, -1, -t), ( 0,  1, -t),
        ( t,  0, -1), ( t,  0,  1), (-t,  0, -1), (-t,  0,  1),
    ]
    # Normalisasi ke unit sphere
    verts = [_normalize(v) for v in base_verts]

    faces = [
        (0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
        (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
        (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
        (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1),
    ]

    # Subdivisi
    for _ in range(subdivisions):
        new_faces = []
        midpoint_cache = {}

        def midpoint(i1, i2):
            key = (min(i1,i2), max(i1,i2))
            if key in midpoint_cache:
                return midpoint_cache[key]
            v1 = verts[i1]; v2 = verts[i2]
            mid = _normalize(((v1[0]+v2[0])/2, (v1[1]+v2[1])/2, (v1[2]+v2[2])/2))
            verts.append(mid)
            idx = len(verts) - 1
            midpoint_cache[key] = idx
            return idx

        for f in faces:
            a, b, c = f
            ab = midpoint(a, b)
            bc = midpoint(b, c)
            ca = midpoint(c, a)
            new_faces += [(a,ab,ca),(b,bc,ab),(c,ca,bc),(ab,bc,ca)]
        faces = new_faces

    # Noise per-vertex-index (shared vertex → nilai sama → tidak ada celah)
    # Noise KECIL (<=0.04) supaya celah tidak muncul
    vertex_noise = {}
    tris = []
    for f in faces:
        tri = []
        for idx in f:
            if idx not in vertex_noise:
                vertex_noise[idx] = rng.uniform(-0.04, 0.04) if rng else 0.0
            vx, vy, vz = verts[idx]
            n = vertex_noise[idx]
            tri.append((
                cx + vx * rx * (1.0 + n),
                cy + vy * ry * (1.0 + n * 0.5),
                cz + vz * rz * (1.0 + n),
            ))
        tris.append(tuple(tri))
    return tris


def _build_cloud_mesh(seed, num_blobs=7):
    """
    Bangun awan dari blob icosphere yang overlap RAPAT.
    - subdivisions=2 → lebih smooth, masih low-poly
    - blob dekat pusat → menyatu, tidak terpisah
    - noise kecil → tidak ada celah antar-face
    """
    rng = random.Random(seed)
    all_faces = []

    # Blob utama: fondasi awan
    main_rx = rng.uniform(0.60, 0.80)
    main_ry = rng.uniform(0.30, 0.42)
    main_rz = rng.uniform(0.48, 0.62)
    blob_configs = [(0.0, 0.0, 0.0, main_rx, main_ry, main_rz)]

    # Blob samping: selalu dalam jangkauan blob utama supaya overlap
    for _ in range(num_blobs - 1):
        bx = rng.uniform(-main_rx * 0.85, main_rx * 0.85)
        by = rng.uniform(0.0, 0.28)
        bz = rng.uniform(-main_rz * 0.6, main_rz * 0.6)
        brx = rng.uniform(0.22, 0.48)
        bry = rng.uniform(0.18, 0.35)
        brz = rng.uniform(0.20, 0.38)
        blob_configs.append((bx, by, bz, brx, bry, brz))

    for cx, cy, cz, rx, ry, rz in blob_configs:
        tris = _make_icosphere(cx, cy, cz, rx, ry, rz, subdivisions=2, rng=rng)
        for v0, v1, v2 in tris:
            n = _face_normal(v0, v1, v2)
            shade_var = rng.uniform(-0.025, 0.025)
            all_faces.append((v0, v1, v2, n, shade_var))

    return all_faces


# Hanya satu awan dinamis untuk siklus air
import numpy as np

_MAIN_CLOUD_SEED = 42
_MAIN_CLOUD_VERTS = None
_MAIN_CLOUD_BASE_COLORS = None

# Arah cahaya (dinormalisasi)
_LIGHT_DIR_RAW = (0.5, 1.0, 0.3)
_lmag = math.sqrt(sum(x*x for x in _LIGHT_DIR_RAW))
LIGHT_DIR = tuple(x / _lmag for x in _LIGHT_DIR_RAW)


# ================================================================
#  DRAW SKY
# ================================================================

def draw_sky(bottom_color, top_color):
    """Gradient langit dinamis — fullscreen quad, tidak terpengaruh depth."""
    glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_LIGHTING_BIT)

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glBegin(GL_QUADS)
    glColor3f(*bottom_color)
    glVertex2f(0, 0)
    glVertex2f(1, 0)
    glColor3f(*top_color)
    glVertex2f(1, 1)
    glVertex2f(0, 1)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopAttrib()


def _init_main_cloud():
    global _MAIN_CLOUD_VERTS, _MAIN_CLOUD_BASE_COLORS
    faces = _build_cloud_mesh(_MAIN_CLOUD_SEED, num_blobs=9)
    lx, ly, lz = LIGHT_DIR
    
    verts = []
    colors = []
    
    for v0, v1, v2, n, shade_var in faces:
        nx, ny, nz = n
        dot = max(0.0, nx*lx + ny*ly + nz*lz)

        bright = 0.62 + dot * 0.30 + shade_var
        bright = max(0.58, min(0.96, bright))

        shadow_t = 1.0 - dot
        r = max(0.55, min(1.0, bright - shadow_t * 0.10))
        g = max(0.55, min(1.0, bright - shadow_t * 0.07))
        b = max(0.60, min(1.0, bright + shadow_t * 0.05))
        
        verts.extend([v0, v1, v2])
        colors.extend([(r, g, b), (r, g, b), (r, g, b)])
        
    _MAIN_CLOUD_VERTS = np.array(verts, dtype=np.float32)
    _MAIN_CLOUD_BASE_COLORS = np.array(colors, dtype=np.float32)

# Definisi kelompok awan siklus (posisi relatif terhadap cloud_x)
# (offset_x, offset_y, offset_z, scale)
_CYCLE_CLOUDS = [
    ( 0.0,  0.0,  0.0, 3.5), # Pusat (Awan paling besar)
    ( 3.5,  0.5,  3.5, 2.4), # Kanan Depan
    (-3.0,  0.2, -4.5, 2.8), # Kiri Belakang
    ( 4.5, -0.3, -2.5, 2.2), # Kanan Belakang
    (-4.0,  0.8,  2.5, 2.0), # Kiri Depan
    ( 1.5,  1.2, -6.0, 2.5), # Tengah Belakang
]

def draw_clouds(time, cloud_x, cloud_water):
    """
    Render sekumpulan awan yang bergerak dan berubah warna bersama-sama
    sebagai satu sistem siklus air. Tidak ada awan statis.
    """
    global _MAIN_CLOUD_VERTS, _MAIN_CLOUD_BASE_COLORS
    if _MAIN_CLOUD_VERTS is None:
        _init_main_cloud()
        
    glDisable(GL_LIGHTING)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)

    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glFrontFace(GL_CCW)

    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.0, 1.0)
    
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, _MAIN_CLOUD_VERTS)

    # ==========================================
    # RENDER KELOMPOK AWAN SIKLUS AIR
    # ==========================================
    # Hitung warna awan berdasarkan kadar air: semakin penuh, semakin gelap
    cloud_tint = 0.58 + (1.0 - cloud_water) * 0.42
    cloud_tint = max(0.35, min(1.0, cloud_tint))
    current_colors = _MAIN_CLOUD_BASE_COLORS * cloud_tint
    
    glColorPointer(3, GL_FLOAT, 0, current_colors)

    for ox, oy, oz, scale in _CYCLE_CLOUDS:
        glPushMatrix()
        # Sedikit pergerakan organik (melayang) untuk masing-masing awan
        drift_y = math.sin(time * 1.5 + ox) * 0.3
        drift_x = math.sin(time * 0.8 + oz) * 0.5
        drift_z = math.cos(time * 0.5 + ox) * 0.5

        # Posisi pusat awan adalah cloud_x, ditambah offset relatif tiap awan
        glTranslatef(cloud_x + ox + drift_x, CLOUD_HEIGHT + oy + drift_y + 1.0, oz + drift_z)
        glScalef(scale, scale * 0.58, scale * 0.78)

        glDrawArrays(GL_TRIANGLES, 0, len(_MAIN_CLOUD_VERTS))
        glPopMatrix()

    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glDisable(GL_POLYGON_OFFSET_FILL)
    glDisable(GL_CULL_FACE)


def draw_cycle_arrows(time):
    """Gambar panah besar untuk memperjelas siklus air"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST) # Biar selalu kelihatan di atas elemen lain
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # 1. PANAH ANGIN (Kanan ke Kiri, di atas)
    # Arah: x=6.0 ke x=-4.0, y=11.0
    # Beranimasi sedikit maju mundur
    offset = (time * 1.5) % 3.0
    ax_start = 6.0 - offset
    ax_end = -2.0 - offset
    ay = 11.0
    az = -2.0
    
    glColor4f(0.2, 0.6, 0.9, 0.8) # Biru muda
    
    # Batang panah angin
    glLineWidth(8.0)
    glBegin(GL_LINES)
    glVertex3f(ax_start, ay, az)
    glVertex3f(ax_end, ay, az)
    glEnd()
    
    # Ujung panah angin (segitiga di kiri)
    glBegin(GL_TRIANGLES)
    glVertex3f(ax_end - 0.8, ay, az)
    glVertex3f(ax_end + 0.4, ay + 0.6, az)
    glVertex3f(ax_end + 0.4, ay - 0.6, az)
    glEnd()

    # 2. PANAH EVAPORASI (Dari laut naik ke atas)
    # Gambar beberapa garis bergelombang dari X > 2.0
    glLineWidth(3.0)
    for i in range(4):
        ex = 4.0 + i * 2.5
        ez = 0.0 + (i % 2) * -2.0
        ey_start = 0.0
        ey_end = 6.0
        
        # Gambar garis lurus ke atas dengan ujung panah
        anim_y = (time * 2.0 + i) % 4.0
        curr_y = ey_start + anim_y
        
        glColor4f(0.3, 0.7, 0.9, 0.7)
        glBegin(GL_LINES)
        glVertex3f(ex, curr_y, ez)
        glVertex3f(ex, curr_y + 1.5, ez)
        glEnd()
        
        # Ujung panah evaporasi atas
        glBegin(GL_TRIANGLES)
        glVertex3f(ex, curr_y + 1.8, ez)
        glVertex3f(ex - 0.2, curr_y + 1.4, ez)
        glVertex3f(ex + 0.2, curr_y + 1.4, ez)
        glEnd()

    glEnable(GL_DEPTH_TEST)
    glDisable(GL_BLEND)
    glLineWidth(1.0)