#include <arduino.h>
// #include "freertos/semphr.h"

// defines
#define SAMPLERATE 10000 // Hz
#define BUFFERSIZE 128 // 128 samples of 2 bytes each, 256 bytes in total
#define INTERRUPT_PIN 2
#define SERIALBAUD 960000
#define READPIN 4

// Task related variables
TaskHandle_t sendTask;
hw_timer_t *samplerTimer = NULL;
volatile bool sampling_done = false;

// ADC related variables
volatile bool bufferA = true;
volatile uint16_t adcBufferA[BUFFERSIZE];
volatile uint16_t adcBufferB[BUFFERSIZE];
volatile uint adcRead = 0;
volatile uint16_t adcBufferIdx = 0;
volatile uint16_t readVal = 0;
volatile long n_samples = 0;


void sendBuffer(){
  // Choose the right bufffer, which is not in use by the ADC
  if (!bufferA){
    // Send the buffer to the Raspberry Pi
    Serial.write((uint8_t *) adcBufferA, BUFFERSIZE * 2);
  }
  else{
    // Send the buffer to the Raspberry Pi
    Serial.write((uint8_t *) adcBufferB, BUFFERSIZE * 2);
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
  if (adcRead >= n_samples){
    timerAlarmDisable(samplerTimer);
    sampling_done = true;
  }
  else {
    adcRead++;
    readADC();
  }
}


void IRAM_ATTR startSampling(){
    detachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN));
    timerRestart(samplerTimer);
    timerAlarmEnable(samplerTimer);
}


void sendDataTask(void *pvParameters){
  for (;;){
    vTaskSuspend(NULL);
    sendBuffer();
  }
}


void setup(){
  // Pin configuration
  pinMode(INTERRUPT_PIN, INPUT_PULLUP);    // Interrupt pin
  pinMode(READPIN, INPUT);               // ADC pin

  // Serial for control and logging
  Serial.begin(SERIALBAUD);
  if (!Serial) {
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
}


void loop(){
  while(!Serial.available()) {}
  n_samples = Serial.parseInt();
  // Wait for the serial to stop reading data
  Serial.flush();
  // Reset everything needed for the burst
  adcRead = 0;
  sampling_done = false;
  adcBufferIdx = 0;
  bufferA = true;
  attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), startSampling, RISING);
  // Wait for the sampling and sending to finish
  while (!sampling_done) {}
  // Send the last buffer, if it is not empty
  if (adcBufferIdx > 0){
    bufferA = !bufferA;
    sendBuffer();
  }
  n_samples = 0;
  ESP.restart();
}