import numpy as np

# JPEG standardına göre 8x8'lik matrisin zigzag okuma rotası (Satır, Sütun indeksleri)
ZIGZAG_ORDER = np.array([
    [0,0], [0,1], [1,0], [2,0], [1,1], [0,2], [0,3], [1,2], 
    [2,1], [3,0], [4,0], [3,1], [2,2], [1,3], [0,4], [0,5], 
    [1,4], [2,3], [3,2], [4,1], [5,0], [6,0], [5,1], [4,2], 
    [3,3], [2,4], [1,5], [0,6], [0,7], [1,6], [2,5], [3,4], 
    [4,3], [5,2], [6,1], [7,0], [7,1], [6,2], [5,3], [4,4], 
    [3,5], [2,6], [1,7], [2,7], [3,6], [4,5], [5,4], [6,3], 
    [7,2], [7,3], [6,4], [5,5], [4,6], [3,7], [4,7], [5,6], 
    [6,5], [7,4], [7,5], [6,6], [5,7], [6,7], [7,6], [7,7]
])

def block_to_zigzag(block):
    """
    8x8'lik kuantize edilmiş 2D bloğu alır, 
    slaytlardaki gibi zigzag okuyarak 64 elemanlı 1D diziye çevirir.
    """
    # 64 elemanlı boş bir dizi oluştur
    zigzag_array = np.zeros(64, dtype=int)
    
    # Rota tablomuzu kullanarak matrisin içinden elemanları çek
    for i, (r, c) in enumerate(ZIGZAG_ORDER):
        zigzag_array[i] = block[r, c]
        
    return zigzag_array

def zigzag_to_block(zigzag_array):
    """
    Geri çözme (Decoding) işlemi için 64 elemanlı 1D zigzag dizisini 
    tekrar 8x8'lik 2D matris haline getirir.
    """
    # 8x8 boş matris oluştur
    block = np.zeros((8, 8), dtype=float)
    
    # Rota tablosuna göre yerlerine koy
    for i, (r, c) in enumerate(ZIGZAG_ORDER):
        block[r, c] = zigzag_array[i]
        
    return block