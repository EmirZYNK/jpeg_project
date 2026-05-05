import numpy as np

def normalize_image(image):
    """
    Image'i [0,1] aralığına çeker
    """
    return image.astype(np.float32) / 255.0


def denormalize_image(image):
    """
    [0,1] aralığındaki image'i tekrar [0,255] uint8'e çevirir
    """
    return np.clip(image * 255, 0, 255).astype(np.uint8)