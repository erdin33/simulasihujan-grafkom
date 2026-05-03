# ============================================================
#  particles.py — Sistem Partikel: Uap + Hujan
# ============================================================

import random
import math
import numpy as np
from OpenGL.GL import *
from day_night import get_day_phase
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

        # ── State Machine Awan ────────────────────
        self.cloud_state = "CLEAR"
        self.cloud_x = 5.0      # Mulai di atas laut
        self.cloud_water = 0.0  # Kapasitas air awan (0.0=putih, 1.0=gelap)
        self._heat = 0.0
        self._wait_timer = 0.0
        self.rainbow_alpha = 0.0

        # Tidak ada vapor awal, tunggu fase evaporasi dimulai

    # ────────────────────────────────────────────────
    #  INIT
    # ────────────────────────────────────────────────
    def _fill_initial_vapor(self):
        sea = self.terrain.get_sea_spawn_positions(MAX_VAPOR // 2)
        for idx, (sx, sy, sz) in enumerate(sea):
            if idx >= MAX_VAPOR:
                break
            self._spawn_vapor(idx, sx, sy, sz)

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
        # Gerakan uap beraturan: Awalnya hanya naik lurus ke atas
        self.v_vel[idx]  = [
            0.0,
            VAPOR_SPEED_Y + random.uniform(0.0, 0.02),
            0.0,
        ]
        self.v_alpha[idx] = random.uniform(0.40, 0.80)
        self.v_alive[idx] = True

    def _spawn_rain(self, idx):
        # Spawn di area awan saat ini (sangat lebar menutupi seluruh hutan)
        x = self.cloud_x + random.uniform(-5.5, 5.5)
        z = random.uniform(-16.0, 15.0)
        y = CLOUD_HEIGHT + random.uniform(0.0, 1.0)
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
    def update(self, dt, time):
        # Memperlambat proses logika siklus air (awan, hujan, evaporasi)
        dt = dt * 0.4
        
        scale = dt * 60.0   # normalisasi ke 60 fps

        phase = 0.25 #get_day_phase(time)
        self._heat = max(0.0, math.sin(phase * math.pi * 2.0))
        evap_power = 0.35 + self._heat * 1.05
        rain_power = 0.8 + self.cloud_water * 0.6

        # ── State Machine Awan ──
        if self.cloud_state == "CLEAR":
            self._wait_timer += dt
            if self._wait_timer >= 5.0:  # Tunggu 5 detik di laut sebelum partikel uap naik
                self._wait_timer = 0.0
                self.cloud_state = "EVAPORATING"
        elif self.cloud_state == "EVAPORATING":
            if self.cloud_water >= 0.15:  # Pindah ke fase kondensasi UI lebih awal saat uap mulai kumpul
                self.cloud_state = "CLOUDING"
        elif self.cloud_state == "CLOUDING":
            if self.cloud_water >= 0.60:  # Kumpulkan uap sampai penuh sebelum bergeser
                self.cloud_x -= 1.8 * dt
                if self.cloud_x <= -10.0:
                    self.cloud_x = -10.0
                if self.cloud_x <= -8.0:      # Langsung hujan setelah sampai daratan
                    self.cloud_state = "RAINING"
        elif self.cloud_state == "RAINING":
            self.cloud_water -= 0.04 * dt * rain_power  # Jauh lebih lambat agar durasi hujan lebih lama
            if self.cloud_water <= 0.0:
                self.cloud_water = 0.0
                self.cloud_state = "RETURNING"
        elif self.cloud_state == "RETURNING":
            self.cloud_x += 1.8 * dt
            if self.cloud_x >= 5.0:
                self.cloud_x = 5.0
                self.cloud_state = "CLEAR"

        # Update transparansi pelangi
        if self.cloud_state == "RETURNING":
            self.rainbow_alpha = min(1.0, self.rainbow_alpha + 0.5 * dt)
        elif self.cloud_state == "CLEAR":
            self.rainbow_alpha = max(0.0, self.rainbow_alpha - 0.15 * dt)
        else:
            self.rainbow_alpha = max(0.0, self.rainbow_alpha - 0.8 * dt)

        # ── Update Vapor ──
        av = self.v_alive
        if av.any():
            self.v_pos[av]   += self.v_vel[av] * scale
            if self.cloud_state in ("CLEAR", "EVAPORATING") or (self.cloud_state == "CLOUDING" and self.cloud_water < 0.60):
                self.v_alpha[av] -= 0.0020 * scale
            else:
                self.v_alpha[av] -= 0.02 * scale  # Fade out lebih cepat saat awan geser

            # Naik lebih cepat saat panas lebih tinggi
            self.v_vel[av, 1] += (
                VAPOR_SPEED_Y * (0.45 + self._heat * 0.95)
                - self.v_vel[av, 1]
            ) * 0.04 * scale

            # Aliran uap mengarah ke posisi awan saat ini
            height_ratio = np.clip(self.v_pos[av, 1] / CLOUD_HEIGHT, 0.0, 1.0)
            dx = self.cloud_x - self.v_pos[av, 0]
            target_vel_x = np.clip(dx * 0.015, -0.06, 0.06) * height_ratio
            self.v_vel[av, 0] += (target_vel_x - self.v_vel[av, 0]) * 0.03 * scale

            # Cek partikel yang sampai awan
            reached_cloud = av & (self.v_pos[:, 1] >= CLOUD_HEIGHT - 0.5)
            faded = av & (self.v_alpha < 0.02)
            
            if self.cloud_state in ("EVAPORATING", "CLOUDING"):
                reached_count = np.sum(reached_cloud)
                if reached_count > 0:
                    self.cloud_water += reached_count * 0.0025 * evap_power  # Pengisian air dikembalikan ke normal/sedikit lebih lambat
                    self.cloud_water = min(1.0, self.cloud_water)
                    if self.cloud_state == "EVAPORATING" and self.cloud_water >= 0.60:
                        self.cloud_state = "CLOUDING"
                    if self.cloud_state == "CLOUDING" and self.cloud_x <= -8.0:
                        self.cloud_state = "RAINING"
            
            kill = reached_cloud | faded
            self.v_alive[kill] = False

        # Spawn vapor HANYA saat proses penguapan (EVAPORATING)
        # Di fase CLEAR, air berhenti menguap sejenak (jeda)
        if self.cloud_state == "EVAPORATING":
            self._v_timer += dt * (1.0 + self._heat * 1.2)
            interval = 0.045
            if self._v_timer >= interval:
                self._v_timer = 0.0
                dead = np.where(~self.v_alive)[0]
                if len(dead):
                    max_batch = min(12, 6 + int(self._heat * 10))
                    batch = min(max_batch, len(dead))
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
            kill = ar & ((self.r_pos[:, 1] < -2.0) | (self.r_alpha < 0.04))
            self.r_alive[kill] = False

        # Spawn hujan HANYA saat raining
        if self.cloud_state == "RAINING":
            self._r_timer += dt * rain_power
            interval = 0.02
            if self._r_timer >= interval:
                self._r_timer = 0.0
                dead = np.where(~self.r_alive)[0]
                if len(dead):
                    rain_count = min(len(dead), 12 + int(self.cloud_water * 24))
                    for idx in dead[:rain_count]:
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