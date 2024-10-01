#include <Arduino.h>

/* The frequency is 20kHz, each click has 10ms length and each pause 20ms */
#define NCLICKS 2000       // Number of clicks
#define FREQUENCY 20000
#define CLICKLENGTH 200    // 200 / 20000 Hz = 0.01s = 10ms
#define TOTALLENGTH 600    // 600 / 20000 Hz = 0.03s = 30ms
#define AUDIO_PIN 5
#define ESP32_PIN 4

/* Global Variables */
volatile uint16_t clickSampleIdx = 0;
// Frequency variables
uint8_t freqIdx = 0;
const uint16_t freqs[] = {250, 500, 1000, 2000, 4000, 8000};
// Click variables
uint8_t click[CLICKLENGTH];
volatile uint16_t clickIdx = 0;
// Control variables
volatile bool burstDone = false;
volatile bool busy = false;
// For debugging purposes
// uint64_t startTime;
// uint64_t endTime;
// float timeElapsed;

// Function prototypes
void updateclick(uint16_t freq);

void setup() {
  // Pin to send high signal to ESP32
  pinMode(ESP32_PIN, OUTPUT);
  digitalWrite(ESP32_PIN, LOW);

  // Pin to send PWM signal to audio filter
  pinMode(AUDIO_PIN, OUTPUT);
  analogWrite(AUDIO_PIN, 128);

  // Start Serial Connection
  Serial.begin(9600);

  // Timers setup
  noInterrupts();                       // Disable interrupts
  // Increase PWM frequency to 62.5kHz (max for 8-bit timer)
  TCCR0B = (TCCR0B & B11111000) | B00000001;
  // Timer 1 setup
  TCCR1A = 0;			                      // Reset entire TCCR1A register
  TCCR1B = 0;			                      // Reset entire TCCR1B register
  TCCR1B |= (1 << WGM12);               // Set CTC mode (Clear Timer on Compare Match)
  TCCR1B |= (1 << CS11);                // Set prescaler to 8
  TCNT1 = 0;			                      // Reset Timer 1 value to 0
  TIMSK1 &= ~(1 << OCIE1A);             // Disable Timer1 compare match A interrupt
  OCR1A = 100;                          // Set compare match register to 16MHz / (8 * 20000Hz) = 100  
  interrupts();                         // activate interrupts
}

void loop() {
  if (!busy && Serial.available()){
    busy = true;
    freqIdx = Serial.read() - '0';
    updateclick(freqs[freqIdx]);
    // Serial.println("Starting burst");
    // startTime = micros();
    noInterrupts();                       // Disable interrupts
    digitalWrite(ESP32_PIN, HIGH);
    TIMSK1 |= (1 << OCIE1A);              // Enable Timer1 compare match A interrupt   
    interrupts();                         // activate interrupts
  }
  if (burstDone){
    // endTime = micros();
    // timeElapsed = ((float) (endTime - startTime)) / 1000000.0 / 64; // The aditional division is required since Timer0 was modified to increase PWM frequency
    // Serial.print("Burst done in: ");
    // Serial.print(timeElapsed);
    // Serial.println(" s");
    burstDone = false;
    busy = false;
    digitalWrite(ESP32_PIN, LOW);
  }
}

ISR(TIMER1_COMPA_vect){
  if (clickSampleIdx < (uint16_t) CLICKLENGTH){
    analogWrite(AUDIO_PIN, click[clickSampleIdx]);
  }
  clickSampleIdx++;
  if (clickSampleIdx == (uint16_t) TOTALLENGTH){
    clickSampleIdx = 0;
    clickIdx++;
  }
  if (clickIdx == (uint16_t) NCLICKS){
    clickIdx = 0;
    TIMSK1 &= ~(1 << OCIE1A);            // Disable Timer1 compare match A interrupt
    burstDone = true;
  }
}

// Function definitions
void updateclick(uint16_t freq){
  // Update click array
  for (uint16_t i = 0; i < CLICKLENGTH; i++) {
    click[i] = (uint8_t) 128 + 127 * sin(2 * PI * (double) freq * i / ( (double) FREQUENCY));
  }  
  // Forward entry: helps reducing the click sound
  for (uint16_t i = 1; i < 11; i++) {
    click[i - 1] = (click[i - 1] * i + 128 * (10 - i)) / 10; 
  }
  // Backward entry: helps reducing the click sound
  for (uint16_t i = 1; i < 11; i++) {
    click[CLICKLENGTH - i] = (click[CLICKLENGTH - i] * i + 128 * (10 - i)) / 10; 
  }
}