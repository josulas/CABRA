#include <BluetoothSerial.h>
#include <arduino.h>
#include "freertos/semphr.h"
#include <driver/dac.h>
#include <SPI.h>
#include <SD.h>

BluetoothSerial SerialBT;
TaskHandle_t Task1;
hw_timer_t *fastTimer = NULL;

// SemaphoreHandle_t clickSemaphore = NULL;
SemaphoreHandle_t waitForFile = NULL;
SemaphoreHandle_t waitForCliksToFinish = NULL;
SemaphoreHandle_t waitForAdcToFinish = NULL;
SemaphoreHandle_t waitForBufferA = NULL;
SemaphoreHandle_t waitForBufferB = NULL;
bool clicksdone = false;

// SdFat SD;
File bufferFile;
const String filename = "/~.temp";
bool bufferA = true;

// ADC related variables
uint16_t adcBufferA[256];
uint16_t adcBufferB[256];
uint8_t writeBuffer[512];
uint16_t adcBufferIdx = 0;
uint16_t readVal = 0;
uint8_t ending = 0;
uint8_t starting = 0;
bool toWrite = false;

// Sound array of 10ms with 100ksps
uint8_t click[1000];
const uint16_t NClicks = 100;
uint16_t clickSampleIdx = 0;
uint16_t clickIdx = 0;

// Frequencies
const uint freqs[] = {250, 500, 1000, 2000, 4000, 8000};

// interrupt index
uint16_t interruptIdx = 0;

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
  toWrite = false;
}

void readADC()
{
  // Read ADC value and write it to the SD card
  readVal = analogRead(A0);
  if (bufferA){
    if (xSemaphoreTake(waitForBufferA, 0) == pdTRUE) {
      adcBufferA[adcBufferIdx++] = readVal;
      xSemaphoreGiveFromISR(waitForBufferA, NULL);
    }
    else{
      Serial.println("Error: Buffer A Mutex not taken");
      ESP.restart();
    }
  }
  else{
    if (xSemaphoreTake(waitForBufferB, 0) == pdTRUE) {
      adcBufferB[adcBufferIdx++] = readVal;
      xSemaphoreGiveFromISR(waitForBufferB, NULL);
    }
    else{
      Serial.println("Error: Buffer B Mutex not taken");
      ESP.restart();
    }
  }
  if (adcBufferIdx == 256){
    bufferA = !bufferA;
    adcBufferIdx = 0;
    toWrite = true;
    // xSemaphoreGiveFromISR(waitForAdcToFinish, NULL);
  }
}

void writeDAC()
{
  // Send SineTable Values To DAC One By One
  dac_output_voltage(DAC_CHANNEL_1, click[clickSampleIdx++]);
  if(clickSampleIdx == 1000){
    clickSampleIdx = 0;
  }
}

void IRAM_ATTR fastTimerISER(){
  // Sampling rate of 100 kHz / 100 = 1ksps
  if (interruptIdx % 100 == 0){
    readADC();
    // if ((interruptIdx % 2560) == 0){
    //   xSemaphoreTake(waitForAdcToFinish, 0);
    // }
  }
  if (interruptIdx < 1000) {
    writeDAC();
  } 
  if (interruptIdx == 3000) {
    interruptIdx = 0;
    clickIdx++;
  }
  if (clickIdx == NClicks) {
    timerAlarmDisable(fastTimer);
    clickIdx = 0;
    clicksdone = true;
  }
  interruptIdx++;
}

void sendDataBT(){
  if (xSemaphoreTake(waitForFile, portMAX_DELAY) == pdTRUE) {
    // bufferFile.seek(0);
    bufferFile = SD.open(filename, "r");
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
    bufferFile.close();
    xSemaphoreGive(waitForFile);
  }
}

void updateclick(uint freq){
  // Update click array
  for (uint16_t i = 0; i < 1000; i++) {
    click[i] = 128 + 127 * sin(2 * PI * freq * i / 100000);
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
  //   Serial.printf(">%d:", freq);
  //   Serial.println(click[i]);
  // }
}

void control(void *pvParameters) {
  uint8_t freq_index = 0;
  uint freq = 0;
  // Fast timer for sound and ADC
  fastTimer = timerBegin(0, 80, true); // 80 MHz / 80 = 1 MHz
  timerAttachInterrupt(fastTimer, &fastTimerISER, true);
  timerAlarmWrite(fastTimer, 10, true); // 10 us
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
      freq = freqs[freq_index];
      updateclick(freq);
      Serial.printf("Sending clicks of: %d Hz\n", freq);
      break;
      }  
    }
    bufferFile = SD.open(filename, "w");
    if (!bufferFile) {
      Serial.printf("Error opening %s.\n", filename);
      return;
    }
    // Serial.println("Enabling ADC and DAC");
    dac_output_enable(DAC_CHANNEL_1);
    clicksdone = false;
    Serial.println("Starting the burst");
    timerRestart(fastTimer);
    timerAlarmEnable(fastTimer);
    vTaskDelay(10 / portTICK_PERIOD_MS);
    while (! clicksdone) {
      if (toWrite) {
        // Serial.println("One ADC buffer has been filled");
        writeFile();
        toWrite = false;
      }
      else{
        delay(1);
      }
    }
    if (adcBufferIdx > 0){
      adcBufferIdx = 0;
      bufferA = !bufferA;
      toWrite = true;
      writeFile();
    }
    bufferFile.close();
    // bufferFile.flush();
    Serial.println("Burst done. Sending the data through bluetooth");
    // wait till the adc writes the last value
    sendDataBT();
    dac_output_disable(DAC_CHANNEL_1);
    Serial.println("Waiting for the next command"); 
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
}

void loop() {
 
}

// void app_main(void)
// {

// }