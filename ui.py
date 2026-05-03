import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

def get_stage_text(state):
    # Penjelasan proses logika siklus air sesuai permintaan
    if state == "CLEAR":
        return "FASE: MENUNGGU\n\nSiklus hujan telah selesai.\nMenunggu air menguap kembali."
    elif state == "EVAPORATING":
        return "FASE: EVAPORASI\n\nAir menguap karena panas\nmatahari (evaporasi)."
    elif state == "CLOUDING":
        return "FASE: KONDENSASI\n\nUap air naik ke atmosfer dan\nmembentuk awan (kondensasi).\nAwan menjadi tebal dan gelap."
    elif state == "RAINING":
        return "FASE: PRESIPITASI\n\nSaat awan sudah jenuh,\nturunlah hujan (presipitasi)."
    elif state == "RETURNING":
        return "FASE: SIKLUS BERULANG\n\nAwan kosong kembali ke laut\nuntuk memulai siklus baru."
    return ""

def draw_text_with_shadow(surface, text, font, color, pos):
    shadow_surface = font.render(text, True, (0, 0, 0))
    surface.blit(shadow_surface, (pos[0] + 1, pos[1] + 1))  # Shadow lebih tipis
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

def draw_ui_box(state, screen_w, screen_h):
    text_str = get_stage_text(state)
    lines = text_str.split('\n')
    
    pygame.font.init()
    # Menggunakan default font Pygame (freesansbold) yang sangat bersih & tajam
    title_font = pygame.font.Font(None, 20)
    body_font = pygame.font.Font(None, 18)
    
    # Calculate box size (Dibuat jauh lebih kecil)
    box_w = 230
    title_h = title_font.get_height() + 6
    body_h = body_font.get_height() + 2
    box_h = title_h + (len(lines) - 1) * body_h + 20
    
    surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    
    # Shadow box
    pygame.draw.rect(surface, (0, 0, 0, 60), (3, 3, box_w, box_h), border_radius=8)
    # Background box (hitam transparan, lebih simpel dan modern)
    pygame.draw.rect(surface, (20, 20, 25, 200), (0, 0, box_w, box_h), border_radius=8)
    # Border
    pygame.draw.rect(surface, (180, 200, 220, 150), (0, 0, box_w, box_h), 1, border_radius=8)
    
    y_offset = 12
    for i, line in enumerate(lines):
        if i == 0:
            color = (120, 200, 255)
            draw_text_with_shadow(surface, line, title_font, color, (15, y_offset))
            y_offset += title_h
            # Garis bawah yang simpel
            pygame.draw.line(surface, (120, 200, 255, 100), (15, y_offset - 3), (box_w - 15, y_offset - 3), 1)
        else:
            color = (240, 240, 240)
            draw_text_with_shadow(surface, line, body_font, color, (15, y_offset))
            y_offset += body_h
            
    text_data = pygame.image.tostring(surface, "RGBA", True)
    
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_w, 0, screen_h)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Gambar di Kiri Bawah layar
    draw_x = 20
    draw_y = 20
    glRasterPos2i(draw_x, draw_y)
    glDrawPixels(box_w, box_h, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()
