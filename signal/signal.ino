#include "flag.h"
#define NET_NAME "SnakeCTF - signal"
#define WDT_TIMEOUT 10000
#define RESET_TIME_MS 300000

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <esp_task_wdt.h>

#define SERVICE_UUID "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define HINT_CHAR_UUID "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
#define URL_CHAR_UUID  "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
#define REG_CHAR_UUID  "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
#define FLAG_CHAR_UUID "6e400004-b5a3-f393-e0a9-e50e24dcca9e"

BLECharacteristic *hintChar;
BLECharacteristic *regChar;
BLECharacteristic *flagChar;
BLECharacteristic *urlChar;
BLEAdvertising *pAdvertising = nullptr;

unsigned long t0 = 0;
unsigned long startMillis = 0;

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) override {
    if (pAdvertising) pAdvertising->start();
  }
  void onDisconnect(BLEServer* pServer) override {
    if (pAdvertising) pAdvertising->start();
  }
};

void setup() {
  esp_task_wdt_config_t wdt_conf = {
    WDT_TIMEOUT,
    0,
    true
  };
  esp_task_wdt_init(&wdt_conf);
  esp_task_wdt_add(NULL);

  BLEDevice::init(NET_NAME);

  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  BLEService *pService = pServer->createService(SERVICE_UUID);

  hintChar = pService->createCharacteristic(HINT_CHAR_UUID, BLECharacteristic::PROPERTY_READ);
  regChar  = pService->createCharacteristic(REG_CHAR_UUID, BLECharacteristic::PROPERTY_WRITE);
  flagChar = pService->createCharacteristic(FLAG_CHAR_UUID, BLECharacteristic::PROPERTY_READ);
  urlChar = pService->createCharacteristic(URL_CHAR_UUID, BLECharacteristic::PROPERTY_READ);

  flagChar->setValue("Locked");
  urlChar->setValue("https://snkc.tf/OKBRUFBA");

  hintChar->setValue("NONE");

  pService->start();

  pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->start();

  startMillis = millis();
}

void loop() {
  esp_task_wdt_reset();

  unsigned long now = millis();
  uint32_t code = ((t0 ^ 0x5A5A5A5A) + 1337) ^ ((now / 1000) & 0xFFFF);
  hintChar->setValue(String(now));

  char expectedStr[16];
  sprintf(expectedStr, "%08X", code);

  for (int i = 0; i < 100; i++) {
    delay(80);
    if (millis() - startMillis < RESET_TIME_MS) {
      esp_task_wdt_reset();
    }
  }
  
  String val = regChar->getValue();
  if ((val.length() > 0) && (val == expectedStr)) {
    flagChar->setValue(FLAG);
  }
  else {
    flagChar->setValue("Locked");
  }
}

