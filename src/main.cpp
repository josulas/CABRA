#include <BluetoothSerial.h>
#include <arduino.h>
#include "freertos/semphr.h"
#include <driver/dac.h>
#include <SPI.h>
#include <SD.h>

#define NCLICKS 100
#define CLICKDURATION 30 // ms
#define SAMPLERATE 10000 // Hz
#define INTERRUPT_PIN 22
#define RXD2 16
#define TXD2 17

BluetoothSerial SerialBT;
char freq;
TaskHandle_t WriteTask;
hw_timer_t *samplerTimer = NULL;

// SemaphoreHandle_t clickSemaphore = NULL;
SemaphoreHandle_t waitForFile = NULL;
SemaphoreHandle_t waitForBufferA = NULL;
SemaphoreHandle_t waitForBufferB = NULL;
volatile bool clicksdone = false;

// SdFat SD;
File bufferFile;
const String filename = "/~.temp";
bool bufferA = true;

// ADC related variables
volatile uint16_t adcBufferA[256];
volatile uint16_t adcBufferB[256];
// uint8_t writeBuffer[512];
volatile uint buffersSent = 0;
volatile uint adcRead = 0;
volatile uint16_t adcBufferIdx = 0;
volatile uint16_t readVal = 0;

void writeFile(){
  if (bufferA){
    if (xSemaphoreTake(waitForBufferB, portMAX_DELAY) == pdTRUE) {
      // memcpy(writeBuffer, adcBufferB, 512);
      bufferFile.write((uint8_t *) adcBufferB, 512);
      xSemaphoreGive(waitForBufferB);
    }
  }
  else{
    if (xSemaphoreTake(waitForBufferA, portMAX_DELAY) == pdTRUE) {
      // memcpy(writeBuffer, adcBufferA, 512);
      bufferFile.write((uint8_t *) adcBufferA, 512);
      xSemaphoreGive(waitForBufferA);
    }
  }
}

void SendViaBT(){
  if (bufferA){
    if (xSemaphoreTake(waitForBufferB, portMAX_DELAY) == pdTRUE) {
      // memcpy(writeBuffer, adcBufferB, 512);
      SerialBT.write((uint8_t *) adcBufferB, 512);
      // bufferFile.write((uint8_t *) adcBufferB, 512);
      xSemaphoreGive(waitForBufferB);
    }
  }
  else{
    if (xSemaphoreTake(waitForBufferA, portMAX_DELAY) == pdTRUE) {
      // memcpy(writeBuffer, adcBufferA, 512);
      SerialBT.write((uint8_t *) adcBufferA, 512);
      xSemaphoreGive(waitForBufferA);
    }
  }
}

void readADC()
{
  // Read ADC value and write it to the SD card
  readVal = analogRead(A0);
  if (bufferA){
    adcBufferA[adcBufferIdx++] = readVal;
    // if (xSemaphoreTake(waitForBufferA, 0) == pdTRUE) {
    //   adcBufferA[adcBufferIdx++] = readVal;
    //   xSemaphoreGiveFromISR(waitForBufferA, NULL);
    // }
    // else{
    //   Serial.println("Error: Buffer A Mutex not taken");
    //   ESP.restart();
    // }
  }
  else{
    adcBufferB[adcBufferIdx++] = readVal;
    // if (xSemaphoreTake(waitForBufferB, 0) == pdTRUE) {
    //   adcBufferB[adcBufferIdx++] = readVal;
    //   xSemaphoreGiveFromISR(waitForBufferB, NULL);
    // }
    // else{
    //   Serial.println("Error: Buffer B Mutex not taken");
    //   ESP.restart();
    // }
  }
  if (adcBufferIdx == 256){
    bufferA = !bufferA;
    adcBufferIdx = 0;
    vTaskResume(WriteTask);
  }
}

