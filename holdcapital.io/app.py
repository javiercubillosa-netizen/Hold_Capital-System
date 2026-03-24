from flask import Flask, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# Conexión automática a Railway
DATABASE_URL = os.getenv("DATABASE_URL")

def obtener_datos_dashboard():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Obtener el Gas de Javier
        cur.execute("SELECT balance FROM gas_system WHERE id = 1;")
        gas = cur.fetchone()['balance']
        
        # 2. Obtener el Capital Total Sumado de todos los motores
        cur.execute("SELECT SUM(total_equidad) as total FROM balance_total;")
        capital = cur.fetchone()['total'] or 0.00
        
        # 3. Obtener las últimas 5 operaciones para la tabla
        cur.execute("SELECT * FROM operaciones ORDER BY fecha DESC LIMIT 5;")
        ops = cur.fetchall()
        
        cur.close()
        conn.close()
        return gas, capital, ops
    except Exception as e:
        print(f"❌ Error DB: {e}")
        return 0.0, 0.0, []

@app.route('/')
def index():
    gas, capital, operaciones = obtener_datos_dashboard()
    return render_template('index.html', 
                           gas=gas, 
                           capital=capital, 
                           operaciones=operaciones,
                           usuario="JAVIER CUBILLOS")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)