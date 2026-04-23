import collections
import heapq

def build_huffman_tree(data):
    """
    Verilen veriden Huffman ağacı oluşturur.
    """
    flat_data = data.flatten().astype(int)
    frequencies = collections.Counter(flat_data)
    
    heap = [[weight, [symbol, ""]] for symbol, weight in frequencies.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    
    return dict(sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p)))

def encode_huffman(quantized_data):
    """
    Huffman tablosunu oluşturur ve sıkıştırma oranını hesaplamak için kullanışlıdır.
    """
    huff_table = build_huffman_tree(quantized_data)
    # Burada gerçek bitstream üretmek yerine tabloyu döndürüyoruz
    return huff_table