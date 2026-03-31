import ccxt, time, base64, json, os, requests, sys, hashlib, signal
import numpy as np
from datetime import datetime

# ==========================================
# 🔑 CONFIGURACIÓN DESDE RAILWAY (VARIABLES)
# ==========================================
CLIENTE = os.getenv("CLIENTE", "JAVIER CUBILLOS")
DESARROLLADOR = "CRYPTOHOLD"

# Variables de Seguridad y Conexión (Desde el panel de Railway)
TOKEN = os.getenv("TELEGRAM_TOKEN", "8597680464:AAHkASdRok39ynNPXwveyWyZLpzolFbNQtw")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5152462398")
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
CAP_TOTAL = float(os.getenv("CAPITAL_TOTAL", 0))

def limpiar_pantalla():
    pass # Innecesario en la nube

# ==========================================
# 🔐 GESTIÓN DE GAS Y PERSISTENCIA
# ==========================================
class PhoenixAdmin:
    def __init__(self):
        # Usamos /data/ si configuraste el Volumen en Railway, sino local.
        self.ruta_gas = "/data/gas_holding.txt" if os.path.exists("/data") else "gas_holding.txt"
        if not os.path.exists(self.ruta_gas):
            self.guardar_gas(20.0)

    def consultar_gas(self):
        try:
            with open(self.ruta_gas, "r") as f:
                return float(base64.b64decode(f.read().strip()).decode())
        except: return 0.0

    def guardar_gas(self, valor):
        encriptado = base64.b64encode(str(round(valor, 2)).encode()).decode()
        with open(self.ruta_gas, "w") as f: f.write(encriptado)

# ==========================================
# 🦅 MOTOR PHOENIX HOLDING (CLOUD ADAPTED)
# ==========================================
class PhoenixHolding:
    def __init__(self, capital_total, api_key, api_secret):
        self.admin = PhoenixAdmin()
        self.cap_total = float(capital_total)
        self.cap_trabajo = self.cap_total * 0.80 
        
        # Estrategia de Holding: Pares principales
        self.pares = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "LINK/USDT", "FET/USDT"]
        
        self.profit_obj = 1.3      
        self.cosecha_porc = 80.0    

        self.exchange = ccxt.binance({
            'apiKey': api_key, 
            'secret': api_secret, 
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        self.archivo_estado = "/data/holding_state.json" if os.path.exists("/data") else "holding_state.json"
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
        if gas <= 0.10: return

        ahora = datetime.now().strftime('%H:%M:%S')
        print(f"--- 🦅 REVISIÓN HOLDING | {ahora} | GAS: ${gas:.2f} ---")

        for p in self.pares:
            try:
                ticker = self.exchange.fetch_ticker(p)
                precio = ticker['last']
                data = self.estado[p]

                # Aquí el bot ejecuta la lógica de monitoreo
                if not data['comprado']:
                    print(f"📡 {p}: Esperando señal de entrada...")
                else:
                    print(f"📊 {p}: HOLDING | PM: ${data['pm']:,.2f} | Precio: ${precio:,.2f}")
                
                # Sincronizar estado periódicamente
                self.guardar_estado()
            except Exception as e:
                print(f"⚠️ Error en {p}: {e}")

# ==========================================
# 🚀 EJECUCIÓN CONTINUA
# ==========================================
if __name__ == "__main__":
    print(f"🦅 MOTOR HOLDING INICIADO PARA {CLIENTE}")
    
    if not API_KEY or CAP_TOTAL == 0:
        print("❌ ERROR CRÍTICO: Faltan variables API_KEY o CAPITAL_TOTAL.")
        sys.exit(1)

    bot = PhoenixHolding(CAP_TOTAL, API_KEY, API_SECRET)
    bot.enviar_telegram(f"🦅 Phoenix Holding Online para {CLIENTE}")

    while True:
        bot.procesar()
        # En Holding, el ciclo puede ser más lento (ej. cada 2 minutos) para evitar bloqueos de IP
        time.sleep(120)
