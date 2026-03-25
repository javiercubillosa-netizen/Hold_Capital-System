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
# ⛽ GESTOR DE GAS Y REGISTRO (POSTGRES)
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

    def registrar_y_descontar(self, par, ganancia):
        """Descuenta el 20% de gas y registra la operación en la web"""
        comision = ganancia * 0.20
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            # 1. Actualizar Gas
            cur.execute("UPDATE gas_system SET balance = balance - %s WHERE id = 1;", (comision,))
            # 2. Registrar en la tabla de operaciones para la Web
            cur.execute("""
                INSERT INTO operaciones (motor, par, tipo, precio, ganancia) 
                VALUES ('Quantum Hedge AI', %s, 'VENTA', 0, %s);
            """, (par, ganancia))
            conn.commit()
            cur.close()
            conn.close()
            return comision
        except Exception as e:
            print(f"⚠️ Error DB: {e}")
            return 0.0

    def actualizar_balance_web(self, usdt, cripto):
        """Actualiza la tarjeta de Capital Real-Time en la web"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("""
                UPDATE balance_total 
                SET capital_usdt=%s, capital_cripto_usdt=%s, total_equidad=%s, ultima_actualizacion=CURRENT_TIMESTAMP 
                WHERE motor='Quantum Hedge AI';
            """, (usdt, cripto, usdt+cripto))
            conn.commit()
            cur.close()
            conn.close()
        except: pass

# ==========================================
# 🧠 MOTOR PHOENIX QUANTUM (Integrado)
# ==========================================
class PhoenixQuantumHedgeAI:
    def __init__(self, capital, api_key, api_secret):
        self.db_manager = PhoenixCloudManager()
        self.cap_total = float(capital)
        self.cap_operativo = self.cap_total * 0.70
        self.monto_ini = self.cap_operativo * 0.125

        self.pares = ["BTC/USDT","ETH/USDT","SOL/USDT","AVAX/USDT","LINK/USDT","FET/USDT"]
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

        # Estado en memoria (Sync con Binance en cada ciclo)
        self.estado = {p:{'tk':0,'pm':0,'ni':0,'pico':0} for p in self.pares}
        self.base_dca = self.cap_total * 0.05
        self.max_recompras = 10
        self.trailing_call = 0.3

    def enviar_telegram(self, m):
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m, "parse_mode": "Markdown"})
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
        print(f"🧠 Quantum Hedge AI | Gas: ${gas:.2f}")

        if gas <= 0.10: return

        # Sync de balance para la Web
        try:
            balance = self.exchange.fetch_balance()
            usdt_libre = float(balance['total'].get('USDT', 0))
            cap_cripto = 0.0
            
            for p in self.pares:
                precio = self.exchange.fetch_ticker(p)['last']
                atr, last = self.calcular_atr(p)
                profit = self.ia_profit(p, precio, atr, last)
                
                # Reporte de capital para la web
                base_asset = p.split('/')[0]
                cant_real = balance['total'].get(base_asset, 0)
                cap_cripto += (cant_real * precio)

                b = self.estado[p]
                
                # --- LÓGICA DE TRADING (Tu lógica v9.5 intacta) ---
                if b['tk'] == 0:
                    vol = (atr/precio)*100 if precio else 0
                    hedge = 0.5 if vol > 3 else 1
                    cantidad = (self.monto_ini * hedge) / precio
                    # self.exchange.create_market_buy_order(p, cantidad) # DESCOMENTAR PARA REAL
                    b.update({'tk': cantidad, 'pm': precio, 'ni': 1, 'pico': precio})
                
                else:
                    if precio > b['pico']: b['pico'] = precio
                    
                    # DCA
                    caida = (1 - (precio / b['pm'])) * 100
                    if caida >= 3 and b['ni'] < self.max_recompras:
                        monto_rec = self.base_dca * (1.4 ** b['ni'])
                        nueva_cant = b['tk'] + (monto_rec / precio)
                        # self.exchange.create_market_buy_order(p, monto_rec/precio) # REAL
                        b['pm'] = ((b['pm'] * b['tk']) + monto_rec) / nueva_cant
                        b['tk'] = nueva_cant
                        b['ni'] += 1
                    
                    # VENTA
                    objetivo = b['pm']*(1+profit/100)
                    if precio >= objetivo and precio <= b['pico']*(1-0.3/100):
                        ganancia = (precio*b['tk'])-(b['pm']*b['tk'])
                        comision = self.db_manager.registrar_y_descontar(p, ganancia)
                        self.enviar_telegram(f"💰 VENTA REAL {p}\nGanancia: ${ganancia-comision:.2f}\n⛽ Gas: -${comision:.2f}")
                        # self.exchange.create_market_sell_order(p, b['tk']) # REAL
                        b.update({'tk':0,'pm':0,'ni':0,'pico':0})

            self.db_manager.actualizar_balance_web(usdt_libre, cap_cripto)

        except Exception as e: print(f"⚠️ Error Quantum: {e}")

if __name__ == "_main_":
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SEC = os.getenv("BINANCE_API_SECRET")
    CAPITAL = os.getenv("CAPITAL_INICIAL", "1000")

    bot = PhoenixQuantumHedgeAI(CAPITAL, API_KEY, API_SEC)
    print("🟢 PHOENIX QUANTUM CLOUD ACTIVO")
    while True:
        bot.procesar()
        time.sleep(45)