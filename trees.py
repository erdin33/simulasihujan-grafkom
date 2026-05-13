# ============================================================
#  trees.py — Pohon-pohon hijau di terrain darat
#  OPTIMIZED: Display Lists — geometry di-compile 1x saat init,
#             draw_trees() / draw_bushes() hanya glCallList() tiap frame.
# ============================================================

import math
import random
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


# ================= POSISI POHON =================
def _generate_tree_positions(seed=42):
    rng = random.Random(seed)

    import river
    river_path = river.get_river_path()

    def is_too_close_to_river(tx, tz):
        for rx, rz in river_path:
            dx, dz = tx - rx, tz - rz
            if dx*dx + dz*dz < (3.5 ** 2):
                return True
        return False

    from terrain import get_world_y

    positions = []

    specs = [
        # (count, x_range,        z_range,        scale_range,    type)
        (20, (-10.0, -6.5),  (-14.0, 14.0), (0.7, 1.1),  'lowland'),
        ( 6, ( -6.5, -4.5),  (-14.0, 14.0), (0.8, 1.2),  'coconut'),
        (25, (-13.0, -8.0),  (-14.0, 14.0), (0.8, 1.3),  'slope'),
        (15, (-14.0, -9.0),  (-13.0, -6.0), (1.0, 1.5),  'mountain_base'),
    ]

    for count, (x0, x1), (z0, z1), (s0, s1), ttype in specs:
        for _ in range(count):
            for _ in range(15):
                x = rng.uniform(x0, x1)
                z = rng.uniform(z0, z1)
                if not is_too_close_to_river(x, z):
                    scale = rng.uniform(s0, s1)
                    positions.append((x, get_world_y(x, z), z, scale, ttype))
                    break

    return positions


def _generate_bush_positions(seed=99):
    rng = random.Random(seed)

    import river
    river_path = river.get_river_path()

    def is_too_close_to_river(tx, tz):
        for rx, rz in river_path:
            dx, dz = tx - rx, tz - rz
            if dx*dx + dz*dz < (3.5 ** 2):
                return True
        return False

    from terrain import get_world_y

    positions = []
    for _ in range(45):
        for _ in range(15):
            x = rng.uniform(-14.0, -5.0)
            z = rng.uniform(-14.0, 14.0)
            if not is_too_close_to_river(x, z):
                break
        scale  = rng.uniform(0.25, 0.50)
        base_y = get_world_y(x, z)
        positions.append((x, base_y, z, scale))

    return positions


# ================= DRAW HELPERS (geometry only, no state change) =================

def _draw_round_tree(cx, base_y, cz, scale=1.0):
    trunk_h = 0.8  * scale
    trunk_r = 0.10 * scale
    crown_r = 0.75 * scale
    crown_y = base_y + trunk_h + crown_r * 0.5

    SIDES = 6
    glColor3f(0.38, 0.24, 0.12)
    glBegin(GL_QUAD_STRIP)
    for k in range(SIDES + 1):
        angle = 2 * math.pi * k / SIDES
        px = cx + trunk_r * math.cos(angle)
        pz = cz + trunk_r * math.sin(angle)
        glVertex3f(px, base_y,           pz)
        glVertex3f(px, base_y + trunk_h, pz)
    glEnd()

    STACKS, SLICES = 5, 7

    def crown_color(s):
        t = s / STACKS
        return (0.15 + 0.10*t, 0.42 + 0.18*t, 0.12 + 0.05*t)

    for s in range(STACKS):
        phi0 = math.pi * s       / STACKS - math.pi / 2
        phi1 = math.pi * (s + 1) / STACKS - math.pi / 2
        c0, c1 = crown_color(s), crown_color(s + 1)

        glBegin(GL_QUADS)
        for sl in range(SLICES):
            t0 = 2 * math.pi * sl       / SLICES
            t1 = 2 * math.pi * (sl + 1) / SLICES

            def pt(phi, theta):
                return (cx + crown_r * math.cos(phi) * math.cos(theta),
                        crown_y + crown_r * math.sin(phi),
                        cz + crown_r * math.cos(phi) * math.sin(theta))

            A, B = pt(phi0, t0), pt(phi0, t1)
            C, D = pt(phi1, t1), pt(phi1, t0)

            glColor3f(*c0); glVertex3f(*A); glVertex3f(*B)
            glColor3f(*c1); glVertex3f(*C); glVertex3f(*D)
        glEnd()


