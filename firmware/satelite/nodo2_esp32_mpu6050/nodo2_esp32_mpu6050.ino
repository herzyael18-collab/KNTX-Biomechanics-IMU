/**
 * @file nodo2_esp32_mpu6050.ino
 * @brief Firmware del Nodo Satélite 2 (Fémur) - Proyecto KNTX (Prototipo As-Built PC4)
 * @hardware ESP32 WROOM-32 (DevKit con pines) + Sensor IMU MPU6050 (I2C 400 kHz)
 * @author Yael Alejandro Yah Hernández (Firmware Satélite / Fusión Madgwick / ESP-NOW)
 *
 * Propósito en PC4 (Análisis de Equivalencia As-Built):
 *  Mientras arriban los BNO085 adicionales para el escalado del PC5, este nodo emplea
 *  el ESP32 WROOM-32 (doble núcleo, 240 MHz) junto con un MPU6050 ejecutando un filtro
 *  Madgwick 6-DOF a 100 Hz para generar la MISMA trama estándar KNTX (cuaterniones +
 *  aceleración) vía ESP-NOW. Esto permite validar de forma inmediata:
 *   - Recepción concurrente real de >= 2 nodos físicos a 100 Hz (RP-01 / RF-01).
 *   - Sincronización SNTP con jitter < 5 ms (eliminando el cuello de botella del Spoofer PC3).
 *   - Cálculo de ángulo articular relativo de rodilla (Fémur-Tibia) sin Gimbal Lock (RF-02).
 *   - Prueba en vivo de desconexión/apagado de nodo satélite ante FreeRTOS (Caso Crítico PC4).
 *
 * Conexión de pines (ESP32 WROOM-32 <-> MPU6050):
 *   - SDA : GPIO 21
 *   - SCL : GPIO 22
 *   - VCC : 3.3 V
 *   - GND : GND
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <math.h>
#include "../../common/kntx_protocol.h"

// ============================================================================
// PARÁMETROS DE HARDWARE Y FILTRO MADGWICK 6-DOF
// ============================================================================
#define PIN_I2C_SDA        21
#define PIN_I2C_SCL        22
#define MY_NODE_ID         NODE_ID_FEMUR  // 2 = Fémur
#define SAMPLE_PERIOD_US   10000UL        // 100 Hz exactos (10 ms)
#define MADGWICK_BETA      0.12f          // Ganancia del filtro de descenso de gradiente
#define STATIC_CALIB_SAMPLES 250          // ~2.5 s de estimación de bias en reposo al arranque

// Dirección MAC real del Gateway ESP32-S3 (verificada en vivo: E0:72:A1:F4:EB:D8)
uint8_t gatewayMac[6] = {0xE0, 0x72, 0xA1, 0xF4, 0xEB, 0xD8};

Adafruit_MPU6050 mpu;

// Estado de sincronización temporal SNTP con el Gateway
volatile int64_t  g_clockOffsetMs = 0;
volatile bool     g_hasSync       = false;

// Estado del cuaternión estimado por filtro Madgwick (w, x, y, z)
static float q0 = 1.0f, q1 = 0.0f, q2 = 0.0f, q3 = 0.0f;

// Bias del giroscopio (rad/s) estimado en inicialización estática (RF-04)
static float g_gyroBiasX = 0.0f, g_gyroBiasY = 0.0f, g_gyroBiasZ = 0.0f;
static uint8_t g_calibStatus = 0; // 0 = sin calibrar, 3 = bias calibrado

// Contadores y temporización no bloqueante
static uint16_t g_seqNum       = 0;
static uint32_t g_txOkCount    = 0;
static uint32_t g_txErrCount   = 0;
static uint64_t g_lastSampleUs = 0;
static uint32_t g_lastStatMs   = 0;

// ============================================================================
// ALGORITMO DE FUSIÓN MADGWICK 6-DOF (SIN ÁNGULOS DE EULER -> SIN GIMBAL LOCK)
// ============================================================================

/**
 * @brief Actualiza el cuaternión [q0,q1,q2,q3] a partir de giroscopio (rad/s) y
 *        acelerómetro (m/s^2 o g) con paso temporal dt (segundos).
 */
