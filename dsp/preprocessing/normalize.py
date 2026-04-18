import numpy as np

def normalize_image(image_np):
    """
    Piksel değerlerini (0-255) matematiksel işlem kolaylığı için (0-1) arasına çeker.
    """
    
    # astype(np.float32): Tamsayı (int) olan değerleri ondalıklı (float) sayıya çevirir.
    # / 255.0: Her bir pikseli 255'e bölerek 0.0 ile 1.0 arasına sıkıştırır.
    normalized = image_np.astype(np.float32) / 255.0
    
    # TERİM AÇIKLAMALARI VE BAĞLANTI:
    # 1. Piksel (0-255): Bilgisayar ekranındaki en küçük noktanın ışık şiddeti değeridir.
    # 2. Normalizasyon: Verinin ölçeğini değiştirmektir ama anlamını bozmaz.
    # [span_12](start_span)[span_13](start_span)BAĞLANTI: 3. ve 4. kişi bu verilerle Kosinüs (DCT) veya Dalgacık (DWT) dönüşümü yapacak[span_12](end_span)[span_13](end_span).
    # Eğer sayılar 255 gibi büyük olursa, bu dönüşüm formülleri çok devasa sayılar üretir 
    # ve program yavaşlar veya hata verir. Normalizasyon, matematiksel kararlılığı sağlar.
    
    return normalized