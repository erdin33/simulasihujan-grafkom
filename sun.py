# sun.py
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from day_night import get_day_phase

def draw_sun_and_moon(time):
    """Gambar Matahari statis (siang terus)"""
    phase = 0.25 #get_day_phase(time)
    
    glDisable(GL_LIGHTING) # Benda angkasa bersinar sendiri
    glDepthMask(GL_FALSE)  # Render di belakang segalanya tanpa tulis depth
    
    # Radius orbit
    orbit_r = 16.0
    
    # Sudut orbit matahari: terbit dari kanan (X=orbit_r) ke kiri
    sun_angle = phase * 2.0 * math.pi
    sun_x = orbit_r * math.cos(sun_angle)
    sun_y = orbit_r * math.sin(sun_angle)
    sun_z = -8.0  # Latar belakang
    
    # Sudut bulan selalu berkebalikan
    moon_angle = sun_angle + math.pi
    moon_x = orbit_r * math.cos(moon_angle)
    moon_y = orbit_r * math.sin(moon_angle)
    moon_z = -8.0

    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    
    # ─── Gambar Matahari ───
    if sun_y > -4.0: # Render sampai sedikit di bawah horizon
        glPushMatrix()
        glTranslatef(sun_x, sun_y, sun_z)
        
        # Warna matahari
        glColor3f(1.0, 0.9, 0.1)
        gluSphere(quadric, 2.0, 32, 32)
        
        # Glow
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 0.8, 0.1, 0.4)
        gluSphere(quadric, 2.8, 32, 32)
        glDisable(GL_BLEND)
        
        glPopMatrix()

    # ─── Gambar Bulan ───
    if moon_y > -4.0:
        glPushMatrix()
        glTranslatef(moon_x, moon_y, moon_z)
        
        # Warna bulan
        glColor3f(0.8, 0.8, 0.9)
        gluSphere(quadric, 1.2, 32, 32)
        
        # Glow bulan
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.8, 0.8, 0.9, 0.3)
        gluSphere(quadric, 1.8, 32, 32)
        glDisable(GL_BLEND)
        
        glPopMatrix()

    gluDeleteQuadric(quadric)
    glDepthMask(GL_TRUE)
