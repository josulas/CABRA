#include <arduino.h>

// defines
#define SAMPLERATE 8000 // Hz
#define NSAMPLESPERBUFFER 128
#define SERIALBAUD 960000
#define READPIN 4

// Task related variables
TaskHandle_t sendTask;
hw_timer_t *samplerTimer = NULL;
volatile bool sampling_done = false;

// ADC related variables
volatile bool currentBufferIsA = true;
volatile uint16_t adcBufferA[NSAMPLESPERBUFFER];
volatile uint16_t adcBufferB[NSAMPLESPERBUFFER];
volatile uint adcRead = 0;
volatile uint16_t adcBufferIdx = 0;
volatile uint16_t readVal = 0;
volatile long n_samples = 0;
char startSamplingFlag = 0;


void sendBuffer(){
  // Choose the right bufffer, which is not in use by the ADC
  if (!currentBufferIsA){
    // Send the buffer
    Serial.write((uint8_t *) adcBufferA, NSAMPLESPERBUFFER * 2);
  }
  else{
    // Send the buffer
    Serial.write((uint8_t *) adcBufferB, NSAMPLESPERBUFFER * 2);
  }
}


void readADC(){
  // Read ADC value and write it to the SD card
  readVal = analogRead(READPIN);
  if (currentBufferIsA){
    adcBufferA[adcBufferIdx++] = readVal;
  }
  else{
    adcBufferB[adcBufferIdx++] = readVal;
  }
  if (adcBufferIdx == NSAMPLESPERBUFFER){
    currentBufferIsA = !currentBufferIsA;
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

void sendDataTask(void *pvParameters){
  for (;;){
    vTaskSuspend(NULL);
    sendBuffer();
  }
}


void setup(){
  // Variable setup
  adcRead = 0;
  sampling_done = false;
  adcBufferIdx = 0;
  currentBufferIsA = true;

  // Pin configuration
  pinMode(READPIN, INPUT);               // ADC pin

  // Serial initialization
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
  Serial.println("Waiting for the number of samples");
  while(!Serial.available()) {}
  n_samples = Serial.parseInt();
  while(!Serial.available()) {}
  Serial.readBytes(&startSamplingFlag, 1);
  Serial.flush(); // Wait for the Serial to stop reading data
  // Start sampling
  timerRestart(samplerTimer);
  timerAlarmEnable(samplerTimer);
  // Wait for the sampling and sending to finish
  while (!sampling_done) {}
  // Send the last buffer, if it is not empty
  if (adcBufferIdx > 0){
    currentBufferIsA = !currentBufferIsA;
    sendBuffer();
  }
  // Reset the variables
  // Variable setup
  adcRead = 0;
  sampling_done = false;
  adcBufferIdx = 0;
  currentBufferIsA = true;
  n_samples = 0;
}