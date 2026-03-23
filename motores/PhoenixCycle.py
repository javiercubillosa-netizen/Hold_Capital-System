import ccxt, time, base64, json, os, requests, sys, hashlib
import numpy as np
from datetime import datetime

# ================= AJUSTE PARA CLOUD (RAILWAY) =================
# Datos de seguridad y acceso leídos desde la pestaña "Variables"
CLIENTE = "JAVIER CUBILLOS"
CLAVE_MAESTRA = os.getenv("CLAVE_MAESTRA", "Javier2026")
TOKEN = os.getenv("TELEGRAM_TOKEN", "8597680464:AAHkASdRok39ynNPXwveyWyZLpzolFbNQtw")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5152462398")

# Credenciales de Exchange y Configuración de Capital
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
CAP_TOTAL = float(os.getenv("CAPITAL_TOTAL", 1000))
DCA_MENSUAL = float(os.getenv("DCA_MENSUAL", 100))

# ==========================================
# 🔐 GAS (Lógica Original Intacta)
# ==========================================
class PhoenixAdmin:
    def __init__(self):
        self.archivo = "gas_balance.txt"
        if not os.path.exists(self.archivo):
            self.guardar_gas(20.0)

    def consultar_gas(self):
        try:
            with open(self.archivo, "r") as f:
                return float(base64.b64decode(f.read().strip()).decode())
        except:
            return 0.0

    def guardar_gas(self, valor):
        encriptado = base64.b64encode(str(round(valor, 2)).encode()).decode()
        with open(self.archivo, "w") as f:
            f.write(encriptado)

# ==========================================
# 🦅 MOTOR PHOENIX CYCLE (SuperD5)
# ==========================================
class PhoenixSuperD5:
    def __init__(self, capital_total, dca_mensual, api_key, api_secret):
        self.admin = PhoenixAdmin()
        self.capital_total = float(capital_total)
        self.capital_inicial = float(capital_total)
        self.dca_mensual_total = float(dca_mensual)

        self.pares_ciclo = ["SOL/USDT", "AVAX/USDT"]
        self.pares_dca_x3 = ["BTC/USDT", "ETH/USDT", "LINK/USDT", "FET/USDT"]
        self.todos_los_pares = self.pares_ciclo + self.pares_dca_x3

        self.FACTOR_BTC_ETH = 1.55
        self.FACTOR_ALT_IA = 1.75
        self.DIA_DCA = 5

        # 🔐 PROTECCIÓN (Valores originales)
        self.stop_global_pct = 0.25
        self.stop_activo_pct = 0.35

        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True, 'recvWindow': 15000}
        })

        self.archivo_state = "phoenix_d5_state.json"
        self.estado = self.cargar_estado()

    def validar_api(self):
        try:
            balance = self.exchange.fetch_balance()
            total = balance['total'].get('USDT', 0)
            print(f"🔐 API OK | Balance: ${total}")
            return True
        except Exception as e:
            print(f"❌ ERROR API: {e}")
            return False

    def check_stop_global(self):
        # Lógica original de cálculo de capital y stop
        capital_actual = self.calcular_capital_actual()
        limite = self.capital_inicial * (1 - self.stop_global_pct)
        if capital_actual <= limite:
            self.enviar_telegram("🛑 STOP GLOBAL ACTIVADO EN PHOENIX CYCLE")
            return True
        return False

    def calcular_capital_actual(self):
        total = 0
        try:
            balance = self.exchange.fetch_balance()
            total += balance['total'].get('USDT', 0)
            for p in self.todos_los_pares:
                base = p.split('/')[0]
                cantidad = balance['total'].get(base, 0)
                if cantidad > 0:
                    ticker = self.exchange.fetch_ticker(p)
                    total += cantidad * ticker['last']
            return total
        except: return self.capital_inicial

    def cargar_estado(self):
        if os.path.exists(self.archivo_state):
            with open(self.archivo_state, 'r') as f: return json.load(f)
        return {p: {'tk': 0.0, 'pm': 0.0, 'dca_fecha': ""} for p in self.todos_los_pares}

    def guardar_estado(self):
        with open(self.archivo_state, 'w') as f: json.dump(self.estado, f, indent=4)

    def enviar_telegram(self, m):
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m})
        except: pass

    def procesar(self):
        if self.check_stop_global(): return
        gas = self.admin.consultar_gas()
        ahora = datetime.now()
        
        print(f"📡 {ahora.strftime('%H:%M:%S')} | Phoenix Cycle | Gas: ${gas:.2f}")

        if gas <= 0.10: return

        mes_actual = ahora.strftime("%Y-%m")

        if ahora.day >= self.DIA_DCA:
            monto_por_par = self.dca_mensual_total / len(self.todos_los_pares)
            for p in self.todos_los_pares:
                if self.estado[p]['dca_fecha'] != mes_actual:
                    try:
                        f = self.FACTOR_BTC_ETH if p in ["BTC/USDT","ETH/USDT"] else self.FACTOR_ALT_IA
                        monto_final = monto_por_par * f
                        
                        # Ejecución de DCA Market
                        ticker = self.exchange.fetch_ticker(p)
                        precio = float(ticker['last'])
                        
                        orden = self.exchange.create_market_buy_order(p, monto_final / precio)
                        self.estado[p]['tk'] += float(orden['filled'])
                        self.estado[p]['dca_fecha'] = mes_actual
                        self.guardar_estado()
                        
                        self.enviar_telegram(f"📥 DCA EJECUTADO: {p} por ${monto_final:.2f}")
                    except Exception as e:
                        print(f"❌ Error DCA {p}: {e}")

        # Consumo de Gas por ciclo
        gas -= 0.001
        self.admin.guardar_gas(gas)

# ================= 🏁 EJECUCIÓN =================
if __name__ == "__main__":
    print("🦅 PHOENIX CYCLE - MODO CLOUD ACTIVO")
    
    if not API_KEY or not API_SECRET:
        print("❌ Error: Faltan llaves de Binance en Railway."); sys.exit()

    bot = PhoenixSuperD5(CAP_TOTAL, DCA_MENSUAL, API_KEY, API_SECRET)

    if not bot.validar_api():
        sys.exit()

    enviar_telegram("🦅 PHOENIX CYCLE ONLINE\nEstrategia SuperD5 iniciada.")

    while True:
        try:
            bot.procesar()
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(30)