void IRAM_ATTR samplerTimerISER(){
  if (adcRead >= SAMPLERATE * NCLICKS * CLICKDURATION / 1000){
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

void sendDataBT(){
  char data[64];
  if (xSemaphoreTake(waitForFile, portMAX_DELAY) == pdTRUE) {
    // bufferFile.seek(0);
    bufferFile = SD.open(filename, "r");
    uint bytes_sent = 0;
    bool finished = false;
    size_t remaining;
    while (! finished) {
      remaining = bufferFile.available();
      if (!remaining) {
        finished = true;
        break;
      }
      if (! remaining % 1024){
        Serial.printf("Remaining: %dkB\n", remaining / 1024);
      }
      if (remaining >= 64){
        bufferFile.readBytes(data, 64);
        SerialBT.write((uint8_t *) data, 64);
        bytes_sent += 64;
      } else {
        bufferFile.readBytes(data, remaining);
        SerialBT.write((uint8_t *) data, remaining);
        bytes_sent += remaining;
      }
    }
    Serial.printf("Bytes sent: %d\n", bytes_sent);
    bufferFile.close();
    xSemaphoreGive(waitForFile);
  }
}

void writeDataTask(void *pvParameters){
  for (;;){
    vTaskSuspend(NULL);
    writeFile();
    // SendViaBT();
    buffersSent++;
  }
}

void setup() {
  // Pin configuration
  pinMode(INTERRUPT_PIN, INPUT);    // Interrupt pin
  pinMode(A0, INPUT);               // ADC pin

  // Interrupt configuration
  attachInterrupt(INTERRUPT_PIN, startSampling, RISING);

  // Serial port config
  Serial.begin(115200);  // Initialize Serial communication only once
  SerialBT.begin(250000);
  SerialBT.begin("CABRA");  // Bluetooth device name
  Serial.println("The device started, now you can pair it with bluetooth!");

  // SD card config
  Serial.print("Initializing SD card...");
  if (!SD.begin(SS)) {
    Serial.println("initialization failed!");
    return;
  }
  Serial.println("initialization done.");

  // Serial with Arduino
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
  if (!Serial2) {
    Serial.println("Error: Serial connection with arduino not initialized");
    return;
  }

  // Semaphore creation
  waitForFile = xSemaphoreCreateBinary();
  waitForBufferA = xSemaphoreCreateBinary();
  waitForBufferB = xSemaphoreCreateBinary();
  // Semaphore initialization
  xSemaphoreGive(waitForBufferA);
  xSemaphoreGive(waitForBufferB);
  xSemaphoreGive(waitForFile);

  // Timer configuration
  samplerTimer = timerBegin(0, 80, true);    // 80 MHz / 800 = 1 MHz
  timerAttachInterrupt(samplerTimer, &samplerTimerISER, true);
  timerAlarmWrite(samplerTimer, (1000000 / SAMPLERATE), true);  // 1 MHz / 1000 = 1 kHz

  // Create a task that will execute the main function
  // xTaskCreatePinnedToCore(
  //   control,   /* Function to implement the task */
  //   "control", /* Name of the task */
  //   10000,  /* Stack size in words */
  //   NULL,   /* Task input parameter */
  //   1,      /* Priority of the task */
  //   &Task1,   /* Task handle. */
  //   1);     /* Core where the task should run */

  // Create a task that will write the data to the SD card
  xTaskCreatePinnedToCore(
    writeDataTask,   /* Function to implement the task */
    "writeDataTask", /* Name of the task */
    10000,  /* Stack size in words */
    NULL,   /* Task input parameter */
    0,      /* Priority of the task */
    &WriteTask,   /* Task handle. */
    0);     /* Core where the task should run */
}

void loop() {
  for (;;){
    if (SerialBT.available()) {
      String incomming = SerialBT.readString();
      incomming.trim();
      if (incomming == "exit") {
        bufferFile.close();
        SD.remove(filename);
        return;
      }
      if (incomming.length() > 0) {
        freq = incomming[0];
      } else {
        Serial.println("Error: Empty command received.");
        continue;
      }
      if (freq < '0' || freq > '5') {
        Serial.println("Invalid frequency index");
        continue;
      }
      break;
    }
    // vTaskDelay(1 / portTICK_PERIOD_MS);
  }
  bufferFile = SD.open(filename, "w");
  if (!bufferFile) {
    Serial.printf("Error opening %s.\n", filename);
    return;
  }
  // For debugging purposes
  adcRead = 0;
  buffersSent = 0;
  // Send command to the arduino
  clicksdone = false;
  adcBufferIdx = 0;
  bufferA = true;
  Serial.println("Starting the burst");
  Serial2.write(freq);
  while (!clicksdone) {
    // vTaskDelay(10 / portTICK_PERIOD_MS);
  }
  if (adcBufferIdx > 0){
    bufferA = !bufferA;
    writeFile();
    // SendViaBT();
    buffersSent++;
  }
  bufferFile.close();
  Serial.printf("Burst done. The ADC was called %d times and %d buffers were written.\n", adcRead, buffersSent);
  
  if (!clicksdone) {
    Serial.println("Error: Clicks not done");
    return;
  }
  Serial.println("Burst done. Sending the data through bluetooth.");
  sendDataBT();
  Serial.println("Waiting for the next command."); 
}