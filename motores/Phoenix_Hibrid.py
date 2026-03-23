import ccxt, time, json, os, requests, sys, numpy as np
import psycopg2 # Necesario para conectar con tu Postgres de Railway
from datetime import datetime
from psycopg2.extras import RealDictCursor

# ==========================================
# 🌐 CONFIGURACIÓN ESTRATÉGICA RAILWAY
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL") # Railway la entrega automáticamente

# ==========================================
# 🔑 FUNCIONES DE ENLACE CON DASHBOARD
# ==========================================
def obtener_config_usuario():
    """Extrae las API Keys y el estado del bot desde la DB de Railway"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Buscamos al usuario admin que creamos antes
        cur.execute("SELECT * FROM usuarios WHERE email = 'admin@holdcapital.io' LIMIT 1")
        user = cur.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return None

# ==========================================
# 🦅 MOTOR PHOENIX HIBRID (Versión Cloud)
# ==========================================
class PhoenixHybridGold:

    def __init__(self, config):
        # Configuramos con los datos de la DB
        self.api_key = config['api_key_cifrada']
        self.api_secret = config['api_secret_cifrada']
        
        # Capital inicial (puedes ajustarlo para que también se lea de la DB)
        self.cap_total = 1000.0 # Valor base si no está en DB
        self.cap_operativo = self.cap_total * 0.70
        self.monto_ini = self.cap_operativo * 0.125

        self.pares = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]

        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

        self.archivo_estado = "phoenix_state.json"
        self.estado = self.cargar_estado()
        self.profit_objetivo = 1.3
        self.trailing_call = 0.3
        self.max_recompras = 10
        self.base_dca = self.cap_total * 0.05

    def cargar_estado(self):
        if os.path.exists(self.archivo_estado):
            with open(self.archivo_estado, 'r') as f:
                return json.load(f)
        return {p: {'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0} for p in self.pares}

    def guardar_estado(self):
        with open(self.archivo_estado, 'w') as f:
            json.dump(self.estado, f, indent=4)

    def calcular_atr(self, par):
        try:
            ohlcv = self.exchange.fetch_ohlcv(par, timeframe='1h', limit=20)
            highs = [x[2] for x in ohlcv]
            lows = [x[3] for x in ohlcv]
            closes = [x[4] for x in ohlcv]
            atr = np.mean(np.array(highs) - np.array(lows))
            return atr, closes[-1]
        except: return 0, 0

    def procesar(self):
        ahora = datetime.now().strftime('%H:%M:%S')
        print(f"--- 📡 Scan Phoenix {ahora} ---")

        for p in self.pares:
            try:
                ticker = self.exchange.fetch_ticker(p)
                precio = ticker['last']
                b = self.estado[p]

                # --- Lógica de Compra inicial ---
                if b['tk'] == 0:
                    atr, last_close = self.calcular_atr(p)
                    if atr > 0 and precio > (last_close + (atr * 1.5)):
                        continue
                    
                    cantidad = self.monto_ini / precio
                    b.update({'tk': cantidad, 'pm': precio, 'ni': 1, 'pico': precio})
                    self.guardar_estado()
                    print(f"🚀 COMPRA {p} ${precio:.2f}")

                # --- Gestión de Posición ---
                else:
                    if precio > b['pico']: b['pico'] = precio
                    objetivo = b['pm'] * (1 + self.profit_objetivo / 100)

                    if precio >= objetivo and precio <= b['pico'] * (1 - (self.trailing_call / 100)):
                        ganancia = (precio * b['tk']) - (b['pm'] * b['tk'])
                        print(f"💰 VENTA {p} Ganancia ${ganancia:.2f}")
                        b.update({'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0})
                        self.guardar_estado()
                        continue

                print(f"📊 {p}: ${precio:.2f} | PM: ${b['pm']:.2f} | Niv: {b['ni']}")
            except Exception as e:
                print(f"⚠️ {p}: Error API")

# ==========================================
# 🏁 CICLO PRINCIPAL (MODO CLOUD)
# ==========================================
if __name__ == "__main__":
    print("🦅 PHOENIX HIBRID v9.0 - MODO CLOUD ACTIVO")
    
    while True:
        config = obtener_config_usuario()
        
        if config and config['hibrid_activo']:
            # El bot solo se crea e inicia si el botón en la WEB está ON
            if 'bot' not in locals():
                bot = PhoenixHybridGold(config)
            
            bot.procesar()
        else:
            print("💤 Phoenix Hibrid en espera (Inactivo en Dashboard)")
            if 'bot' in locals(): del bot # Liberamos memoria si se apaga

        time.sleep(45)