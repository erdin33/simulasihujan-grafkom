# ============================================================
#  particles.py — Sistem Partikel: Uap + Hujan
# ============================================================

import random
import numpy as np
from OpenGL.GL import *
from config import (
    MAX_VAPOR, MAX_RAIN, CLOUD_HEIGHT,
    VAPOR_SPEED_Y, RAIN_SPEED_Y,
)


class ParticleSystem:
    """
    Siklus:
      1. Uap spawn di permukaan laut (Y rendah)
      2. Uap naik → mencapai CLOUD_HEIGHT → mati (jadi awan)
      3. Hujan spawn dari area awan → turun → mati saat Y < tanah
    """

    def __init__(self, terrain):
        self.terrain = terrain

        # ── Vapor arrays ──────────────────────────
        self.v_pos   = np.zeros((MAX_VAPOR, 3), dtype=np.float32)
        self.v_vel   = np.zeros((MAX_VAPOR, 3), dtype=np.float32)
        self.v_alpha = np.zeros(MAX_VAPOR,      dtype=np.float32)
        self.v_alive = np.zeros(MAX_VAPOR,      dtype=bool)

        # ── Rain arrays ───────────────────────────
        self.r_pos   = np.zeros((MAX_RAIN, 3),  dtype=np.float32)
        self.r_vel   = np.zeros((MAX_RAIN, 3),  dtype=np.float32)
        self.r_alpha = np.zeros(MAX_RAIN,       dtype=np.float32)
        self.r_alive = np.zeros(MAX_RAIN,       dtype=bool)

        self._v_timer = 0.0
        self._r_timer = 0.0

        # Spawn vapor awal agar tidak kosong saat buka
        self._fill_initial_vapor()
        self._fill_initial_rain()

    # ────────────────────────────────────────────────
    #  INIT
    # ────────────────────────────────────────────────
    def _fill_initial_vapor(self):
        sea = self.terrain.get_sea_spawn_positions(MAX_VAPOR // 2)
        for idx, (sx, sy, sz) in enumerate(sea):
            if idx >= MAX_VAPOR:
                break
            self._spawn_vapor(idx, sx, sy, sz)

    def _fill_initial_rain(self):
        for idx in range(MAX_RAIN // 3):
            self._spawn_rain(idx)

    # ────────────────────────────────────────────────
    #  SPAWN
    # ────────────────────────────────────────────────
    def _spawn_vapor(self, idx, x, y, z):
        # Posisi di permukaan laut dengan sedikit offset acak
        self.v_pos[idx]  = [
            x + random.uniform(-0.4, 0.4),
            y + random.uniform(0.0, 0.3),
            z + random.uniform(-0.4, 0.4),
        ]
        # Naik ke atas, sedikit drift horizontal
        self.v_vel[idx]  = [
            random.uniform(-0.008, 0.008),
            VAPOR_SPEED_Y + random.uniform(0.0, 0.03),
            random.uniform(-0.008, 0.008),
        ]
        self.v_alpha[idx] = random.uniform(0.35, 0.70)
        self.v_alive[idx] = True

    def _spawn_rain(self, idx):
        # Spawn di area awan (di atas laut & gunung)
        x = random.uniform(-12, 5)
        z = random.uniform(-12, 12)
        y = CLOUD_HEIGHT + random.uniform(0.0, 2.0)
        self.r_pos[idx]  = [x, y, z]
        self.r_vel[idx]  = [
            random.uniform(-0.004, 0.004),
            -(RAIN_SPEED_Y + random.uniform(0.0, 0.04)),
            random.uniform(-0.004, 0.004),
        ]
        self.r_alpha[idx] = random.uniform(0.45, 0.85)
        self.r_alive[idx] = True

    # ────────────────────────────────────────────────
    #  UPDATE
    # ────────────────────────────────────────────────
    def update(self, dt):
        scale = dt * 60.0   # normalisasi ke 60 fps

        # ── Update Vapor ──
        av = self.v_alive
        if av.any():
            self.v_pos[av]   += self.v_vel[av] * scale
            self.v_alpha[av] -= 0.0025 * scale

            # Matikan: sudah tinggi (jadi awan) atau pudar
            kill = av & ((self.v_pos[:, 1] > CLOUD_HEIGHT) | (self.v_alpha < 0.04))
            self.v_alive[kill] = False

        # Spawn vapor baru dari laut
        self._v_timer += dt
        if self._v_timer >= 0.04:
            self._v_timer = 0.0
            dead = np.where(~self.v_alive)[0]
            if len(dead):
                batch = min(8, len(dead))
                sea   = self.terrain.get_sea_spawn_positions(batch)
                for k, (sx, sy, sz) in enumerate(sea):
                    if k >= len(dead):
                        break
                    self._spawn_vapor(dead[k], sx, sy, sz)

        # ── Update Rain ──
        ar = self.r_alive
        if ar.any():
            self.r_pos[ar]   += self.r_vel[ar] * scale
            self.r_alpha[ar] -= 0.003 * scale

            # Matikan: menyentuh tanah atau pudar
            kill = ar & ((self.r_pos[:, 1] < -2.0) | (self.r_alpha < 0.04))
            self.r_alive[kill] = False

        # Spawn hujan baru
        self._r_timer += dt
        if self._r_timer >= 0.018:
            self._r_timer = 0.0
            dead = np.where(~self.r_alive)[0]
            for idx in dead[:10]:
                self._spawn_rain(idx)

    # ────────────────────────────────────────────────
    #  DRAW
    # ────────────────────────────────────────────────
    def draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)   # partikel tidak saling occlude

        # ── Vapor: titik putih-biru ──────────────
        glPointSize(3.5)
        glBegin(GL_POINTS)
        for i in range(MAX_VAPOR):
            if self.v_alive[i]:
                a = float(self.v_alpha[i])
                glColor4f(0.88, 0.92, 1.0, a)
                glVertex3fv(self.v_pos[i])
        glEnd()

        # ── Hujan: garis pendek biru ─────────────
        glLineWidth(1.4)
        glBegin(GL_LINES)
        for i in range(MAX_RAIN):
            if self.r_alive[i]:
                a  = float(self.r_alpha[i])
                px, py, pz = self.r_pos[i]
                glColor4f(0.45, 0.70, 1.0, a)
                glVertex3f(px, py, pz)
                glColor4f(0.45, 0.70, 1.0, 0.0)
                glVertex3f(px, py + 0.35, pz)
        glEnd()

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

    # ── Info untuk title bar ──
    def stats(self):
        return int(self.v_alive.sum()), int(self.r_alive.sum())