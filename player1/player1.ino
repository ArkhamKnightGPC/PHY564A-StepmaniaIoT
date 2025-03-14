#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "minHeap.hpp"
#include "esp_timer.h"

const int ledInputPins[4] = {26, 13, 16, 12};
const int buttonOutputPins[4] = {25, 14, 17, 4};

minHeap arrowsColumns[4]; // Arrow arrival times

BLEServer* pServer = NULL;
BLECharacteristic* txCharacteristic = NULL; // Transmit characteristic
BLECharacteristic* rxCharacteristic = NULL; // Receive characteristic
bool deviceConnected = false;
bool oldDeviceConnected = false;
uint32_t value = 0;

const int ledPin = 2; // Use the appropriate GPIO pin for your setup

#define ESP_UUID "19b10000-e8f2-537e-4f6c-d104768a1214"
#define TX_UUID "19b10001-e8f2-537e-4f6c-d104768a1214" // Send data
#define RX_UUID "19b10002-e8f2-537e-4f6c-d104768a1214" // Receive data

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    deviceConnected = true;
  };

  void onDisconnect(BLEServer* pServer) override {
    deviceConnected = false;
  }
};

// Callback class to handle received messages on RX_UUID
class MyCharacteristicCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* rxCharacteristic) override {
    uint8_t* receivedBytes = (uint8_t*)rxCharacteristic->getData(); // Get raw byte array
    size_t length = rxCharacteristic->getLength(); // Get data length

    if (length % 4 != 0) {
      Serial.println("Error: Received data length is not a multiple of 4!");
      return;
    }

    Serial.print("Received ");
    Serial.print(length / 4);
    Serial.println(" float values:");
    int column;
    for (size_t i = 0; i < length; i += 4) {
      float value;
      memcpy(&value, receivedBytes + i, sizeof(float)); // Convert 4 bytes to float

      if(i == 0){//this indicates the column!!
        column = (int)value;
      }else{//this represents an arrow!
        arrowsColumns[column].insert(value);
      }

      Serial.println(value, 6); // Print float with 6 decimal places
    }
  }
};

// Function to send messages using TX_UUID
void sendMessage(const char* message) {
  if (deviceConnected) {
    txCharacteristic->setValue(message);
    txCharacteristic->notify();
    Serial.print("Sent message: ");
    Serial.println(message);
  }
}

void IRAM_ATTR ButtonEvent() {
  Serial.println("INTERRUPT WAS TRIGGERED!");

  for(int i=0; i<4; i++){
    int buttonState = digitalRead(buttonOutputPins[i]);
    if(buttonState == 0){ //button pressed
      
      int64_t esp_time = esp_timer_get_time();
      float reactionTime = float(esp_time);
      float arrowTime = arrowsColumns[i].extractMin();

      if(abs(reactionTime - arrowTime) < 2 || true){
        String message = "HIT " + String(i) + " " + String(arrowTime) + " " + String(reactionTime);
        sendMessage(message.c_str());//arrow has been popped from heap! we send message and move on!
      }else{
        arrowsColumns[i].insert(arrowTime); //insert time back into minHeap
      }

      digitalWrite(ledInputPins[i], HIGH);
    }else{
      digitalWrite(ledInputPins[i], LOW);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  for(int i=0; i<4; i++){
    pinMode(ledInputPins[i], OUTPUT);
    pinMode(buttonOutputPins[i], INPUT_PULLUP);
    attachInterrupt(buttonOutputPins[i], ButtonEvent, FALLING);
  }

  BLEDevice::init("STEPMANIAplayer1");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  BLEService *pService = pServer->createService(ESP_UUID);

  // Create a BLE Characteristic for TX
  txCharacteristic = pService->createCharacteristic(
                      TX_UUID,
                      BLECharacteristic::PROPERTY_READ   |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );

  // Create a BLE Characteristic for RX
  rxCharacteristic = pService->createCharacteristic(
                      RX_UUID,
                      BLECharacteristic::PROPERTY_WRITE
                    );

  // Register callback for RX_UUID
  rxCharacteristic->setCallbacks(new MyCharacteristicCallbacks());

  // Add descriptors
  txCharacteristic->addDescriptor(new BLE2902());
  rxCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(ESP_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);  
  BLEDevice::startAdvertising();
  Serial.println("Waiting for client connection...");
}

void loop() {
  // Handle connection status
  if (!deviceConnected && oldDeviceConnected) {
    Serial.println("Device disconnected.");
    delay(500);
    pServer->startAdvertising(); 
    Serial.println("Start advertising");
    oldDeviceConnected = deviceConnected;
  }
  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
    Serial.println("Device Connected");
  }
}
