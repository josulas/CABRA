#include <BluetoothSerial.h>
#include <arduino.h>
#include "freertos/semphr.h"
#include <driver/dac.h>
#include <SPI.h>
// #include <SD.h>
#include <SDfat.h>

#define NCLICKS 2000
#define CLICKDURATION 30 // ms
#define SAMPLERATE 10000 // Hz
#define BUFFERSIZE 2048 // 4KB / 2, since each sample is 2 bytes
#define INTERRUPT_PIN 22
#define RXD2 16
#define TXD2 17
#define BLUETOOTHBAUD 500000
#define SENDDATABUFFERSIZE 64

BluetoothSerial SerialBT;
char sendDataBuffer[SENDDATABUFFERSIZE];
char freq;
TaskHandle_t WriteTask;
hw_timer_t *samplerTimer = NULL;

SemaphoreHandle_t waitForFile = NULL;
// SemaphoreHandle_t waitForBufferA = NULL;
// SemaphoreHandle_t waitForBufferB = NULL;
volatile bool clicksdone = false;

File bufferFile;
SdFat SD;
const int SD_CS_PIN = SS;  // Use the correct chip select pin, SS is often the default pin for ESP32 boards.
const uint32_t SPI_SPEED = SD_SCK_MHZ(25);  // 25 MHz is a good speed for most SD cards
const String filename = "/~.temp";
bool bufferA = true;

// ADC related variables
volatile uint16_t adcBufferA[BUFFERSIZE];
volatile uint16_t adcBufferB[BUFFERSIZE];
// uint8_t writeBuffer[512];
volatile uint buffersSent = 0;
volatile uint adcRead = 0;
volatile uint16_t adcBufferIdx = 0;
volatile uint16_t readVal = 0;

void writeFile(){
  if (bufferA){
    bufferFile.write((uint8_t *) adcBufferB, BUFFERSIZE * 2);
    // if (xSemaphoreTake(waitForBufferB, portMAX_DELAY) == pdTRUE) {
    //   // memcpy(writeBuffer, adcBufferB, 512);
      
    //   xSemaphoreGive(waitForBufferB);
    // }
  }
  else{
    bufferFile.write((uint8_t *) adcBufferA, BUFFERSIZE * 2);
    // if (xSemaphoreTake(waitForBufferA, portMAX_DELAY) == pdTRUE) {
    //   // memcpy(writeBuffer, adcBufferA, 512);
      
    //   xSemaphoreGive(waitForBufferA);
    // }
  }
}

// void SendViaBT(){
//   if (bufferA){
//     if (xSemaphoreTake(waitForBufferB, portMAX_DELAY) == pdTRUE) {
//       // memcpy(writeBuffer, adcBufferB, 512);
//       SerialBT.write((uint8_t *) adcBufferB, 512);
//       // bufferFile.write((uint8_t *) adcBufferB, 512);
//       xSemaphoreGive(waitForBufferB);
//     }
//   }
//   else{
//     if (xSemaphoreTake(waitForBufferA, portMAX_DELAY) == pdTRUE) {
//       // memcpy(writeBuffer, adcBufferA, 512);
//       SerialBT.write((uint8_t *) adcBufferA, 512);
//       xSemaphoreGive(waitForBufferA);
//     }
//   }
// }

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
  if (adcBufferIdx == BUFFERSIZE){
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
  if (xSemaphoreTake(waitForFile, portMAX_DELAY) == pdTRUE) {
    // bufferFile.seek(0);
    bufferFile = SD.open(filename, FILE_READ);
    uint bytes_sent = 0;
    bool finished = false;
    size_t remaining;
    while (! finished) {
      remaining = bufferFile.available();
      if (!remaining) {
        finished = true;
        break;
      }
      if (remaining >= SENDDATABUFFERSIZE){
        bufferFile.readBytes(sendDataBuffer, SENDDATABUFFERSIZE);
        SerialBT.write((uint8_t *) sendDataBuffer, SENDDATABUFFERSIZE);
        bytes_sent += SENDDATABUFFERSIZE;
      } else {
        bufferFile.readBytes(sendDataBuffer, remaining);
        SerialBT.write((uint8_t *) sendDataBuffer, remaining);
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
  SerialBT.begin(BLUETOOTHBAUD);
  SerialBT.begin("CABRA");  // Bluetooth device name
  Serial.println("The device started, now you can pair it with bluetooth!");

  // SD card config
  Serial.print("Initializing SD card...");
  // if (!SD.begin(SS)) {
  //   Serial.println("initialization failed!");
  //   return;
  // }
  if (!SD.begin(SD_CS_PIN, SPI_SPEED)) {
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
  // waitForBufferA = xSemaphoreCreateBinary();
  // waitForBufferB = xSemaphoreCreateBinary();
  // Semaphore initialization
  xSemaphoreGive(waitForFile);
  // xSemaphoreGive(waitForBufferA);
  // xSemaphoreGive(waitForBufferB);
  
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

  // ADC configuration
  // analogSetAttenuation(ADC_0db);

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
  bufferFile = SD.open(filename, O_WRITE | O_TRUNC);
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
  Serial.flush();
  Serial.end();
  // SerialBT.end();
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
  Serial.begin(115200);
  // SerialBT.begin(BLUETOOTHBAUD);
  Serial.printf("Burst done. The ADC was called %d times and %d buffers were written.\n", adcRead, buffersSent);
  
  if (!clicksdone) {
    Serial.println("Error: Clicks not done");
    return;
  }
  Serial.println("Burst done. Sending the data through bluetooth.");
  sendDataBT();
  Serial.println("Waiting for the next command."); 
}