void madgwickUpdateIMU(float gx, float gy, float gz, float ax, float ay, float az, float dt) {
  float recipNorm;
  float s0, s1, s2, s3;
  float qDot1, qDot2, qDot3, qDot4;
  float _2q0, _2q1, _2q2, _2q3, _4q0, _4q1, _4q2, _8q1, _8q2, q0q0, q1q1, q2q2, q3q3;

  // Tasa de cambio del cuaternión a partir de velocidad angular
  qDot1 = 0.5f * (-q1 * gx - q2 * gy - q3 * gz);
  qDot2 = 0.5f * ( q0 * gx + q2 * gz - q3 * gy);
  qDot3 = 0.5f * ( q0 * gy - q1 * gz + q3 * gx);
  qDot4 = 0.5f * ( q0 * gz + q1 * gy - q2 * gx);

  // Corrección gravitacional solo si el acelerómetro tiene magnitud válida
  float aNormSq = ax * ax + ay * ay + az * az;
  if (aNormSq > 1e-6f) {
    recipNorm = 1.0f / sqrtf(aNormSq);
    ax *= recipNorm;
    ay *= recipNorm;
    az *= recipNorm;

    _2q0 = 2.0f * q0; _2q1 = 2.0f * q1; _2q2 = 2.0f * q2; _2q3 = 2.0f * q3;
    _4q0 = 4.0f * q0; _4q1 = 4.0f * q1; _4q2 = 4.0f * q2;
    _8q1 = 8.0f * q1; _8q2 = 8.0f * q2;
    q0q0 = q0 * q0; q1q1 = q1 * q1; q2q2 = q2 * q2; q3q3 = q3 * q3;

    // Paso de descenso de gradiente para minimizar error de referencia gravitacional
    s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay;
    s1 = _4q1 * q3q3 - _2q3 * ax + 4.0f * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az;
    s2 = 4.0f * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az;
    s3 = 4.0f * q1q1 * q3 - _2q1 * ax + 4.0f * q2q2 * q3 - _2q2 * ay;

    float sNormSq = s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3;
    if (sNormSq > 1e-12f) {
      recipNorm = 1.0f / sqrtf(sNormSq);
      s0 *= recipNorm; s1 *= recipNorm; s2 *= recipNorm; s3 *= recipNorm;
      qDot1 -= MADGWICK_BETA * s0;
      qDot2 -= MADGWICK_BETA * s1;
      qDot3 -= MADGWICK_BETA * s2;
      qDot4 -= MADGWICK_BETA * s3;
    }
  }

  // Integración numérica y renormalización
  q0 += qDot1 * dt;
  q1 += qDot2 * dt;
  q2 += qDot3 * dt;
  q3 += qDot4 * dt;

  recipNorm = 1.0f / sqrtf(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
  q0 *= recipNorm;
  q1 *= recipNorm;
  q2 *= recipNorm;
  q3 *= recipNorm;
}

// ============================================================================
// CALLBACKS ESP-NOW (SNTP + DIAGNÓSTICO DE ENVÍO)
// ============================================================================

void onEspNowRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  (void)info;
  if (len == (int)sizeof(kntx_sync_t) && data[0] == KNTX_MSG_SYNC) {
    kntx_sync_t syncMsg;
    memcpy(&syncMsg, data, sizeof(kntx_sync_t));
    g_clockOffsetMs = (int64_t)syncMsg.gateway_ms - (int64_t)millis();
    g_hasSync = true;
  }
}

void onEspNowSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  (void)tx_info;
  if (status == ESP_NOW_SEND_SUCCESS) g_txOkCount++;
  else g_txErrCount++;
}

/**
 * @brief Calibración estática de bias del giroscopio al arranque (RF-04).
 */
