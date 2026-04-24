# dsp/jpeg2000/dwt.py

import pywt
import numpy as np
from .wavelet_filters import get_wavelet, get_max_level

def apply_dwt_2d(image_data: np.ndarray, wavelet_name: str = 'haar', level: int = 3):
    """
    Görüntüye 2D Ayrık Dalgacık Dönüşümü (DWT) uygular.
    
    Args:
        image_data: 2D Numpy dizisi (Örn: 512x512 gri tonlamalı resim)
        wavelet_name: Kullanılacak filtre ('haar', 'db4', 'db8')
        level: Ayrıştırma seviyesi (DWT Level, UI'dan 1-5 arası geliyor)
        
    Returns:
        coeffs: PyWavelets wavedec2 yapısı. 
        [cA_n, (cH_n, cV_n, cD_n), ..., (cH_1, cV_1, cD_1)]
    """
    wavelet = get_wavelet(wavelet_name)
    
    # Kullanıcının seçtiği level, resmin boyutu için çok büyükse güvenli limite çek
    max_safe_level = get_max_level(image_data.shape, wavelet_name)
    safe_level = min(level, max_safe_level)
    
    if safe_level != level:
        print(f"Uyarı: Level {level} çok yüksek. Güvenli seviye olan {safe_level} kullanılıyor.")
    
    # Çok seviyeli 2D DWT işlemi
    # mode='symmetric', görüntünün sınırlarında oluşan artefaktları engellemek için standarttır
    coeffs = pywt.wavedec2(image_data, wavelet, mode='symmetric', level=safe_level)
    
    return coeffs