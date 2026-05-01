import numpy as np
import collections

def calculate_huffman_size(quantized_channel):
    """
    Kuantize edilmiş verinin Huffman sonrası teorik boyutunu bit cinsinden hesaplar.
    Hocaya sunumda 'Huffman sonrası şu kadar bit yer kaplıyor' diyebilmek için.
    """
    data = quantized_channel.flatten().astype(int)
    if len(data) == 0: return 0
    
    # Her bir sayının kaç kez geçtiğini say (Frekans analizi)
    frequencies = collections.Counter(data)
    total_symbols = len(data)
    
    # Entropi hesapla: Bir verinin teorik olarak sıkıştırılabileceği en alt sınır
    entropy = 0
    for freq in frequencies.values():
        p = freq / total_symbols
        entropy += -p * np.log2(p)
    
    # Toplam Bit = Sembol Sayısı * Entropi
    theoretical_bits = total_symbols * entropy
    return theoretical_bits / 8  # Byte cinsinden döndür