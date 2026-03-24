from flask import Flask, render_template
import os

app = Flask(__name__)

# Ruta principal: La cara de HoldCapital.io
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    # Railway usa el puerto que le asigne el sistema
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
