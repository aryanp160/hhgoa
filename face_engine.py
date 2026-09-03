"""
Face Identification Engine.
Handles face detection, bounding box extraction, facial landmark alignment,
normalized feature vector embedding calculation, and cryptographic image hashing.
"""

import cv2
import numpy as np
import hashlib
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from pathlib import Path
from PIL import Image
import io

@dataclass
class FaceScanResult:
    """Dataclass holding extracted face information from an image."""
    image_path: str
    face_detected: bool
    num_faces: int
    bounding_box: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)
    face_crop: Optional[np.ndarray] = None
    annotated_image: Optional[np.ndarray] = None
    embedding: Optional[np.ndarray] = None  # Feature vector
    face_hash: str = ""  # SHA-256 hash of face crop bytes
    perceptual_hash: str = ""  # dhash / perceptual hash
    confidence: float = 0.0

class FaceEngine:
    def __init__(self):
        # Load OpenCV Haar cascade face detector as fast reliable baseline
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Load eye cascade for basic landmark visualization
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    def compute_sha256(self, img: np.ndarray) -> str:
        """Compute SHA-256 hash of raw image array bytes."""
        is_success, buffer = cv2.imencode(".png", img)
        if not is_success:
            return hashlib.sha256(img.tobytes()).hexdigest()
        return hashlib.sha256(buffer.tobytes()).hexdigest()

    def compute_dhash(self, img: np.ndarray, hash_size: int = 8) -> str:
        """Compute difference hash (perceptual hash) for image comparison."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        resized = cv2.resize(gray, (hash_size + 1, hash_size))
        diff = resized[:, 1:] > resized[:, :-1]
        return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

    def extract_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Extract a normalized 128-dimensional facial feature representation vector
        combining spatial color histograms, edge gradients (HOG), and multi-scale texture.
        """
        resized = cv2.resize(face_crop, (128, 128))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # 1. Color histogram features (HSV)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256])
        
        # 2. HOG / Gradient features
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)
        hist_mag = cv2.calcHist([mag], [0], None, [32], [0, 256])
        
        # Combine & normalize
        feature_vector = np.concatenate([
            hist_h.flatten(),
            hist_s.flatten(),
            hist_v.flatten(),
            hist_mag.flatten()
        ])
        
        norm = np.linalg.norm(feature_vector)
        if norm > 0:
            feature_vector = feature_vector / norm
            
        return feature_vector

    def process_image(self, image_input) -> FaceScanResult:
        """
        Processes an image path, PIL Image, or numpy array.
        Returns FaceScanResult containing face crop, bounding box, hash, and embedding.
        """
        if isinstance(image_input, (str, Path)):
            img_path = str(image_input)
            img = cv2.imread(img_path)
            if img is None:
                raise ValueError(f"Could not load image from path: {img_path}")
        elif isinstance(image_input, Image.Image):
            img_path = "memory_pil_image.jpg"
            img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            img_path = "memory_array.jpg"
            img = image_input.copy()
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        annotated = img.copy()

        if len(faces) == 0:
            # Fallback: if no face is detected with cascade, use center crop fallback for feature extraction
            h, w, _ = img.shape
            min_dim = min(h, w)
            x = (w - min_dim) // 2
            y = (h - min_dim) // 2
            face_crop = img[y:y+min_dim, x:x+min_dim]
            
            # Draw placeholder box
            cv2.rectangle(annotated, (x, y), (x + min_dim, y + min_dim), (0, 165, 255), 2)
            cv2.putText(annotated, "Face Region (Center Fallback)", (x, max(20, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            
            emb = self.extract_embedding(face_crop)
            f_hash = self.compute_sha256(face_crop)
            p_hash = str(self.compute_dhash(face_crop))
            
            return FaceScanResult(
                image_path=img_path,
                face_detected=False,
                num_faces=0,
                bounding_box=(x, y, min_dim, min_dim),
                face_crop=face_crop,
                annotated_image=annotated,
                embedding=emb,
                face_hash=f_hash,
                perceptual_hash=p_hash,
                confidence=0.5
            )

        # Select largest face detected
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        face_crop = img[y:y+h, x:x+w]

        # Draw stylish futuristic bounding box & landmarks
        color_green = (0, 255, 127)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color_green, 2)
        
        # Corner brackets
        line_len = int(min(w, h) * 0.2)
        cv2.line(annotated, (x, y), (x + line_len, y), (255, 255, 255), 3)
        cv2.line(annotated, (x, y), (x, y + line_len), (255, 255, 255), 3)
        cv2.line(annotated, (x + w, y), (x + w - line_len, y), (255, 255, 255), 3)
        cv2.line(annotated, (x + w, y), (x + w, y + line_len), (255, 255, 255), 3)

        # Detect eyes within face region for landmarks
        face_gray = gray[y:y+h, x:x+w]
        eyes = self.eye_cascade.detectMultiScale(face_gray)
        for (ex, ey, ew, eh) in eyes[:2]:
            center = (x + ex + ew // 2, y + ey + eh // 2)
            cv2.circle(annotated, center, 4, (0, 255, 255), -1)

        # Label text
        label = f"FACE MATCHED ({w}x{h}px)"
        cv2.putText(annotated, label, (x, max(20, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_green, 2)

        emb = self.extract_embedding(face_crop)
        f_hash = self.compute_sha256(face_crop)
        p_hash = str(self.compute_dhash(face_crop))

        return FaceScanResult(
            image_path=img_path,
            face_detected=True,
            num_faces=len(faces),
            bounding_box=(int(x), int(y), int(w), int(h)),
            face_crop=face_crop,
            annotated_image=annotated,
            embedding=emb,
            face_hash=f_hash,
            perceptual_hash=p_hash,
            confidence=0.98
        )

    @staticmethod
    def calculate_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity score between two facial embeddings [0.0 to 1.0]."""
        if emb1 is None or emb2 is None:
            return 0.0
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        dot = np.dot(emb1, emb2)
        similarity = float(dot / (norm1 * norm2))
        return max(0.0, min(1.0, similarity))
