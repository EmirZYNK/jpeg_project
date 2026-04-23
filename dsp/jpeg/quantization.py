import numpy as np

# Standart JPEG Parlaklık (Luminance) Tablosu
JPEG_LUM_TABLE = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
])

def quantize_block(dct_block, quality=50):
    """
    DCT bloğunu belirlenen kalite seviyesine göre quantize eder.
    Quality 1-100 arasıdır. 100 en yüksek kalite (en az sıkıştırma).
    """
    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - quality * 2
    
    # Tabloyu kaliteye göre ölçeklendir
    q_table = np.floor((JPEG_LUM_TABLE * scale + 50) / 100)
    q_table[q_table < 1] = 1 # 0'a bölünmeyi engelle
    
    return np.round(dct_block / q_table)

def process_quantization(dct_coeffs, quality=50):
    h, w = dct_coeffs.shape
    quantized_coeffs = np.zeros((h, w))
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = dct_coeffs[i:i+8, j:j+8]
            if block.shape == (8, 8):
                quantized_coeffs[i:i+8, j:j+8] = quantize_block(block, quality)
                
    return quantized_coeffs