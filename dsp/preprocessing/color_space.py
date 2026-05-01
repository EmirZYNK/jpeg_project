import numpy as np
import cv2

def rgb_to_ycbcr(image_rgb):
    """
    RGB -> YCbCr dönüşümü yapar ve 4:2:0 Chroma Subsampling uygular.
    Renk kanallarını (Cb, Cr) yarıya indirerek veri boyutunu %50 düşürür.
    """
    img_array = np.array(image_rgb)
    ycbcr_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2YCrCb)
    Y, Cr, Cb = cv2.split(ycbcr_image)
    
    # Renk kanallarını (Cb ve Cr) yarı yarıya küçültüyoruz (Subsampling)
    Cb_sub = cv2.resize(Cb, (Cb.shape[1]//2, Cb.shape[0]//2), interpolation=cv2.INTER_AREA)
    Cr_sub = cv2.resize(Cr, (Cr.shape[1]//2, Cr.shape[0]//2), interpolation=cv2.INTER_AREA)
    
    return Y, Cb_sub, Cr_sub

def ycbcr_to_rgb(Y, Cb_sub, Cr_sub):
    """
    Küçültülmüş renk kanallarını geri büyütür ve RGB'ye döner.
    """
    # Renk kanallarını tekrar orijinal Y boyuna getiriyoruz
    Cb = cv2.resize(Cb_sub, (Y.shape[1], Y.shape[0]), interpolation=cv2.INTER_CUBIC)
    Cr = cv2.resize(Cr_sub, (Y.shape[1], Y.shape[0]), interpolation=cv2.INTER_CUBIC)
    
    ycbcr_image = cv2.merge([Y, Cr, Cb])
    rgb_image = cv2.cvtColor(ycbcr_image, cv2.COLOR_YCrCb2RGB)
    
    return rgb_image