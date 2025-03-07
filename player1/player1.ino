#include <WiFi.h>
#include <PubSubClient.h>

#include "fifo.hpp"

const char* ssid = "wifi-robot";
const char* password = "";
const char* mqtt_server = "192.168.0.103";
WiFiClient espClient;
PubSubClient client(espClient);

const int ledInputPin = 25; //D2
const int buttonOutputPin = 26;  //D3

fifo *myFifo;

void setup_wifi() {
  delay(50);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  int c=0;
  while (WiFi.status() != WL_CONNECTED) {
    c=c+1;
    Serial.print(".");
    if(c>10){
        ESP.restart(); //let's try again :(
    }
  }
  Serial.println(WiFi.localIP());
}

void connect_mqttServer() {
  while (!client.connected()) {//loop until reconnection
      if(WiFi.status() != WL_CONNECTED){//check WiFi!
        setup_wifi();
      }

      Serial.print("Attempting MQTT connection...");
      if (client.connect("PLAYER1")){ 
        Serial.println("connected!");
        // Subscribe to topics here
        client.subscribe("ping");
        client.subscribe("reactionTimes");
      } 
      else {
        //attempt not successful
        Serial.print("failed, rc=");
        Serial.print(client.state());
        Serial.println(" trying again in 2 seconds");
        delay(2000);
      }
  }
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println();

  if (String(topic) == "ping") {
    client.publish("pong", "ping");
  }
  if (String(topic) == "reactionTimes") {
    client.publish("reactionTimes", String(myFifo->pop()).c_str());
  }

}

void IRAM_ATTR ISR() {
  Serial.println("INTERRUPT WAS TRIGGERED!");

  int buttonState = digitalRead(buttonOutputPin);
  if(buttonState == 0){ //button pressed

    //int reactionTime = millis();
    int reactionTime = 100;
    myFifo->add(reactionTime);//add reaction time to FIFO

    digitalWrite(ledInputPin, HIGH);
  }else{
    digitalWrite(ledInputPin, LOW);
  }
}

void setup() {
  Serial.begin(115200);

  setup_wifi();
  client.setServer(mqtt_server, 1883);//1883 is the default port for MQTT server
  client.setCallback(callback);

  pinMode(ledInputPin, OUTPUT);
  pinMode(buttonOutputPin, INPUT_PULLUP);

  attachInterrupt(buttonOutputPin, ISR, CHANGE);

  myFifo = new fifo();

  Serial.println("SETUP IS DONE");
}

void loop() {
  if (!client.connected()) {
    connect_mqttServer();
  }
  client.loop();
}
