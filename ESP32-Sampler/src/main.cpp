#include <arduino.h>
// #include "freertos/semphr.h"

// defines
#define NCLICKS 500
#define CYCLEDURATION 30 // ms
#define SAMPLERATE 10000 // Hz
#define BUFFERSIZE 128 // 128 samples of 2 bytes each, 256 bytes in total
#define INTERRUPT_PIN 2
#define RXD2 16
#define TXD2 17
#define CONTROLSERIALBAUD 115200
#define TRANSMISSIOSERIALBAUD 960000
#define READPIN 4

// Task related variables
TaskHandle_t sendTask;
hw_timer_t *samplerTimer = NULL;
volatile bool clicksdone = false;

// ADC related variables
volatile bool bufferA = true;
volatile uint16_t adcBufferA[BUFFERSIZE];
volatile uint16_t adcBufferB[BUFFERSIZE];
volatile uint buffersSent = 0;
volatile uint adcRead = 0;
volatile uint16_t adcBufferIdx = 0;
volatile uint16_t readVal = 0;


void sendBuffer(){
  // Choose the right bufffer, which is not in use by the ADC
  if (!bufferA){
    // Send the buffer to the Raspberry Pi
    Serial2.write((uint8_t *) adcBufferA, BUFFERSIZE * 2);
    // Make sure everything is received
    // Serial2.flush();

  }
  else{
    // Send the buffer to the Raspberry Pi
    Serial2.write((uint8_t *) adcBufferB, BUFFERSIZE * 2);
    // Make sure everything is received
    // Serial2.flush();
  }
}


void readADC(){
  // Read ADC value and write it to the SD card
  readVal = analogRead(READPIN);
  if (bufferA){
    adcBufferA[adcBufferIdx++] = readVal;
  }
  else{
    adcBufferB[adcBufferIdx++] = readVal;
  }
  if (adcBufferIdx == BUFFERSIZE){
    bufferA = !bufferA;
    adcBufferIdx = 0;
    vTaskResume(sendTask);
  }
}


void IRAM_ATTR samplerTimerISER(){
  if (adcRead >= SAMPLERATE * NCLICKS * CYCLEDURATION / 1000){
    timerAlarmDisable(samplerTimer);
    clicksdone = true;
  }
  else {
    adcRead++;
    readADC();
  }
}


void IRAM_ATTR startSampling(){
    timerRestart(samplerTimer);
    timerAlarmEnable(samplerTimer);
}


void sendDataTask(void *pvParameters){
  for (;;){
    vTaskSuspend(NULL);
    sendBuffer();
    buffersSent++;
  }
}


void setup(){
  // Pin configuration
  pinMode(INTERRUPT_PIN, INPUT_PULLUP);    // Interrupt pin
  pinMode(READPIN, INPUT);               // ADC pin

  // Serial for control and logging
  Serial.begin(CONTROLSERIALBAUD);
  if (!Serial) {
    return;
  }

  // Serial for sending data
  Serial2.begin(TRANSMISSIOSERIALBAUD, SERIAL_8N1, RXD2, TXD2);
  if (!Serial2) {
    Serial.println("Error: Serial connection with arduino not initialized");
    return;
  }
  
  // Timer configuration
  samplerTimer = timerBegin(0, 80, true);    // 80 MHz / 800 = 1 MHz
  timerAttachInterrupt(samplerTimer, &samplerTimerISER, true);
  timerAlarmWrite(samplerTimer, (1000000 / SAMPLERATE), true); 

  // ADC configuration
  // analogSetAttenuation(ADC_0db);

  // Create a task that will send the data to the Raspberry Pi
  xTaskCreatePinnedToCore(
    sendDataTask,   /* Function to implement the task */
    "sendDataTask", /* Name of the task */
    10000,  /* Stack size in words */
    NULL,   /* Task input parameter */
    0,      /* Priority of the task */
    &sendTask,   /* Task handle. */
    0);     /* Core where the task should run */

  attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), startSampling, RISING);
  
}


void loop(){
  // Inform the user the board is ready
  Serial.println("Waiting for interruption");
  Serial.flush();
  Serial.end();
  // For logging purposes
  adcRead = 0;
  buffersSent = 0;
  // Reset everything needed for the burst
  clicksdone = false;
  adcBufferIdx = 0;
  bufferA = true;
  // Wait for the sampling and sending to finish
  while (!clicksdone) {}
  // Disable interruption
  // detachInterrupt(INTERRUPT_PIN);
  // Send the last buffer, if it is not empty
  if (adcBufferIdx > 0){
    bufferA = !bufferA;
    sendBuffer();
    buffersSent++;
  }
  // Re-enable control serial communication
  Serial.begin(CONTROLSERIALBAUD);
  // Print log
  Serial.printf("Burst done. The ADC was called %d times and %d buffers were sent.\n", adcRead, buffersSent);
  ESP.restart();
}