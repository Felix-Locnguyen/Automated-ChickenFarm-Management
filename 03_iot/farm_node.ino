/* farm_node.ino — Firmware "node chuồng gà" ESP32 (Phase 2, Bước 8)
 *
 * Node này làm THAY 4 thiết bị trong 1 chuồng: cảm biến + quạt + đèn sưởi + máy cho ăn.
 * Nói chuyện với backend qua MQTT — ĐÚNG PROTOCOL đã test ở Bước 3-6:
 *
 *   📤 PUBLISH  farm/sensor/{SENSOR_ID}       mỗi SENSOR_INTERVAL_MS:
 *       {"temperature":28.5,"humidity":55,"food_level":75,"water_level":80}
 *   📤 PUBLISH  farm/device/{FEEDER_ID}/status  (báo trạng thái THẬT sau khi cho ăn):
 *       {"state":"done","actual_grams":2498.0,"target_grams":2500.0}
 *       {"state":"error","error":"ket-motor","target_grams":2500.0}
 *   📥 SUBSCRIBE farm/device/{FAN_ID}/command     ON / OFF
 *   📥 SUBSCRIBE farm/device/{LIGHT_ID}/command   ON / OFF
 *   📥 SUBSCRIBE farm/device/{FEEDER_ID}/command  FEED {amount_kg: 2.5}
 *
 * PHẦN CỨNG (dây nối):
 *   DHT22        GPIO 4        → temperature + humidity
 *   HC-SR04      TRIG 5, ECHO 18 → food_level (độ đầy silo thức ăn, %)
 *   Relay quạt   GPIO 25       (IN1 module 4 kênh — QUÁN TÍNH thường LOW=ON)
 *   Relay đèn    GPIO 26       (IN2)
 *   Relay motor  GPIO 27       (IN3 — motor máy cho ăn)
 *   HX711        DOUT 32, SCK 33 → load-cell cân thức ăn (grams)
 *
 * THƯ VIỆN CẦN CÀI (Arduino Library Manager):
 *   - PubSubClient         (Nick O'Leary)   — MQTT
 *   - DHT sensor library   (Adafruit)       — DHT22
 *   - HX711 Arduino Library(bogde)          — load-cell
 *   - ArduinoJson          (Benoit Blanchon) — parse lệnh FEED
 *
 * HIỆU CHUẨN HX711: đặt vật nặng ĐÃ TRỌNG LƯỢNG BIẾT (vd 1kg) lên cân,
 * sửa HX711_CALIBRATION sao cho đọc ra đúng 1000g. Xem serial monitor.
 *
 * BÀI HỌC KỸ THUẬT (tương tự uplink backend):
 *   - KHÔNG dùng delay() trong loop khi motor đang chạy → sẽ chặn nhận MQTT.
 *   - Thay vào đó: STATE MACHINE + millis() — loop luôn chạy, việc "đang cho ăn"
 *     chỉ là 1 trạng thái, mỗi lượt loop kiểm tra "đã đủ gram chưa?".
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <HX711.h>
#include <ArduinoJson.h>

// ============ CẤU HÌNH — SỬA 3 KHỐI NÀY CHO TRÙNG VỚI DB ============
const char* WIFI_SSID     = "TenWiFiCuaBan";
const char* WIFI_PASSWORD = "MatKhauWiFi";
const char* MQTT_HOST     = "192.168.1.100";   // IP máy chạy mosquitto (KHÔNG dùng "localhost"!)
uint16_t    MQTT_PORT     = 1883;

// device_id TRONG DB — lấy bằng: curl http://localhost:8000/api/devices
// (node chuồng A1 trong seed data: sensor=13, fan=1, light=2, feeder=3)
int SENSOR_ID  = 13;
int FAN_ID     = 1;
int LIGHT_ID   = 2;
int FEEDER_ID  = 3;
// =====================================================================

#define DHT_PIN       4
#define DHT_TYPE      DHT22

#define RELAY_FAN_PIN    25
#define RELAY_LIGHT_PIN  26
#define RELAY_MOTOR_PIN  27
#define RELAY_ON   LOW    // module relay thường QUÁN TÍNH: LOW = đóng relay = BẬT
#define RELAY_OFF  HIGH

#define ULTRA_TRIG_PIN  5
#define ULTRA_ECHO_PIN  18
#define SILO_EMPTY_CM   40.0   // silo rỗng: khoảng cách 40cm → 0%
#define SILO_FULL_CM    5.0    // silo đầy:  5cm  → 100%

#define HX711_DOUT_PIN  32
#define HX711_SCK_PIN   33
float HX711_CALIBRATION = -12700.0;   // SỬA khi hiệu chuẩn thật (xem header)

const unsigned long SENSOR_INTERVAL_MS = 5000;    // 5s/lần — trùng nhịp test bench
const unsigned long FEED_STALL_TIMEOUT_MS = 15000; // 15s không tăng gram → kẹt motor

WiFiClient espClient;
PubSubClient mqtt(espClient);
DHT dht(DHT_PIN, DHT_TYPE);
HX711 loadCell;

// ---- State machine cho việc cho ăn (KHÔNG delay() — bài học thread-safety) ----
enum FeedState { FEED_IDLE, FEED_RUNNING };
FeedState feedState = FEED_IDLE;
float feedTargetGrams = 0.0;
float lastWeightGrams = 0.0;
unsigned long feedStartMs = 0;
unsigned long lastWeightChangeMs = 0;
float lastStableWeight = 0.0;

unsigned long lastSensorMs = 0;
char topicSensor[64], topicFan[64], topicLight[64], topicFeeder[64], topicFeederStatus[64];

// ============================ WIFI ============================
void wifiConnect() {
  Serial.printf("Dang ket noi WiFi '%s'", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.printf("\nWiFi OK — IP: %s\n", WiFi.localIP().toString().c_str());
}

// ============================ MQTT ============================
void publishJson(const char* topic, JsonDocument& doc) {
  char buffer[256];
  size_t n = serializeJson(doc, buffer, sizeof(buffer));
  bool ok = mqtt.publish(topic, buffer, n);
  Serial.printf("%s %s: %s\n", ok ? "PUBLISH OK" : "PUBLISH THAT BAI", topic, buffer);
}

void reportFeederStatus(const char* state, const char* error = nullptr) {
  // Backend CHƯA subscribe topic này (Phase sau) — nhưng firmware PHẢI
  // báo sự thật ngay từ đầu: "tôi đã rải thật bao nhiêu gram".
  StaticJsonDocument<192> doc;
  doc["state"] = state;
  doc["actual_grams"] = round(lastWeightGrams * 10) / 10.0;
  doc["target_grams"] = feedTargetGrams;
  if (error) doc["error"] = error;
  publishJson(topicFeederStatus, doc);
}

void onFeederCommand(JsonDocument& doc) {
  const char* cmd = doc["command"] | "";
  if (strcmp(cmd, "FEED") != 0) return;   // feeder CHỈ hiểu FEED

  float kg = doc["params"]["amount_kg"] | 0.0;
  if (kg <= 0) {
    Serial.println("LENH FEED sai: amount_kg <= 0 — bo qua");
    return;
  }
  feedTargetGrams = kg * 1000.0;
  lastStableWeight = lastWeightGrams;      // mốc so sánh để phát hiện kẹt motor
  lastWeightChangeMs = millis();
  feedStartMs = millis();
  feedState = FEED_RUNNING;
  digitalWrite(RELAY_MOTOR_PIN, RELAY_ON);
  Serial.printf("FEED: motor BAT — rai toi khi can xac nhan %.0fg\n", feedTargetGrams);
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  // Chạy TRONG network thread của PubSubClient — GIỐNG backend: ở đây
  // CHỈ parse + ra lệnh tức thì (relay là GPIO, không blocking), KHÔNG query gì nặng.
  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, payload, length)) {
    Serial.printf("Payload JSON sai tren %s\n", topic);
    return;
  }
  const char* cmd = doc["command"] | "?";
  Serial.printf("Nhan lenh %s tren %s\n", cmd, topic);

  if (strcmp(topic, topicFan) == 0) {
    digitalWrite(RELAY_FAN_PIN, (strcmp(cmd, "ON") == 0) ? RELAY_ON : RELAY_OFF);
  } else if (strcmp(topic, topicLight) == 0) {
    digitalWrite(RELAY_LIGHT_PIN, (strcmp(cmd, "ON") == 0) ? RELAY_ON : RELAY_OFF);
  } else if (strcmp(topic, topicFeeder) == 0) {
    onFeederCommand(doc);
  }
}

void mqttReconnectIfNeeded() {
  if (mqtt.connected()) return;
  Serial.print("Dang ket noi MQTT broker...");
  // ClientId PHẢI duy nhất — trùng clientId 2 thiết bị thì broker đá 1 thằng
  String clientId = String("farm-node-") + SENSOR_ID + "-" + random(1000);
  if (mqtt.connect(clientId.c_str())) {
    Serial.println(" OK");
    mqtt.subscribe(topicFan);
    mqtt.subscribe(topicLight);
    mqtt.subscribe(topicFeeder);
    Serial.printf("Da subscribe: %s, %s, %s\n", topicFan, topicLight, topicFeeder);
  } else {
    Serial.printf(" that bai (rc=%d) — thu lai sau 5s\n", mqtt.state());
    delay(5000);   // delay ở đây AN TOÀN: chỉ chạy khi broker chết, không có việc khác
  }
}

// ====================== CẢM BIẾN =======================
float readFoodLevelPercent() {
  digitalWrite(ULTRA_TRIG_PIN, LOW);  delayMicroseconds(2);
  digitalWrite(ULTRA_TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(ULTRA_TRIG_PIN, LOW);
  long duration = pulseIn(ULTRA_ECHO_PIN, HIGH, 30000);  // timeout 30ms
  if (duration == 0) return -1;                          // cảm biến hỏng/không có gì
  float cm = duration * 0.034 / 2.0;
  float pct = (SILO_EMPTY_CM - cm) / (SILO_EMPTY_CM - SILO_FULL_CM) * 100.0;
  return constrain(pct, 0, 100);   // kẹp trong [0,100]
}

void publishSensorReading() {
  float temperature = dht.readTemperature();
  float humidity    = dht.readHumidity();
  float foodLevel   = readFoodLevelPercent();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT22 doc loi — bo qua lan nay");
    return;
  }
  // TODO Phase sau: thêm cảm biến mức nước (float switch / HC-SR04 thứ 2)
  float waterLevel = 80.0;

  StaticJsonDocument<192> doc;
  doc["temperature"] = round(temperature * 10) / 10.0;
  doc["humidity"]    = round(humidity * 10) / 10.0;
  doc["food_level"]  = (foodLevel < 0) ? 75.0 : foodLevel;   // lỗi cảm biến → giá trị giả lập
  doc["water_level"] = waterLevel;
  publishJson(topicSensor, doc);
}

// ====================== MÁY CHO ĂN (state machine) =====================
void feedTick() {
  if (feedState != FEED_RUNNING) return;

  if (loadCell.is_ready()) {
    lastWeightGrams = loadCell.get_units(2);   // trung bình 2 lần đọc → ít noise
  }

  // Cân CHƯA tăng trong FEED_STALL_TIMEOUT_MS → motor quay mà không ra thức ăn
  if (abs(lastWeightGrams - lastStableWeight) > 5.0) {   // lệch >5g = đang rải thật
    lastStableWeight = lastWeightGrams;
    lastWeightChangeMs = millis();
  }

  if (lastWeightGrams >= feedTargetGrams - 10.0) {   // đủ (sai số 10g)
    digitalWrite(RELAY_MOTOR_PIN, RELAY_OFF);
    feedState = FEED_IDLE;
    Serial.printf("FEED xong — can xac nhan %.1fg / %.0fg\n",
                  lastWeightGrams, feedTargetGrams);
    reportFeederStatus("done");

  } else if (millis() - lastWeightChangeMs > FEED_STALL_TIMEOUT_MS) {
    digitalWrite(RELAY_MOTOR_PIN, RELAY_OFF);   // DỪNG NGAY — an toàn motor
    feedState = FEED_IDLE;
    Serial.println("FEED LOI: ket motor (can khong tang) — motor da dung");
    reportFeederStatus("error", "ket-motor");

  } else if (millis() - feedStartMs > 120000) {  // an toàn: quá 2 phút → dừng
    digitalWrite(RELAY_MOTOR_PIN, RELAY_OFF);
    feedState = FEED_IDLE;
    reportFeederStatus("error", "qua-gio");
  }
  // KHÔNG delay() ở đây — loop vẫn chạy đều, vẫn nhận MQTT
}

// ============================ SETUP / LOOP ============================
void setup() {
  Serial.begin(115200);
  randomSeed(micros());

  pinMode(RELAY_FAN_PIN, OUTPUT);    digitalWrite(RELAY_FAN_PIN, RELAY_OFF);
  pinMode(RELAY_LIGHT_PIN, OUTPUT);  digitalWrite(RELAY_LIGHT_PIN, RELAY_OFF);
  pinMode(RELAY_MOTOR_PIN, OUTPUT);  digitalWrite(RELAY_MOTOR_PIN, RELAY_OFF);
  pinMode(ULTRA_TRIG_PIN, OUTPUT);   pinMode(ULTRA_ECHO_PIN, INPUT);

  dht.begin();
  loadCell.begin(HX711_DOUT_PIN, HX711_SCK_PIN);
  loadCell.set_scale(HX711_CALIBRATION);
  loadCell.tare();   // tare khi silo TRỐNG — nhớ tháo thức ăn trước khi cấp nguồn!

  // Gộp topic 1 lần — tránh lặp code
  snprintf(topicSensor,       sizeof topicSensor,       "farm/sensor/%d", SENSOR_ID);
  snprintf(topicFan,          sizeof topicFan,          "farm/device/%d/command", FAN_ID);
  snprintf(topicLight,        sizeof topicLight,        "farm/device/%d/command", LIGHT_ID);
  snprintf(topicFeeder,       sizeof topicFeeder,       "farm/device/%d/command", FEEDER_ID);
  snprintf(topicFeederStatus, sizeof topicFeederStatus, "farm/device/%d/status", FEEDER_ID);

  wifiConnect();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);   // default 256 bytes — chật với JSON nhiều field
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) wifiConnect();   // WiFi chết → kết nối lại
  mqttReconnectIfNeeded();
  mqtt.loop();          // giữ kết nối MQTT sống + dispatch callback

  if (millis() - lastSensorMs >= SENSOR_INTERVAL_MS) {
    lastSensorMs = millis();
    if (mqtt.connected()) publishSensorReading();
  }

  feedTick();           // kiểm tra tiến độ cho ăn — mỗi lượt loop
  // KHÔNG delay() cuối loop!
}
