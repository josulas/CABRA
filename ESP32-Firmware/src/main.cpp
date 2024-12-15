#include <Arduino.h>

// defines
#define SAMPLERATE 16000 // Hz
#define TIMERFREQUENCY 1000000 // Hz
#define NSAMPLESPERBUFFER 128
#define MAXSAMPLES 2000
#define SERIALBAUD 960000
#define READPIN 13

// Task related variables
TaskHandle_t sendTask;
hw_timer_t *samplerTimer = NULL;

// ADC related variables
volatile uint16_t adcBuffer[MAXSAMPLES];
volatile uint16_t adcBufferIdx = 0;
volatile uint16_t sendBufferIdx = 0;
volatile long n_samples = 0;
volatile bool samplingComplete = false;
char startSamplingFlag = 0;

void IRAM_ATTR samplerTimerISER(){
  if (adcBufferIdx < n_samples) {
    adcBuffer[adcBufferIdx] = analogRead(READPIN);
    adcBufferIdx = adcBufferIdx + 1;
  } else {
    samplingComplete = true;
    timerStop(samplerTimer); // Stop the timer when sampling is complete
  }
}

void sendDataTask(void *pvParameters){
  for (;;){
    vTaskSuspend(NULL);
    Serial.write((uint8_t *) (adcBuffer + sendBufferIdx), NSAMPLESPERBUFFER * 2);
    sendBufferIdx = sendBufferIdx + NSAMPLESPERBUFFER;
  }
}


void setup(){
  // Pin configuration
  pinMode(READPIN, INPUT);               // ADC pin

  // Serial initialization
  Serial.setTxBufferSize(2 * NSAMPLESPERBUFFER);
  Serial.begin(SERIALBAUD);
  if (!Serial) {
    return;
  }

  // Create a task that will send the data to the Raspberry Pi
  xTaskCreatePinnedToCore(
    sendDataTask,   /* Function to implement the task */
    "sendDataTask", /* Name of the task */
    1000,  /* Stack size in words */
    NULL,   /* Task input parameter */
    0,      /* Priority of the task */
    &sendTask,   /* Task handle. */
    0);     /* Core where the task should run */

  // Timer configuration
  samplerTimer = timerBegin(TIMERFREQUENCY);    // 1 MHz
  timerStop(samplerTimer);
  timerAttachInterrupt(samplerTimer, &samplerTimerISER);
}


void loop(){
  while(!Serial.available()) {}
  n_samples = Serial.parseInt();
  while(!Serial.available()) {}
  Serial.readBytes(&startSamplingFlag, 1);
  Serial.flush(); // Wait for the Serial to stop reading data
  // Start sampling
  timerRestart(samplerTimer);
  timerAlarm(samplerTimer, (TIMERFREQUENCY / SAMPLERATE), true, 0);
  timerStart(samplerTimer);
  // Wait for the sampling and sending to finish
  while (!samplingComplete) {
    if (adcBufferIdx >= sendBufferIdx + NSAMPLESPERBUFFER){
      vTaskResume(sendTask);
    }
  }
  // Send the remaining data
  while(sendBufferIdx <= n_samples - NSAMPLESPERBUFFER){
    Serial.write((uint8_t *) (adcBuffer + sendBufferIdx), NSAMPLESPERBUFFER * 2);
    sendBufferIdx = sendBufferIdx + NSAMPLESPERBUFFER;
  }
  if (n_samples > sendBufferIdx){
    Serial.write((uint8_t *) (adcBuffer + sendBufferIdx), (n_samples - sendBufferIdx) * 2);
  }
  // Serial.printf("ADC was sampled %d times\n", adcBufferIdx);
  // Reset the variables
  samplingComplete = false;
  adcBufferIdx = 0;
  sendBufferIdx = 0;
  n_samples = 0;
}