void calibrateGyroStatic() {
  Serial.println("[CALIB] Mantener Nodo 2 (Femur) inmovil para calibracion estatica de giroscopio...");
  double sumX = 0.0, sumY = 0.0, sumZ = 0.0;
  sensors_event_t a, g, temp;

  for (int i = 0; i < STATIC_CALIB_SAMPLES; i++) {
    mpu.getEvent(&a, &g, &temp);
    sumX += g.gyro.x;
    sumY += g.gyro.y;
    sumZ += g.gyro.z;
    delay(10); // Solo permitido en rutina de inicialización previa al bucle crítico
  }

  g_gyroBiasX = (float)(sumX / STATIC_CALIB_SAMPLES);
  g_gyroBiasY = (float)(sumY / STATIC_CALIB_SAMPLES);
  g_gyroBiasZ = (float)(sumZ / STATIC_CALIB_SAMPLES);
  g_calibStatus = 3;
  Serial.printf("[OK] Bias giroscopio calibrado: [%.4f, %.4f, %.4f] rad/s\n",
                g_gyroBiasX, g_gyroBiasY, g_gyroBiasZ);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(400000); // Fast-mode I2C 400 kHz local (< 10 cm)

  Serial.println("\n====================================================");
  Serial.println("  KNTX - NODO SATELITE 2 (FEMUR) | ESP32 + MPU6050");
  Serial.println("  Madgwick 6-DOF 100 Hz | ESP-NOW | Sync SNTP");
  Serial.println("====================================================");

  // Inicializar ESP-NOW
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(KNTX_ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);
  if (esp_now_init() == ESP_OK) {
    esp_now_register_recv_cb(onEspNowRecv);
    esp_now_register_send_cb(onEspNowSent);
    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, gatewayMac, 6);
    peerInfo.channel = KNTX_ESPNOW_CHANNEL;
    peerInfo.encrypt = false;
    esp_now_add_peer(&peerInfo);
    Serial.print("[OK] ESP-NOW activo | MAC Nodo 2 (Femur): ");
    Serial.println(WiFi.macAddress());
  }

  // Inicializar MPU6050
  if (!mpu.begin()) {
    Serial.println("[ERROR] MPU6050 no encontrado en I2C (GPIO21=SDA, GPIO22=SCL).");
  } else {
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_1000_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_44_HZ);
    calibrateGyroStatic();
  }

  g_lastSampleUs = esp_timer_get_time();
  g_lastStatMs   = millis();
}

void loop() {
  uint64_t nowUs = esp_timer_get_time();
  if ((nowUs - g_lastSampleUs) >= SAMPLE_PERIOD_US) {
    float dt = (float)(nowUs - g_lastSampleUs) * 1e-6f;
    g_lastSampleUs = nowUs;
    if (dt <= 0.0f || dt > 0.1f) dt = 0.01f;

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    float gx = g.gyro.x - g_gyroBiasX;
    float gy = g.gyro.y - g_gyroBiasY;
    float gz = g.gyro.z - g_gyroBiasZ;

    float ax_g = a.acceleration.x / 9.80665f;
    float ay_g = a.acceleration.y / 9.80665f;
    float az_g = a.acceleration.z / 9.80665f;

    // Fusión sensorial sin singularidades de Euler
    madgwickUpdateIMU(gx, gy, gz, ax_g, ay_g, az_g, dt);

    int64_t syncedTimeMs = (int64_t)millis() + g_clockOffsetMs;
    if (syncedTimeMs < 0) syncedTimeMs = 0;

    kntx_packet_t pkt;
    pkt.msg_type     = KNTX_MSG_DATA;
    pkt.node_id      = MY_NODE_ID;
    pkt.timestamp_ms = (uint32_t)syncedTimeMs;
    pkt.quat[0]      = q0;
    pkt.quat[1]      = q1;
    pkt.quat[2]      = q2;
    pkt.quat[3]      = q3;
    pkt.accel[0]     = ax_g;
    pkt.accel[1]     = ay_g;
    pkt.accel[2]     = az_g;
    pkt.calib_status = g_calibStatus;
    pkt.seq_num      = g_seqNum++;

    esp_now_send(gatewayMac, (uint8_t *)&pkt, sizeof(kntx_packet_t));
  }

  if ((millis() - g_lastStatMs) >= 2000) {
    g_lastStatMs = millis();
    Serial.printf("[NODO2-FEMUR] TX_OK=%lu | TX_ERR=%lu | Sync=%s (off=%lld ms) | q=[%.3f,%.3f,%.3f,%.3f]\n",
                  (unsigned long)g_txOkCount,
                  (unsigned long)g_txErrCount,
                  g_hasSync ? "SI" : "NO",
                  (long long)g_clockOffsetMs,
                  q0, q1, q2, q3);
  }
}
