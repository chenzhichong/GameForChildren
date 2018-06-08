#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include <Enerlib.h>
#include <ArduinoJson.h>

/* Set up nRF24L01 radio on SPI bus plus pins 7 & 8 */
RF24 radio(7,8);

//初始化Energy
Energy energy;

//初始化ArduinoJson
StaticJsonBuffer<200> jsonBuffer;
JsonObject& root = jsonBuffer.createObject();

// Radio pipe addresses for the 2 nodes to communicate.
const uint64_t pipes[2] = { 0xF0F0F0F0E1LL, 0xF0F0F0F0D2LL };

// CMD enum
typedef enum { cmd_shoot = 1, cmd_respone } cmd_e;

//cmd
cmd_e cmd = cmd_shoot;

// 负载设置
const int min_payload_size = 4;
const int max_payload_size = 32;
const int payload_size_increments_by = 1;
int next_payload_size = min_payload_size;
char receive_payload[max_payload_size+1]; // +1 to allow room for a terminating NULL char

//管脚定义
const int button_pin = 2;
const int ir_pin = 3;

//声明变量
const int delay_time = 200;
const unsigned long idle_wait_time = 5000;
unsigned long idle_start_at = 0;
unsigned long id_transmit = 0;

//数据传输同步
const int data_sync_witdh = 3;
const unsigned char sync_start_tx[data_sync_witdh]={0,255,255};//开始帧
const unsigned char sync_end_tx[data_sync_witdh]={255,255,0};//结束帧

//按键状态
int button_state = 0;
int last_button_state = 0;

void setup() {
  Serial.begin(115200);
  Serial.println(F("gun go!go!go!"));
  pinMode(button_pin, INPUT_PULLUP);
  pinMode(ir_pin, OUTPUT);
  id_transmit = 0;

  //创建一个json，与主机通讯
  // {
  //   "ver": "0.1",
  //   "ID": 0,
  //   "role": "Gun1"
  //   "cmd":0,
  // }
  //root["ver"] = "0.1";
  root["ID"] = id_transmit;
  root["role"] = "Gun1";
  root["cmd"] = int(cmd);
  root.prettyPrintTo(Serial);
  
  // Setup and configure rf radio
  radio.begin();

  // enable dynamic payloads
  radio.enableDynamicPayloads();

  // optionally, increase the delay between retries & # of retries
  radio.setRetries(5,15);

  //设置通道地址
  radio.openWritingPipe(pipes[0]);
  radio.openReadingPipe(1,pipes[1]);

  // Start listening
  radio.startListening();

  // Dump the configuration of the rf unit for debugging
  radio.printDetails();
  Serial.println();

  //配置结束，开始记录空闲
  idle_start_at = millis();
}

void shoot() {
  char data[32];
  char buf[32];
  int index_data;
  //填充数据
  id_transmit++;
  root["ID"] = id_transmit;
  cmd = cmd_shoot;
  root["cmd"] = int(cmd);

  // First, stop listening so we can talk.
  radio.stopListening();

  // Take the time, and send it.  This will block until complete
  int size_root = root.measureLength();
  Serial.print(F("Now sending length "));
  Serial.println(size_root);
  root.printTo(Serial);
  Serial.println();
  //先发送起始帧
  //radio.write(sync_start_tx, data_sync_witdh);
  //发送总的长度
  //radio.write(size_root, 2);
  //发送帧数，每帧31字节，头2字节是序号
  //printTo这个函数需要多加一个字节存放null字符
  root.printTo(data, size_root + 1);
  radio.write(data, size_root);  
  //最后发送结束帧
  //radio.write(sync_end_tx, data_sync_witdh);

  // Now, continue listening
  radio.startListening();

  // Wait here until we get a response, or timeout
  unsigned long started_waiting_at = millis();
  bool timeout = false;
  while ( ! radio.available() && ! timeout )
    if (millis() - started_waiting_at > 500 )
      timeout = true;

  // Describe the results
  if ( timeout )
  {
    Serial.println(F("Failed, response timed out."));
  }
  else
  {
    // Grab the response, compare, and send to debugging spew
    uint8_t len = radio.getDynamicPayloadSize();
    
    // If a corrupt dynamic payload is received, it will be flushed
    if(!len){
      return; 
    }
    
    radio.read( receive_payload, len );

    // Put a zero at the end for easy printing
    receive_payload[len] = 0;

    // Spew it
    Serial.print(F("Got response size="));
    Serial.print(len);
    Serial.print(F(" value="));
    Serial.println(receive_payload);
  }
}

void wakeISR() {
   if (energy.WasSleeping()) {
    //待机时的中断响应
    Serial.println(F("Now, we need to wake up!"));
    detachInterrupt(digitalPinToInterrupt(2));
  } else {
    //非待机时的中断响应
  }
}

void loop() {  
  button_state = digitalRead(button_pin);
  if (button_state != last_button_state) {
    //Serial.println(button_state);
    if (button_state == HIGH) {
      //按键没按
      Serial.println(F("Button not Pressed!"));
      digitalWrite(ir_pin, LOW);
      radio.powerDown();
    } else {
      //按键按下
      Serial.println(F("Button Pressed!"));
      digitalWrite(ir_pin, HIGH);
      radio.powerUp();
      shoot();
      delay(delay_time);
    }
    delay(50);
    idle_start_at = millis();
  }
    last_button_state = button_state;
  if (millis() - idle_start_at > idle_wait_time ) {
    Serial.println(F("Idle too long, need to power down!"));
    //设置中断
    attachInterrupt(digitalPinToInterrupt(2), wakeISR, CHANGE);
    energy.PowerDown();
  }
}
