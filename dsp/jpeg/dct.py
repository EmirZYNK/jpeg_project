import numpy as np
from scipy.fftpack import dct

def apply_dct_2d(block):
    """
    8x8'lik bir piksel bloğuna 2 Boyutlu Ayrık Kosinüs Dönüşümü (2D-DCT) uygular.
    Piksel uzayından (spatial domain), frekans uzayına (frequency domain) geçiş yapar.
    """
    # Önce satırlara DCT uygula, sonra sütunlara DCT uygula (scipy standardı)
    # norm='ortho' enerji korunumu için gereklidir.
    return dct(dct(block.T, norm='ortho').T, norm='ortho')

def blockwise_dct(image_channel):
    """
    Koca bir görüntü kanalını (örn: sadece Y veya sadece Cb) alır, 
    8x8 bloklara böler ve her birine DCT uygular.
    """
    h, w = image_channel.shape
    
    # Görüntü boyutları 8'in katı değilse, padding (kenarlara boşluk) eklememiz gerekir
    # Şimdilik basitçe görüntüyü 8'in katına kırpıyoruz (ileride padding eklenebilir)
    h_adj = (h // 8) * 8
    w_adj = (w // 8) * 8
    channel_adj = image_channel[:h_adj, :w_adj]
    
    dct_image = np.zeros((h_adj, w_adj), dtype=np.float32)
    
    # Görüntünün üzerinde 8x8 pencerelerle gezin (Matris çarpımları)
    for i in range(0, h_adj, 8):
        for j in range(0, w_adj, 8):
            # 8x8'lik bloğu al
            block = channel_adj[i:i+8, j:j+8]
            
            # JPEG standardı gereği pikselleri 0-255 arasından -128 ile +127 arasına çekeriz
            # Bu, kosinüs dalgalarının etrafında salındığı sıfır noktasını merkeze alır
            block_centered = block.astype(float) - 128.0
            
            # DCT'yi uygula ve yeni matrise kaydet
            dct_image[i:i+8, j:j+8] = apply_dct_2d(block_centered)
            
    return dct_image