import math
from OpenGL.GL import *

def draw_rainbow(alpha):
    if alpha <= 0.01: return
    
    glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_LIGHTING_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    colors = [
        (1.0, 0.0, 0.0),
        (1.0, 0.4, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.5, 1.0),
        (0.3, 0.0, 0.5),
        (0.6, 0.0, 1.0)
    ]
    
    center_x = -20.0  #DEPAN BELAKANG
    center_y = -2.0    # ✅ Lebih turun agar bawah terbenam ke tanah
    center_z = -9.0     # KIRI KANAN
    
    base_radius = 2.8
    thickness = 0.22
    segments = 40
    
    for i, color in enumerate(reversed(colors)):
        real_i = len(colors) - 1 - i
        r_inner = base_radius - (real_i + 1) * thickness
        r_outer = base_radius - real_i * thickness
        
        glBegin(GL_QUAD_STRIP)
        c_r, c_g, c_b = color
        for j in range(segments + 1):
            theta = math.pi * (j / segments)
            
            z_out = center_z + r_outer * math.cos(theta)
            y_out = center_y + r_outer * math.sin(theta)
            z_in  = center_z + r_inner * math.cos(theta)
            y_in  = center_y + r_inner * math.sin(theta)
            
            tilt = math.sin(theta) * 0.3
            
            fade_y = max(0.0, min(1.0, (y_out - center_y + 0.5) / 2.0))
            current_alpha = alpha * 0.45 * fade_y
            
            glColor4f(c_r, c_g, c_b, current_alpha)
            glVertex3f(center_x + tilt, y_out, z_out)
            glVertex3f(center_x + tilt, y_in,  z_in)
            
        glEnd()
        
    glPopAttrib()