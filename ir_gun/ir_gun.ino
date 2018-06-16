#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include <Enerlib.h>
#include <ArduinoJson.h>

// 创建nRF24L01实例
RF24 radio(7,8);

// 创建Energy实例
Energy energy;

// 创建ArduinoJson实例
StaticJsonBuffer<100> json_buffer_send;
JsonObject& root_send = json_buffer_send.createObject();
StaticJsonBuffer<100> json_buffer_receive;

// 读写通道地址
const uint64_t pipes[2] = { 0xF0F0F0F0E1LL, 0xF0F0F0F0D2LL };

// CMD枚举
typedef enum { cmd_invalid = 0, cmd_shoot = 1, cmd_confirm, cmd_adjust, cmd_end, cmd_respone } cmd_e;

// cmd
// cmd_e cmd = cmd_shoot;

// 状态枚举
typedef enum { state_invalid = 0, state_normal = 1, state_adjust, state_powerdown } state_e;

// 状态变量
volatile state_e state_flag = state_invalid;

// 负载设置
const int min_payload_size = 4;
const int max_payload_size = 32;
const int payload_size_increments_by = 1;
int next_payload_size = min_payload_size;
char receive_payload[max_payload_size+1]; // +1 to allow room for a terminating NULL char

// 管脚定义
const int button_trigger_pin = 2;
const int ir_pin = 3;
const int button_func_pin = 4;

// 按键状态
int button_trigger_state = 1;
int last_button_trigger_state = 1;
int button_func_state = 1;
int last_button_func_state = 1;
unsigned long button_func_duration;

// 声明变量
const int delay_time = 200;
const unsigned long idle_wait_time = 50000;
const unsigned long response_waiting_time = 500;
unsigned long idle_start_at = 0;
unsigned long id_transmit = 0;

// 数据传输同步
const int data_sync_witdh = 3;
const unsigned char sync_start_tx[data_sync_witdh]={0,255,255};//开始帧
const unsigned char sync_end_tx[data_sync_witdh]={255,255,0};//结束帧

void setup() {
  Serial.begin(115200);
  Serial.println(F("gun go!go!go!"));
  pinMode(button_trigger_pin, INPUT_PULLUP);
  pinMode(button_func_pin, INPUT_PULLUP);
  pinMode(ir_pin, OUTPUT);
  id_transmit = 0;

  //创建一个json，与主机通讯
  // {
  //   "ver": "0.1", 目前没有这个值
  //   "ID": 0,
  //   "role": "Gun1"
  //   "cmd":0,
  // }
  //root["ver"] = "0.1";
  root_send["ID"] = id_transmit;
  root_send["gun"] = "p";
  root_send["cmd"] = int(cmd_invalid);
  root_send.prettyPrintTo(Serial);
  Serial.println(json_buffer_send.size());

  // 初始化nRF24L01
  radio.begin();

  // 使能动态负载
  radio.enableDynamicPayloads();

  // 可选，设置发送失败重试次数和间隔
  radio.setRetries(5,15);

  // 设置通道地址
  radio.openWritingPipe(pipes[0]);
  radio.openReadingPipe(1,pipes[1]);

  // 开始监听
  radio.startListening();

  // 打印nRF24L01配置信息
  radio.printDetails();
  Serial.println();

  // 初始状态为normal
  state_flag = state_normal;

  // 配置结束，开始记录空闲
  idle_start_at = millis();
}

