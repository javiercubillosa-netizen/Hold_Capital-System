import ccxt, time, base64, json, os, requests, sys, signal
from datetime import datetime

# ==========================================
# 🔑 CONFIGURACIÓN DINÁMICA (RAILWAY ENV)
# ==========================================
# Estos valores los toma de la pestaña "Variables" en Railway
CLIENTE = os.getenv("CLIENTE", "JAVIER CUBILLOS")
TOKEN = os.getenv("TELEGRAM_TOKEN", "8597680464:AAHkASdRok39ynNPXwveyWyZLpzolFbNQtw")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5152462398")

# API Keys de Binance (Configurarlas en Railway)
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
CAPITAL_USDT = float(os.getenv("CAPITAL_TOTAL", 100)) # Valor por defecto 100

class PhoenixAdmin:
    def __init__(self):
        # Usamos persistencia en Railway si configuraste un Volume, sino local
        self.archivo = "/data/gas_balance.txt" if os.path.exists("/data") else "gas_balance.txt"
        if not os.path.exists(self.archivo):
            self.guardar_gas(20.0)

    def consultar_gas(self):
        try:
            with open(self.archivo, "r") as f:
                return float(base64.b64decode(f.read().strip()).decode())
        except: return 0.0

    def guardar_gas(self, valor):
        encriptado = base64.b64encode(str(round(valor, 2)).encode()).decode()
        with open(self.archivo, "w") as f: f.write(encriptado)

class PhoenixHolding:
    def __init__(self, api_key, api_secret, cap_total):
        self.admin = PhoenixAdmin()
        self.cap_trabajo = float(cap_total) * 0.80
        self.pares = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "LINK/USDT", "FET/USDT"]
        self.profit_obj = 1.3
        self.cosecha_porc = 80.0

        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        self.archivo_estado = "/data/phoenix_state.json" if os.path.exists("/data") else "phoenix_state.json"
        self.estado = self.cargar_estado()

    def cargar_estado(self):
        if os.path.exists(self.archivo_estado):
            try:
                with open(self.archivo_estado, 'r') as f: return json.load(f)
            except: pass
        return {p: {'comprado': False, 'pm': 0.0, 'cant': 0.0, 'recompras': 0, 'last_p': 0.0} for p in self.pares}

    def guardar_estado(self):
        with open(self.archivo_estado, 'w') as j: json.dump(self.estado, j, indent=4)

    def enviar_telegram(self, m):
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m}, timeout=5)
        except: pass

    def procesar(self):
        gas = self.admin.consultar_gas()
        if gas <= 0.10: 
            print("⛽ SIN GAS - PAUSADO"); return

        for p in self.pares:
            try:
                ticker = self.exchange.fetch_ticker(p)
                precio = ticker['last']
                data = self.estado[p]

                # LÓGICA DE COMPRA (SIMPLIFICADA PARA NUBE)
                if not data['comprado']:
                    monto_u = max(11.0, (self.cap_trabajo * 0.10) / len(self.pares))
                    # Aquí iría la ejecución real de Binance...
                    print(f"📡 Monitoreando {p} a ${precio}")

                # LÓGICA DE COSECHA (VENTA AL 80%)
                if data['comprado'] and precio >= data['pm'] * (1 + self.profit_obj/100):
                    # Ejecutar Venta
                    ganancia = (precio - data['pm']) * (data['cant'] * 0.8)
                    gas -= (ganancia * 0.20)
                    self.admin.guardar_gas(gas)
                    self.enviar_telegram(f"💰 COSECHA {p}: +${ganancia:.2f}")
                    # Reset...
            except Exception as e:
                print(f"⚠️ Error en {p}: {e}")

# ==========================================
# EJECUCIÓN CONTINUA (MODO SERVER)
# ==========================================
if __name__ == "__main__":
    print(f"🦅 MOTOR PHOENIX INICIADO PARA {CLIENTE}")
    if not API_KEY or not API_SECRET:
        print("❌ ERROR: Faltan API Keys en Variables de Entorno.")
        sys.exit(1)
        
    bot = PhoenixHolding(API_KEY, API_SECRET, CAPITAL_USDT)
    while True:
        bot.procesar()
        time.sleep(60) # Ciclo de 1 minuto para no saturar la API
