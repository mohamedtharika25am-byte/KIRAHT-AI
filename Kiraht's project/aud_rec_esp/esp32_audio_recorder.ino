#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "driver/i2s.h"

#define I2S_WS 15
#define I2S_SD 13
#define I2S_SCK 14
#define I2S_PORT I2S_NUM_0

void setup() {
  Serial.begin(115200);
  pinMode(I2S_WS, OUTPUT);
  
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);

  if (!SD.begin()) {
    Serial.println("SD Card Mount Failed");
    return;
  }
}

void loop() {
  size_t bytes_read;
  char buffer[1024];
  i2s_read(I2S_PORT, &buffer, sizeof(buffer), &bytes_read, portMAX_DELAY);
  
  File file = SD.open("/recording.pcm", FILE_APPEND);
  if (file) {
    file.write((uint8_t*)buffer, bytes_read);
    file.close();
  }
}
