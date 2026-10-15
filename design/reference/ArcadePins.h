#pragma once
#include <Arduino.h>
// Matches upstream 40c9750e68a3fcec678eb5b699f36182dd5195eb.
// Runtime implementation is in arcade_due_manual_switch/arcade_due_manual_switch.ino.
namespace Arcade {
// Per player: A, B, SELECT, START, UP, DOWN, LEFT, RIGHT.
constexpr uint8_t controls[2][8]={{22,23,24,25,26,27,28,29},{30,31,32,33,34,35,36,37}};
constexpr uint8_t latch[2]={2,5}, clock[2]={3,6}, data[2]={4,7};
constexpr uint8_t status=8;
// D9 is not connected. The silver switch button is not a Due input.
inline void configureInputs(){
 for(uint8_t p=0;p<2;++p){
  for(uint8_t i=0;i<8;++i)pinMode(controls[p][i],INPUT_PULLUP);
  pinMode(latch[p],INPUT);pinMode(clock[p],INPUT);
  digitalWrite(data[p],LOW);pinMode(data[p],INPUT); // Hi-Z idle, never drive HIGH.
 }
 pinMode(status,INPUT);digitalWrite(9,LOW);pinMode(9,INPUT);
}
}
