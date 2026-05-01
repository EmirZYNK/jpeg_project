import numpy as np

def normalize_pixels(image_np):
    """Pikselleri 0-1 aralığına normalize eder."""
    return image_np.astype(np.float32) / 255.0

def denormalize_pixels(norm_np):
    """Normalize veriyi tekrar 0-255 aralığına çeker."""
    return np.clip(norm_np * 255, 0, 255).astype(np.uint8)