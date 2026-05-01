import numpy as np
from scipy.fftpack import idct

def apply_idct_2d(block):
    """
    8x8'lik bir frekans bloğunu tekrar piksel bloğuna çevirir (Ters Dönüşüm).
    """
    return idct(idct(block.T, norm='ortho').T, norm='ortho')

def blockwise_idct(dct_channel):
    """
    Tüm kanal üzerinde pencerelerle gezerek Ters DCT uygular.
    """
    h, w = dct_channel.shape
    reconstructed_image = np.zeros((h, w), dtype=np.float32)
    
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = dct_channel[i:i+8, j:j+8]
            
            # Ters DCT uygula
            pixel_block = apply_idct_2d(block)
            
            # Hatırlarsan merkeze çekmek için DCT'den önce 128 çıkarmıştık.
            # Şimdi 128 ekleyerek pikselleri 0-255 uzayına geri getiriyoruz.
            pixel_block += 128.0
            
            reconstructed_image[i:i+8, j:j+8] = pixel_block
            
    # Pikseller matematiksel işlemlerden dolayı küsuratlı veya <0, >255 çıkabilir.
    # Onları 0 ile 255 arasına sıkıştırıp tam sayı (uint8) yapıyoruz.
    return np.clip(reconstructed_image, 0, 255).astype(np.uint8)