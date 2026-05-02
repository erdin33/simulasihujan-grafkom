# day_night.py
import math
from OpenGL.GL import *
from OpenGL.GLU import *

CYCLE_DURATION = 30.0  # 1 hari penuh = 30 detik

def get_day_phase(time):
    """Mengembalikan nilai 0.0 s/d 1.0 (0=Pagi, 0.5=Malam, 1.0=Pagi lagi)"""
    return (time % CYCLE_DURATION) / CYCLE_DURATION

def get_sky_colors(phase):
    """Mengembalikan warna langit bawah dan atas berdasarkan fase hari"""
    
    # Warna didefinisikan (Bawah, Atas)
    C_DAY    = ((0.35, 0.55, 0.85), (0.10, 0.25, 0.60))
    C_SUNSET = ((0.80, 0.40, 0.20), (0.30, 0.20, 0.40))
    C_NIGHT  = ((0.05, 0.05, 0.12), (0.01, 0.01, 0.05))
    C_SUNRISE= ((0.60, 0.40, 0.30), (0.20, 0.25, 0.50))
    
    # 0.0=Sunrise, 0.25=Day, 0.5=Sunset, 0.75=Night, 1.0=Sunrise
    if phase < 0.25:
        # Sunrise -> Day
        t = phase / 0.25
        return _lerp_colors(C_SUNRISE, C_DAY, t)
    elif phase < 0.5:
        # Day -> Sunset
        t = (phase - 0.25) / 0.25
        return _lerp_colors(C_DAY, C_SUNSET, t)
    elif phase < 0.75:
        # Sunset -> Night
        t = (phase - 0.5) / 0.25
        return _lerp_colors(C_SUNSET, C_NIGHT, t)
    else:
        # Night -> Sunrise
        t = (phase - 0.75) / 0.25
        return _lerp_colors(C_NIGHT, C_SUNRISE, t)

def _lerp_color(c1, c2, t):
    return (
        c1[0] + (c2[0] - c1[0]) * t,
        c1[1] + (c2[1] - c1[1]) * t,
        c1[2] + (c2[2] - c1[2]) * t,
    )

def _lerp_colors(c_tuple1, c_tuple2, t):
    bot = _lerp_color(c_tuple1[0], c_tuple2[0], t)
    top = _lerp_color(c_tuple1[1], c_tuple2[1], t)
    return bot, top

def draw_night_overlay(phase):
    """Menggambar quad transparan untuk meredupkan layar saat malam"""
    glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_LIGHTING_BIT)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Hitung tingkat kegelapan berdasarkan cosine wave
    # phase 0.75 adalah tengah malam (tergelap)
    # phase 0.25 adalah tengah hari (terang benderang)
    darkness = math.cos((phase - 0.75) * 2.0 * math.pi)
    
    if darkness > 0.0:
        alpha = darkness * 0.70  # Maksimal 70% opacity malam
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1, 0, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Warna biru malam/hitam
        glColor4f(0.02, 0.02, 0.10, alpha)
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
