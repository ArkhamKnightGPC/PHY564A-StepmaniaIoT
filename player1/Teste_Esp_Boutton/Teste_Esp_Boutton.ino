#define BUTTON1_PIN  26  
#define LED1_PIN     25  
#define BUTTON2_PIN  13  
#define LED2_PIN     14  
#define BUTTON3_PIN  34  
#define LED3_PIN     15  
#define BUTTON4_PIN  35  
#define LED4_PIN     21  


void IRAM_ATTR handleButton1() {
    Serial.println("Bouton 1------------ appuyé");
}

void IRAM_ATTR handleButton2() {
    Serial.println("Bouton 2------------ appuyé");
}

void IRAM_ATTR handleButton3() {
    Serial.println("Bouton 3------------ appuyé");
}

void IRAM_ATTR handleButton4() {
    Serial.println("Bouton 4------------ appuyé");
}



void setup() {
    Serial.begin(115200);  // Initialisation du moniteur série

    pinMode(LED1_PIN, OUTPUT);
    pinMode(LED2_PIN, OUTPUT);
    pinMode(LED3_PIN, OUTPUT);
    pinMode(LED4_PIN, OUTPUT);

    pinMode(BUTTON1_PIN, INPUT_PULLUP);
    pinMode(BUTTON2_PIN, INPUT_PULLUP);
    pinMode(BUTTON3_PIN, INPUT_PULLUP);
    pinMode(BUTTON4_PIN, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(BUTTON1_PIN), handleButton1, FALLING);
    attachInterrupt(digitalPinToInterrupt(BUTTON2_PIN), handleButton2, FALLING);
    attachInterrupt(digitalPinToInterrupt(BUTTON3_PIN), handleButton3, FALLING);
    attachInterrupt(digitalPinToInterrupt(BUTTON4_PIN), handleButton4, FALLING);
}

void loop() {
  if (digitalRead(BUTTON1_PIN) == LOW) {
      digitalWrite(LED1_PIN, HIGH);  // Allumer la LED
  } else {
      digitalWrite(LED1_PIN, LOW);   // Éteindre la LED
  }

  if (digitalRead(BUTTON2_PIN) == LOW) {
      digitalWrite(LED2_PIN, HIGH);  // Allumer la LED
  } else {
      digitalWrite(LED2_PIN, LOW);   // Éteindre la LED
  }
  if (digitalRead(BUTTON3_PIN) == LOW) {
      digitalWrite(LED3_PIN, HIGH);  // Allumer la LED
  } else {
      digitalWrite(LED3_PIN, LOW);   // Éteindre la LED
  }

  if (digitalRead(BUTTON4_PIN) == LOW) {
      digitalWrite(LED4_PIN, HIGH);  // Allumer la LED
  } else {
      digitalWrite(LED4_PIN, LOW);   // Éteindre la LED
  }

  delay(10);
}

