import cv2 # OpenCV: Görüntü işleme kütüphanesi. Resimleri matris olarak okumamızı sağlar.
import numpy as np # NumPy: Yüksek performanslı çok boyutlu diziler (matrisler) kütüphanesi.

def rgb_to_ycbcr(image_np):
    """
    Bu fonksiyon RGB (Kırmızı-Yeşil-Mavi) formatındaki görüntüyü 
    [span_3](start_span)YCbCr (Parlaklık-Mavi Farkı-Kırmızı Farkı) formatına dönüştürür[span_3](end_span).
    """
    
    # cv2.cvtColor: Renk uzayı dönüşümü yapar. 
    # cv2.COLOR_BGR2YCrCb: OpenCV resmi BGR (Mavi-Yeşil-Kırmızı) okuduğu için 
    # onu doğrudan YCbCr'ye (Parlaklık ve Renk farkı kanalları) çeviririz.
    ycbcr_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2YCrCb)
    
    # TERİM AÇIKLAMALARI VE BAĞLANTI:
    # 1. Y (Luminance): Görüntünün parlaklık (siyah-beyaz) bilgisidir. İnsan gözü buna hassastır.
    # 2. Cb/Cr (Chrominance): Renk farkı bilgileridir. İnsan gözü renkteki detaylara daha az hassastır.
    # BAĞLANTI: Sıkıştırma algoritmaları (JPEG), insan gözünün zayıflığından faydalanmak için 
    # Cb/Cr kanallarını Y kanalından ayırarak sadece renkleri daha fazla sıkıştırır.
    
    return ycbcr_image