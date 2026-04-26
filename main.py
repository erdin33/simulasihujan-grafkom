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
from sky_clouds import draw_sky, draw_clouds

# ─── Import modul baru ───
from mountain import draw_mountain
from river    import draw_river, draw_underground_flow
from trees    import draw_trees, draw_bushes


# ================= SETUP OPENGL =================
def setup_opengl(w, h):
    glClearColor(0.10, 0.25, 0.55, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, w / h, 0.1, 300.0)
    glMatrixMode(GL_MODELVIEW)


# ================= RENDER =================
def render(camera, terrain, particles, time):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_sky()

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
    draw_sea()                  # 🌊 Laut
    terrain.draw()              # 🟩 Terrain darat (hijau)

    draw_underground_flow()     # 💧 Aliran bawah tanah

    draw_river()                # 🏞️ Sungai (di atas terrain)
    draw_mountain()             # ⛰️ Gunung + bukit kecil
    draw_trees()                # 🌳 Pohon-pohon
    draw_bushes()               # 🌿 Semak-semak

    draw_clouds(time)           # ☁️ Awan
    particles.draw()            # 💨 Partikel uap & hujan


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

        particles.update(dt)

        render(camera, terrain, particles, time)
        pygame.display.flip()

        v_count, r_count = particles.stats()
        pygame.display.set_caption(
            f"{TITLE} | Uap: {v_count} | Hujan: {r_count} | FPS: {clock.get_fps():.0f}"
        )


if __name__ == "__main__":
    main()