#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "ABCDEFGH";
const char* password = "12345678";
//const char* mqtt_server = "192.168.1.27"; // ej: 192.168.1.100

unsigned long actual = 0;
unsigned long anterior = 0;


WiFiClient espClient;
PubSubClient client(espClient);
String client_id = "ESP32Client";

void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(2, 0);
    delay(500);
  }

  Serial.println("WiFi conectado.");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
  client.connect(client_id.c_str());
  digitalWrite(2, 1);
}

void reconnect() {
  while (!client.connected()) {
    digitalWrite(2,0);
    Serial.print("Connecting to MQTT Broker as ");
    Serial.println(client_id.c_str());
      
    if (client.connect(client_id.c_str())) { //, mqtt_username, NULL)) {
      digitalWrite(2,1);
      Serial.println("Connected to MQTT broker");
      client.subscribe("control/esp32");
      } 
        
    else {
      Serial.print("Failed to connect to MQTT broker, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// Función Callback ultraligera en el ESP32
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.println("dentro de callback, lengh = " + String(topic));
  if (length > 0) {
    char estado = (char)payload[0]; // Lee directamente el primer carácter ('1' o '0')
    Serial.println("Mensaje Recibido = " + String(estado));
    if (estado == '1') {
      digitalWrite(32, HIGH);
      Serial.println("Comando recibido: ENCENDER (1)");
    } 
    else if (estado == '0') {
      digitalWrite(32, LOW);
      Serial.println("Comando recibido: APAGAR (0)");
    }
  }
}


float voltaje() {
  float v = 0;
  for(int i=0; i<100; i++)
  {
    v = v + analogReadMilliVolts(35); // analogRead(35);//*142;
  }
  
  return (v/100)/1000;
}

float corriente()
{
  float c = 0;
  for(int i=0; i<100; i++)
  {
    c = c + analogReadMilliVolts(34);//  analogRead(34);
  }

  return (c/100)/1000;
}


void setup() {
  delay(1000); 
  
  Serial.begin(115200);
  pinMode(35, INPUT);//sensor de voltaje
  pinMode(34, INPUT);//sensor de corriente  
  pinMode(2, OUTPUT);//led confirma conexion a internet
  pinMode(32, OUTPUT);//pinMode(32, OUTPUT);//salida a relay
  
  setup_wifi();

  
  
  client.setServer("192.168.1.27", 1883);//client.setServer("192.168.1.27", 1883);
  //client.connect(client_id.c_str());
  client.setCallback(callback);
}



void loop() {
  
  if (!client.connected()) {
    digitalWrite(2,0);
    reconnect();
    Serial.println("Reconectando...");
    }
  
  client.loop();
  actual = millis();
  
  if((actual - anterior) > 5000) {
    anterior = actual;
    
    float v = voltaje();
    float c = corriente();
    float p = v*c;
    
    String payload = "{\"voltaje\":" + String(v) + ", \"corriente\":" + String(c) + ", \"potencia\":" + String(p) + "}";
    //Publicar en el tópico 'sensores/esp32'
    client.publish("sensores/esp32", payload.c_str());
    Serial.println("payload = " + payload);
  }


}
