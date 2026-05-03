import math
from OpenGL.GL import *

def draw_rainbow(alpha):
    if alpha <= 0.01: return
    
    glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_LIGHTING_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST) # Digambar di latar belakang
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Warna-warna pelangi (Merah, Jingga, Kuning, Hijau, Biru, Nila, Ungu)
    colors = [
        (1.0, 0.0, 0.0), # Merah
        (1.0, 0.4, 0.0), # Jingga
        (1.0, 1.0, 0.0), # Kuning
        (0.0, 1.0, 0.0), # Hijau
        (0.0, 0.5, 1.0), # Biru
        (0.3, 0.0, 0.5), # Nila
        (0.6, 0.0, 1.0)  # Ungu
    ]
    
    # Posisi pelangi melengkung melintasi sungai (menghubungkan hutan kiri dan bukit kanan)
    center_x = -7.5
    center_y = -1.0
    center_z = -10.0
    
    # Radius disesuaikan agar pas menjadi jembatan
    base_radius = 8.0
    thickness = 0.35
    
    segments = 40
    
    # Tambahkan sedikit offset Z agar tidak clipping
    for i, color in enumerate(colors):
        r_inner = base_radius - (i + 1) * thickness
        r_outer = base_radius - i * thickness
        
        glBegin(GL_QUAD_STRIP)
        c_r, c_g, c_b = color
        for j in range(segments + 1):
            theta = math.pi * (j / segments) # Setengah lingkaran
            
            x_out = center_x + r_outer * math.cos(theta)
            y_out = center_y + r_outer * math.sin(theta)
            
            x_in = center_x + r_inner * math.cos(theta)
            y_in = center_y + r_inner * math.sin(theta)
            
            # Agar pelangi terlihat pudar secara natural di dekat tanah
            fade_y = max(0.0, min(1.0, (y_out - 1.0) / 6.0))
            current_alpha = alpha * 0.45 * fade_y  # Maksimal 45% transparan
            
            glColor4f(c_r, c_g, c_b, current_alpha)
            glVertex3f(x_out, y_out, center_z)
            glVertex3f(x_in, y_in, center_z)
            
        glEnd()
        
    glPopAttrib()
