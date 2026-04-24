# dsp/jpeg2000/wavelet_filters.py

import pywt

def get_wavelet(wavelet_name: str) -> pywt.Wavelet:
    """
    Frontend'den gelen dalgacık ismini (string) alıp PyWavelets nesnesine çevirir.
    
    Desteklenen filtreler: 'haar', 'db4', 'db8'
    """
    # UI'dan gelen değerleri PyWavelets karşılıklarına eşleştiriyoruz
    valid_wavelets = {
        'haar': 'haar',
        'db4': 'db4',
        'db8': 'db8'
    }
    
    if wavelet_name.lower() not in valid_wavelets:
        # Desteklenmeyen bir filtre gelirse varsayılan olarak haar kullan
        print(f"Uyarı: '{wavelet_name}' desteklenmiyor. 'haar' filtresine geçiliyor.")
        return pywt.Wavelet('haar')
        
    return pywt.Wavelet(valid_wavelets[wavelet_name.lower()])

def get_max_level(image_shape, wavelet_name: str) -> int:
    """
    Verilen resim boyutu ve filtreye göre uygulanabilecek maksimum DWT seviyesini döndürür.
    Bu, kullanıcının UI'dan girdiği DWT Level'ı valide etmek için faydalıdır.
    """
    wavelet = get_wavelet(wavelet_name)
    return pywt.dwt_max_level(data_len=min(image_shape), filter_len=wavelet.dec_len)