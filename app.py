import os, ccxt, json
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder='holdcapital.io/templates')

# Variables
API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()

@app.route('/')
def index():
    # Forzamos valores por defecto si falla la conexión
    saldo = "Conectando..."
    try:
        if API_KEY and API_SECRET:
            ex = ccxt.binance({'apiKey': API_KEY, 'secret': API_SECRET})
            bal = ex.fetch_balance()
            saldo = f"{bal['total'].get('USDT', 0.0):,.2f}"
    except: saldo = "Error API"
    
    return render_template('index.html', cliente="JAVIER CUBILLOS", saldo=saldo, gas="20.00")

@app.route('/api/data')
def api_data():
    saldo = "0.00"
    try:
        if API_KEY and API_SECRET:
            ex = ccxt.binance({'apiKey': API_KEY, 'secret': API_SECRET})
            bal = ex.fetch_balance()
            saldo = f"{bal['total'].get('USDT', 0.0):,.2f}"
    except: pass
    
    return jsonify({"saldo": saldo, "gas": "20.00", "status": "Phoenix Online"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
