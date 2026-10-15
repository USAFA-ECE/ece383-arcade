#include <Arduino.h>
#include <Keyboard.h>
// Adapted locally from USAFA-ECE/ece383-arcade controllers/due_interface.c
// Snapshot: 40c9750e68a3fcec678eb5b699f36182dd5195eb (2026-10-14).
// Native USB -> Pi. Silver button switches HDMI directly; D9 is unused.
// Confirm status polarity and NES ISR timing on the actual hardware.
const uint8_t C1_PINS[8] = {22,23,24,25,26,27,28,29};
const uint8_t C2_PINS[8] = {30,31,32,33,34,35,36,37};
// NES order for BOTH arrays: A B Select Start Up Down Left Right.
const uint8_t EMU1_LATCH=2, EMU1_CLOCK=3, EMU1_DATA=4;
const uint8_t EMU2_LATCH=5, EMU2_CLOCK=6, EMU2_DATA=7;
const uint8_t MODE_PIN=8;
// Default agrees with upstream MODE_PIN: HIGH = Pi selected.
// Set LOW if the measured switch status is HIGH for the FPGA instead.
const uint8_t PI_SELECTED_LEVEL=HIGH;
const uint8_t MODE_STABLE_TICKS=20; // 20 consecutive samples at 1 kHz
const uint8_t DEB_MAX=8;
volatile bool routingReady=false, piSelected=false;
volatile uint8_t shiftReg[2]={0xFF,0xFF}, bitIndex[2]={8,8};
uint8_t counters[2][8]={{0}}, stableMask[2]={0,0}, lastHidMask=0;
bool modeCandidate=false;
uint8_t modeTicks=0;

inline void driveData(uint8_t pin,uint8_t bitVal) {
  // LOW or high impedance only. External R6/R7 pull up to FPGA JA6 3.3 V.
  // Never actively drive a HIGH into the FPGA.
  digitalWrite(pin,LOW);
  pinMode(pin,bitVal ? INPUT : OUTPUT);
}
inline uint8_t readButtonsRaw(const uint8_t pins[8]) {
  uint8_t raw=0xFF;
  for(uint8_t i=0;i<8;++i) if(digitalRead(pins[i])==LOW) raw &= ~(1u<<i);
  return raw;
}
void latchPort(uint8_t port) {
  const uint8_t raw=(routingReady && !piSelected)
      ? readButtonsRaw(port ? C2_PINS : C1_PINS) : 0xFF;
  shiftReg[port]=raw; bitIndex[port]=0;
  driveData(port ? EMU2_DATA : EMU1_DATA,raw & 1u);
}
void clockPort(uint8_t port) {
  uint8_t idx=bitIndex[port];
  if(idx<8) ++idx; // Saturate: extra clocks must stay released, not wrap.
  bitIndex[port]=idx;
  const uint8_t bit=(routingReady && !piSelected && idx<8)
      ? ((shiftReg[port]>>idx)&1u) : 1;
  driveData(port ? EMU2_DATA : EMU1_DATA,bit);
}
void isrLatch1(){latchPort(0);} void isrClock1(){clockPort(0);}
void isrLatch2(){latchPort(1);} void isrClock2(){clockPort(1);}

void quiesceRouting() {
  noInterrupts();
  routingReady=false;
  for(uint8_t p=0;p<2;++p){shiftReg[p]=0xFF;bitIndex[p]=8;}
  driveData(EMU1_DATA,1); driveData(EMU2_DATA,1);
  interrupts();
  Keyboard.releaseAll(); lastHidMask=0;
}
void updateRouting() {
  const bool sample=(digitalRead(MODE_PIN)==PI_SELECTED_LEVEL);
  if(modeTicks==0 || sample!=modeCandidate) {
    modeCandidate=sample; modeTicks=1;
    // During source transitions/bounce, send input to neither device.
    quiesceRouting();
    return;
  }
  if(modeTicks<MODE_STABLE_TICKS) ++modeTicks;
  if(modeTicks==MODE_STABLE_TICKS && !routingReady) {
    noInterrupts();
    piSelected=modeCandidate;
    shiftReg[0]=shiftReg[1]=0xFF; bitIndex[0]=bitIndex[1]=8;
    driveData(EMU1_DATA,1); driveData(EMU2_DATA,1);
    routingReady=true;
    interrupts();
  }
}
void updateButtons() {
  for(uint8_t p=0;p<2;++p) for(uint8_t i=0;i<8;++i) {
    const uint8_t pin=p ? C2_PINS[i] : C1_PINS[i];
    if(digitalRead(pin)==LOW) {if(counters[p][i]<DEB_MAX) ++counters[p][i];}
    else {if(counters[p][i]>0) --counters[p][i];}
    if(counters[p][i]==DEB_MAX) stableMask[p] |= 1u<<i;
    if(counters[p][i]==0) stableMask[p] &= ~(1u<<i);
  }
}
void updateKeyboard() {
  if(!routingReady || !piSelected) {
    if(lastHidMask){Keyboard.releaseAll();lastHidMask=0;}
    return;
  }
  // Either player can navigate the Pi menu with upstream's same key map.
  // OR masks avoid releasing a key that the other player still holds.
  const uint8_t mask=stableMask[0] | stableMask[1];
  const uint8_t changed=mask ^ lastHidMask;
  const uint8_t keys[8]={'a','b',' ',KEY_RETURN,
      KEY_UP_ARROW,KEY_DOWN_ARROW,KEY_LEFT_ARROW,KEY_RIGHT_ARROW};
  for(uint8_t i=0;i<8;++i) if(changed & (1u<<i)) {
    if(mask & (1u<<i)) Keyboard.press(keys[i]);
    else Keyboard.release(keys[i]);
  }
  lastHidMask=mask;
}
void tick1kHz(){updateButtons();updateRouting();updateKeyboard();}
void setup() {
  for(uint8_t i=0;i<8;++i){pinMode(C1_PINS[i],INPUT_PULLUP);pinMode(C2_PINS[i],INPUT_PULLUP);}
  pinMode(MODE_PIN,INPUT); // R5 biases open cable LOW; U2 supplies 0/3.3 V.
  digitalWrite(9,LOW);pinMode(9,INPUT); // Unconnected, no HDMI pulse output.
  const uint8_t inputs[4]={EMU1_LATCH,EMU1_CLOCK,EMU2_LATCH,EMU2_CLOCK};
  for(uint8_t i=0;i<4;++i) pinMode(inputs[i],INPUT);
  driveData(EMU1_DATA,1);driveData(EMU2_DATA,1);
  // Preserve upstream's RISING edges; scope the target core before use.
  attachInterrupt(digitalPinToInterrupt(EMU1_LATCH),isrLatch1,RISING);
  attachInterrupt(digitalPinToInterrupt(EMU1_CLOCK),isrClock1,RISING);
  attachInterrupt(digitalPinToInterrupt(EMU2_LATCH),isrLatch2,RISING);
  attachInterrupt(digitalPinToInterrupt(EMU2_CLOCK),isrClock2,RISING);
  Keyboard.begin();
}
void loop() {
  static uint32_t last=0;
  const uint32_t now=micros();
  if((uint32_t)(now-last)>=1000){last=now;tick1kHz();}
}
