"""
Sample image generator for offline testing & demonstration.
Creates synthetic face scan test images in samples/ directory.
"""

import cv2
import numpy as np
from pathlib import Path
import config

def generate_sample_faces():
    samples_dir = config.SAMPLES_DIR
    samples_dir.mkdir(exist_ok=True)

    def draw_face(bg_color, skin_color, eye_color, hair_color, text_name):
        img = np.ones((400, 400, 3), dtype=np.uint8) * np.array(bg_color, dtype=np.uint8)
        
        # Face shape
        cv2.ellipse(img, (200, 200), (90, 120), 0, 0, 360, skin_color, -1)
        
        # Hair
        cv2.ellipse(img, (200, 140), (95, 60), 0, 180, 360, hair_color, -1)
        
        # Eyes
        cv2.ellipse(img, (160, 180), (15, 10), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(img, (240, 180), (15, 10), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(img, (160, 180), 6, eye_color, -1)
        cv2.circle(img, (240, 180), 6, eye_color, -1)
        
        # Eyebrows
        cv2.line(img, (140, 160), (180, 165), hair_color, 3)
        cv2.line(img, (220, 165), (260, 160), hair_color, 3)

        # Nose
        cv2.line(img, (200, 185), (195, 220), (100, 100, 150), 2)
        cv2.line(img, (195, 220), (205, 220), (100, 100, 150), 2)

        # Mouth
        cv2.ellipse(img, (200, 260), (35, 15), 0, 0, 180, (50, 50, 200), -1)

        # Label text
        cv2.putText(img, text_name, (20, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2)

        return img

    face1 = draw_face((40, 30, 20), (180, 210, 240), (120, 60, 20), (30, 30, 30), "Subject Alpha (@arivera_ai)")
    face2 = draw_face((30, 40, 30), (160, 190, 220), (40, 120, 40), (20, 80, 120), "Subject Beta (@elena_tech)")
    face3 = draw_face((50, 20, 40), (190, 215, 245), (150, 50, 150), (10, 10, 10), "Subject Gamma (@marcus_vance)")

    cv2.imwrite(str(samples_dir / "sample_face_1.jpg"), face1)
    cv2.imwrite(str(samples_dir / "sample_face_2.jpg"), face2)
    cv2.imwrite(str(samples_dir / "sample_face_3.jpg"), face3)

    print(f"Generated 3 sample face images in {samples_dir}")

if __name__ == "__main__":
    generate_sample_faces()
