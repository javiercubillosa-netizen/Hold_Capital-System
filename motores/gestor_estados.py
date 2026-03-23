import psycopg2
import os

# Esta función conecta el motor con la base de datos de Railway
def obtener_conexion():
    try:
        # Railway proporciona esta variable automáticamente si añades PostgreSQL
        database_url = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"❌ Error de conexión a la DB: {e}")
        return None

def verificar_permiso_operacion(usuario_id, sistema_nombre):
    """
    Consulta si el interruptor del sistema está en 'Activo' en la base de datos.
    sistema_nombre puede ser: 'hibrid', 'quantum', 'cycle' o 'atlas'
    """
    conn = obtener_conexion()
    if conn:
        try:
            cur = conn.cursor()
            # Buscamos en la tabla de usuarios si el sistema específico está activo
            query = f"SELECT {sistema_nombre}_activo FROM usuarios WHERE id = %s"
            cur.execute(query, (usuario_id,))
            resultado = cur.fetchone()
            cur.close()
            conn.close()
            
            # Si el resultado es True (1), el motor tiene permiso de operar
            return resultado[0] if resultado else False
        except Exception as e:
            print(f"⚠️ Error al consultar estado: {e}")
            return False
    return False

def registrar_log_operacion(usuario_id, mensaje):
    """Guarda un registro de lo que hace el motor para que el cliente lo vea en la web"""
    conn = obtener_conexion()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO logs_actividad (usuario_id, mensaje) VALUES (%s, %s)", (usuario_id, mensaje))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ No se pudo guardar el log: {e}")