#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <string>

BLEServer *pServer = NULL;
BLECharacteristic *pTxCharacteristic;
bool deviceConnected = false;
bool oldDeviceConnected = false;
uint8_t txValue = 0;

// UUIDs du service et des caractéristiques
#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

// Gestion de la connexion BLE
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("Client BLE connecté !");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("Client BLE déconnecté !");
    }
};

// Gestion des données reçues
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        //std::string rxValue = pCharacteristic->getValue();
        String rxValue = pCharacteristic->getValue();  // Utilisation de String d'Arduino


        if (rxValue.length() > 0) {
            Serial.println("*********");
            Serial.print("Donnée reçue : ");
            for (int i = 0; i < rxValue.length(); i++) {
                Serial.print(rxValue[i]);
            }
            Serial.println();
            Serial.println("*********");
        }
    }
};

void setup() {
    Serial.begin(115200);

    // Initialisation du périphérique BLE
    BLEDevice::init("UART Service For ESP32");

    // Création du serveur BLE
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Création du service BLE
    BLEService *pService = pServer->createService(SERVICE_UUID);

    // Création des caractéristiques BLE
    pTxCharacteristic = pService->createCharacteristic(
                            CHARACTERISTIC_UUID_TX,
                            BLECharacteristic::PROPERTY_NOTIFY
                        );
    pTxCharacteristic->addDescriptor(new BLE2902());

    BLECharacteristic *pRxCharacteristic = pService->createCharacteristic(
                                               CHARACTERISTIC_UUID_RX,
                                               BLECharacteristic::PROPERTY_WRITE
                                           );
    pRxCharacteristic->setCallbacks(new MyCallbacks());

    // Démarrage du service et publicité BLE
    pService->start();
    pServer->getAdvertising()->start();
    Serial.println("En attente d'une connexion BLE...");
}

void loop() {
    if (deviceConnected) {
        pTxCharacteristic->setValue(&txValue, 1);
        pTxCharacteristic->notify();
        Serial.print("Envoi de : ");
        Serial.println(txValue);
        txValue++;
        delay(100); // Réduire la fréquence pour éviter la surcharge
    }

    // Gestion de la reconnexion
    if (!deviceConnected && oldDeviceConnected) {
        delay(500);
        pServer->startAdvertising();
        Serial.println("Reconnexion en cours...");
        oldDeviceConnected = deviceConnected;
    }

    // Gestion de la connexion
    if (deviceConnected && !oldDeviceConnected) {
        Serial.println("Connexion établie !");
        oldDeviceConnected = deviceConnected;
    }
}
