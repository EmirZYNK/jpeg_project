import pywt

def get_available_wavelets():
    """Desteklenen filtreleri döndürür."""
    return {
        'haar': 'haar',
        'db1': 'db1',
        'db2': 'db2',
        'bior4.4': 'bior4.4',
        'sym2': 'sym2'
    }

def get_filter_info(wavelet_name):
    """Filtre hakkında teknik bilgi verir (Hoca sorarsa diye)."""
    w = pywt.Wavelet(wavelet_name)
    return {
        'name': w.name,
        'family': w.family_name,
        'length': w.dec_len # Filtre boyu
    }