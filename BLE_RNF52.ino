/*********************************************************************
  XIAO nRF52840 BLE - LED NeoPixel
  BLE Characteristic ONLY
  Mode + Brightness + Device Info (Notify)
*********************************************************************/

#include <bluefruit.h>
#include <Adafruit_NeoPixel.h>

// ================= BLE UUID =================
#define SERVICE_UUID "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define MODE_UUID    "6E400005-B5A3-F393-E0A9-E50E24DCCA9E"
#define BRIGHT_UUID  "6E400006-B5A3-F393-E0A9-E50E24DCCA9E"
#define INFO_UUID    "6E400010-B5A3-F393-E0A9-E50E24DCCA9E"

// ================= BLE OBJECT =================
BLEService rgbService(SERVICE_UUID);
BLECharacteristic modeChar(MODE_UUID);
BLECharacteristic brightChar(BRIGHT_UUID);
BLECharacteristic infoChar(INFO_UUID);

// ================= DEVICE INFO =================
#define DEVICE_NAME     "XIAO_BLE"
#define FIRMWARE_VER    "3.2.1"
#define MODEL_ID        "08"
#define DEVICE_PICTURE  ""
#define BATTERY_LEVEL   60

// ================= NeoPixel =================
#define LED_PIN 2
#define NUM_LEDS 10
#define DEFAULT_BRIGHTNESS 80

Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);
uint32_t colors[NUM_LEDS];
uint32_t offColor;

// ================= MODE =================
enum Mode : uint8_t { OFF=0, MODE1=1, MODE2=2, MODE3=3 };
Mode currentMode = OFF;
uint8_t brightness = DEFAULT_BRIGHTNESS;
unsigned long lastUpdate;
uint8_t pos = 0;
bool state = false;

// ================= Forward =================
void runEffect();
void applyMode(Mode m);
void applyBrightness(uint8_t v);
uint16_t getInterval(Mode m);
void clearAll();
void sendDeviceInfo();

// ================= MODE CALLBACK =================
void mode_write(uint16_t conn, BLECharacteristic* chr, uint8_t* data, uint16_t len)
{
  if (!len) return;
  if (data[0] <= 3) applyMode((Mode)data[0]);
}

// ================= BRIGHT CALLBACK =================
void bright_write(uint16_t conn, BLECharacteristic* chr, uint8_t* data, uint16_t len)
{
  if (!len) return;
  applyBrightness(data[0]);
}

// ================= SETUP =================
void setup()
{
  Serial.begin(115200);

  // NeoPixel
  strip.begin();
  strip.setBrightness(brightness);
  strip.show();

  colors[0] = strip.Color(255,0,0);
  colors[1] = strip.Color(255,127,0);
  colors[2] = strip.Color(255,255,0);
  colors[3] = strip.Color(0,255,0);
  colors[4] = strip.Color(0,255,255);
  colors[5] = strip.Color(0,0,255);
  colors[6] = strip.Color(75,0,130);
  colors[7] = strip.Color(148,0,211);
  colors[8] = strip.Color(255,0,255);
  colors[9] = strip.Color(255,20,147);
  offColor = strip.Color(0,0,0);
  clearAll();

  // BLE
  Bluefruit.begin();
  Bluefruit.setTxPower(4);
  Bluefruit.setName(DEVICE_NAME);
  Bluefruit.Periph.setConnectCallback(connect_callback);

  rgbService.begin();

  modeChar.setProperties(CHR_PROPS_WRITE);
  modeChar.setWriteCallback(mode_write);
  modeChar.setFixedLen(1);
  modeChar.begin();

  brightChar.setProperties(CHR_PROPS_WRITE);
  brightChar.setWriteCallback(bright_write);
  brightChar.setFixedLen(1);
  brightChar.begin();

  // INFO CHAR (Notify)
  infoChar.setProperties(CHR_PROPS_NOTIFY);
  infoChar.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
  infoChar.setMaxLen(120);
  infoChar.begin();

  // Advertising
  Bluefruit.Advertising.addService(rgbService);
  Bluefruit.Advertising.addName();
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.start(0);

  Serial.println("BLE Device ready!");
}

void loop()
{
  if (millis() - lastUpdate >= getInterval(currentMode)) {
    lastUpdate = millis();
    runEffect();
  }
}

// ================= CONNECT CALLBACK =================
void connect_callback(uint16_t conn)
{
  Serial.println("BLE Connected");
  sendDeviceInfo();   // 灯 quăng info sang python
}

// ================= SEND INFO =================
void sendDeviceInfo()
{
  char buffer[150];
  snprintf(buffer, sizeof(buffer),
    "Battery Level=%d\n"
    "Device Name=%s\n"
    "Device Picture=%s\n"
    "Firmware Version=%s\n"
    "Model ID=%s\n",
    BATTERY_LEVEL,
    DEVICE_NAME,
    DEVICE_PICTURE,
    FIRMWARE_VER,
    MODEL_ID
  );

  infoChar.notify(buffer, strlen(buffer));
}

// ================= EFFECT =================
void applyMode(Mode m) {
  currentMode = m;
  pos = 0;
  state = false;
  clearAll();
}

void applyBrightness(uint8_t v) {
  brightness = v;
  strip.setBrightness(v);
  strip.show();
}

void runEffect()
{
  switch (currentMode) {
    case MODE1:
      state = !state;
      if(state) for(int i=0;i<NUM_LEDS;i++) strip.setPixelColor(i, colors[i]);
      else strip.fill(offColor);
      strip.show();
      break;

    case MODE2:
      clearAll();
      strip.setPixelColor(pos, colors[pos]);
      strip.show();
      pos = (pos + 1) % NUM_LEDS;
      break;

    case MODE3:
      clearAll();
      for (int i=0;i<=pos;i++) strip.setPixelColor(i, colors[i]);
      strip.show();
      pos = (pos + 1) % NUM_LEDS;
      break;

    default:
      clearAll();
  }
}

uint16_t getInterval(Mode m) {
  return (m==MODE1)?400: (m==MODE2)?80: (m==MODE3)?120: 100;
}

void clearAll() {
  strip.fill(offColor);
  strip.show();
}
