import pywt

def reconstruct_dwt_2d(coeffs, wavelet_name='db4'):
    # Emir'den gelen katsayıları görsele dönüştürür
    return pywt.waverec2(coeffs, wavelet=wavelet_name)