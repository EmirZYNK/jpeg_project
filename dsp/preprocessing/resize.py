import cv2

def smart_resize(image_np, target_size=(512, 512)):
    """Görüntüyü analiz için istenen boyuta getirir."""
    return cv2.resize(image_np, target_size, interpolation=cv2.INTER_AREA)