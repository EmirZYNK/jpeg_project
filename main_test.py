import cv2
import numpy as np
from dsp.preprocessing.color_space import rgb_to_ycbcr
from dsp.preprocessing.resize import standard_resize
from dsp.preprocessing.normalize import normalize_image

def sistem_test_dongusu(resim_yolu):
    ham_resim = cv2.imread(resim_yolu)
    
    if ham_resim is None:
        print("HATA: Dosya yolu gecersiz.")
        return

    boyutlandirilmis_resim = standard_resize(ham_resim)
    ycbcr_resim = rgb_to_ycbcr(boyutlandirilmis_resim)
    islenmis_veri = normalize_image(ycbcr_resim)
    
    print(f"Boyut: {islenmis_veri.shape}")
    print(f"Tip: {islenmis_veri.dtype}")
    print(f"Max: {islenmis_veri.max()}")
    print(f"Min: {islenmis_veri.min()}")

    cv2.imshow("Test", islenmis_veri)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return islenmis_veri

hazir_matris = sistem_test_dongusu('C:/Users/0/Downloads/kedo.jpg')