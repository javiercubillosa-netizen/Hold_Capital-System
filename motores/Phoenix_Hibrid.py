import ccxt, time, json, os, requests, sys, numpy as np
import psycopg2 
from datetime import datetime
from psycopg2.extras import RealDictCursor

# ==========================================
# 🌐 CONFIGURACIÓN ESTRATÉGICA RAILWAY
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")

# ==========================================
# ⛽ CLASE DE GESTIÓN DE GAS (POSTGRES)
# ==========================================
class PhoenixGas:
    def __init__(self):
        self.db_url = DATABASE_URL

    def leer_gas(self):
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("SELECT balance FROM gas_system WHERE id = 1;")
            res = cur.fetchone()
            cur.close()
            conn.close()
            return float(res[0]) if res else 0.0
        except Exception as e:
            print(f"❌ Error al leer GAS: {e}")
            return 0.0

    def registrar_operacion_y_descontar(self, motor, par, ganancia):
        comision = ganancia * 0.20
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("UPDATE gas_system SET balance = balance - %s WHERE id = 1;", (comision,))
            cur.execute("""
                INSERT INTO operaciones (motor, par, tipo, precio, ganancia) 
                VALUES (%s, %s, 'VENTA', 0, %s);
            """, (motor, par, ganancia))
            conn.commit()
            cur.close()
            conn.close()
            print(f"✅ Gas actualizado: -${comision:.2f} | Historial guardado.")
        except Exception as e:
            print(f"⚠️ Error al actualizar Gas/Historial: {e}")

# ==========================================
# 🦅 MOTOR PHOENIX HIBRID (Integración Web)
# ==========================================
class PhoenixHybridGold:
    def __init__(self, config):
        self.api_key = config['api_key_cifrada']
        self.api_secret = config['api_secret_cifrada']
        
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })

        self.pares = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]
        self.gas_manager = PhoenixGas()
        self.estado = {p: {'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0} for p in self.pares}
        
        self.profit_objetivo = 1.3
        self.trailing_call = 0.3
        self.monto_ini = 125.0

    # --- 🛰️ NUEVA FUNCIÓN: REPORTE A LA WEB ---
    def actualizar_balance_web(self):
        """Calcula el capital en Binance y actualiza la tabla balance_total"""
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
                WHERE motor = 'Hybrid Gold';
            """, (usdt_libre, capital_en_cripto, total_equidad))
            conn.commit()
            cur.close()
            conn.close()
            print(f"📊 Web Actualizada | Hybrid Gold Total: ${total_equidad:.2f}")
        except Exception as e:
            print(f"⚠️ Error reporte web: {e}")

    def procesar(self):
        ahora = datetime.now().strftime('%H:%M:%S')
        saldo_gas = self.gas_manager.leer_gas()
        
        print(f"--- 📡 Scan Phoenix Hybrid | Gas: ${saldo_gas:.2f} | {ahora} ---")

        if saldo_gas <= 0.50:
            print("🚫 GAS INSUFICIENTE. Operaciones pausadas.")
            return

        for p in self.pares:
            try:
                ticker = self.exchange.fetch_ticker(p)
                precio = ticker['last']
                b = self.estado[p]

                if b['tk'] > 0:
                    if precio > b['pico']: b['pico'] = precio
                    objetivo = b['pm'] * (1 + self.profit_objetivo / 100)
                    if precio >= objetivo and precio <= b['pico'] * (1 - (self.trailing_call / 100)):
                        ganancia = (precio * b['tk']) - (b['pm'] * b['tk'])
                        self.gas_manager.registrar_operacion_y_descontar('Hybrid Gold', p, ganancia)
                        b.update({'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0})

                elif b['tk'] == 0:
                    cantidad = self.monto_ini / precio
                    b.update({'tk': cantidad, 'pm': precio, 'ni': 1, 'pico': precio})
                    print(f"🚀 COMPRA EJECUTADA {p} @ ${precio:.2f}")

            except Exception as e:
                print(f"⚠️ Error en par {p}: {e}")
        
        # Al finalizar el escaneo de todos los pares, informamos a la web
        self.actualizar_balance_web()

# ==========================================
# 🏁 CICLO PRINCIPAL
# ==========================================
def obtener_config_usuario():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE email = 'admin@holdcapital.io' LIMIT 1")
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    except: return None

if __name__ == "__main__":
    print("🦅 PHOENIX HIBRID v10.0 - MODO DASHBOARD ACTIVO")
    bot = None
    
    while True:
        config = obtener_config_usuario()
        if config and config.get('hibrid_activo'):
            if bot is None:
                bot = PhoenixHybridGold(config)
            bot.procesar()
        else:
            print("💤 Phoenix Hibrid en espera (OFF en Dashboard)")
            bot = None 

        time.sleep(45)