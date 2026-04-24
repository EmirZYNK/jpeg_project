# dsp/jpeg2000/quantization.py

import numpy as np

def calculate_step_sizes(quality: int, num_levels: int):
    """
    UI'dan gelen 'Quality' (1-100) değerini DWT alt bantları için 
    kuantalama adım boyutlarına (step sizes) dönüştürür.
    """
    # Quality 100 ise kayıpsız (lossless) gibi davran, step 1 olsun.
    if quality >= 100:
        base_step = 1.0
    elif quality < 50:
        base_step = 5000 / quality
    else:
        base_step = 200 - quality * 2
        
    # Değerleri normalize edelim (JPEG quant matrisi mantığına benzer)
    base_step = max(1.0, base_step / 10.0)
    
    step_sizes = []
    # Index 0: cA (Approximation / LL bandı) - Görselliğin kalbidir, az kuantize edilir
    step_sizes.append(max(1.0, base_step * 0.5))
    
    # Diğer bantlar: (cH, cV, cD) - Detay bantları
    # num_levels'dan 1'e doğru gider (En küçük çözünürlükten, en büyüğe)
    for i in range(1, num_levels + 1):
        weight = i  # Derin seviyeler (küçük resimler) az, sığ seviyeler çok kuantize edilir
        step_cH = base_step * weight * 1.2
        step_cV = base_step * weight * 1.2
        step_cD = base_step * weight * 1.5 # Diagonal detaylar en az önemli olanlardır
        
        step_sizes.append((max(1.0, step_cH), max(1.0, step_cV), max(1.0, step_cD)))
        
    return step_sizes

def quantize_dwt(coeffs: list, quality: int = 50):
    """
    DWT katsayılarını belirlenen kaliteye göre kuantize eder.
    
    Args:
        coeffs: apply_dwt_2d'den gelen katsayı listesi
        quality: UI'dan gelen kalite (1-100)
    """
    if quality >= 100:
        # Kayıpsız sıkıştırma seçildiyse (veya quality 100 ise) doğrudan yuvarla
        return [np.round(c) if isinstance(c, np.ndarray) 
                else tuple(np.round(x) for x in c) for c in coeffs]

    num_levels = len(coeffs) - 1
    step_sizes = calculate_step_sizes(quality, num_levels)
    
    quantized_coeffs = []
    
    # 1. LL Bandını (cA) Kuantize et
    q_cA = np.round(coeffs[0] / step_sizes[0])
    quantized_coeffs.append(q_cA)
    
    # 2. Detay Bantlarını (cH, cV, cD) Kuantize et
    for i in range(1, len(coeffs)):
        cH, cV, cD = coeffs[i]
        s_cH, s_cV, s_cD = step_sizes[i]
        
        q_cH = np.round(cH / s_cH)
        q_cV = np.round(cV / s_cV)
        q_cD = np.round(cD / s_cD)
        
        quantized_coeffs.append((q_cH, q_cV, q_cD))
        
    return quantized_coeffs

def dequantize_dwt(quantized_coeffs: list, quality: int = 50):
    """
    5. Kişi (Decoder) için yardımcı fonksiyon.
    Kuantize edilmiş veriyi, step size'lar ile çarparak orijinal ölçeğine getirir.
    (Tam olarak eski haline gelmez, kayıp burada yaşanır - Lossy Compression)
    """
    if quality >= 100:
        return quantized_coeffs
        
    num_levels = len(quantized_coeffs) - 1
    step_sizes = calculate_step_sizes(quality, num_levels)
    
    dequantized_coeffs = []
    
    # 1. LL Bandı
    dq_cA = quantized_coeffs[0] * step_sizes[0]
    dequantized_coeffs.append(dq_cA)
    
    # 2. Detay Bantları
    for i in range(1, len(quantized_coeffs)):
        q_cH, q_cV, q_cD = quantized_coeffs[i]
        s_cH, s_cV, s_cD = step_sizes[i]
        
        dq_cH = q_cH * s_cH
        dq_cV = q_cV * s_cV
        dq_cD = q_cD * s_cD
        
        dequantized_coeffs.append((dq_cH, dq_cV, dq_cD))
        
    return dequantized_coeffs