int send_cmd(cmd_e cmd) {
  // 定义32bytes用于发送
  char data[32];
  // char buf[32];
  // int index_data;
  // 填充数据
  id_transmit++;
  root_send["ID"] = id_transmit;
  root_send["cmd"] = int(cmd);

  // 先停止监听才能发送
  radio.stopListening();

  // 发送数据，会一直阻塞直到发送完毕
  int size_root = root_send.measureLength();
  Serial.print(F("Now sending length of cmd:"));
  Serial.println(size_root);
  // 将json打印到串口
  root_send.printTo(Serial);
  Serial.println();
  // 先发送起始帧
  //radio.write(sync_start_tx, data_sync_witdh);
  // 发送总的长度
  //radio.write(size_root, 2);
  // 发送帧数，每帧31字节，头2字节是序号

  // 将json打印为str用于传输，printTo这个函数需要多加一个字节存放null字符
  root_send.printTo(data, size_root + 1);
  radio.write(data, size_root);
  // 最后发送结束帧
  //radio.write(sync_end_tx, data_sync_witdh);

  // 开始监听
  radio.startListening();

  // 等待直到识别端反馈respone，或者超时
  unsigned long started_waiting_at = millis();
  bool timeout = false;
  while (!radio.available() && !timeout)
    if (millis() - started_waiting_at > response_waiting_time)
      timeout = true;

  // 输出结果
  if (timeout) {
    Serial.println(F("Failed, response timed out."));
    return cmd_invalid;
  } else {
    // 收到反馈
    uint8_t len = radio.getDynamicPayloadSize();

    // 如果接收到错误的包，芯片会清除
    if(!len) {
      return cmd_invalid;
    }

    radio.read(receive_payload, len);

    // 结尾置零
    receive_payload[len] = 0;

    // 打印接收内容
    Serial.print(F("Got response size="));
    Serial.print(len);
    Serial.print(F(" value="));
    Serial.println(receive_payload);
    JsonObject& root_receive = json_buffer_receive.parseObject(receive_payload);
    Serial.print(F("json_buffer_receive size:"));
    Serial.println(json_buffer_receive.size());
    if (!root_receive.success()) {
        Serial.println("ERROR:parseObject() failed");
        json_buffer_receive.clear();
        return cmd_invalid;
    }
    int ret = root_receive["cmd"];
    json_buffer_receive.clear();
    return ret;
  }
}

void wakeISR() {
   if (energy.WasSleeping()) {
    // 待机时的中断响应
    Serial.println(F("Now, we need to wake up!"));
    detachInterrupt(digitalPinToInterrupt(2));
    radio.powerUp();
    state_flag = state_normal;
  } else {
    // 非待机时的中断响应
  }
}

void loop() {
  // 扳机检测
  button_trigger_state = digitalRead(button_trigger_pin);
  if (button_trigger_state != last_button_trigger_state) {
    if (button_trigger_state == HIGH) {
      // 按键没按
      Serial.println(F("Trigger not Pressed!"));
      digitalWrite(ir_pin, LOW);
    } else {
      // 按键按下
      Serial.println(F("Trigger Pressed!"));
      int tmp_cmd;
      switch (state_flag) {
        case state_normal:
          tmp_cmd = send_cmd(cmd_shoot);
          // 如果有反馈，需要延时100ms
          if (tmp_cmd == cmd_respone) {
            digitalWrite(ir_pin, HIGH);
            delay(100);
            digitalWrite(ir_pin, LOW);
          }
          break;
        case state_adjust:
          tmp_cmd = send_cmd(cmd_confirm);
          // 接收到end指令，就返回正常模式
          if (tmp_cmd == cmd_end)
            state_flag = state_normal;
          break;
        case state_powerdown:
          break;
      }
      delay(delay_time);
    }
    delay(50);
    idle_start_at = millis();
  }
  last_button_trigger_state = button_trigger_state;

  // 功能键长按检测
  button_func_state = digitalRead(button_func_pin);
  if (button_func_state == LOW) {
    // 按键按下
    delay(100);
    button_func_state = digitalRead(button_func_pin);
    if ((button_func_state == LOW) && (state_flag != state_adjust)) {
      Serial.println(F("FB Pressed!"));
      button_func_duration = millis();
      while (button_func_state == LOW) {
        if (millis() - button_func_duration >= 3*1000) {
          Serial.println(F("Detect function button Pressed!!"));
          int tmp_cmd = send_cmd(cmd_adjust);
          if (tmp_cmd == cmd_respone) {
            state_flag = state_adjust;
            Serial.println(F("Entry adjust mode!!"));
          }
          break;
        }
        delay(100);
        button_func_state = digitalRead(button_func_pin);
      }
    }
    delay(50);
    idle_start_at = millis();
  }

  if (millis() - idle_start_at > idle_wait_time ) {
    Serial.println(F("Idle too long, need to power down!"));
    // 设置中断
    attachInterrupt(digitalPinToInterrupt(2), wakeISR, CHANGE);
    state_flag = state_powerdown;
    radio.powerDown();
    energy.PowerDown();
  }
}
