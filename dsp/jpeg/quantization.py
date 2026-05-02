import numpy as np

# ---------------- 1. NATURAL (DOĞAL) MATRİSLER (Standart JPEG) ----------------
# Fotoğraflar ve doğal sahneler için optimize edilmiştir.
Q_Y_NATURAL = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
])

Q_C_NATURAL = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99]
])

# ---------------- 2. SYNTHETIC (SENTETİK) MATRİSLER ----------------
# Grafik, logo ve yazılardaki "Ringing (Dalgalanma)" etkisini önlemek için
# Yüksek frekanslar (sağ alt köşeler) çok yüksek değerlere çıkarılmamıştır.
Q_Y_SYNTHETIC = np.array([
    [10, 10, 15, 20, 25, 30, 35, 40],
    [10, 15, 20, 25, 30, 35, 40, 45],
    [15, 20, 25, 30, 35, 40, 45, 50],
    [20, 25, 30, 35, 40, 45, 50, 55],
    [25, 30, 35, 40, 45, 50, 55, 60],
    [30, 35, 40, 45, 50, 55, 60, 65],
    [35, 40, 45, 50, 55, 60, 65, 70],
    [40, 45, 50, 55, 60, 65, 70, 75]
])
Q_C_SYNTHETIC = Q_Y_SYNTHETIC  # Renkleri de keskin tutuyoruz

# ---------------- 3. BIOMEDICAL (BİYOMEDİKAL) MATRİSLER ----------------
# Teşhis için detay kaybı kabul edilemez. Neredeyse dümdüz bir matris.
# Tüm frekansları korur, sıkıştırma oranı düşük olur ama kalite mükemmel kalır.
Q_Y_BIOMEDICAL = np.ones((8, 8)) * 8 
Q_C_BIOMEDICAL = np.ones((8, 8)) * 10


def get_category_matrix(is_luminance, category):
    """Seçilen kategoriye uygun base matrisi döndürür."""
    if category == 'biomedical':
        return Q_Y_BIOMEDICAL if is_luminance else Q_C_BIOMEDICAL
    elif category == 'synthetic':
        return Q_Y_SYNTHETIC if is_luminance else Q_C_SYNTHETIC
    else: # natural
        return Q_Y_NATURAL if is_luminance else Q_C_NATURAL


def get_scale_factor(quality):
    """1-100 arası kalite değerini JPEG standardı bir çarpana çevirir."""
    if quality <= 0: quality = 1
    if quality > 100: quality = 100
    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - quality * 2
    return scale / 100.0


def blockwise_quantization(dct_channel, quality, is_luminance=True, category='natural'):
    """ DCT uygulanmış kanalı Kategoriye özel Q-matrisine bölerek kuantize eder. """
    scale = get_scale_factor(quality)
    base_matrix = get_category_matrix(is_luminance, category)
    
    q_matrix = base_matrix * scale
    q_matrix = np.maximum(q_matrix, 1) # 0'a bölmeyi engelle
    
    h, w = dct_channel.shape
    quantized_channel = np.zeros_like(dct_channel)
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = dct_channel[i:i+8, j:j+8]
            # Matrisi böl ve en yakın tam sayıya yuvarla
            quantized_channel[i:i+8, j:j+8] = np.round(block / q_matrix)
            
    return quantized_channel


def blockwise_dequantization(quantized_channel, quality, is_luminance=True, category='natural'):
    """ Sıkıştırılmış veriyi tekrar açmak için doğru kategori matrisi ile çarpar. """
    scale = get_scale_factor(quality)
    base_matrix = get_category_matrix(is_luminance, category)
    
    q_matrix = base_matrix * scale
    q_matrix = np.maximum(q_matrix, 1)
    
    h, w = quantized_channel.shape
    dequantized_channel = np.zeros_like(quantized_channel, dtype=float)
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = quantized_channel[i:i+8, j:j+8]
            dequantized_channel[i:i+8, j:j+8] = block * q_matrix
            
    return dequantized_channel