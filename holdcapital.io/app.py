import os
from flask import Flask, render_template

# Este ajuste le dice a Flask dónde están las carpetas reales
app = Flask(__name__, 
            template_folder='templates', 
            static_folder='static')

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    # Railway asigna el puerto automáticamente
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
