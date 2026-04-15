from flask import Flask
from routes.upload import upload_bp

app = Flask(__name__)

# Blueprint register
app.register_blueprint(upload_bp)


@app.route("/")
def home():
    return "Backend Server Running!"


if __name__ == "__main__":
    app.run(debug=True)