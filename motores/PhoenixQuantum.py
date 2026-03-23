import ccxt, time, base64, json, os, requests, sys, hashlib
import numpy as np
from datetime import datetime

# ================= VARIABLES DE ENTORNO (RAILWAY) =================
TOKEN = os.getenv("TELEGRAM_TOKEN", "8597680464:AAHkASdRok39ynNPXwveyWyZLpzolFbNQtw")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5152462398")
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
CAPITAL_TOTAL = float(os.getenv("CAPITAL_INICIAL", 100)) 

CLAVE_SECRETA = "PHOENIX_SECRET_2026"
ARCHIVO_GAS = "gas.txt"

def enviar_telegram(m):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": m, "parse_mode": "Markdown"},
            timeout=10
        )
    except: pass

class PhoenixGas:
    def generar_firma(self, cliente, gas):
        data = f"{cliente}:{float(gas):.2f}:{CLAVE_SECRETA}"
        return hashlib.sha256(data.encode()).hexdigest()

    def crear_gas(self, cliente, gas):
        firma = self.generar_firma(cliente, gas)
        data = {"cliente": cliente, "gas": gas, "firma": firma}
        return base64.b64encode(json.dumps(data).encode()).decode()

    def leer_gas(self):
        if not os.path.exists(ARCHIVO_GAS):
            self.guardar_gas("PHOENIX_SYSTEM", 50.0)
        with open(ARCHIVO_GAS, "r") as f:
            data = json.loads(base64.b64decode(f.read()).decode())
        if data["firma"] != self.generar_firma(data["cliente"], data["gas"]):
            print("🚨 GAS ALTERADO"); sys.exit()
        return data["cliente"], data["gas"]

    def guardar_gas(self, cliente, gas):
        with open(ARCHIVO_GAS, "w") as f:
            f.write(self.crear_gas(cliente, gas))

    def descontar(self, cliente, gas, ganancia):
        comision = ganancia * 0.20
        gas -= comision
        self.guardar_gas(cliente, max(0, gas))
        return comision, gas

class PhoenixQuantumHedgeAI:
    def __init__(self, capital, api_key, api_secret):
        self.gas_manager = PhoenixGas()
        self.cap_total = capital
        self.cap_operativo = self.cap_total * 0.70
        self.monto_ini = self.cap_operativo * 0.125
        self.pares = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","LINK/USDT","FET/USDT"]
        self.exchange = ccxt.binance({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True})
        self.estado = self.cargar_estado()

    def cargar_estado(self):
        if os.path.exists("phoenix_state.json"):
            return json.load(open("phoenix_state.json"))
        return {p:{'tk':0,'pm':0,'ni':0,'pico':0} for p in self.pares}

    def guardar_estado(self):
        json.dump(self.estado, open("phoenix_state.json","w"), indent=4)

    # LÓGICA DE IA INTEGRAL (SIN CAMBIOS)
    def ia_profit(self, par, precio, atr, last):
        vol = (atr/precio)*100 if precio else 0
        mom = ((precio-last)/last)*100 if last else 0
        base = 1.3
        if "SOL" in par or "AVAX" in par: base = 1.5
        if "LINK" in par: base = 1.7
        if "FET" in par: base = 2.2
        profit = base + (vol*0.4) + (mom*0.2)
        return max(0.8, min(profit, 3.5))

    def calcular_atr(self, par):
        try:
            ohlcv = self.exchange.fetch_ohlcv(par,'1h',limit=20)
            highs = [x[2] for x in ohlcv]; lows = [x[3] for x in ohlcv]; closes = [x[4] for x in ohlcv]
            return np.mean(np.array(highs)-np.array(lows)), closes[-1]
        except: return 0,0

    def procesar(self):
        cliente, gas = self.gas_manager.leer_gas()
        print(f"🧠 Phoenix Quantum | Gas: {gas:.2f}")

        for p in self.pares:
            try:
                precio = self.exchange.fetch_ticker(p)['last']
                atr, last = self.calcular_atr(p)
                profit = self.ia_profit(p, precio, atr, last)
                b = self.estado[p]

                if b['tk'] == 0:
                    # Lógica de compra Quantum
                    cantidad = (self.monto_ini)/precio
                    b.update({'tk':cantidad,'pm':precio,'ni':1,'pico':precio})
                    self.guardar_estado()
                    enviar_telegram(f"🟢 PHOENIX QUANTUM: COMPRA\nPar: {p}\nPrecio: ${precio:.2f}")
                else:
                    # Lógica de venta Quantum con Trailing
                    if precio > b['pico']: b['pico'] = precio
                    objetivo = b['pm']*(1+profit/100)
                    if precio >= objetivo and precio <= b['pico']*(1-0.3/100):
                        ganancia = (precio*b['tk'])-(b['pm']*b['tk'])
                        comision, gas = self.gas_manager.descontar(cliente, gas, ganancia)
                        enviar_telegram(f"🔴 PHOENIX QUANTUM: VENTA\nPar: {p}\nGanancia: ${ganancia:.2f}")
                        b.update({'tk':0,'pm':0,'ni':0,'pico':0})
                        self.guardar_estado()
            except Exception as e: print(f"⚠️ {p}: {e}")

if __name__ == "__main__":
    print("🧠 SISTEMA PHOENIX QUANTUM v9.0")
    if not API_KEY or not API_SECRET:
        print("❌ Faltan credenciales API"); sys.exit()

    bot = PhoenixQuantumHedgeAI(CAPITAL_TOTAL, API_KEY, API_SECRET)
    enviar_telegram("🚀 PHOENIX QUANTUM ONLINE\nSistema iniciado correctamente.")

    while True:
        try:
            bot.procesar()
            time.sleep(45)
        except Exception as e:
            time.sleep(10)