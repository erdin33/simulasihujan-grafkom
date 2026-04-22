import math
import numpy as np
import pyrr
from pygame.locals import K_w, K_s, K_a, K_d, K_q, K_e
from config import CAM_START_POS, CAM_START_YAW, CAM_START_PITCH, CAM_SPEED, CAM_SENS


class Camera:
    def __init__(self):
        self.pos   = pyrr.Vector3(CAM_START_POS, dtype=float)
        self.yaw   = CAM_START_YAW
        self.pitch = CAM_START_PITCH
        self.speed = CAM_SPEED
        self.sens  = CAM_SENS
        self._update_vectors()

    def _update_vectors(self):
        yr = math.radians(self.yaw)
        pr = math.radians(self.pitch)

        front = np.array([
            math.cos(yr) * math.cos(pr),
            math.sin(pr),
            math.sin(yr) * math.cos(pr),
        ], dtype=float)

        self.front = pyrr.Vector3(front / np.linalg.norm(front))

        world_up = np.array([0.0, 1.0, 0.0])

        right = np.cross(self.front, world_up)
        self.right = pyrr.Vector3(right / np.linalg.norm(right))

        up = np.cross(self.right, self.front)
        self.up = pyrr.Vector3(up / np.linalg.norm(up))

    def rotate(self, dx, dy):
        self.yaw   += dx * self.sens
        self.pitch -= dy * self.sens

        self.pitch = max(-89.0, min(89.0, self.pitch))
        self._update_vectors()

    def move(self, keys):
        if keys[K_w]: self.pos += self.front * self.speed
        if keys[K_s]: self.pos -= self.front * self.speed
        if keys[K_a]: self.pos -= self.right * self.speed
        if keys[K_d]: self.pos += self.right * self.speed
        if keys[K_q]: self.pos[1] -= self.speed
        if keys[K_e]: self.pos[1] += self.speed

    def get_view_matrix(self):
        eye    = np.array(self.pos)
        target = eye + np.array(self.front)
        up     = np.array(self.up)

        return pyrr.matrix44.create_look_at(eye, target, up, dtype=np.float32)