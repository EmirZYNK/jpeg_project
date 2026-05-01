import numpy as np

# JPEG Standardı Parlaklık (Luminance - Y) Kuantizasyon Matrisi (Kalite 50 için)
Q_Y = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
])

# JPEG Standardı Renk (Chrominance - Cb, Cr) Kuantizasyon Matrisi (Kalite 50 için)
Q_C = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99]
])

def get_scale_factor(quality):
    """Kullanıcının arayüzden girdiği 1-100 arası kalite değerini JPEG standardı bir çarpana çevirir."""
    if quality <= 0: quality = 1
    if quality > 100: quality = 100
    
    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - quality * 2
    return scale / 100.0

def blockwise_quantization(dct_channel, quality, is_luminance=True):
    """
    DCT uygulanmış kanalı alır, Q-matrisine bölerek yüksek frekansları sıfırlar.
    İşte kayıplı sıkıştırma BURADA gerçekleşir. Çoğu piksel "0" olur.
    """
    scale = get_scale_factor(quality)
    q_matrix = (Q_Y * scale) if is_luminance else (Q_C * scale)
    
    # 0'a bölme hatasını engellemek için minimum 1 yapıyoruz
    q_matrix = np.maximum(q_matrix, 1)
    
    h, w = dct_channel.shape
    quantized_channel = np.zeros_like(dct_channel)
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = dct_channel[i:i+8, j:j+8]
            # Matrisi böl ve en yakın tam sayıya yuvarla (Çoğu değer sıfır olacak!)
            quantized_channel[i:i+8, j:j+8] = np.round(block / q_matrix)
            
    return quantized_channel

def blockwise_dequantization(quantized_channel, quality, is_luminance=True):
    """
    Sıkıştırılmış veriyi (sıfırlarla dolu matrisi) tekrar geri açmak (decoder) 
    için kullanılır. Q-matrisi ile tekrar çarparız.
    Ancak tam sayıya yuvarlandığı için orijinal veriyi %100 GERİ ELDE EDEMEYİZ.
    """
    scale = get_scale_factor(quality)
    q_matrix = (Q_Y * scale) if is_luminance else (Q_C * scale)
    q_matrix = np.maximum(q_matrix, 1)
    
    h, w = quantized_channel.shape
    dequantized_channel = np.zeros_like(quantized_channel, dtype=float)
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = quantized_channel[i:i+8, j:j+8]
            dequantized_channel[i:i+8, j:j+8] = block * q_matrix
            
    return dequantized_channel