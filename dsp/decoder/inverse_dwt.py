import pywt
import numpy as np

def apply_idwt_2d(coeffs, wavelet='db1'):
    """
    Kuantize edilmiş dalgacık katsayılarını tekrar piksel haline getirir.
    """
    reconstructed = pywt.waverec2(coeffs, wavelet)
    
    # Değerleri 0-255 arasına sabitle ve tam sayı yap
    return np.clip(reconstructed, 0, 255).astype(np.uint8)