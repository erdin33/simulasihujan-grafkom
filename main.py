# ============================================================
#  main.py — Simulasi Siklus Air (UPDATE)
#  Tambahan: gunung, sungai, pohon dari file terpisah
# ============================================================

import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config    import WINDOW_W, WINDOW_H, FPS, TITLE
from camera    import Camera
from terrain   import Terrain, draw_sea
from particles import ParticleSystem
from sky_clouds import draw_sky, draw_clouds, draw_cycle_arrows

# ─── Import modul baru ───
from river    import draw_river, draw_underground_flow
from trees    import draw_trees, draw_bushes
from sun      import draw_sun_and_moon
from day_night import get_day_phase, get_sky_colors, draw_night_overlay

# ================= UI TEXT =================
def get_stage_text(state):
    if state == "CLEAR":
        return "Langit cerah, panas matahari mulai menguapkan air"
    elif state == "EVAPORATING":
        return "Air laut & tanah menguap → uap naik ke langit"
    elif state == "CLOUDING":
        return "Uap mengembun jadi awan dan awan mulai menebal"
    elif state == "RAINING":
        return "Awan berat sudah mendung → hujan turun"
    elif state == "RETURNING":
        return "Awan kosong kembali ke laut untuk siklus ulang"
    return ""


def _blend_colors(c1, c2, t):
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t,
    )


def draw_ui_text(state, cloud_x):
    font = pygame.font.SysFont('Arial', 24, bold=True)
    text_str = get_stage_text(state)
    
    text_surface = font.render(text_str, True, (255, 255, 255))
    shadow_surface = font.render(text_str, True, (0, 0, 0))
    
    base = pygame.Surface((text_surface.get_width() + 4, text_surface.get_height() + 4), pygame.SRCALPHA)
    base.blit(shadow_surface, (2, 2))
    base.blit(text_surface, (0, 0))
    
    text_data = pygame.image.tostring(base, "RGBA", True)
    tw, th = base.get_size()
    
    # Ambil matriks 3D saat ini
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    
    # Tentukan posisi 3D di mana teks harus melayang
    if state in ("CLEAR", "EVAPORATING", "RAINING"):
        pos_3d = (cloud_x, 4.0, 0.0) # Di atas laut / uap / hujan
    elif state in ("CLOUDING", "RETURNING"):
        pos_3d = (cloud_x, 11.0, 0.0) # Di atas kelompok awan
    else:
        pos_3d = (cloud_x, 5.0, 0.0)
        
    try:
        winX, winY, winZ = gluProject(pos_3d[0], pos_3d[1], pos_3d[2], modelview, projection, viewport)
        draw_x = int(winX - tw / 2)
        draw_y = int(winY)
    except Exception:
        draw_x, draw_y = 20, viewport[3] - th - 20
    
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, viewport[2], 0, viewport[3])

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Pastikan teks digambar
    if winZ < 1.0: 
        glRasterPos2i(draw_x, draw_y)
        glDrawPixels(tw, th, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()


# ================= SETUP OPENGL =================
def setup_opengl(w, h):
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, w / h, 0.1, 300.0)
    glMatrixMode(GL_MODELVIEW)


# ================= RENDER =================
def render(camera, terrain, particles, time):
    phase = 0.25 # Fixed daylight
    bottom_col, top_col = get_sky_colors(phase)
    
    # Orbital sinar matahari memberi panas untuk evaporasi
    if particles.cloud_water > 0.2:
        storm = min(1.0, max(0.0, (particles.cloud_water - 0.2) / 0.8))
        sky_bottom = _blend_colors(bottom_col, (0.18, 0.25, 0.33), storm * 0.9)
        sky_top    = _blend_colors(top_col,    (0.08, 0.12, 0.18), storm * 0.9)
    else:
        sky_bottom, sky_top = bottom_col, top_col
    
    # Update warna background dengan warna langit atas
    glClearColor(sky_top[0], sky_top[1], sky_top[2], 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_sky(sky_bottom, sky_top)

    glLoadIdentity()
    eye    = camera.pos
    target = camera.pos + camera.front
    up     = camera.up
    gluLookAt(
        eye[0],    eye[1],    eye[2],
        target[0], target[1], target[2],
        up[0],     up[1],     up[2],
    )

    # ─── SCENE (urutan penting untuk depth) ───
    terrain.draw()              # 🟩 Terrain darat (hijau)
    draw_underground_flow()     # 💧 Aliran bawah tanah

    draw_river()                # 🏞️ Sungai (di atas terrain)
    draw_trees()                # 🌳 Pohon-pohon
    draw_bushes()               # 🌿 Semak-semak

    draw_clouds(time, particles.cloud_x, particles.cloud_water) # ☁️ Awan Siklus Air
    particles.draw()            # 💨 Partikel uap & hujan
    
    # draw_night_overlay(phase)   # Dihapus agar siang terus
    draw_sea(time)              # 🌊 Laut bergelombang


# ================= MAIN =================
def main():
    pygame.init()

    display_flags  = DOUBLEBUF | OPENGL | RESIZABLE
    current_w, current_h = WINDOW_W, WINDOW_H
    pygame.display.set_mode((current_w, current_h), display_flags)
    pygame.display.set_caption(TITLE)

    setup_opengl(current_w, current_h)

    camera    = Camera()
    terrain   = Terrain()
    particles = ParticleSystem(terrain)

    clock = pygame.time.Clock()
    time  = 0.0

    print("=== SIMULASI SIKLUS AIR ===")
    print("  W/A/S/D  : Gerak kamera")
    print("  Mouse    : Lihat sekeliling")
    print("  ESC      : Keluar")

    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    is_focused = True

    while True:
        dt    = clock.tick(FPS) / 1000.0
        time += dt

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit(); sys.exit()

            if event.type == VIDEORESIZE:
                current_w, current_h = event.w, max(event.h, 1)
                pygame.display.set_mode((current_w, current_h), display_flags)
                setup_opengl(current_w, current_h)
                glViewport(0, 0, current_w, current_h)

            if event.type == WINDOWFOCUSLOST:
                is_focused = False
                pygame.event.set_grab(False)
                pygame.mouse.set_visible(True)

            if event.type == WINDOWFOCUSGAINED:
                is_focused = True
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
                pygame.mouse.get_rel()

            if event.type == MOUSEMOTION and is_focused:
                dx, dy = event.rel
                camera.rotate(dx, dy)

        keys = pygame.key.get_pressed()
        camera.move(keys)

        particles.update(dt, time)

        render(camera, terrain, particles, time)
        pygame.display.flip()

        v_count, r_count = particles.stats()
        pygame.display.set_caption(
            f"{TITLE} | Uap: {v_count} | Hujan: {r_count} | FPS: {clock.get_fps():.0f}"
        )


if __name__ == "__main__":
    main()