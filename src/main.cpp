#include <Arduino.h>
#include <BluetoothSerial.h>
#include "freertos/semphr.h"
#include <driver/dac.h>
#include <SPI.h>
#include <SD.h>

BluetoothSerial SerialBT;
TaskHandle_t Task1;
TaskHandle_t Task2;
hw_timer_t *soundTimer = NULL;
hw_timer_t *adcTimer = NULL;
hw_timer_t *clickTimer = NULL;
// SemaphoreHandle_t clickSemaphore = NULL;
SemaphoreHandle_t waitForFile = NULL;
SemaphoreHandle_t waitForCliksToFinish = NULL;
SemaphoreHandle_t waitForAdcToFinish = NULL;
SemaphoreHandle_t waitForBufferA = NULL;
SemaphoreHandle_t waitForBufferB = NULL;
bool burst_done = false;

// SdFat SD;
File bufferFile;
const String filename = "/~.temp";
bool bufferA = true;
uint8_t adcBufferA[512];
uint8_t adcBufferB[512];
uint16_t adcBufferIdx = 0;

// Sound array of 10ms with 100ksps
uint8_t click[1000];
const uint16_t NClicks = 2000;
const uint16_t silent_pause_ms = 20;
uint16_t SampleIdx = 0;
uint16_t clickIdx = 0;
uint16_t readVal = 0;
uint8_t ending = 0;
uint8_t starting = 0;
const uint freq[] = {250, 500, 1000, 2000, 4000, 8000};


void IRAM_ATTR fileWriteISR(){
  if (bufferA){
    if (xSemaphoreTake(waitForBufferB, portMAX_DELAY) == pdTRUE) {
      bufferFile.write(adcBufferB, 512);
      xSemaphoreGiveFromISR(waitForBufferB, NULL);
    }
  }
  else{
    if (xSemaphoreTake(waitForBufferA, portMAX_DELAY) == pdTRUE) {
      bufferFile.write(adcBufferA, 512);
      xSemaphoreGiveFromISR(waitForBufferA, NULL);
    }
  }
}

void IRAM_ATTR adcTimerISR()
{
  // Read ADC value and write it to the SD card
  readVal = analogRead(A0);
  starting = (uint8_t) (readVal / 256);
  ending = (uint8_t) (readVal % 256);
  if (bufferA){
    if (xSemaphoreTake(waitForBufferA, 0) == pdTRUE) {
      adcBufferA[adcBufferIdx++] = starting;
      adcBufferA[adcBufferIdx++] = ending;
      xSemaphoreGiveFromISR(waitForBufferA, NULL);
    }
    else{
      Serial.println("Error: Buffer A Mutex not taken");
      ESP.restart();
    }
  }
  else{
    if (xSemaphoreTake(waitForBufferB, 0) == pdTRUE) {
      adcBufferB[adcBufferIdx++] = starting;
      adcBufferB[adcBufferIdx++] = ending;
      xSemaphoreGiveFromISR(waitForBufferB, NULL);
    }
    else{
      Serial.println("Error: Buffer B Mutex not taken");
      ESP.restart();
    }
  }
  if (adcBufferIdx == 512){
    bufferA = !bufferA;
    adcBufferIdx = 0;
  }
}

void IRAM_ATTR soundTimerISR()
{
  // Send SineTable Values To DAC One By One
  dac_output_voltage(DAC_CHANNEL_1, click[SampleIdx++]);
  if(SampleIdx == 1000)
  {
    SampleIdx = 0;
    timerAlarmDisable(soundTimer);
    // xSemaphoreGive(clickSemaphore);
  }
}

void IRAM_ATTR clickTimerISR(){
  if (clickIdx == NClicks) {
    timerAlarmDisable(adcTimer);
    timerAlarmDisable(clickTimer);
    adcBufferIdx = 0;
    clickIdx = 0;
    burst_done = true;
    xSemaphoreGiveFromISR(waitForCliksToFinish, NULL);
  }
  timerRestart(soundTimer);
  timerAlarmEnable(soundTimer);
  // xSemaphoreTake(clickSemaphore, portMAX_DELAY); // Change to 20 ms later 
  clickIdx++;
  
}

void playClicks(void *pvParameters) {
  // Timer for sound generation
  soundTimer = timerBegin(0, 80, true); // 80 MHz / 80 = 1 MHz
  timerAttachInterrupt(soundTimer, &soundTimerISR, true);
  timerAlarmWrite(soundTimer, 10, true);

  //Timer for clicks
  clickTimer = timerBegin(1, 8000, true); // 80 MHz / 80000 = 10 kHz
  timerAttachInterrupt(clickTimer, &clickTimerISR, true);
  timerAlarmWrite(clickTimer, 300, true);

  // clickSemaphore = xSemaphoreCreateBinary();
  for (;;) {
    vTaskSuspend(Task2);
    burst_done = false;
    if (xSemaphoreTake(waitForCliksToFinish, 0) == pdTRUE) {
      timerRestart(clickTimer);
      timerAlarmEnable(clickTimer);
    }
    else{
      Serial.println("Error: Click Mutex not taken");
      ESP.restart();
    }
  }
}

