import os
import ccxt
from flask import Flask, render_template, jsonify

# Ajuste de rutas para que Flask encuentre tus carpetas según tu estructura de GitHub
app = Flask(__name__, 
            template_folder='templates',  # Si están en la raíz, dejar solo 'templates'
            static_folder='static')

# Variables de Entorno (Asegúrate de que se llamen ASÍ en Railway)
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

def get_balance():
    # Validación robusta de llaves
    if not API_KEY or not API_SECRET:
        print("🚨 Error: No se encontraron las API Keys en Railway Variables")
        return "Conectar API"
    
    try:
        # Configuración con ajuste de tiempo para evitar errores de sincronización
        exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True} 
        })
        
        balance = exchange.fetch_balance()
        # Sumamos USDT + lo que tengas en cripto convertido a USDT (Equidad Total)
        total_usdt = float(balance['total'].get('USDT', 0.0))
        
        return f"{total_usdt:,.2f}"
    except Exception as e:
        print(f"❌ Error de conexión con Binance: {e}")
        return "Error de Conexión"

@app.route('/')
def index():
    saldo_actual = get_balance()
    return render_template('index.html', 
                           usuario="JAVIER C-PHOENIX", 
                           capital=saldo_actual, 
                           gas="20.00")

@app.route('/actualizar')
def actualizar():
    return jsonify({
        "capital": get_balance(),
        "gas": "20.00",
        "status": "Phoenix Online"
    })

if __name__ == "__main__":
    # Railway asigna el puerto dinámicamente
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
