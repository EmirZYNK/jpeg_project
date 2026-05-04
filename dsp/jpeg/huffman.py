import heapq
from collections import Counter

class HuffmanNode:
    """Huffman Ağacı için düğüm (node) yapısı"""
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        # heapq'nun frekansa göre sıralayabilmesi için küçüktür (<) operatörünü tanımlıyoruz
        return self.freq < other.freq

def build_huffman_tree(symbol_frequencies):
    """Frekanslara göre Huffman Ağacını inşa eder (Slayt 2'deki tablo hazırlığı)."""
    heap = [HuffmanNode(sym, freq) for sym, freq in symbol_frequencies.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        # En düşük frekanslı iki düğümü al ve birleştir
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        
        heapq.heappush(heap, merged)
        
    return heap[0] if heap else None

def generate_huffman_codes(node, current_code="", huffman_dict=None):
    """Ağaçta gezinerek her sembole '0' ve '1' lerden oluşan kodlar atar."""
    if huffman_dict is None:
        huffman_dict = {}
        
    if node is not None:
        if node.char is not None:
            # Sola giderken 0, sağa giderken 1 ekleyerek kodu oluştur
            huffman_dict[node.char] = current_code
        generate_huffman_codes(node.left, current_code + "0", huffman_dict)
        generate_huffman_codes(node.right, current_code + "1", huffman_dict)
        
    return huffman_dict

def huffman_encode(data_list):
    """
    RLE ve DPCM'den gelen verileri alır, frekans analizi yapar ve 
    slaytlardaki gibi "1011010..." şeklinde bir bitstream (bit akışı) oluşturur.
    """
    if not data_list:
        return "", {}
        
    # 1. Sembollerin frekansını say (Hangi sayıdan/tuple'dan kaç tane var?)
    frequencies = Counter(data_list)
    
    # 2. Ağacı inşa et
    root = build_huffman_tree(frequencies)
    
    # 3. Sözlüğü oluştur (Örn: { (0,0): "01", 5: "1011" })
    huffman_dict = generate_huffman_codes(root)
    
    # 4. Tüm veriyi 1 ve 0 stringine dönüştür (Bitstream)
    bitstream = "".join(huffman_dict[sym] for sym in data_list)
    
    return bitstream, huffman_dict