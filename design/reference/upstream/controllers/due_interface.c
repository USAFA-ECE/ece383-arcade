#include <Arduino.h>
#include <Keyboard.h>

// ======================================================
// BUTTON PINS (wire button -> GND, use INPUT_PULLUP)
// NES bit order: A,B,Select,Start,Up,Down,Left,Right
// ======================================================
const uint8_t C1_PINS[8] = {22,23,24,25,26,27,28,29};
const uint8_t C2_PINS[8] = {30,31,32,33,34,35,36,37};

// ======================================================
// FPGA EMULATED NES PORTS (host drives LATCH/CLOCK)
// ======================================================
const uint8_t EMU1_LATCH = 2;
const uint8_t EMU1_CLOCK = 3;
const uint8_t EMU1_DATA  = 4;

const uint8_t EMU2_LATCH = 5;
const uint8_t EMU2_CLOCK = 6;
const uint8_t EMU2_DATA  = 7;

// Enable/disable HID keyboard output to the Pi (HIGH = enabled)
const uint8_t MODE_PIN = 8;

// HDMI switch "button press" output (drives NPN base via resistor)
const uint8_t HDMI_SW_PIN = 9;
const uint16_t HDMI_PULSE_MS = 100; // how long to "press" the HDMI button

// ======================================================
// NES SHIFT STATE
// ======================================================
volatile uint8_t shiftReg[2] = {0xFF, 0xFF};
volatile uint8_t bitIndex[2] = {0, 0};

// ======================================================
// OPEN COLLECTOR DATA OUTPUT (mimics real NES controller)
// bit=0 => drive LOW
// bit=1 => Hi-Z (INPUT), rely on external 10k pull-up on FPGA side
// ======================================================
inline void driveData(uint8_t pin, uint8_t bitVal)
{
  if (bitVal == 0) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
  } else {
    pinMode(pin, INPUT); // Hi-Z
  }
}

// ======================================================
// READ BUTTONS (NO DEBOUNCE, USED FOR NES SNAPSHOT)
// ======================================================
inline uint8_t readButtonsRaw(const uint8_t pins[8])
{
  uint8_t pressedMask = 0;
  for (uint8_t i = 0; i < 8; i++) {
    if (digitalRead(pins[i]) == LOW) pressedMask |= (1u << i);
  }
  return (uint8_t)(~pressedMask); // NES raw: pressed=0, released=1
}

// ======================================================
// LATCH + CLOCK HANDLERS (interrupt-driven)
// ======================================================
void latchPort(uint8_t port)
{
  uint8_t raw = (port == 0) ? readButtonsRaw(C1_PINS)
                            : readButtonsRaw(C2_PINS);

  shiftReg[port] = raw;
  bitIndex[port] = 0;

  uint8_t bit0 = raw & 0x01;
  if (port == 0) driveData(EMU1_DATA, bit0);
  else           driveData(EMU2_DATA, bit0);
}

void clockPort(uint8_t port)
{
  uint8_t idx = ++bitIndex[port];

  uint8_t bitVal = 1;
  if (idx < 8) bitVal = (shiftReg[port] >> idx) & 0x01;

  if (port == 0) driveData(EMU1_DATA, bitVal);
  else           driveData(EMU2_DATA, bitVal);
}

// ISR wrappers
void isrLatch1(){ latchPort(0); }
void isrClock1(){ clockPort(0); }
void isrLatch2(){ latchPort(1); }
void isrClock2(){ clockPort(1); }

// ======================================================
// SOFTWARE DEBOUNCE FOR HID (Controller 1) + HDMI pulse logic
// ======================================================
const uint16_t TICK_US = 1000;  // 1 kHz tick
const uint8_t  DEB_MAX = 8;     // ~8 ms debounce at 1kHz

// Controller 1 debounce (all 8 buttons)
uint8_t debCntC1[8] = {0};
uint8_t stableMaskC1 = 0;       // 1=pressed, stable (NES bit positions)
uint8_t lastSentMaskC1 = 0;     // 1=pressed, last sent to Keyboard

// Controller 2 debounce: Start only
uint8_t debCntC2Start = 0;
bool stableC2StartPressed = false;

// HDMI pulse state (one pulse per "both start" press event)
bool bothStartPrev = false;
bool hdmiPulsing = false;
uint32_t hdmiPulseEndMs = 0;

inline void hdmiPressStart() {
  // Drive base HIGH -> transistor ON -> "button pressed"
  digitalWrite(HDMI_SW_PIN, HIGH);
  hdmiPulsing = true;
  hdmiPulseEndMs = millis() + HDMI_PULSE_MS;
}

