import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.compression import compression_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
OUTPUTS_DIR = os.path.join(BASE_DIR, "data", "outputs")
PLOTS_DIR = os.path.join(BASE_DIR, "data", "plots")

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)

app.register_blueprint(compression_bp, url_prefix="/api")


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/outputs/<path:filename>")
def outputs(filename):
    return send_from_directory(OUTPUTS_DIR, filename)


@app.route("/plots/<path:filename>")
def plots(filename):
    return send_from_directory(PLOTS_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001)