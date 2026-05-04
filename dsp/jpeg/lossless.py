import numpy as np

def encode_block(zigzag_array, prev_dc):
    """
    Slayt 4'teki DPCM ve RLE ayrımını yapar.
    1D zigzag dizisini alır, kodlanmış DC farkını ve AC RLE listesini döndürür.
    """
    # ----- 1. DPCM (Sadece DC Katsayısı) -----
    current_dc = zigzag_array[0]
    dc_diff = current_dc - prev_dc  # Sadece önceki blokla aradaki farkı al
    
    # ----- 2. RLE (AC Katsayıları) -----
    ac_coeffs = zigzag_array[1:]
    
    # Kalan kısmın neresi tamamen sıfır? (EOB - End of Block bulmak için)
    last_non_zero = -1
    for i in range(len(ac_coeffs) - 1, -1, -1):
        if ac_coeffs[i] != 0:
            last_non_zero = i
            break
            
    rle_data = []
    
    # Eğer AC kısmının hepsi sıfırsa
    if last_non_zero == -1:
        rle_data.append((0, 0)) # (0,0) özel bir işarettir: "Bloğun sonuna kadar her şey sıfır" (EOB)
        return dc_diff, rle_data
        
    zero_count = 0
    for i in range(last_non_zero + 1):
        val = ac_coeffs[i]
        if val == 0:
            zero_count += 1
            # JPEG standardında 16 ardışık sıfır, ZRL (Zero Run Length) yani (15, 0) olarak yazılır
            while zero_count > 15:
                rle_data.append((15, 0)) 
                zero_count -= 16
        else:
            rle_data.append((zero_count, val)) # (Sıfır sayısı, Gelen sayı)
            zero_count = 0
            
    # Geri kalan kısımlar sıfır olduğu için EOB (End of Block) işaretini koy
    rle_data.append((0, 0)) 
    
    return dc_diff, rle_data


def decode_block(dc_diff, rle_data, prev_dc):
    """
    Sıkıştırılmış veriyi tekrar 64 elemanlı zigzag dizisine çevirir (Slayt 4 alt kısım).
    """
    zigzag = np.zeros(64, dtype=int)
    
    # 1. Ters DPCM
    current_dc = prev_dc + dc_diff
    zigzag[0] = current_dc
    
    # 2. Ters RLE
    idx = 1
    for zero_count, val in rle_data:
        if zero_count == 0 and val == 0:  # EOB işareti
            break  # Kalan her şey zaten baştaki np.zeros yüzünden 0 kalacak
        
        idx += zero_count  # Sıfırları atla
        if idx < 64:
            zigzag[idx] = val
            idx += 1
            
    return zigzag, current_dc