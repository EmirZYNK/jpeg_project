import sys
import os
from flask import Flask
from routes.upload import upload_bp

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

app.register_blueprint(upload_bp)


@app.route("/")
def home():
    return "Backend Server Running!"


if __name__ == "__main__":
    app.run(debug=True)