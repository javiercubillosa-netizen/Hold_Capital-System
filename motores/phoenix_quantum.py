import ccxt, time, base64, json, os, requests, sys, hashlib, signal
import numpy as np
from datetime import datetime

# ==========================================
# 🔑 CONFIGURACIÓN DESDE RAILWAY (VARIABLES)
# ==========================================
CLIENTE = os.getenv("CLIENTE", "JAVIER CUBILLOS")
DESARROLLADOR = "CRYPTOHOLD"
CLAVE_MAESTRA = os.getenv("CLAVE_MAESTRA", "Javier2026")
CLAVE_SECRETA_GAS = "PHOENIX_SECRET_2026"

TOKEN = os.getenv("TELEGRAM_TOKEN", "8597680464:AAHkASdRok39ynNPXwveyWyZLpzolFbNQtw")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5152462398")

# API KEYS y Capital
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
CAP_TOTAL = float(os.getenv("CAPITAL_TOTAL", 0))

def limpiar_pantalla():
    pass # Innecesario en la nube

# ==========================================
# 🔐 GESTIÓN DE GAS (RUTAS PERSISTENTES)
# ==========================================
class PhoenixGas:
    def __init__(self):
        # Si existe la carpeta /data (Volumen Railway), la usamos
        self.ruta = "/data/gas.txt" if os.path.exists("/data") else "gas.txt"

    def generar_firma(self, cliente, gas):
        data = f"{cliente}:{float(gas):.2f}:{CLAVE_SECRETA_GAS}"
        return hashlib.sha256(data.encode()).hexdigest()

    def leer_gas(self):
        if not os.path.exists(self.ruta):
            self.guardar_gas(CLIENTE, 20.0)
        try:
            with open(self.ruta, "r") as f:
                data = json.loads(base64.b64decode(f.read()).decode())
            if data["firma"] != self.generar_firma(data["cliente"], data["gas"]):
                print("🚨 ALERTA: FIRMA DE GAS INVÁLIDA"); return CLIENTE, 0.0
            return data["cliente"], data["gas"]
        except: return CLIENTE, 0.0

    def guardar_gas(self, cliente, gas):
        firma = self.generar_firma(cliente, gas)
        data = {"cliente": cliente, "gas": gas, "firma": firma}
        with open(self.ruta, "w") as f:
            f.write(base64.b64encode(json.dumps(data).encode()).decode())

    def descontar(self, cliente, gas, ganancia):
        comision = ganancia * 0.20
        nuevo_gas = max(0, gas - comision)
        self.guardar_gas(cliente, nuevo_gas)
        return comision, nuevo_gas

# ==========================================
# 🦅 MOTOR PHOENIX QUANTUM HEDGE AI (CLOUD)
# ==========================================
class PhoenixQuantumAI:
    def __init__(self, cap_ingresado, api_key, api_secret):
        self.gas_manager = PhoenixGas()
        self.cap_total = float(cap_ingresado)
        self.cap_trabajo = self.cap_total * 0.80 
        self.monto_ini_bloque = (self.cap_trabajo * 0.10) / 6 

        self.pares = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","LINK/USDT","FET/USDT"]

        self.exchange = ccxt.binance({
            'apiKey': api_key, 
            'secret': api_secret, 
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        self.archivo_estado = "/data/quantum_state.json" if os.path.exists("/data") else "quantum_state.json"
        self.estado = self.cargar_estado()

    def cargar_estado(self):
        if os.path.exists(self.archivo_estado):
            try: return json.load(open(self.archivo_estado))
            except: pass
        return {p:{'tk':0,'pm':0,'ni':0,'pico':0} for p in self.pares}

    def guardar_estado(self):
        with open(self.archivo_estado, 'w') as j: json.dump(self.estado, j, indent=4)

    def enviar_telegram(self, m):
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m}, timeout=5)
        except: pass

    # ... (calcular_atr e ia_profit_dinamico se mantienen iguales)
    def calcular_atr(self, par):
        try:
            ohlcv = self.exchange.fetch_ohlcv(par,'1h',limit=20)
            highs = [x[2] for x in ohlcv]; lows = [x[3] for x in ohlcv]
            return np.mean(np.array(highs)-np.array(lows)), ohlcv[-1][4]
        except: return 0,0

    def ia_profit_dinamico(self, par, precio, atr, last):
        vol = (atr/precio)*100 if precio else 0
        base = 1.3
        if "SOL" in par or "AVAX" in par: base = 1.6
        if "FET" in par: base = 2.0
        profit = base + (vol * 0.5)
        return max(1.1, min(profit, 4.0))

    def procesar(self):
        cliente, gas = self.gas_manager.leer_gas()
        if gas <= 0.10: return

        for p in self.pares:
            try:
                precio = self.exchange.fetch_ticker(p)['last']
                atr, last = self.calcular_atr(p)
                profit_ia = self.ia_profit_dinamico(p, precio, atr, last)
                b = self.estado[p]

                # LÓGICA DE TRADING (RESUMIDA PARA EL LOG)
                if b['tk'] == 0:
                    print(f"📡 {p} buscando entrada IA...")
                    # Ejecutar compra real si hay saldo...
                else:
                    # Lógica DCA y Venta...
                    print(f"📊 {p}: ${precio:,.2f} | Profit IA: {profit_ia:.2f}%")
            except: pass

# ==========================================
# INICIO AUTOMÁTICO
# ==========================================
if __name__ == "__main__":
    print(f"🧠 PHOENIX QUANTUM AI ACTIVO PARA {CLIENTE}")
    
    if not API_KEY or CAP_TOTAL == 0:
        print("❌ ERROR: Faltan Variables de Entorno (API_KEY o CAPITAL).")
        sys.exit(1)

    bot = PhoenixQuantumAI(CAP_TOTAL, API_KEY, API_SECRET)
    while True:
        bot.procesar()
        time.sleep(45)
