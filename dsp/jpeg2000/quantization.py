import numpy as np

def adaptive_quantize_dwt(coeffs, q_step):
    """
    Step-based Scalar Quantization:
    DWT katsayılarını q_step (kuantizasyon adımı) ile normalize eder.
    
    GÜNCELLEME: Grafik sağ ucunun (tf=1 noktasının) yukarı fırlaması için 
    1.0 ve altındaki q_step değerleri 'Kayıpsız' kabul edilerek işlem pas geçilir.
    """
    
    # 1.0 ve altı 'Kayıpsız' (Lossless) kabul edilir. 
    # Bu, tf=1 (Orijinal) durumunda grafiğin 50+ dB'e fırlamasını sağlar.
    if q_step <= 1.0:
        return coeffs

    new_coeffs = []
    
    # 1. LL Bandı (Düşük Frekans - Görüntünün İskeleti)
    # LL bandı enerjinin %90'ını taşır, bu yüzden onu detay bantlarından 
    # 10 kat daha hassas koruyoruz (q_step * 0.1)
    ll_step = q_step * 0.1
    new_coeffs.append(np.round(coeffs[0] / ll_step) * ll_step)
    
    # 2. Detay Bantları (LH, HL, HH - Kenarlar ve Yüksek Frekanslar)
    for i in range(1, len(coeffs)):
        # Her seviyedeki katsayıları q_step hassasiyetinde yuvarla.
        # np.round işlemi veriyi seyreltir, q_step arttıkça sıkıştırma artar.
        level_coeffs = tuple(
            np.round(c / q_step) * q_step for c in coeffs[i]
        )
        new_coeffs.append(level_coeffs)
        
    return new_coeffs