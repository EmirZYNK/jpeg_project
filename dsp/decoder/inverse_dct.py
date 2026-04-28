import numpy as np
from scipy.fftpack import idct

def apply_2d_idct(block):
    """
    8x8'lik tek bir frekans bloğuna Ters 2D Ayrık Kosinüs Dönüşümü (IDCT) uygular.
    Pikselleri geri elde etmemizi sağlar.
    """
    # Type 3 IDCT, normalizasyon 'ortho' (ileri DCT'nin tam tersidir)
    return idct(idct(block.T, norm='ortho').T, norm='ortho')

def process_image_idct(dct_coefficients):
    """
    Tüm DCT katsayısı matrisini alır, 8x8 bloklara böler ve 
    her birine Ters DCT (IDCT) uygulayarak tam resmi yeniden oluşturur.
    """
    h, w = dct_coefficients.shape
    reconstructed_image = np.zeros((h, w))
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = dct_coefficients[i:i+8, j:j+8]
            
            # Kenarlarda 8x8'den küçük parça kalmaması için kontrol
            if block.shape == (8, 8):
                reconstructed_image[i:i+8, j:j+8] = apply_2d_idct(block)
                
    return reconstructed_image