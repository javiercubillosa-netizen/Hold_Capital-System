import os, ccxt
from flask import Flask, render_template, jsonify

# Esto obliga a Flask a mirar EXACTAMENTE en tu carpeta holdcapital.io
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'holdcapital.io', 'templates')

app = Flask(_name_, template_folder=template_dir)

# Variables de Binance desde Railway
API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()

def get_balance():
    if not API_KEY or not API_SECRET:
        return "Configurar API"
    try:
        exchange = ccxt.binance({'apiKey': API_KEY, 'secret': API_SECRET})
        balance = exchange.fetch_balance()
        usdt = balance['total'].get('USDT', 0.0)
        return f"{usdt:,.2f}"
    except Exception as e:
        return "Error Conexión"

@app.route('/')
def index():
    # Carga el HTML y le pasa los datos iniciales
    return render_template('index.html', 
                           cliente="JAVIER CUBILLOS", 
                           saldo=get_balance(), 
                           gas="20.00")

@app.route('/api/data')
def api_data():
    # Esta es la ruta que el script de tu HTML busca cada 30 segundos
    return jsonify({
        "saldo": get_balance(),
        "gas": "20.00",
        "status": "Phoenix System Online"
    })

if __name__ == "__main__":
    # Railway usa el puerto 8080 por defecto en muchos casos
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
