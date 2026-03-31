import os, ccxt
from flask import Flask, render_template, jsonify

app = Flask(__name__, 
            template_folder='holdcapital.io/templates',
            static_folder='holdcapital.io/static')

API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()

def get_balance():
    if not API_KEY or not API_SECRET:
        return "0.00"
    try:
        exchange = ccxt.binance({'apiKey': API_KEY, 'secret': API_SECRET})
        balance = exchange.fetch_balance()
        return f"{balance['total'].get('USDT', 0.0):,.2f}"
    except:
        return "Error API"

@app.route('/')
def index():
    return render_template('index.html', 
                           cliente="JAVIER CUBILLOS", 
                           saldo=get_balance(), 
                           gas="20.00")

# CAMBIAMOS EL NOMBRE DE LA RUTA AQUÍ
@app.route('/datos_phoenix')
def api_data():
    return jsonify({
        "saldo": get_balance(),
        "gas": "20.00",
        "status": "Phoenix Online"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