def _draw_pine_tree(cx, base_y, cz, scale=1.0):
    trunk_h = 0.6  * scale
    trunk_r = 0.08 * scale
    SIDES   = 5

    glColor3f(0.32, 0.20, 0.10)
    glBegin(GL_QUAD_STRIP)
    for k in range(SIDES + 1):
        angle = 2 * math.pi * k / SIDES
        px = cx + trunk_r * math.cos(angle)
        pz = cz + trunk_r * math.sin(angle)
        glVertex3f(px, base_y,           pz)
        glVertex3f(px, base_y + trunk_h, pz)
    glEnd()

    layers = [
        (base_y + trunk_h*0.50,               0.70*scale, 1.00*scale, (0.18, 0.42, 0.18)),
        (base_y + trunk_h*0.50 + 0.55*scale,  0.50*scale, 0.80*scale, (0.22, 0.50, 0.22)),
        (base_y + trunk_h*0.50 + 1.05*scale,  0.32*scale, 0.65*scale, (0.28, 0.58, 0.25)),
    ]
    CONE_SIDES = 7

    for ly, lr, lh, lc in layers:
        peak_y   = ly + lh
        angles   = [2 * math.pi * k / CONE_SIDES for k in range(CONE_SIDES)]
        base_pts = [(cx + lr * math.cos(a), ly, cz + lr * math.sin(a)) for a in angles]

        glBegin(GL_TRIANGLES)
        for k in range(CONE_SIDES):
            nk  = (k + 1) % CONE_SIDES
            bA, bB = base_pts[k], base_pts[nk]
            face_light = math.cos((angles[k] + angles[nk]) / 2 - math.pi * 0.3)
            shade = 0.75 + 0.25 * max(0.0, face_light)
            glColor3f(lc[0]*shade, lc[1]*shade, lc[2]*shade)
            glVertex3f(*bA); glVertex3f(*bB); glVertex3f(cx, peak_y, cz)
        glEnd()

        glColor3f(lc[0]*0.6, lc[1]*0.6, lc[2]*0.6)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(cx, ly - 0.02, cz)
        for p in base_pts:
            glVertex3f(p[0], p[1] - 0.02, p[2])
        glVertex3f(base_pts[0][0], base_pts[0][1] - 0.02, base_pts[0][2])
        glEnd()


def _draw_coconut_tree(cx, base_y, cz, scale=1.0):
    trunk_h  = 1.6  * scale
    trunk_r  = 0.06 * scale
    tilt_x   = 0.6  * scale
    SIDES    = 6
    segments = 5

    glColor3f(0.42, 0.32, 0.18)
    for i in range(segments):
        t0 = i       / segments
        t1 = (i + 1) / segments
        cx0, cy0, r0 = cx + tilt_x*(t0**2), base_y + trunk_h*t0, trunk_r*(1 - t0*0.3)
        cx1, cy1, r1 = cx + tilt_x*(t1**2), base_y + trunk_h*t1, trunk_r*(1 - t1*0.3)

        glBegin(GL_QUAD_STRIP)
        for k in range(SIDES + 1):
            angle = 2 * math.pi * k / SIDES
            ca, sa = math.cos(angle), math.sin(angle)
            glVertex3f(cx0 + r0*ca, cy0, cz + r0*sa)
            glVertex3f(cx1 + r1*ca, cy1, cz + r1*sa)
        glEnd()

    top_x = cx + tilt_x
    top_y = base_y + trunk_h
    leaf_len = 0.9 * scale

    for i in range(6):
        angle  = 2 * math.pi * i / 6.0
        end_x  = top_x + leaf_len * math.cos(angle)
        end_z  = cz    + leaf_len * math.sin(angle)
        end_y  = top_y - 0.45 * scale
        mid_x  = top_x + leaf_len * 0.4 * math.cos(angle)
        mid_z  = cz    + leaf_len * 0.4 * math.sin(angle)
        mid_y  = top_y + 0.15 * scale
        px, pz = -math.sin(angle)*0.15*scale, math.cos(angle)*0.15*scale

        glBegin(GL_TRIANGLES)
        glColor3f(0.25, 0.60, 0.20); glVertex3f(top_x, top_y, cz)
        glColor3f(0.20, 0.55, 0.15)
        glVertex3f(mid_x+px, mid_y, mid_z+pz)
        glVertex3f(mid_x-px, mid_y, mid_z-pz)

        glColor3f(0.20, 0.55, 0.15); glVertex3f(mid_x+px, mid_y, mid_z+pz)
        glColor3f(0.15, 0.45, 0.10); glVertex3f(end_x, end_y, end_z)
        glColor3f(0.20, 0.55, 0.15); glVertex3f(mid_x-px, mid_y, mid_z-pz)
        glEnd()


