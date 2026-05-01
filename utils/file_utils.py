import os
from utils.constants import ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_kb(filepath):
    return round(os.path.getsize(filepath) / 1024, 2)

def clean_folder(folder_path):
    """Klasördeki eski dosyaları temizler."""
    for f in os.listdir(folder_path):
        os.remove(os.path.join(folder_path, f))