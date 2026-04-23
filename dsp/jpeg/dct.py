import numpy as np
from scipy.fftpack import dct, idct

def apply_2d_dct(block):
    """
    8x8'lik bir bloğa 2D Ayrık Kosinüs Dönüşümü uygular.
    """
    # Type 2 DCT, normalizasyon 'ortho'
    return dct(dct(block.T, norm='ortho').T, norm='ortho')

def process_image_dct(image_data):
    """
    Görüntüyü 8x8 bloklara böler ve her birine DCT uygular.
    """
    h, w = image_data.shape
    dct_coefficients = np.zeros((h, w))
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = image_data[i:i+8, j:j+8]
            if block.shape == (8, 8):
                dct_coefficients[i:i+8, j:j+8] = apply_2d_dct(block)
                
    return dct_coefficients