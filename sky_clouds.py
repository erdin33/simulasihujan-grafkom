# ============================================================
#  sky_clouds.py — Langit + Awan (FIXED & IMPROVED)
# ============================================================

import math
from OpenGL.GL import *
from OpenGL.GLU import *
from config import SKY_BOTTOM, SKY_TOP, CLOUD_HEIGHT


# ================= SKY =================
def draw_sky():
    # ❗ simpan state penting
    glPushAttrib(GL_ENABLE_BIT)

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    # ===== PROJECTION =====
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)

    # ===== MODELVIEW =====
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # ===== DRAW =====
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

    # ===== RESTORE =====
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glPopAttrib()  # 🔥 BALIKIN STATE


# ================= CLOUDS =================
def draw_clouds(time):
    """
    Awan transparan yang bergerak pelan.
    """

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LIGHTING)
    glEnable(GL_DEPTH_TEST)

    cloud_defs = [
        (-6.0, -4.0, 5.0, 1.2, 0.04),
        (-2.0,  3.0, 6.5, 1.5, 0.06),
        ( 1.5, -1.0, 4.5, 1.0, 0.03),
        (-4.5,  6.0, 4.0, 1.1, 0.05),
        ( 3.0,  5.0, 3.5, 0.9, 0.07),
    ]

    for i, (cx, cz, w, h, speed) in enumerate(cloud_defs):

        # Gerakan awan (drift)
        ox = math.sin(time * speed + i) * 1.5
        cy = CLOUD_HEIGHT + i * 0.3

        # Layer awan (biar fluffy)
        layers = [
            (cy - 0.1, w * 1.0, h * 0.6, 0.25),
            (cy,       w * 1.1, h * 0.8, 0.35),
            (cy + 0.2, w * 0.85, h * 0.5, 0.20),
        ]

        for ly, lw, lh, alpha in layers:

            # sedikit variasi warna biar hidup
            shade = 0.9 + 0.1 * math.sin(time + i)

            glColor4f(shade, shade, shade, alpha)

            glBegin(GL_QUADS)
            glVertex3f(cx + ox - lw, ly,        cz - lh)
            glVertex3f(cx + ox + lw, ly,        cz - lh)
            glVertex3f(cx + ox + lw, ly + 0.5,  cz + lh)
            glVertex3f(cx + ox - lw, ly + 0.5,  cz + lh)
            glEnd()

    glDisable(GL_BLEND)