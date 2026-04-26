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


# Cache mesh: {seed: list_of_faces}
_CLOUD_MESHES = {}

# Definisi awan: (seed, base_x, y_offset, base_z, scale, drift_speed)
_CLOUD_DEFS = [
    (1,  -7.0,  0.0,  -4.5,  2.4,  0.035),
    (2,  -2.0,  0.8,   3.5,  3.0,  0.050),
    (3,   4.5,  0.3,  -1.5,  2.0,  0.028),
    (4,  -5.0,  1.2,   7.0,  2.2,  0.042),
    (5,   7.5,  0.5,   5.0,  1.8,  0.060),
    (6,   1.5,  1.5,  -7.0,  2.6,  0.033),
    (7,  -9.5,  0.9,   2.5,  1.5,  0.055),
    (8,   9.0,  0.4,  -3.5,  2.1,  0.047),
    (8,   9.0,  0.4,  -3.5,  2.1,  0.075),
]

# Arah cahaya (dinormalisasi)
_LIGHT_DIR_RAW = (0.5, 1.0, 0.3)
_lmag = math.sqrt(sum(x*x for x in _LIGHT_DIR_RAW))
LIGHT_DIR = tuple(x / _lmag for x in _LIGHT_DIR_RAW)


# ================================================================
#  DRAW SKY
# ================================================================

def draw_sky():
    """Gradient langit — fullscreen quad, tidak terpengaruh depth."""
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
    r, g, b = SKY_BOTTOM
    glColor3f(r, g, b)
    glVertex2f(0, 0)
    glVertex2f(1, 0)
    r, g, b = SKY_TOP
    glColor3f(r, g, b)
    glVertex2f(1, 1)
    glVertex2f(0, 1)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopAttrib()


# Display list cache: {seed: gl_list_id}
_CLOUD_DISPLAY_LISTS = {}


def _compile_cloud_display_list(seed):
    """
    Compile satu awan ke OpenGL Display List.
    Semua perhitungan warna/normal dilakukan SEKALI di sini,
    lalu disimpan di GPU. Render tinggal glCallList() — sangat cepat.
    """
    faces = _CLOUD_MESHES[seed]
    lx, ly, lz = LIGHT_DIR

    dl = glGenLists(1)
    glNewList(dl, GL_COMPILE)
    glBegin(GL_TRIANGLES)
    for v0, v1, v2, n, shade_var in faces:
        nx, ny, nz = n
        dot = max(0.0, nx*lx + ny*ly + nz*lz)

        bright = 0.62 + dot * 0.30 + shade_var
        bright = max(0.58, min(0.96, bright))

        shadow_t = 1.0 - dot
        r = max(0.55, min(1.0, bright - shadow_t * 0.10))
        g = max(0.55, min(1.0, bright - shadow_t * 0.07))
        b = max(0.60, min(1.0, bright + shadow_t * 0.05))

        glColor3f(r, g, b)
        glVertex3f(*v0)
        glVertex3f(*v1)
        glVertex3f(*v2)
    glEnd()
    glEndList()
    return dl


def draw_clouds(time):
    """
    Render awan low-poly 3D.
    Geometry di-compile ke Display List → CPU tidak ngitung apa-apa per frame,
    tinggal glTranslatef + glCallList per awan.
    """
    glDisable(GL_LIGHTING)
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)

    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glFrontFace(GL_CCW)

    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.0, 1.0)

    for seed, base_x, y_off, base_z, scale, speed in _CLOUD_DEFS:

        # Build mesh (sekali)
        if seed not in _CLOUD_MESHES:
            _CLOUD_MESHES[seed] = _build_cloud_mesh(seed, num_blobs=7)

        # Compile ke display list (sekali)
        if seed not in _CLOUD_DISPLAY_LISTS:
            _CLOUD_DISPLAY_LISTS[seed] = _compile_cloud_display_list(seed)

        drift_x = math.sin(time * speed + seed * 1.3) * 1.8
        drift_z = math.cos(time * speed * 0.35 + seed) * 0.4

        glPushMatrix()
        glTranslatef(base_x + drift_x, CLOUD_HEIGHT + y_off, base_z + drift_z)
        glScalef(scale, scale * 0.58, scale * 0.78)

        # Satu panggilan → GPU langsung render, tidak ada loop Python
        glCallList(_CLOUD_DISPLAY_LISTS[seed])

        glPopMatrix()

    glDisable(GL_POLYGON_OFFSET_FILL)
    glDisable(GL_CULL_FACE)