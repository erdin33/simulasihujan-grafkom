import math
from pyrr import Vector3, vector3, vector, matrix44
from pygame.locals import K_w, K_s, K_a, K_d, K_q, K_e, K_LSHIFT
from config import CAM_START_POS, CAM_START_YAW, CAM_START_PITCH, CAM_SPEED, CAM_SENS

class Camera:
    def __init__(self):
        # Initialize natively as Pyrr Vector3 (which are numpy arrays under the hood)
        self.pos      = Vector3(CAM_START_POS, dtype=float)
        self.world_up = Vector3([0.0, 1.0, 0.0], dtype=float) 
        
        self.yaw      = CAM_START_YAW
        self.pitch    = CAM_START_PITCH
        self.speed    = CAM_SPEED
        self.sens     = CAM_SENS
        
        self._update_vectors()

    def _update_vectors(self):
        yr = math.radians(self.yaw)
        pr = math.radians(self.pitch)
        
        # Cache cos(pr) to avoid computing it twice
        cos_pr = math.cos(pr)

        # 1. Front vector is inherently normalized when derived from spherical coordinates
        self.front = Vector3([
            math.cos(yr) * cos_pr,
            math.sin(pr),
            math.sin(yr) * cos_pr
        ])

        # 2. Right vector needs normalization (world_up and front might not be 90 degrees)
        # Use pyrr's native cross product and normalize functions
        right = vector3.cross(self.front, self.world_up)
        self.right = vector.normalize(right)

        # 3. Up vector is inherently normalized (cross product of two orthogonal unit vectors)
        self.up = vector3.cross(self.right, self.front)

    def rotate(self, dx, dy):
        self.yaw   += dx * self.sens
        self.pitch -= dy * self.sens

        # Clamp pitch to prevent screen flipping (gimbal lock)
        self.pitch = max(-89.0, min(89.0, self.pitch))
        self._update_vectors()

    def move(self, keys):
        if keys[K_LSHIFT]:
            current_speed = self.speed * 3.0
        else:
            current_speed = self.speed
        # Pyrr Vector3 objects handle scalar multiplication and addition natively
        if keys[K_w]: self.pos += self.front * current_speed
        if keys[K_s]: self.pos -= self.front * current_speed
        if keys[K_a]: self.pos -= self.right * current_speed
        if keys[K_d]: self.pos += self.right * current_speed
        
        # Use .y property for cleaner access
        if keys[K_q]: self.pos.y -= current_speed
        if keys[K_e]: self.pos.y += current_speed

    def get_view_matrix(self):
        # Remove all redundant numpy conversions. 
        # Pyrr's create_look_at natively accepts Pyrr vectors.
        target = self.pos + self.front
        return matrix44.create_look_at(self.pos, target, self.up, dtype=float)