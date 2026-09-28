import json
import sqlite3
import threading
from flask import Flask, jsonify, render_template, request
import paho.mqtt.client as mqtt
import logging
from datetime import datetime  # <--- Importante para evaluar la hora

# Configuración de Logs
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("MQTT_Server")

DB_NAME = "basedatos_iot.db"


def set_estado_circuito(a,b):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
# Endpoint 1: Obtener último Voltaje y Corriente
            cursor.execute('''
                SELECT voltaje, corriente, potencia 
                FROM lecturas 
                ORDER BY id DESC LIMIT 1
            ''')
        rows = cursor.fetchone()
    
    
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO lecturas (voltaje, corriente, potencia, automatico, boton1) VALUES (?, ?, ?, ?, ?)",
                (rows[0], rows[1], rows[2], a, b)
            )

        conn.commit()
        
        log.info(f"Guardado: volt={rows[0]}V, corr={rows[1]}A, pot={rows[2]}VA, auto={a}, boton={b}")
    
    except Exception as e:
        log.error("Error!, en funcion set_estado_circuito(a,b):", e)



# Variables globales para el estado del circuito
def estado_circuito():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
# Endpoint 1: Obtener último estado del circuito y automatico
        cursor.execute('''
            SELECT automatico, boton1
            FROM lecturas 
            ORDER BY id DESC LIMIT 1
        ''')
        rows = cursor.fetchone()
    
    circuito = {
    "automatico": rows[0],
    "boton1": rows[1]
    }
    return circuito

def estado_relay1(a,b):
#Modo Automatico
    #circuito = estado_circuito()
    if a == 1:
        hora_actual = datetime.now().hour
        if hora_actual >= 17 or hora_actual < 5:#Encender desde las 17:00 hasta las 5:00
            set_estado_circuito(a, b)
            return "1"
        
        else:
            set_estado_circuito(a, b)
            return "0"

#Modo Manual
    else:
        set_estado_circuito(a, b)
        return "1" if b == 1 else "0"#Operador Ternario en python 

# --- 1. INICIALIZAR BASE DE DATOS ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT (datetime('now', 'localtime')),
                voltaje REAL,
                corriente REAL,
                potencia Real,
                automatico,
                boton1
            )
        ''')
        conn.commit()
    

init_db()

# --- 2. LÓGICA DE CLIENTE MQTT ---
def on_connect(client, userdata, flags, rc):
    log.info(f"Conectado al Broker MQTT con código: {rc}")
    client.subscribe("sensores/esp32")
    #client.publish("control/esp32", estado_circuito())
    
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
    except json.JSONDecodeError as e:
        log.warning("JSON inválido: %s", e)
        return

    # 2. Extraer y convertir a float
    try:
        volt = float(data['voltaje'])*162
        corr = float(data['corriente'])*(1.66/5)
    except (KeyError, TypeError, ValueError) as e:
        log.warning("Datos incompletos o no numéricos: %s (%s)", data, e)
        return

    #Calculo de potencia aparente
    pot = volt * corr
    #Recuperando datos de misma base de datos para introducir los valores 
    #automatico y boton1
    circuito = estado_circuito()
    client.publish("control/esp32", circuito["boton1"])
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            #cursor.execute("INSERT INTO lecturas (fecha, voltaje, corriente, potencia) VALUES (?, ?, ?, ?)",(datetime('now', 'localtime'), volt, corr, pot))
            cursor.execute(
                "INSERT INTO lecturas (voltaje, corriente, potencia,automatico, boton1) VALUES (?, ?, ?, ?, ?)",
                (volt, corr, pot, circuito["automatico"], circuito["boton1"])
            )

        conn.commit()
        
        log.info(f"Guardado: volt={volt}V, corr={corr}A, pot={pot}VA")
    
    except Exception as e:
        log.error("Error!, procesando mensaje:", e)

# Instancia global del cliente MQTT para publicar respuestas/comandos
client = mqtt.Client()

def run_mqtt():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()

# Ejecutar MQTT en un hilo secundario
mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
mqtt_thread.start()

# --- 3. SERVIDOR WEB FLASK ---
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/datos')
def get_data():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
# Endpoint 1: Obtener último Voltaje y Corriente
        cursor.execute('''
            SELECT voltaje, corriente 
            FROM lecturas 
            ORDER BY id DESC LIMIT 1
        ''')
        rows = cursor.fetchone()
    
    if rows:
        return jsonify({"voltaje": rows[0], "corriente": rows[1]})
    
    return jsonify({"voltaje": 0.0, "corriente": 0.0})


# Endpoint 2: Obtener Potencia por fecha para Highcharts
@app.route('/api/wattimetro')
def get_wattimetro():
    fecha = request.args.get('fecha')
    if not fecha:
        return jsonify({"potencia": []})
        
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%s', fecha) * 1000, potencia 
            FROM lecturas 
            WHERE date(fecha) = date(?)
            ORDER BY fecha ASC
        ''', (fecha,))
        rows = cursor.fetchall()
    

    
# Formato esperado por Highcharts: [[timestamp1, potencia1], [timestamp2, potencia2], ...]
    datos_potencia = [[r[0], r[1]] for r in rows]
    return jsonify({"potencia": datos_potencia})


# Endpoint 3: Obtener Estado del Control
@app.route('/api/estado')
def get_estado():
    return jsonify(estado_circuito())

# Endpoint 4: Cambiar Modo o Estado (POST desde index.html)
@app.route('/api/control', methods=['POST'])
def post_control():

    payload = request.get_json()

    if payload:
        '''
        if 'automatico' in payload:
            
            
            #estado_circuito['manual'] = int(payload['manual'])
            #estado_circuito['automatico'] = 0 if estado_circuito['manual'] == 1 else 1 #operacion ternaria en python
            
        elif 'boton1' in payload:
            boton = int(payload['boton1'])
            #estado_circuito['boton1'] = int(payload['boton1'])
        '''
        relay1 = estado_relay1(int(payload['automatico']), int(payload['boton1']))#retorna 1, si automatico y esta en el horario, sino manual
        #set_estado_circuito(int(payload['automatico']), int(payload['boton1']))
        
        # Enviar comando al ESP32 por MQTT
        client.publish("control/esp32", relay1)
        return jsonify({"success": True, "estado": relay1})

    return jsonify({"success": False}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

