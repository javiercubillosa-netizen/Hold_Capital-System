import os, ccxt, json, base64
from flask import Flask, render_template, jsonify

app = Flask(_name_)

# ==========================================
# 🔑 CONFIGURACIÓN DESDE RAILWAY
# ==========================================
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
CLIENTE = os.getenv("CLIENTE", "JAVIER CUBILLOS")

# Rutas de persistencia (Deben coincidir con los motores)
RUTA_GAS = "/data/gas_balance.txt" if os.path.exists("/data") else "gas_balance.txt"

def obtener_saldo_binance():
    try:
        if not API_KEY or not API_SECRET:
            return 0.0
        exchange = ccxt.binance({'apiKey': API_KEY, 'secret': API_SECRET})
        balance = exchange.fetch_balance()
        return round(balance['total'].get('USDT', 0.0), 2)
    except:
        return 0.0

def obtener_gas_local():
    try:
        if os.path.exists(RUTA_GAS):
            with open(RUTA_GAS, "r") as f:
                # Decodificamos el formato base64 que usan tus motores
                return float(base64.b64decode(f.read().strip()).decode())
        return 20.0 # Saldo inicial por defecto
    except:
        return 0.0

# ==========================================
# 🌐 RUTAS DE LA PÁGINA WEB
# ==========================================

@app.route('/')
def index():
    # Esta ruta carga tu HTML principal
    saldo = obtener_saldo_binance()
    gas = obtener_gas_local()
    return render_template('index.html', cliente=CLIENTE, saldo=saldo, gas=gas)

@app.route('/api/data')
def api_data():
    # Esta ruta permite que el dashboard se actualice sin recargar la página
    return jsonify({
        "saldo": obtener_saldo_binance(),
        "gas": obtener_gas_local(),
        "status": "Phoenix System: Conectado | Modo Cloud Activo"
    })

if _name_ == "_main_":
    # Railway asigna el puerto automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
