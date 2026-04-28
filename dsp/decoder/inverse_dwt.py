import pywt
import numpy as np

# Filtreyi alabilmek için jpeg2000 klasöründeki modülü çağırıyoruz
from dsp.jpeg2000.wavelet_filters import get_wavelet

def apply_idwt_2d(coeffs: list, wavelet_name: str = 'haar'):
    """
    DWT katsayıları listesini (Aproksimasyon ve Detay matrisleri) alıp 
    Ters 2D Ayrık Dalgacık Dönüşümü (IDWT) uygular.
    
    Args:
        coeffs: PyWavelets formatındaki katsayı listesi.
        wavelet_name: Geri dönüşümde kullanılacak filtre (örn: 'haar', 'db4').
        
    Returns:
        reconstructed_image: Yeniden oluşturulmuş 2D piksel matrisi.
    """
    wavelet = get_wavelet(wavelet_name)
    
    # waverec2: 2D Inverse Discrete Wavelet Transform (Yeniden Yapılandırma)
    # mode='symmetric', sınır artefaktlarını önlemek için ileri dönüşümle aynı olmalıdır.
    reconstructed_image = pywt.waverec2(coeffs, wavelet, mode='symmetric')
    
    return reconstructed_image