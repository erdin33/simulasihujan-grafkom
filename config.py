# ============================================================
#  config.py — Semua konstanta dan konfigurasi global
# ============================================================

# Window
WINDOW_W    = 1000
WINDOW_H    = 700
FPS         = 60
TITLE       = "Simulasi Siklus Air — OpenGL"

# Terrain
TERRAIN_SIZE  = 60      # Grid NxN
TERRAIN_SCALE = 0.5     # Jarak antar titik (unit OpenGL)
SEA_LIMIT     = 0.38    # Fraksi grid yang jadi laut (kiri)

# Partikel
MAX_VAPOR       = 600
MAX_RAIN        = 800
CLOUD_HEIGHT    = 7.0   # Ketinggian awan terbentuk (Y)
VAPOR_SPEED_Y   = 0.05  # Kecepatan naik uap
RAIN_SPEED_Y    = 0.10  # Kecepatan turun hujan

# Kamera (posisi awal)
CAM_START_POS   = [0.0, 5.0, 15.0]   # X, Y, Z
CAM_START_YAW   = -90.0              # Menghadap -Z (ke terrain)
CAM_START_PITCH = 0.0              # Sedikit nunduk ke bawah
CAM_SPEED       = 0.2
CAM_SENS        = 0.1

# Warna langit (bawah → atas)
SKY_BOTTOM = (0.35, 0.55, 0.85)
SKY_TOP    = (0.10, 0.25, 0.60)