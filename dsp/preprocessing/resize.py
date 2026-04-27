import cv2

def standard_resize(image_np, target_size=512):
    """
    [span_6](start_span)Görüntüyü projemiz için belirlenen standart boyuta (512x512) getirir[span_6](end_span).
    """
    
    # cv2.resize: Matrisin boyutlarını değiştirir.
    # interpolation=cv2.INTER_AREA: Küçültme yaparken pikselleri en iyi koruyan yöntemdir.
    resized = cv2.resize(image_np, (target_size, target_size), interpolation=cv2.INTER_AREA)
    
    # TERİM AÇIKLAMALARI VE BAĞLANTI:
    # 1. [span_7](start_span)512x512: Bu boyut, 8'e tam bölünebildiği için seçilmiştir[span_7](end_span).
    # 2. [span_8](start_span)[span_9](start_span)8x8 Bloklama: JPEG, tüm resmi değil, 8x8'lik küçük kareleri işler[span_8](end_span)[span_9](end_span).
    # BAĞLANTI: Eğer resim 512x512 olmazsa (örneğin 513 olursa), kenarda kalan 1 piksellik 
    # fark 8x8'lik blok döngüsünü bozar. Bu yüzden senin resize işlemin, 3. kişinin 
    # [span_10](start_span)bloklama döngüsünün hatasız çalışmasını sağlar[span_10](end_span).
    
    return resized