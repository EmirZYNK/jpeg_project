import numpy as np

def adaptive_quantize_dwt(coeffs, compression_ratio):
    """
    Subband Adaptive Quantization:
    Düşük frekanslı ana resme (LL) dokunmaz, detay kanallarını agresifçe temizler.
    
    Güncelleme: compression_ratio <= 1 ise katsayıları olduğu gibi bırakarak 
    neredeyse kayıpsız (lossless) bir kalite sağlar.
    """
    
    # EĞER ÇARPAN 1 VE ALTINDAYSA (ORİJİNAL KALİTE), HİÇ BOZMADAN GERİ DÖNDÜR
    # Bu sayede yüksek BPP değerlerinde PSNR değeri kısıtlanmaz, yukarı fırlar.
    if compression_ratio <= 1:
        return coeffs 

    # Oran arttıkça threshold (eşik) karesel artar. 
    # Bölü 8 değeri, detayları daha dengeli temizlemek için optimize edilmiştir.
    threshold = (compression_ratio / 8) ** 2 
    
    new_coeffs = []
    
    # 1. LL Kanalı (Düşük Frekans) - Görüntünün ana hatları, burayı her zaman koruyoruz.
    new_coeffs.append(coeffs[0])
    
    # 2. Detay Kanalları (LH, HL, HH) - Çok seviyeli (Multi-level) yapı
    for i in range(1, len(coeffs)):
        # Her seviyedeki katsayıları eşik değerine göre filtrele.
        # Mutlak değeri eşikten küçük olan katsayılar 0 yapılır.
        level_coeffs = tuple(
            np.where(np.abs(c) < threshold, 0, c) for c in coeffs[i]
        )
        new_coeffs.append(level_coeffs)
        
    return new_coeffs