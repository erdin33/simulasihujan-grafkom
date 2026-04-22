import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from config import WINDOW_W, WINDOW_H, FPS, TITLE
from camera import Camera
from terrain import Terrain, draw_sea
from particles import ParticleSystem
from sky_clouds import draw_sky, draw_clouds


# ================= SETUP OPENGL =================
def setup_opengl():
    glClearColor(0.10, 0.25, 0.55, 1.0)

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WINDOW_W / WINDOW_H, 0.1, 300.0)

    glMatrixMode(GL_MODELVIEW)


# ================= RENDER =================
def render(camera, terrain, particles, time):
    # CLEAR
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # SKY (background)
    draw_sky()

    # CAMERA
    glLoadIdentity()

    eye    = camera.pos
    target = camera.pos + camera.front
    up     = camera.up

    gluLookAt(
        eye[0], eye[1], eye[2],
        target[0], target[1], target[2],
        up[0], up[1], up[2]
    )

    # ================= SCENE =================
    draw_sea()        # 🌊 LAUT FLAT (penting di sini)
    terrain.draw()    # ⛰️ DARAT
    draw_clouds(time)
    particles.draw()


# ================= MAIN =================
def main():
    pygame.init()
    pygame.display.set_mode((WINDOW_W, WINDOW_H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(TITLE)

    setup_opengl()

    camera    = Camera()
    terrain   = Terrain()
    particles = ParticleSystem(terrain)

    clock = pygame.time.Clock()
    time  = 0.0

    print("=== SIMULASI SIKLUS AIR ===")

    while True:
        dt    = clock.tick(FPS) / 1000.0
        time += dt

        # EVENT
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # INPUT
        keys = pygame.key.get_pressed()
        camera.move(keys)

        # UPDATE
        particles.update(dt)

        # RENDER
        render(camera, terrain, particles, time)
        pygame.display.flip()

        # INFO
        v_count, r_count = particles.stats()
        pygame.display.set_caption(
            f"{TITLE} | Uap: {v_count} | Hujan: {r_count} | FPS: {clock.get_fps():.0f}"
        )


if __name__ == "__main__":
    main()