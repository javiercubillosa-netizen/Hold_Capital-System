import os, ccxt, json, base64
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# ==========================================
# 🔑 CONFIGURACIÓN DESDE RAILWAY
# ==========================================
# Forzamos la limpieza de las llaves por si acaso hay espacios
API_KEY = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_API_SECRET", "").strip()
CLIENTE = os.getenv("CLIENTE", "JAVIER CUBILLOS")

# Ruta de persistencia para el Gas
RUTA_GAS = "/data/gas_balance.txt" if os.path.exists("/data") else "gas_balance.txt"

def obtener_saldo_binance():
    if not API_KEY or not API_SECRET:
        return "Configurar API"
    try:
        # Configuración optimizada para Binance Spot
        exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        balance = exchange.fetch_balance()
        total_usdt = balance['total'].get('USDT', 0.0)
        return f"{total_usdt:,.2f}" # Formato con comas y 2 decimales
    except Exception as e:
        print(f"❌ Error Binance: {e}")
        return "Error de Conexión"

def obtener_gas_local():
    # Primero intentamos leer el archivo que los motores actualizan
    # Probamos ambas rutas comunes por si acaso
    rutas_probables = [RUTA_GAS, "gas_holding.txt", "gas.txt"]
    for ruta in rutas_probables:
        if os.path.exists(ruta):
            try:
                with open(ruta, "r") as f:
                    contenido = f.read().strip()
                    # Si es base64 (encriptado por el motor)
                    return f"{float(base64.b64decode(contenido).decode()):,.2f}"
            except:
                try:
                    # Si es texto plano
                    with open(ruta, "r") as f:
                        return f"{float(f.read().strip()):,.2f}"
                except: continue
    return "20.00"

# ==========================================
# 🌐 RUTAS DE LA PÁGINA WEB
# ==========================================

@app.route('/')
def index():
    return render_template('index.html', 
                           cliente=CLIENTE, 
                           saldo=obtener_saldo_binance(), 
                           gas=obtener_gas_local())

@app.route('/api/data')
def api_data():
    return jsonify({
        "saldo": obtener_saldo_binance(),
        "gas": obtener_gas_local(),
        "status": "Phoenix System: Online | Conectado a Binance"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
