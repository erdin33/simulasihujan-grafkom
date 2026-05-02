# ============================================================
#  mountain.py — Gunung 
# ============================================================

import math
import random
from OpenGL.GL import *
from config import TERRAIN_SIZE, TERRAIN_SCALE

def draw_mountain():
    """
    Menggambar gunung berbentuk bukit hijau yang mulus dengan puncak coklat.
    Posisinya digeser lebih ke kanan tapi tidak menyentuh pasir.
    Bagian bawah melengkung halus (smooth) menyatu dengan tanah.
    """
    glDisable(GL_LIGHTING)
    
    # ── posisi & ukuran ──────────────────────────────────────
    cx = -14.0
    cz = -13.0
    
    base_y   = 0.10          # persis di atas tanah dasar (0.1)
    peak_y   = 7.0           # puncak lebih tinggi
    radius   = 7.0           # diletakkan di pojok kiri belakang, ukuran besar
    
    # Warna: Hijau menyatu rumput -> Gunung Biru -> Puncak Salju Putih
    GRASS = (0.45, 0.65, 0.25)
    BLUE_MT = (0.25, 0.55, 0.65)
    WHITE_SNOW = (0.95, 0.95, 0.95)
    
    BAND_COLORS = [
        GRASS,      # 0: Bawah (menyatu rumput)
        BLUE_MT,    # 1: Transisi ke biru gunung
        BLUE_MT,    # 2: Tengah gunung
        BLUE_MT,    # 3: Atas gunung
        WHITE_SNOW, # 4: Batas salju
        WHITE_SNOW, # 5: Puncak salju
    ]
    
    LAYERS = len(BAND_COLORS) - 1
    SIDES  = 30  # Sisi diperbanyak agar ekstra mulus
    
    rng = random.Random(42)
    
    def draw_cone(center_x, center_z, b_y, p_y, r_base, color_bands):
        layers_count = len(color_bands) - 1
        rings = []
        for i in range(layers_count + 1):
            t = i / layers_count
            # Bentuk gunung kerucut lurus (segitiga kartun)
            r = r_base * (1.0 - t)
            y = b_y + (p_y - b_y) * t
            if i == layers_count:
                r = 0.0
            
            pts = []
            for k in range(SIDES):
                angle = 2.0 * math.pi * k / SIDES
                # Beri tekstur bergerigi (ridges) pada gunung
                noise = 0.0
                if i > 0 and r > 0:
                    noise = r * 0.12 * math.sin(angle * 6) * math.cos(angle * 4)
                r_noisy = r + noise
                
                x_pos = center_x + r_noisy * math.cos(angle)
                z_pos = center_z + r_noisy * math.sin(angle)
                
                y_pos = y
                pts.append((x_pos, y_pos, z_pos))
            rings.append(pts)
            
        for i in range(layers_count):
            bot_ring = rings[i]
            top_ring = rings[i+1]
            c_bot = color_bands[i]
            c_top = color_bands[i+1]
            
            glBegin(GL_QUADS)
            for k in range(SIDES):
                nk = (k + 1) % SIDES
                
                # Shading halus per-vertex (Gouraud style tanpa GL_LIGHTING)
                angle_k = 2.0 * math.pi * k / SIDES
                light_factor_k = 0.85 + 0.15 * math.cos(angle_k)
                
                angle_nk = 2.0 * math.pi * nk / SIDES
                light_factor_nk = 0.85 + 0.15 * math.cos(angle_nk)
                
                glColor3f(c_bot[0]*light_factor_k, c_bot[1]*light_factor_k, c_bot[2]*light_factor_k)
                glVertex3f(*bot_ring[k])
                
                glColor3f(c_bot[0]*light_factor_nk, c_bot[1]*light_factor_nk, c_bot[2]*light_factor_nk)
                glVertex3f(*bot_ring[nk])
                
                glColor3f(c_top[0]*light_factor_nk, c_top[1]*light_factor_nk, c_top[2]*light_factor_nk)
                glVertex3f(*top_ring[nk])
                
                glColor3f(c_top[0]*light_factor_k, c_top[1]*light_factor_k, c_top[2]*light_factor_k)
                glVertex3f(*top_ring[k])
            glEnd()

    draw_cone(cx, cz, base_y, peak_y, radius, BAND_COLORS)