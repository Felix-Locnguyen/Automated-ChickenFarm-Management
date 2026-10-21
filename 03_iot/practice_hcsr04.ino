#include <Wire.h>
#include <LiquidCrystal_I2C>
#include "DHT.h"

#define LED_RED 26      // LED đỏ nối GPIO26
#define LED_GREEN 27    // LED xanh nối GPIO27

#define TRIG_PIN 5 // TRIG của HC-SR04 nối GPIO5
#define ECHO_PIN 18 // ECHO cử HC-SR04 nối  GPIO18

LiquidCrystal_I2C lcd(0x27, 16, 2);
void setup() {
  Serial.begin(115200); // Tốc độ truyền dữ liệu 
  lcd.init(); // Khởi tạo màn hình
  lcd.backlight(); // bật đền nền lcd
  
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  }

float getDistance() {
  // Phát xung trigger
  //Đặt chân TRIG xuống mức thấp trong 2 micro giây để chuẩn bị phát xung.
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  // Phát một xung cao trong 10 micro giây ở chân TRIG. Đây là tín hiệu để cảm biến phát ra sóng siêu âm.
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN,LOW);

  // Đo thời gian echo 
  long duration = pulseIn(ECHO_PIN, HIGH);
  // Tính khoảng cách (cm)
  float = distance = duration * 0.034 / 2;
  return distance;
}

void loop() {
  float distance  = getDistance();
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Disst:");
  lcd.print(distance );
  lcd.print(" cm");

  //  logic led theo khoang cach 
  if (distance < 10000) {
    digitalWrite(LED_RED,HIGH);
    digitalWrite(LED_GREEN,LOW);
  }
  else {
    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN,HIGH);
  }
  
  delay(1000);
}

