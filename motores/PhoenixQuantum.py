import ccxt, time, json, os, requests, sys, hashlib
import numpy as np
import psycopg2 
from datetime import datetime
from psycopg2.extras import RealDictCursor

# ==========================================
# 🌐 CONFIGURACIÓN ESTRATÉGICA RAILWAY
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================================
# ⛽ GESTOR DE GAS Y REGISTRO (POSTGRES)
# ==========================================
class PhoenixCloudGas:
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
            return res[0], float(res[1]) if res else (None, 0.0)
        except Exception as e:
            print(f"❌ Error al leer GAS: {e}")
            return "JAVIER CUBILLOS", 0.0

    def registrar_y_descontar(self, par, ganancia):
        comision = ganancia * 0.20
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("UPDATE gas_system SET balance = balance - %s WHERE id = 1;", (comision,))
            cur.execute("""
                INSERT INTO operaciones (motor, par, tipo, precio, ganancia) 
                VALUES ('Quantum Hedge AI', %s, 'VENTA', 0, %s);
            """, (par, ganancia))
            conn.commit()
            cur.close()
            conn.close()
            return comision
        except Exception as e:
            print(f"⚠️ Error actualizando DB: {e}")
            return 0.0

# ==========================================
# 🧠 MOTOR PHOENIX QUANTUM (Hedge AI Cloud)
# ==========================================
class PhoenixQuantumHedgeAI:
    def __init__(self, capital, api_key, api_secret):
        self.db_manager = PhoenixCloudGas()
        self.cap_total = capital
        self.cap_operativo = self.cap_total * 0.70
        self.monto_ini = self.cap_operativo * 0.125
        
        self.pares = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","LINK/USDT","FET/USDT"]
        
        self.exchange = ccxt.binance({
            'apiKey': api_key, 
            'secret': api_secret, 
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

        self.estado = {p:{'tk':0,'pm':0,'ni':0,'pico':0} for p in self.pares}

    # --- 🛰️ NUEVA FUNCIÓN: REPORTE DE BALANCE A LA WEB ---
    def actualizar_balance_web(self):
        """Calcula capital total en Binance y actualiza la tabla balance_total"""
        try:
            balance = self.exchange.fetch_balance()
            usdt_libre = float(balance['total'].get('USDT', 0))
            
            capital_en_cripto = 0.0
            for p in self.pares:
                base = p.split('/')[0]
                cantidad = balance['total'].get(base, 0)
                if cantidad > 0:
                    ticker = self.exchange.fetch_ticker(p)
                    capital_en_cripto += cantidad * ticker['last']
            
            total_equidad = usdt_libre + capital_en_cripto

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                UPDATE balance_total 
                SET capital_usdt = %s, 
                    capital_cripto_usdt = %s, 
                    total_equidad = %s, 
                    ultima_actualizacion = CURRENT_TIMESTAMP
                WHERE motor = 'Quantum Hedge AI';
            """, (usdt_libre, capital_en_cripto, total_equidad))
            conn.commit()
            cur.close()
            conn.close()
            print(f"📊 Web Actualizada | Quantum Total: ${total_equidad:.2f}")
        except Exception as e:
            print(f"⚠️ Error reporte web Quantum: {e}")

    def enviar_telegram(self, m):
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          json={"chat_id": CHAT_ID, "text": m, "parse_mode": "Markdown"})
        except: pass

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
        cliente, gas = self.db_manager.leer_gas()
        print(f"🧠 Phoenix Quantum | Cliente: {cliente} | Gas: ${gas:.2f}")

        if gas <= 0.50:
            print("🚫 SALDO DE GAS CRÍTICO. Pausando operaciones.")
            return

        for p in self.pares:
            try:
                precio = self.exchange.fetch_ticker(p)['last']
                atr, last = self.calcular_atr(p)
                profit = self.ia_profit(p, precio, atr, last)
                b = self.estado[p]

                if b['tk'] > 0:
                    if precio > b['pico']: b['pico'] = precio
                    objetivo = b['pm']*(1+profit/100)
                    if precio >= objetivo and precio <= b['pico']*(1-0.3/100):
                        ganancia = (precio*b['tk'])-(b['pm']*b['tk'])
                        comision = self.db_manager.registrar_y_descontar(p, ganancia)
                        self.enviar_telegram(f"🔴 PHOENIX QUANTUM: VENTA\n📦 Par: {p}\n💰 Ganancia: ${ganancia:.2f}\n⛽ Gas: -${comision:.2f}")
                        b.update({'tk':0,'pm':0,'ni':0,'pico':0})
                
                elif b['tk'] == 0:
                    cantidad = self.monto_ini / precio
                    b.update({'tk':cantidad, 'pm':precio, 'ni':1, 'pico':precio})
                    self.enviar_telegram(f"🟢 PHOENIX QUANTUM: COMPRA\n📦 Par: {p}\n💵 Precio: ${precio:.2f}")

            except Exception as e: print(f"⚠️ Error {p}: {e}")
        
        # Al final del proceso, reportamos a la web
        self.actualizar_balance_web()

# ==========================================
# 🏁 EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")
    CAPITAL_TOTAL = float(os.getenv("CAPITAL_INICIAL", 100))

    print("🧠 SISTEMA PHOENIX QUANTUM v10.0 ONLINE")
    bot = PhoenixQuantumHedgeAI(CAPITAL_TOTAL, API_KEY, API_SECRET)

    while True:
        try:
            bot.procesar()
            time.sleep(45)
        except Exception as e:
            print(f"⚠️ Error de ciclo: {e}")
            time.sleep(15)