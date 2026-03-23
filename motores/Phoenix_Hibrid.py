import ccxt, time, json, os, requests, sys, numpy as np
from datetime import datetime

# ==========================================
# 🌐 CONFIG SERVIDOR (CAMBIAR IP)
# ==========================================
SERVER_URL = "http://127.0.0.1:5000"

# ==========================================
# 🔑 SEGURIDAD
# ==========================================
CLIENTE = "PHOENIX_SYSTEM"
CLAVE_MAESTRA = "Javier2026"
TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

def enviar_telegram(m):
    try:
        if TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          json={"chat_id": CHAT_ID, "text": m})
    except:
        pass

# ==========================================
# 🌐 ESTADO DESDE SERVIDOR
# ==========================================
def obtener_estado(cliente):
    try:
        r = requests.post(f"{SERVER_URL}/api/estado",
                          json={"cliente": cliente})

        data = r.json()

        if data["status"] != "ok":
            print(f"🛑 SISTEMA DETENIDO: {data['status']}")
            sys.exit()

        return data["gas"]

    except Exception as e:
        print("❌ ERROR CONEXIÓN SERVIDOR:", e)
        sys.exit()

# ==========================================
# 🌐 DESCONTAR GAS EN SERVIDOR (PRO)
# ==========================================
def descontar_gas(cliente, comision):
    try:
        r = requests.post(f"{SERVER_URL}/api/descontar",
                          json={
                              "cliente": cliente,
                              "consumo": comision
                          })

        data = r.json()

        if data.get("status") != "ok":
            print("🛑 ERROR EN DESCUENTO:", data)

    except Exception as e:
        print("⚠️ ERROR DESCONTANDO GAS:", e)

# ==========================================
# 🦅 MOTOR PHOENIX
# ==========================================
class PhoenixHybridGold:

    def __init__(self, capital, api_key, api_secret):

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

        self.archivo_estado = "phoenix_state.json"
        self.estado = self.cargar_estado()

        self.profit_objetivo = 1.3
        self.trailing_call = 0.3
        self.max_recompras = 10
        self.base_dca = self.cap_total * 0.05

    def cargar_estado(self):
        if os.path.exists(self.archivo_estado):
            with open(self.archivo_estado, 'r') as f:
                return json.load(f)
        return {p: {'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0} for p in self.pares}

    def guardar_estado(self):
        with open(self.archivo_estado, 'w') as f:
            json.dump(self.estado, f, indent=4)

    def calcular_atr(self, par):
        try:
            ohlcv = self.exchange.fetch_ohlcv(par, timeframe='1h', limit=20)
            highs = [x[2] for x in ohlcv]
            lows = [x[3] for x in ohlcv]
            closes = [x[4] for x in ohlcv]
            atr = np.mean(np.array(highs) - np.array(lows))
            return atr, closes[-1]
        except:
            return 0, 0

    def procesar(self):
        cliente = CLIENTE
        gas = obtener_estado(cliente)

        ahora = datetime.now().strftime('%H:%M:%S')
        print(f"\n--- 📡 Scan Phoenix {ahora} | ⛽ Gas: ${gas:.2f} ---")

        if gas <= 0:
            print("🛑 SISTEMA DETENIDO POR GAS")
            return

        for p in self.pares:
            try:
                ticker = self.exchange.fetch_ticker(p)
                precio = ticker['last']
                b = self.estado[p]

                # ==========================================
                # 🟢 COMPRA INICIAL
                # ==========================================
                if b['tk'] == 0:
                    atr, last_close = self.calcular_atr(p)

                    if atr > 0 and precio > (last_close + (atr * 1.5)):
                        print(f"⏳ {p}: ATR bloquea entrada")
                        continue

                    cantidad = self.monto_ini / precio

                    b.update({'tk': cantidad, 'pm': precio, 'ni': 1, 'pico': precio})
                    self.guardar_estado()

                    enviar_telegram(f"🚀 COMPRA {p} ${precio:.2f}")

                # ==========================================
                # 🔴 GESTIÓN POSICIÓN
                # ==========================================
                else:
                    if precio > b['pico']:
                        b['pico'] = precio

                    objetivo = b['pm'] * (1 + self.profit_objetivo / 100)

                    # ======================================
                    # 💰 VENTA + DESCUENTO SaaS
                    # ======================================
                    if precio >= objetivo:
                        if precio <= b['pico'] * (1 - (self.trailing_call / 100)):

                            ganancia = (precio * b['tk']) - (b['pm'] * b['tk'])

                            comision = ganancia * 0.20

                            # 🔥 DESCUENTO EN SERVIDOR
                            descontar_gas(cliente, comision)

                            print(f"💰 Ganancia: ${ganancia:.2f}")
                            print(f"⛽ Comisión: ${comision:.2f}")

                            enviar_telegram(f"💰 VENTA {p} Ganancia ${ganancia:.2f}")

                            b.update({'tk': 0.0, 'pm': 0.0, 'ni': 0, 'pico': 0.0})
                            self.guardar_estado()
                            continue

                    # ======================================
                    # 📉 DCA INTELIGENTE
                    # ======================================
                    caida = (1 - (precio / b['pm'])) * 100

                    if caida >= 70:
                        step = 3
                    elif caida >= 50:
                        step = 5
                    else:
                        step = 3

                    if caida >= step and b['ni'] < self.max_recompras:

                        if "BTC" in p or "ETH" in p:
                            factor = 1.55
                        else:
                            factor = 1.75

                        monto_rec = self.base_dca * (factor ** b['ni'])

                        nueva_cant = b['tk'] + (monto_rec / precio)

                        b['pm'] = ((b['pm'] * b['tk']) + monto_rec) / nueva_cant
                        b['tk'] = nueva_cant
                        b['ni'] += 1
                        b['pico'] = precio

                        self.guardar_estado()

                        enviar_telegram(f"📉 DCA {p} nivel {b['ni']} | monto ${monto_rec:.2f}")

                print(f"📊 {p}: ${precio:.2f} | PM: ${b['pm']:.2f} | Niv: {b['ni']}")

            except Exception as e:
                print(f"⚠️ {p}: Error API")

# ==========================================
# 🏁 MAIN
# ==========================================
if __name__ == "__main__":
    try:
        print("🦅 PHOENIX HYBRID GOLD v8.1 (SaaS PRO)")

        if input("🔑 Clave: ") != CLAVE_MAESTRA:
            sys.exit()

        api = input("API KEY: ")
        sec = input("SECRET: ")
        cap = input("Capital: ")

        bot = PhoenixHybridGold(cap, api, sec)

        while True:
            bot.procesar()
            time.sleep(45)

    except KeyboardInterrupt:
        print("\n🛑 SISTEMA DETENIDO POR USUARIO")
        print("💾 Cierre profesional correcto")