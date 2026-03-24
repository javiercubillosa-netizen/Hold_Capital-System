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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
=======
    # Railway usa el puerto que le asigne el sistema
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
>>>>>>> 42aa9999b7ba17e1582507601fc3fbefad5feec1
