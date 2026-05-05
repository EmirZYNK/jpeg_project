import cv2
import numpy as np


def generate_error_map(original, reconstructed):
    if original is None or reconstructed is None:
        return np.zeros((100, 100, 3), dtype=np.uint8)

    if original.shape[:2] != reconstructed.shape[:2]:
        reconstructed = cv2.resize(
            reconstructed,
            (original.shape[1], original.shape[0])
        )

    if original.dtype != np.uint8:
        original = np.clip(original, 0, 255).astype(np.uint8)

    if reconstructed.dtype != np.uint8:
        reconstructed = np.clip(reconstructed, 0, 255).astype(np.uint8)

    if len(original.shape) == 2:
        original = cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)

    if len(reconstructed.shape) == 2:
        reconstructed = cv2.cvtColor(reconstructed, cv2.COLOR_GRAY2BGR)

    if original.shape[2] != reconstructed.shape[2]:
        reconstructed = reconstructed[:, :, :3]

    diff = cv2.absdiff(original, reconstructed)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    if np.max(diff_gray) == 0:
        return np.zeros_like(original)

    diff_gray = np.clip(diff_gray * 5, 0, 255).astype(np.uint8)
    diff_color = cv2.applyColorMap(diff_gray, cv2.COLORMAP_INFERNO)

    return diff_color