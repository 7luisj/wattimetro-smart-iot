### 🐍 Configuración del Entorno Virtual e Instalación

Para aislar las dependencias del proyecto 
y evitar conflictos con otras librerías de Python 
en el sistema, sigue estos pasos:

1. **Crear el entorno virtual:**
   bash:
   python3 -m venv env

### Instalación de dependencias

Para instalar todas las librerías necesarias de Python 
para el servidor Flask y el cliente MQTT, 
ejecuta el siguiente comando en tu terminal 
2. **(con tu entorno virtual activado):**
   bash
   pip install -r requirements.txt




Wattímetro Smart IoT ⚡📱

Un sistema IoT completo para la monitorización en tiempo real 
del consumo de energía eléctrica y el control remoto/automatizado 
de cargas a través del protocolo MQTT, 
SQLite y una interfaz web construida en Flask con Highcharts.

📋 Características Principales
Medición en Tiempo Real: 
Captura de voltaje y corriente en el microcontrolador ESP32 
y transmisión en tiempo real hacia el broker MQTT.

Control Inteligente de Cargas:
Modo Automático: Programación horaria en el servidor Python 
que activa el relé únicamente entre las 17:00 y las 05:00 horas.

Modo Manual: Interruptor remoto desde el dashboard web 
para encendido y apagado bajo demanda.

Persistencia de Datos: Almacenamiento local ligero en SQLite3 
para el registro de lecturas y estados del circuito.

Dashboard Web Interactivo:
Visualización dinámica de métricas de voltaje y corriente.
Gráfico de consumo de potencia aparente (VA) con filtro interactivo 
por fechas utilizando Highcharts.

Arquitectura Liviana: Comunicación cliente-servidor optimizada 
para reducir el sobreprocesamiento en el ESP32.

🏗️ Arquitectura del Sistema
[Sensores (V/I)] ---> [ESP32] --(MQTT / JSON)--> [Mosquitto Broker]
                                                          |
                                                    (Paho-MQTT)
                                                          v
[Navegador Web] <--- (HTTP / API REST) ---> [Servidor Flask] <---> [Base de Datos SQLite3]


📁 Estructura del Repositorio
.
├── Servidor_mqtt_flask_2.py   # Servidor principal Flask y cliente MQTT en Python
├── ESP32_mqtt_Server.ino      # Código fuente en C++ para el microcontrolador ESP32
├── templates/
│   └── index_2.html           # Dashboard e interfaz web de usuario
├── requirements.txt           # Dependencias de Python
└── basedatos_iot.db           # Base de datos SQLite (se genera automáticamente)


🛠️ Tecnologías Utilizadas
Microcontrolador: ESP32 (Arduino Framework, C++)
Backend: Python 3, Flask, Paho-MQTT, SQLite3
Frontend: HTML5, CSS3, JavaScript (ES6), Highcharts
Protocolo de Comunicación: MQTT, HTTP REST

🔌 Diagrama de Conexiones (ESP32)

Componente / Periférico
Pin ESP32
Descripción
Sensor de Voltaje
GPIO 35
Entrada analógica (Medición de Voltaje)
Sensor de Corriente
GPIO 34
Entrada analógica (Medición de Corriente)
Relé / Actuador
GPIO 32
Salida digital de control de carga
LED Indicador WiFi
GPIO 02
Salida digital para estado de conexión

🚀 Instalación y Configuración
1. Requisitos Previos
Servidor MQTT (ej. Mosquitto Broker) corriendo en la red local o Raspberry Pi.
Entorno Python 3.9+.
Arduino IDE configurado para la placa ESP32 con la librería PubSubClient.
2. Configuración del Servidor (Python/Flask)
Clona este repositorio:
git clone https://github.com/tu-usuario/wattimetro-smart-iot.git
cd wattimetro-smart-iot


Crea y activa un entorno virtual:
python3 -m venv env
source env/bin/activate  # En Linux/Raspberry Pi
# env\Scripts\activate   # En Windows


Instala las dependencias necesarias:
pip install -r requirements.txt


Ejecuta el servidor Flask:
python Servidor_mqtt_flask_2.py

El servidor web se desplegará en http://localhost:5000 o en la IP de la Raspberry Pi en tu red local.
3. Configuración del ESP32
Abre el archivo ESP32_mqtt_Server.ino en Arduino IDE.
Configura las credenciales de tu red Wi-Fi y la dirección IP del Broker MQTT:
const char* ssid = "TU_RED_WIFI";
const char* password = "TU_CONTRASEÑA";
client.setServer("192.168.1.XX", 1883); // IP de tu Broker/Raspberry Pi


Sube el programa a tu placa ESP32.
🌐 API REST Endpoints

Método		Endpoint 				Descripción
GET		/					Carga el dashboard principal index.html.
GET		/api/datos				Obtiene el último voltaje y corriente registrados.
GET		/api/wattimetro?fecha=YYYY-MM-DD	Retorna la serie de tiempo de potencia para el gráfico.
GET		/api/estado				Retorna el estado actual del control (automatico y boton1).
POST		/api/control				Recibe payload JSON para alternar modos o encender/apagar.

📡 Tópicos MQTT
sensores/esp32 (Publicado por ESP32): 
Envía lecturas en formato JSON {"voltaje": V, "corriente": I, "potencia": P}.

control/esp32 (Publicado por Python / Suscrito por ESP32): 
Recibe comandos de activación directa '1' (encender) o '0' (apagar).

