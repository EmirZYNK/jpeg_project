import numpy as np
from scipy.fftpack import idct

def apply_idct_2d(block):
    return idct(idct(block.T, norm="ortho").T, norm="ortho")


def blockwise_idct(dct_channel, original_h=None, original_w=None):
    h, w = dct_channel.shape
    reconstructed = np.zeros((h, w), dtype=np.float32)

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = dct_channel[i:i+8, j:j+8]
            pixel_block = apply_idct_2d(block)
            pixel_block += 128.0
            reconstructed[i:i+8, j:j+8] = pixel_block

    reconstructed = np.clip(reconstructed, 0, 255).astype(np.uint8)

    if original_h is not None and original_w is not None:
        reconstructed = reconstructed[:original_h, :original_w]

    return reconstructed