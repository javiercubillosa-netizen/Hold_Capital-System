import os, ccxt, json
from flask import Flask, render_template, jsonify

# Configuramos Flask para que busque en la carpeta correcta según tu foto
app = Flask(__name__, 
            template_folder='holdcapital.io/templates', 
            static_folder='holdcapital.io/static')

API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()

def get_binance_balance():
    try:
        if API_KEY and API_SECRET:
            exchange = ccxt.binance({'apiKey': API_KEY, 'secret': API_SECRET})
            balance = exchange.fetch_balance()
            return f"{balance['total'].get('USDT', 0.0):,.2f}"
    except: pass
    return "0.00"

@app.route('/')
def index():
    # Enviamos las variables exactas que pusimos en el HTML
    return render_template('index.html', 
                           cliente="JAVIER CUBILLOS", 
                           saldo=get_binance_balance(), 
                           gas="20.00")

@app.route('/api/data')
def api_data():
    # Esta es la ruta que da el error 404, ahora está bien definida
    return jsonify({
        "saldo": get_binance_balance(),
        "gas": "20.00",
        "status": "Phoenix System: Conectado"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
