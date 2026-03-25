import ccxt, time, base64, json, os, requests, sys, numpy as np, hashlib
import psycopg2
from datetime import datetime

# ==========================================
# 🌐 CONFIGURACIÓN CLOUD (RAILWAY)
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CLAVE_MAESTRA = os.getenv("CLAVE_MAESTRA", "Javier2026")

# ==========================================
# ⛽ GESTOR DE GAS Y ESTADO (POSTGRES)
# ==========================================
class PhoenixCloudManager:
    def __init__(self):
        self.db_url = DATABASE_URL

    def leer_gas(self):
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("SELECT cliente, balance FROM gas_system WHERE id = 1;")
            res = cur.fetchone()
            cur.close()
            conn.close()
            return res[0], float(res[1]) if res else ("PHOENIX_SYSTEM", 0.0)
        except:
            return "PHOENIX_SYSTEM", 0.0

    def actualizar_balance_web(self, motor, usdt, cripto):
        """Envía los datos de capital a la tabla balance_total de la web"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("""
                UPDATE balance_total 
                SET capital_usdt=%s, capital_cripto_usdt=%s, total_equidad=%s, ultima_actualizacion=CURRENT_TIMESTAMP 
                WHERE motor=%s;
            """, (usdt, cripto, usdt+cripto, motor))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error balance web: {e}")

# ==========================================
# 🚀 ESTRATEGIA HOLDING DCA PRO
# ==========================================
class PhoenixHoldingDCA_PRO:
    def __init__(self, exchange, capital, mensual):
        self.exchange = exchange
        self.capital = float(capital)
        self.mensual = float(mensual)
        self.db_manager = PhoenixCloudManager()
        
        # En la nube, usamos un diccionario en memoria. 
        # El sync_real se encargará de mantenerlo veraz con Binance.
        self.pares_holding = ["BTC/USDT","ETH/USDT","LINK/USDT","FET/USDT"]
        self.estado = {p:{"cantidad":0,"precio_promedio":0,"invertido":0} for p in self.pares_holding}
        
        self.portafolio = {"BTC/USDT":0.4,"ETH/USDT":0.3,"LINK/USDT":0.15,"FET/USDT":0.15}

    def sync_real(self):
        try:
            balance = self.exchange.fetch_balance()
            capital_cripto = 0.0
            usdt_libre = float(balance['total'].get('USDT', 0))

            for p in self.estado:
                base = p.split("/")[0]
                real_qty = balance['total'].get(base, 0)
                ticker = self.exchange.fetch_ticker(p)['last']
                
                # Actualizamos estado en memoria según realidad de Binance
                self.estado[p]["cantidad"] = real_qty
                capital_cripto += (real_qty * ticker)

            # Reportar a la web bajo el nombre 'Cycle SuperD5' o 'Holding'
            self.db_manager.actualizar_balance_web('Cycle SuperD5', usdt_libre, capital_cripto)

        except Exception as e:
            print("⚠️ Error sync holding:", e)

    def dca(self):
        if datetime.now().day != 1: return
        # Lógica DCA original...
        pass

    def take_profit(self):
        # Lógica Take Profit original...
        pass

# ==========================================
# 🦅 MOTOR HIBRID (Trading Activo)
# ==========================================
class PhoenixHybridGold:
    def __init__(self, capital, api, secret):
        self.db_manager = PhoenixCloudManager()
        self.cap_total = float(capital)
        self.exchange = ccxt.binance({
            'apiKey': api, 'secret': secret, 'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True, 'defaultType': 'spot'}
        })
        self.pares = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT"]
        self.estado = {p:{'tk':0,'pm':0,'ni':0,'pico':0} for p in self.pares}

    def procesar(self):
        cliente, gas = self.db_manager.leer_gas()
        print(f"📡 Phoenix Pro | Gas: ${gas:.2f}")
        
        # Reportar balance de trading activo a la web
        try:
            bal = self.exchange.fetch_balance()
            usdt = bal['total'].get('USDT', 0)
            self.db_manager.actualizar_balance_web('Hybrid Gold', usdt, 0) # Simplificado para el hibrido
        except: pass

        for p in self.pares:
            try:
                precio = self.exchange.fetch_ticker(p)['last']
                # Lógica de trading original...
            except: pass

# ==========================================
# 🏁 MAIN CLOUD
# ==========================================
if __name__ == "__main__":
    # Variables desde Railway
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SEC = os.getenv("BINANCE_API_SECRET")
    CAPITAL = float(os.getenv("CAPITAL_INICIAL", 1000))
    MENSUAL = float(os.getenv("INVERSION_MENSUAL", 100))

    bot = PhoenixHybridGold(CAPITAL, API_KEY, API_SEC)
    holding = PhoenixHoldingDCA_PRO(bot.exchange, CAPITAL, MENSUAL)

    print("🦅 PHOENIX PRO MAX ONLINE")

    while True:
        try:
            bot.procesar()
            holding.sync_real()
            holding.dca()
            holding.take_profit()
            time.sleep(45)
        except Exception as e:
            print(f"⚠️ Error ciclo: {e}")
            time.sleep(10)