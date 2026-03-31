import os, ccxt
from flask import Flask, render_template, jsonify

app = Flask(__name__, 
            template_folder='holdcapital.io/templates',
            static_folder='holdcapital.io/static')

# Variables desde Railway
API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()

def get_balance():
    if not API_KEY or not API_SECRET:
        return "Conectar API"
    try:
        exchange = ccxt.binance({'apiKey': API_KEY, 'secret': API_SECRET})
        balance = exchange.fetch_balance()
        return f"{balance['total'].get('USDT', 0.0):,.2f}"
    except:
        return "Error"

@app.route('/')
def index():
    # Carga inicial de la página
    return render_template('index.html', 
                           cliente="JAVIER CUBILLOS", 
                           saldo=get_balance(), 
                           gas="20.00")

@app.route('/actualizar')
def actualizar():
    # Nueva ruta simple para evitar el 404
    return jsonify({
        "saldo": get_balance(),
        "gas": "20.00",
        "status": "Phoenix Online"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
