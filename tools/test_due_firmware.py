#!/usr/bin/env python3
"""Host behavior checks with mocked Arduino/Keyboard APIs; not MCU timing tests."""
from pathlib import Path
import tempfile,subprocess,json
root=Path(__file__).resolve().parents[1]
sketch=root/'design/reference/arcade_due_manual_switch/arcade_due_manual_switch.ino'
with tempfile.TemporaryDirectory(prefix='arcade-due-test-') as temp:
 d=Path(temp)
 (d/'Arduino.h').write_text('''#pragma once
#include <cstdint>
#include <cassert>
constexpr int LOW=0,HIGH=1,INPUT=0,OUTPUT=1,INPUT_PULLUP=2,RISING=3;
extern int levels[64],modes[64],driven[64],edges[64];
inline void pinMode(uint8_t p,int m){modes[p]=m;}
inline int digitalRead(uint8_t p){return levels[p];}
inline void digitalWrite(uint8_t p,int v){driven[p]=v;}
inline int digitalPinToInterrupt(uint8_t p){return p;}
inline void attachInterrupt(int p,void(*)(),int edge){edges[p]=edge;}
inline void noInterrupts(){} inline void interrupts(){}
inline uint32_t micros(){static uint32_t t=0;return t+=1000;}
''')
 (d/'Keyboard.h').write_text('''#pragma once
#include <set>
#include <cstdint>
constexpr uint8_t KEY_RETURN=176,KEY_UP_ARROW=218,KEY_DOWN_ARROW=217,KEY_LEFT_ARROW=216,KEY_RIGHT_ARROW=215;
struct FakeKeyboard { std::set<uint8_t> keys; void begin(){} void press(uint8_t k){keys.insert(k);} void release(uint8_t k){keys.erase(k);} void releaseAll(){keys.clear();} };
extern FakeKeyboard Keyboard;
''')
 source='''#include <Arduino.h>
#include <Keyboard.h>
#include <iostream>
int levels[64],modes[64],driven[64],edges[64];
FakeKeyboard Keyboard;
#include SKETCH
void ticks(int n){while(n--)tick1kHz();}
void released(uint8_t p){assert(modes[p]==INPUT);}
int main(){
 for(int& p:levels)p=HIGH;
 setup();
 for(int p=22;p<=37;++p)assert(modes[p]==INPUT_PULLUP);
 assert(modes[8]==INPUT && modes[9]==INPUT);
 for(int p:{2,3,5,6})assert(edges[p]==RISING);
 released(4);released(7);
 ticks(25);assert(routingReady && piSelected);
 levels[22]=LOW;ticks(8);assert(Keyboard.keys.count('a'));
 latchPort(0);released(4);clockPort(0);released(4);
 levels[30]=LOW;ticks(8);assert(Keyboard.keys.count('a'));
 levels[22]=HIGH;ticks(8);assert(Keyboard.keys.count('a'));
 levels[30]=HIGH;ticks(8);assert(!Keyboard.keys.count('a'));
 levels[22]=LOW;levels[33]=LOW;ticks(8);
 levels[8]=LOW;ticks(1);assert(!routingReady && Keyboard.keys.empty());released(4);released(7);
 ticks(20);assert(routingReady && !piSelected && Keyboard.keys.empty());
 latchPort(0);assert(modes[4]==OUTPUT && driven[4]==LOW);
 clockPort(0);released(4);
 for(int i=0;i<300;++i)clockPort(0);
 released(4);assert(bitIndex[0]==8);
 latchPort(1);released(7);
 for(int i=0;i<3;++i)clockPort(1);
 assert(modes[7]==OUTPUT && driven[7]==LOW); // P2 Start = bit 3 = D33
 levels[8]=HIGH;ticks(1);assert(!routingReady && Keyboard.keys.empty());released(4);released(7);
 ticks(20);assert(routingReady && piSelected && Keyboard.keys.count('a') && Keyboard.keys.count(KEY_RETURN));
 for(int i=0;i<12;++i){levels[8]=(i%2)?HIGH:LOW;ticks(1);assert(!routingReady && Keyboard.keys.empty());released(4);released(7);}
 assert(modes[9]==INPUT && driven[9]==LOW);
 std::cout << "PASS: upstream pin order; all 16 pull-ups; D9 unused; status debounce; exclusive HID/NES routing; both-player menu input; open-drain data; serial order; clock saturation; transition release.\\n";
}
'''.replace('SKETCH',json.dumps(str(sketch)))
 (d/'test.cpp').write_text(source)
 subprocess.run(['g++','-std=c++11','-Wall','-Wextra','-Werror','-I',str(d),str(d/'test.cpp'),'-o',str(d/'test')],check=True)
 result=subprocess.run([str(d/'test')],check=True,capture_output=True,text=True)
 print(result.stdout,end='')
 (root/'design/firmware-validation.txt').write_text(result.stdout+'\nHost mocks only. Arduino Due target compilation, interrupt latency and hardware are not verified.\n')