def _draw_bush(x, base_y, z, scale):
    crown_r = 0.45 * scale
    crown_y = base_y + crown_r * 0.8
    STACKS, SLICES = 3, 6

    for s in range(STACKS):
        phi0 = math.pi * s       / STACKS - math.pi / 2
        phi1 = math.pi * (s + 1) / STACKS - math.pi / 2
        t0, t1 = s / STACKS, (s + 1) / STACKS
        c0 = (0.20 + 0.08*t0, 0.45 + 0.12*t0, 0.16 + 0.06*t0)
        c1 = (0.20 + 0.08*t1, 0.45 + 0.12*t1, 0.16 + 0.06*t1)

        glBegin(GL_QUADS)
        for sl in range(SLICES):
            th0 = 2 * math.pi * sl       / SLICES
            th1 = 2 * math.pi * (sl + 1) / SLICES

            def pt(phi, theta):
                return (x + crown_r * math.cos(phi) * math.cos(theta),
                        crown_y + crown_r * math.sin(phi),
                        z + crown_r * math.cos(phi) * math.sin(theta))

            A, B = pt(phi0, th0), pt(phi0, th1)
            C, D = pt(phi1, th1), pt(phi1, th0)

            glColor3f(*c0); glVertex3f(*A); glVertex3f(*B)
            glColor3f(*c1); glVertex3f(*C); glVertex3f(*D)
        glEnd()


# ================= DISPLAY LIST CACHE =================
# Both lists are compiled once on first draw, then only glCallList() is used.

_TREES_LIST_ID  = None   # OpenGL display list id for all trees
_BUSHES_LIST_ID = None   # OpenGL display list id for all bushes


def _build_trees_list():
    global _TREES_LIST_ID
    positions = _generate_tree_positions()
    dl = glGenLists(1)
    glNewList(dl, GL_COMPILE)
    glDisable(GL_LIGHTING)
    for (x, y, z, scale, ttype) in positions:
        if ttype == 'lowland':
            _draw_round_tree(x, y, z, scale)
        elif ttype == 'slope':
            _draw_pine_tree(x, y, z, scale)
        elif ttype == 'coconut':
            _draw_coconut_tree(x, y, z, scale)
        else:  # mountain_base
            _draw_round_tree(x, y, z, scale * 0.9)
            _draw_pine_tree(x + scale*0.8, y, z + scale*0.5, scale*0.7)
    glEndList()
    _TREES_LIST_ID = dl


def _build_bushes_list():
    global _BUSHES_LIST_ID
    positions = _generate_bush_positions()
    dl = glGenLists(1)
    glNewList(dl, GL_COMPILE)
    glDisable(GL_LIGHTING)
    for (x, base_y, z, scale) in positions:
        _draw_bush(x, base_y, z, scale)
    glEndList()
    _BUSHES_LIST_ID = dl


# ================= PUBLIC API =================

def draw_trees():
    """Compile once, replay every frame."""
    global _TREES_LIST_ID
    if _TREES_LIST_ID is None:
        _build_trees_list()
    glCallList(_TREES_LIST_ID)


def draw_bushes():
    """Compile once, replay every frame."""
    global _BUSHES_LIST_ID
    if _BUSHES_LIST_ID is None:
        _build_bushes_list()
    glCallList(_BUSHES_LIST_ID)


def invalidate_vegetation_cache():
    """Call this if terrain changes at runtime and you need to rebuild the lists."""
    global _TREES_LIST_ID, _BUSHES_LIST_ID
    if _TREES_LIST_ID is not None:
        glDeleteLists(_TREES_LIST_ID, 1)
        _TREES_LIST_ID = None
    if _BUSHES_LIST_ID is not None:
        glDeleteLists(_BUSHES_LIST_ID, 1)
        _BUSHES_LIST_ID = None