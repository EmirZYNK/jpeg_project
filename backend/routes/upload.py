from flask import Blueprint, request, jsonify

upload_bp = Blueprint("upload_bp", __name__)


@upload_bp.route("/upload", methods=["POST"])
def upload_image():
    return jsonify({
        "message": "Resim alındı."
    })


@upload_bp.route("/compress", methods=["POST"])
def compress_image():
    return jsonify({
        "message": "Compress işlemi alındı."
    })