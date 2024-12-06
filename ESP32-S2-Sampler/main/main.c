#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/adc.h"
#include "esp_adc_cal.h"

// ADC channel and configuration
#define ADC_CHANNEL ADC1_CHANNEL_6  // GPIO14 corresponds to ADC1_CHANNEL_6

void app_main(void)
{
    // Initialize ADC1
    adc1_config_width(ADC_BITWIDTH_12); // Set resolution to 12 bits
    adc1_config_channel_atten(ADC_CHANNEL, ADC_ATTEN_DB_12); // Set attenuation to 12dB

    printf("ADC Example: Reading raw ADC values\n");

    while (true)
    {
        // Read raw ADC value
        int adc_reading = adc1_get_raw(ADC_CHANNEL);

        // Print the raw ADC value (12-bit)
        printf("Raw ADC Value: %d\n", adc_reading);

        // Delay for stability
        vTaskDelay(pdMS_TO_TICKS(500)); // 500ms delay
    }
}
