from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from routes.compression import compression_bp
import os

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
CORS(app) # Frontend ile Backend'in sorunsuz haberleşmesi için

# Klasörlerin var olduğundan emin olalım
os.makedirs('../data/uploads', exist_ok=True)
os.makedirs('../data/outputs', exist_ok=True)

# Blueprint'leri (rotaları) kaydet
app.register_blueprint(compression_bp, url_prefix='/api')

# Ana sayfayı render et
@app.route('/')
def index():
    return render_template('index.html')

# Frontend statik dosyaları (css, js) için
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# İşlenmiş görselleri frontend'e sunmak için
@app.route('/outputs/<path:filename>')
def serve_outputs(filename):
    return send_from_directory('../data/outputs', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)