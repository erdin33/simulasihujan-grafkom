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

from ui import draw_ui_box
from rainbow import draw_rainbow


def _blend_colors(c1, c2, t):
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t,
    )

def draw_storm_overlay(storm_intensity):
    if storm_intensity <= 0.0: return
    
    glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_LIGHTING_BIT)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    alpha = storm_intensity * 0.55  # Maksimal 55% kegelapan di permukaan bumi
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor4f(0.05, 0.08, 0.12, alpha) # Warna mendung / bayangan awan
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(1, 0)
    glVertex2f(1, 1)
    glVertex2f(0, 1)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
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
    storm = 0.0
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

    # (Matahari tidak digambar sesuai permintaan)
    # draw_sun_and_moon(time)
    # ─── SCENE DARATAN & LAUT ───
    terrain.draw()              # 🟩 Terrain darat (hijau)
<<<<<<< HEAD
    draw_sea(time)              # 🌊 Laut bergelombang
=======
>>>>>>> ca991069cdabe3776f220fa529e87e2108cf43e2
    draw_underground_flow()     # 💧 Aliran bawah tanah
    draw_river(time)            # 🏞️ Sungai (di atas terrain)
    draw_trees()                # 🌳 Pohon-pohon
    draw_bushes()               # 🌿 Semak-semak

    # Gambar pelangi jika muncul (setelah semua objek solid agar kedalaman (depth) transparan berfungsi benar)
    draw_rainbow(particles.rainbow_alpha)

    # ─── OVERLAY MENDUNG DI PERMUKAAN BUMI ───
    # Karena awan cumulonimbus menutupi matahari, area di bawah awan menjadi gelap
    draw_storm_overlay(storm)

    # ─── SCENE AWAN & CUACA ───
    draw_clouds(time, particles.cloud_x, particles.cloud_water) # ☁️ Awan Siklus Air
    particles.draw()            # 💨 Partikel uap & hujan
    
<<<<<<< HEAD
    # UI Text Info Box
    viewport = glGetIntegerv(GL_VIEWPORT)
    draw_ui_box(particles.cloud_state, viewport[2], viewport[3])
=======
    # draw_night_overlay(phase)   # Dihapus agar siang terus
    draw_sea(time)              # 🌊 Laut bergelombang
>>>>>>> ca991069cdabe3776f220fa529e87e2108cf43e2


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
    print("  SPACE/P  : Pause/Resume")
    print("  ESC      : Keluar")

    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    is_focused = True
    is_paused = False

    while True:
        dt    = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key in (K_SPACE, K_p):
                    is_paused = not is_paused

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

        if not is_paused:
            time += dt
            particles.update(dt, time)

        render(camera, terrain, particles, time)
        pygame.display.flip()

        v_count, r_count = particles.stats()
        pause_text = " [PAUSED]" if is_paused else ""
        pygame.display.set_caption(
            f"{TITLE}{pause_text} | Uap: {v_count} | Hujan: {r_count} | FPS: {clock.get_fps():.0f}"
        )


if __name__ == "__main__":
    main()