void sendDataBT(){
  if (xSemaphoreTake(waitForFile, portMAX_DELAY) == pdTRUE) {
    bufferFile.seek(0);
    uint bytes_sent = 0;
    Serial.println("Sending the file through bluetooth");
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
      SerialBT.write(bufferFile.read());
      bytes_sent++;
    }
    Serial.printf("Bytes sent: %d\n", bytes_sent);
    bufferFile.seek(0);
    xSemaphoreGive(waitForFile);
  }
}

void control(void *pvParameters) {
  uint8_t freq_index = 0;
  uint a_freq = 0;
  // Timer for adc
  adcTimer = timerBegin(2, 80, true); // 80 MHz / 80 = 1 MHz
  timerAttachInterrupt(adcTimer, &adcTimerISR, true);
  timerAlarmWrite(adcTimer, 100, true); // 10 kHz
  for (;;){
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
        freq_index = (uint8_t) (incomming[0] - '0');
      } else {
        Serial.println("Error: Empty command received.");
        continue;
      }
      if (freq_index < 0 || freq_index > 5) {
        Serial.println("Invalid frequency index");
        continue;
      }
      a_freq = freq[freq_index];
      Serial.printf("Sending clicks of: %d Hz\n", a_freq);
      // Update click array
      for (uint16_t i = 0; i < 1000; i++) {
        click[i] = 128 + 127 * sin(2 * PI * a_freq * i / 100000);
      }  
      // Forward entry: helps reducing the click sound
      for (uint16_t i = 1; i < 11; i++) {
        click[i - 1] = (click[i - 1] * i + 128 * (10 - i)) / 10; 
      }
      // Backward entry: helps reducing the click sound
      for (uint16_t i = 1; i < 11; i++) {
        click[1000 - i] = (click[1000 - i] * i + 128 * (10 - i)) / 10; 
      }
      // plot the click array:
      // for (uint16_t i = 0; i < 1000; i++) {
      //   Serial.printf(">%d:", a_freq);
      //   Serial.println(click[i]);
      // }
      
      break;
      }  
    }
    // Serial.println("Enabling ADC and DAC");
    Serial.println("Starting the burst");
    dac_output_enable(DAC_CHANNEL_1);
    vTaskResume(Task2);
    timerRestart(adcTimer);
    timerAlarmEnable(adcTimer);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    Serial.println("Waiting for the burst to finish");
    if (xSemaphoreTake(waitForCliksToFinish, portMAX_DELAY) == pdTRUE) {
      Serial.println("Burst done");
      // wait till the adc writes the last value
      sendDataBT();
      Serial.println("Waiting for the next command");
      dac_output_disable(DAC_CHANNEL_1);
    }
  }
}

void setup() {
  // DAC output config
  pinMode(DAC_CHANNEL_1, OUTPUT);
  dac_output_enable(DAC_CHANNEL_1);
  analogWrite(DAC_CHANNEL_1, 128);
  dac_output_disable(DAC_CHANNEL_1);

  // Serial port config
  Serial.begin(115200);  // Initialize Serial communication only once
  SerialBT.begin("CABRA");  // Bluetooth device name
  Serial.println("The device started, now you can pair it with bluetooth!");

  // SD card config
  Serial.print("Initializing SD card...");
  if (!SD.begin(SS)) {
    Serial.println("initialization failed!");
    return;
  }
  Serial.println("initialization done.");

  // File creation
  bufferFile = SD.open(filename, "wr");
  if (!bufferFile) {
    Serial.printf("Error opening %s.\n", filename);
    return;
  }

  // Semaphore creation
  waitForFile = xSemaphoreCreateBinary();
  waitForCliksToFinish = xSemaphoreCreateBinary();
  waitForBufferA = xSemaphoreCreateBinary();
  waitForBufferB = xSemaphoreCreateBinary();
  waitForAdcToFinish = xSemaphoreCreateBinary();
  // Semaphore initialization
  xSemaphoreGive(waitForBufferA);
  xSemaphoreGive(waitForBufferB);
  xSemaphoreGive(waitForFile);
  xSemaphoreGive(waitForCliksToFinish);
  xSemaphoreGive(waitForAdcToFinish);

  // Create a task that will execute the main function
  xTaskCreatePinnedToCore(
    control,   /* Function to implement the task */
    "control", /* Name of the task */
    10000,  /* Stack size in words */
    NULL,   /* Task input parameter */
    0,      /* Priority of the task */
    &Task1,   /* Task handle. */
    0);     /* Core where the task should run */

  xTaskCreatePinnedToCore(
    playClicks,   /* Function to implement the task */
    "playClicsk", /* Name of the task */
    1000,  /* Stack size in words */
    NULL,   /* Task input parameter */
    0,      /* Priority of the task */
    &Task2,   /* Task handle. */
    1);     /* Core where the task should run */
}

void loop() {
 
}