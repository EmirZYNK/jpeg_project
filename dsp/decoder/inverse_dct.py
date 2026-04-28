import numpy as np
from scipy.fftpack import idct

def apply_inverse_dct(dct_data):
    # Gelen veriyi 8x8 bloklar halinde geri çözer
    return idct(idct(dct_data.T, norm='ortho').T, norm='ortho')