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
# ⛽ GESTOR DE BASE DE DATOS (GAS Y ESTADO)
# ==========================================
class PhoenixCloudDB:
    def __init__(self):
        self.db_url = DATABASE_URL

    def consultar_gas(self):
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("SELECT balance FROM gas_system WHERE id = 1;")
            res = cur.fetchone()
            cur.close()
            conn.close()
            return float(res[0]) if res else 0.0
        except: return 0.0

    def actualizar_gas_y_operacion(self, monto_descuento, par, monto_invertido):
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            # Descontar gas
            cur.execute("UPDATE gas_system SET balance = balance - %s WHERE id = 1;", (monto_descuento,))
            # Registrar DCA en el historial de la WEB
            cur.execute("""
                INSERT INTO operaciones (motor, par, tipo, precio, ganancia) 
                VALUES ('Cycle SuperD5', %s, 'DCA BUY', 0, %s);
            """, (par, -monto_invertido)) # Ganancia negativa porque es inversión
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"❌ Error DB: {e}")

# ==========================================
# 🦅 MOTOR PHOENIX CYCLE (SuperD5 Cloud)
# ==========================================
class PhoenixSuperD5:
    def __init__(self, capital_total, dca_mensual, api_key, api_secret):
        self.db = PhoenixCloudDB()
        self.capital_inicial = float(capital_total)
        self.dca_mensual_total = float(dca_mensual)

        self.pares_ciclo = ["SOL/USDT", "AVAX/USDT"]
        self.pares_dca_x3 = ["BTC/USDT", "ETH/USDT", "LINK/USDT", "FET/USDT"]
        self.todos_los_pares = self.pares_ciclo + self.pares_dca_x3

        self.FACTOR_BTC_ETH = 1.55
        self.FACTOR_ALT_IA = 1.75
        self.DIA_DCA = 5

        self.stop_global_pct = 0.25

        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

        # Estado en memoria (Para Railway es mejor persistir esto en una tabla luego)
        self.estado = {p: {'tk': 0.0, 'dca_fecha': ""} for p in self.todos_los_pares}

    def enviar_telegram(self, m):
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m})
        except: pass

    def procesar(self):
        gas = self.db.consultar_gas()
        ahora = datetime.now()
        mes_actual = ahora.strftime("%Y-%m")
        
        print(f"📡 {ahora.strftime('%H:%M:%S')} | Phoenix Cycle | Gas: ${gas:.2f}")

        if gas <= 0.10: 
            print("🚫 GAS INSUFICIENTE para Phoenix Cycle")
            return

        # --- LÓGICA DE COMPRA MENSUAL (DCA) ---
        if ahora.day >= self.DIA_DCA:
            monto_por_par = self.dca_mensual_total / len(self.todos_los_pares)
            
            for p in self.todos_los_pares:
                if self.estado[p]['dca_fecha'] != mes_actual:
                    try:
                        f = self.FACTOR_BTC_ETH if p in ["BTC/USDT","ETH/USDT"] else self.FACTOR_ALT_IA
                        monto_final = monto_por_par * f
                        
                        ticker = self.exchange.fetch_ticker(p)
                        precio = float(ticker['last'])
                        
                        # Ejecución Market
                        orden = self.exchange.create_market_buy_order(p, monto_final / precio)
                        
                        self.estado[p]['tk'] += float(orden['filled'])
                        self.estado[p]['dca_fecha'] = mes_actual
                        
                        # Actualizar Gas y registrar en la WEB
                        # En Cycle, el consumo de gas es pequeño por ciclo, pero 
                        # descontamos una pequeña comisión por gestión de DCA.
                        self.db.actualizar_gas_y_operacion(0.01, p, monto_final)
                        
                        self.enviar_telegram(f"🦅 PHOENIX CYCLE\n📥 DCA EJECUTADO: {p}\n💰 Inversión: ${monto_final:.2f}")
                        
                    except Exception as e:
                        print(f"❌ Error DCA {p}: {e}")

# ==========================================
# 🏁 CICLO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    # Leemos configuración de las variables de Railway
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")
    CAP_TOTAL = float(os.getenv("CAPITAL_TOTAL", 1000))
    DCA_MENSUAL = float(os.getenv("DCA_MENSUAL", 100))

    print("🦅 PHOENIX CYCLE - MODO CLOUD ACTIVO")
    
    bot = PhoenixSuperD5(CAP_TOTAL, DCA_MENSUAL, API_KEY, API_SECRET)

    while True:
        try:
            bot.procesar()
            time.sleep(60) # Scan cada minuto
        except Exception as e:
            print(f"⚠️ Error Crítico: {e}")
            time.sleep(30)