inline void hdmiPressStopIfDone() {
  if (hdmiPulsing && (int32_t)(millis() - hdmiPulseEndMs) >= 0) {
    digitalWrite(HDMI_SW_PIN, LOW); // transistor OFF -> release button
    hdmiPulsing = false;
  }
}

void tick1kHz()
{
  // -------- Debounce Controller 1 (all buttons) --------
  uint8_t instantC1 = 0;
  for (uint8_t i = 0; i < 8; i++) {
    if (digitalRead(C1_PINS[i]) == LOW) instantC1 |= (1u << i);
  }

  for (uint8_t i = 0; i < 8; i++) {
    bool pressedNow = (instantC1 >> i) & 1u;

    if (pressedNow) {
      if (debCntC1[i] < DEB_MAX) debCntC1[i]++;
    } else {
      if (debCntC1[i] > 0) debCntC1[i]--;
    }

    if (debCntC1[i] == DEB_MAX) stableMaskC1 |=  (1u << i);
    if (debCntC1[i] == 0)       stableMaskC1 &= ~(1u << i);
  }

  // -------- Debounce Controller 2 Start only --------
  bool c2StartNow = (digitalRead(C2_PINS[3]) == LOW); // Start is index 3

  if (c2StartNow) {
    if (debCntC2Start < DEB_MAX) debCntC2Start++;
  } else {
    if (debCntC2Start > 0) debCntC2Start--;
  }
  if (debCntC2Start == DEB_MAX) stableC2StartPressed = true;
  if (debCntC2Start == 0)       stableC2StartPressed = false;

  // -------- HDMI pulse trigger: rising edge of "both Start stable" --------
  bool c1StartStable = (stableMaskC1 & (1u << 3)) != 0; // Start = bit3
  bool bothStartNow = c1StartStable && stableC2StartPressed;

  if (!bothStartPrev && bothStartNow && !hdmiPulsing) {
    hdmiPressStart();
  }
  bothStartPrev = bothStartNow;

  hdmiPressStopIfDone();

  // -------- HID keyboard output (Controller 1 only) --------
  if (digitalRead(MODE_PIN) == LOW) {
    if (lastSentMaskC1) {
      Keyboard.releaseAll();
      lastSentMaskC1 = 0;
    }
    return;
  }

  uint8_t changed = stableMaskC1 ^ lastSentMaskC1;

  auto handle = [&](uint8_t bit, uint8_t key) {
    if (changed & (1u << bit)) {
      if (stableMaskC1 & (1u << bit)) Keyboard.press(key);
      else                            Keyboard.release(key);
    }
  };

  // NES bits: 0 A,1 B,2 Select,3 Start,4 Up,5 Down,6 Left,7 Right
  handle(4, KEY_UP_ARROW);
  handle(5, KEY_DOWN_ARROW);
  handle(6, KEY_LEFT_ARROW);
  handle(7, KEY_RIGHT_ARROW);

  handle(0, 'a');
  handle(1, 'b');
  handle(3, KEY_RETURN);
  handle(2, ' ');

  lastSentMaskC1 = stableMaskC1;
}

void setup()
{
  // Buttons
  for (uint8_t i = 0; i < 8; i++) {
    pinMode(C1_PINS[i], INPUT_PULLUP);
    pinMode(C2_PINS[i], INPUT_PULLUP);
  }

  pinMode(MODE_PIN, INPUT_PULLUP);

  // HDMI control pin drives NPN base: LOW = off, HIGH = "press"
  pinMode(HDMI_SW_PIN, OUTPUT);
  digitalWrite(HDMI_SW_PIN, LOW);

  // Emu inputs
  pinMode(EMU1_LATCH, INPUT_PULLUP);
  pinMode(EMU1_CLOCK, INPUT_PULLUP);
  pinMode(EMU2_LATCH, INPUT_PULLUP);
  pinMode(EMU2_CLOCK, INPUT_PULLUP);

  // Emu data outputs idle released (Hi-Z)
  pinMode(EMU1_DATA, INPUT);
  pinMode(EMU2_DATA, INPUT);

  attachInterrupt(digitalPinToInterrupt(EMU1_LATCH), isrLatch1, RISING);
  attachInterrupt(digitalPinToInterrupt(EMU1_CLOCK), isrClock1, RISING);
  attachInterrupt(digitalPinToInterrupt(EMU2_LATCH), isrLatch2, RISING);
  attachInterrupt(digitalPinToInterrupt(EMU2_CLOCK), isrClock2, RISING);

  Keyboard.begin();
}

void loop()
{
  static uint32_t last = 0;
  uint32_t now = micros();
  if ((uint32_t)(now - last) >= TICK_US) {
    last += TICK_US;
    tick1kHz();
  }
}
