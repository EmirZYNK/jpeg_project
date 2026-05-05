import numpy as np
from scipy.fftpack import dct

def apply_dct_2d(block):
    return dct(dct(block.T, norm="ortho").T, norm="ortho")


def pad_to_block_size(channel, block_size=8):
    h, w = channel.shape

    pad_h = (block_size - h % block_size) % block_size
    pad_w = (block_size - w % block_size) % block_size

    padded = np.pad(
        channel,
        ((0, pad_h), (0, pad_w)),
        mode="edge"
    )

    return padded, h, w


def blockwise_dct(channel):
    padded, original_h, original_w = pad_to_block_size(channel)
    h, w = padded.shape

    dct_channel = np.zeros((h, w), dtype=np.float32)

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = padded[i:i+8, j:j+8].astype(np.float32)
            block -= 128.0
            dct_channel[i:i+8, j:j+8] = apply_dct_2d(block)

    return dct_channel, original_h, original_w