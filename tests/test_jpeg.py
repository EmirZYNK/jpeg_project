import unittest
import numpy as np
from dsp.jpeg.dct import apply_dct_2d
from dsp.decoder.inverse_dct import apply_idct_2d

class TestJPEG(unittest.TestCase):
    def test_dct_idct_integrity(self):
        # 8x8'lik rastgele bir blok oluştur
        original_block = np.random.randint(0, 255, (8, 8)).astype(float) - 128
        # DCT uygula
        dct_coeffs = apply_dct_2d(original_block)
        # Geri çevir
        reconstructed = apply_idct_2d(dct_coeffs)
        
        # Orijinal ile geri çevrilen arasındaki fark çok küçük olmalı
        np.testing.assert_allclose(original_block + 128, reconstructed, atol=1)

if __name__ == '__main__':
    unittest.main()