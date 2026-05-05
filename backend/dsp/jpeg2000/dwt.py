import numpy as np
import pywt


def apply_dwt_2d(image_gray, wavelet="haar", level=2):
    coeffs = pywt.wavedec2(
        image_gray.astype(np.float32),
        wavelet=wavelet,
        level=level
    )
    return coeffs


def apply_idwt_2d(coeffs, wavelet="haar", original_shape=None):
    reconstructed = pywt.waverec2(coeffs, wavelet=wavelet)

    if original_shape is not None:
        reconstructed = reconstructed[:original_shape[0], :original_shape[1]]

    return reconstructed