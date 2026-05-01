import pywt
import numpy as np
# Yeni modülden kuantizasyon fonksiyonunu içeri aktarıyoruz
# Not: quantization.py dosyasını oluşturduğundan emin olmalısın
from dsp.jpeg2000.quantization import adaptive_quantize_dwt

def apply_dwt_2d(image_channel, wavelet='bior4.4', level=2):
    """
    Görüntü kanalına Multi-level (Çok Seviyeli) 2 Boyutlu 
    Dalgacık Dönüşümü (DWT) uygular.
    
    Args:
        image_channel: İşlenecek kanal (Y, Cb veya Cr)
        wavelet: Kullanılacak ana dalgacık (haar, db1, bior4.4 vb.)
        level: Dekompozisyon derinliği
    """
    # pywt.wavedec2 fonksiyonu çok seviyeli dönüşümü otomatik yapar
    coeffs = pywt.wavedec2(image_channel, wavelet, level=level)
    return coeffs

# quantize_dwt fonksiyonu buradan kaldırıldı! 
# Artık dsp/jpeg2000/quantization.py içinde daha gelişmiş haliyle bulunuyor.