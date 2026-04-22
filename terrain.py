# ============================================================
#  terrain.py — FINAL (Flat Ocean + Curved Coast + Mountain)
# ============================================================

import math
import random
import numpy as np
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE


# ================= LAUT (FLAT) =================
def draw_sea():
    glDisable(GL_LIGHTING)
    glColor3f(0.1, 0.4, 0.85)

    glBegin(GL_QUADS)
    glVertex3f(-50, 0.0, -50)
    glVertex3f(  0, 0.0, -50)
    glVertex3f(  0, 0.0,  50)
    glVertex3f(-50, 0.0,  50)
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