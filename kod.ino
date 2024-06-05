int i = 0;
int sensorLow = 0;
int sensorHigh = 4095;
int brightness = 0;
int sensorValue = 0;
int outsideSensorValue = 0;
int outsideBrightness = 0;
int sensorBrightness = 0;

const int fotoResPin = 2;
const int ledPin = 15;
const int ledPin2 = 4;
const int fotoResPinOutside = 13;
bool rising = true;

void setup() {
  delay(5000);
  Serial.begin(9600);
  pinMode(fotoResPin, INPUT); // Nastavíme pin pre fotorezistor ako vstup
  pinMode(fotoResPinOutside, INPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(ledPin, OUTPUT); // Nastavíme vstavanú LED ako výstup
  Serial.println("Hello");
  Serial.println("INITIALISATION...");
  sensorValue = analogRead(fotoResPin);
  sensorLow = sensorValue;
  analogWrite(ledPin,255);
  analogWrite(ledPin2,255);
  delay(100);
  sensorValue = analogRead(fotoResPin);
  sensorHigh = sensorValue;
  Serial.println("Normal value: ");
  Serial.println(sensorLow);
  Serial.println("Highest value: ");
  Serial.println(sensorHigh);
  Serial.println("........");
  delay(5000);
}

void loop() {
  sensorValue = analogRead(fotoResPin);
  outsideSensorValue = analogRead(fotoResPinOutside);
  
  // Mapovanie hodnôt zo senzora na rozsah PWM (0-255)
  
  outsideBrightness = map(outsideSensorValue, 0, 4095, 0, 100);
  sensorBrightness = map(sensorValue, sensorLow, sensorHigh, 0, 100);
  //if(brightness < 0){
    //brightness = 0;
  //} else if(brightness > 255){
    //brightness = 255;
  //}
  if(brightness == 0){
    rising = true;
  } else if(brightness == 255){
    rising = false;
  }
  if(rising){
    brightness++;
  } else if(!rising){
    brightness--;
  }
  Serial.print("LedResistor ");
  Serial.print(sensorBrightness);
  //Serial.print("LED brightness value: ");
  //Serial.println(brightness);
  Serial.print(" OutResistor ");
  Serial.println(outsideBrightness);
  analogWrite(ledPin, brightness); // Nastavíme intenzitu svietenia LED
  analogWrite(ledPin2,brightness);
  delay(1000);
}
