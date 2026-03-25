import ccxt, time, base64, json, os, requests, sys, numpy as np, hashlib
import psycopg2 # Importante para Railway
from datetime import datetime

# ==========================================
# 🌐 CONFIGURACIÓN CLOUD (RAILWAY)
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CLAVE_MAESTRA = os.getenv("CLAVE_MAESTRA", "Javier2026")

# ==========================================
# ⛽ GESTOR DE GAS Y COSECHA (POSTGRES)
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

    def registrar_venta_y_descontar(self, motor, par, ganancia):
        """Aplica lógica de Gas (20%) y registra Cosecha (80%) en la DB"""
        comision_gas = ganancia * 0.20
        cosecha = ganancia * 0.80
        
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            # 1. Descontar Gas
            cur.execute("UPDATE gas_system SET balance = balance - %s WHERE id = 1;", (comision_gas,))
            # 2. Registrar Operación en la Web (Cosecha va implícita en la ganancia)
            cur.execute("""
                INSERT INTO operaciones (motor, par, tipo, precio, ganancia) 
                VALUES (%s, %s, 'VENTA', 0, %s);
            """, (motor, par, ganancia))
            conn.commit()
            cur.close()
            conn.close()
            return comision_gas, cosecha
        except Exception as e:
            print(f"⚠️ Error DB: {e}")
            return 0.0, 0.0

# ==========================================
# 🦅 MOTOR PHOENIX HIBRID (Integrado)
# ==========================================
class PhoenixHybridGold:
    def __init__(self, capital, api_key, api_secret):
        self.db_manager = PhoenixCloudManager()
        self.cap_total = float(capital)
        self.cap_operativo = self.cap_total * 0.70
        self.monto_ini = self.cap_operativo * 0.125

        self.pares = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

        # Estado en memoria (En Railway se limpia al reiniciar, lo ideal es sync_estado_real)
        self.estado = {p: {'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0} for p in self.pares}
        self.profit_objetivo = 1.3
        self.trailing_call = 0.3

    def actualizar_balance_web(self):
        """Envía el balance actual de este motor a la tabla balance_total"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = float(balance['total'].get('USDT', 0))
            cripto = 0.0
            for p in self.pares:
                base = p.split('/')[0]
                cant = balance['total'].get(base, 0)
                if cant > 0:
                    cripto += cant * self.exchange.fetch_ticker(p)['last']
            
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                UPDATE balance_total 
                SET capital_usdt=%s, capital_cripto_usdt=%s, total_equidad=%s, ultima_actualizacion=CURRENT_TIMESTAMP 
                WHERE motor='Hybrid Gold';
            """, (usdt, cripto, usdt+cripto))
            conn.commit()
            cur.close()
            conn.close()
        except: pass

    def enviar_telegram(self, m):
        try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": m})
        except: pass

    def procesar(self):
        cliente, gas = self.db_manager.leer_gas()
        print(f"🦅 Hybrid Gold | Gas: ${gas:.2f}")

        if gas <= 0.10: return

        for p in self.pares:
            try:
                precio = self.exchange.fetch_ticker(p)['last']
                b = self.estado[p]

                # --- Lógica de COMPRA ---
                if b['tk'] == 0:
                    cantidad = self.monto_ini / precio
                    # self.exchange.create_market_buy_order(p, cantidad) # DESCOMENTAR PARA REAL
                    b.update({'tk': cantidad, 'pm': precio, 'ni': 1, 'pico': precio})
                    print(f"🚀 COMPRA {p} a ${precio}")

                # --- Lógica de VENTA ---
                else:
                    if precio > b['pico']: b['pico'] = precio
                    objetivo = b['pm'] * (1 + self.profit_objetivo / 100)

                    if precio >= objetivo and precio <= b['pico'] * (1 - (self.trailing_call / 100)):
                        ganancia = (precio * b['tk']) - (b['pm'] * b['tk'])
                        
                        # ACTUALIZAR DB (Gas y Cosecha)
                        comision, cosecha = self.db_manager.registrar_venta_y_descontar('Hybrid Gold', p, ganancia)
                        
                        self.enviar_telegram(f"💰 VENTA {p}\nGanancia: ${ganancia:.2f}\n🌾 Cosecha: ${cosecha:.2f}\n⛽ Gas: -${comision:.2f}")
                        
                        # self.exchange.create_market_sell_order(p, b['tk']) # DESCOMENTAR PARA REAL
                        b.update({'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0})

            except Exception as e:
                print(f"⚠️ Error en {p}: {e}")
        
        self.actualizar_balance_web()

if __name__ == "__main__":
    # En Railway las variables vienen del entorno, no del input()
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")
    CAPITAL = os.getenv("CAPITAL_INICIAL", "1000")

    bot = PhoenixHybridGold(CAPITAL, API_KEY, API_SECRET)
    while True:
        bot.procesar()
        time.sleep(45)