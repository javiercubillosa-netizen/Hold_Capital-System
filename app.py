import os
from flask import Flask, render_template, request, flash, redirect, url_for
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

app = Flask(__name__)
# En Railway, esto se configura en la pestaña 'Variables'
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'clave_temporal_de_desarrollo_123')

# --- LÓGICA DE CIFRADO ---
def generar_suite_cifrado(password_usuario):
    password = password_usuario.encode()
    salt = b'hold_capital_salt_fijo' 
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return Fernet(key)

# --- RUTAS DE LA PÁGINA ---

# 1. Página de Inicio (Redirige al Dashboard)
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# 2. El Dashboard (El panel con las tarjetas de Phoenix y Atlas)
@app.route('/dashboard')
def dashboard():
    # Datos simulados que luego vendrán de tu base de datos
    datos_usuario = {
        "bono": 50.00,
        "estados": {
            "hibrid": "Inactivo",
            "quantum": "Inactivo",
            "cycle": "Inactivo",
            "atlas": "Inactivo"
        }
    }
    return render_template('dashboard.html', usuario=datos_usuario)

# 3. Configuración de API Keys (Donde el cliente pone sus llaves)
@app.route('/configurar-sistema', methods=['GET', 'POST'])
def configurar_keys():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        pass_ops = request.form.get('pass_ops')
        
        try:
            suite = generar_suite_cifrado(pass_ops)
            api_cifrada = suite.encrypt(api_key.encode()).decode()
            secret_cifrada = suite.encrypt(api_secret.encode()).decode()
            
            # Aquí guardarás api_cifrada y secret_cifrada en PostgreSQL de Railway
            flash("¡Credenciales cifradas y guardadas con éxito!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash("Error al procesar las llaves. Intente nuevamente.", "danger")
            
    return render_template('configurar.html')

if __name__ == '__main__':
    # Puerto dinámico para que Railway pueda asignar uno
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)