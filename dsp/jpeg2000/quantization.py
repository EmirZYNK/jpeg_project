import numpy as np

def adaptive_quantize_dwt(coeffs, compression_ratio):
    """
    Subband Adaptive Quantization:
    Düşük frekanslı ana resme (LL) dokunmaz, 
    detay kanallarını (LH, HL, HH) agresifçe temizler.
    """
    # Oran arttıkça threshold (eşik) karesel artar
    threshold = (compression_ratio / 10) ** 2 
    
    new_coeffs = []
    # 1. LL Kanalı (Düşük Frekans) - Burayı koruyoruz
    new_coeffs.append(coeffs[0])
    
    # 2. Detay Kanalları (Multi-level)
    for i in range(1, len(coeffs)):
        # Her seviyedeki (LH, HL, HH) detayları eşik değerine göre sıfırla
        level_coeffs = tuple(
            np.where(np.abs(c) < threshold, 0, c) for c in coeffs[i]
        )
        new_coeffs.append(level_coeffs)
        
    return new_coeffs