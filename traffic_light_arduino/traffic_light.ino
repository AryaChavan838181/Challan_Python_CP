const int buttonPin = 7;
const int greenLED = 2;
const int yellowLED = 3;
const int redLED = 4;

int currentLED = 0;
bool buttonPressed = false;

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);
  pinMode(redLED, OUTPUT);

  Serial.begin(9600);
  Serial.println("Setup complete");

  currentLED = 0;
  updateLEDs();
}

void loop() {
  int reading = digitalRead(buttonPin);

  if (reading == LOW && !buttonPressed) {  
    buttonPressed = true;
    currentLED = (currentLED + 1) % 3;      // Cycle through 0,1,2
    updateLEDs();
    Serial.print("LED number: ");
    Serial.println(currentLED + 1);
    delay(200);  // debounce delay
  }

  if (reading == HIGH) {
    buttonPressed = false; 
  }
}

void updateLEDs() {
  digitalWrite(greenLED, currentLED == 0 ? HIGH : LOW);
  digitalWrite(yellowLED, currentLED == 1 ? HIGH : LOW);
  digitalWrite(redLED, currentLED == 2 ? HIGH : LOW);
}
