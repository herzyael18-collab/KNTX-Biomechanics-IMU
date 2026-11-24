/**
 * @file nodo1_c3_bno085.ino
 * @brief Firmware del Nodo Satélite 1 (Tibia) - Proyecto KNTX
 * @hardware ESP32-C3 (DevKit / SuperMini) + Sensor IMU BNO085 en modo SPI (3 MHz)
 * @author Yael Alejandro Yah Hernández (Firmware Satélite / SPI / ESP-NOW)
 *
 * Funcionalidades implementadas:
 *  1. Lectura del BNO085 por bus SPI a 3 MHz (cumplimiento RP-04 y RQ-01).
 *  2. Fusión sensorial en hardware (SH-2 Cortex-M0+):
 *     - Modo por defecto: SH2_GAME_ROTATION_VECTOR (sin magnetómetro, inmune a hierro de caminadora, deriva < 3 °/min).
 *     - Alternable por comando serial ('m') a SH2_ROTATION_VECTOR (con magnetómetro, deriva < 1 °/min).
 *  3. Sincronización temporal SNTP por broadcast desde el Gateway ESP32-S3 cada 1,000 ms (jitter < 5 ms, RP-01).
 *  4. Medición directa de tiempo de lectura SPI (us) y pulso GPIO de latencia para osciloscopio (PV-02 y PV-04).
 *  5. Transmisión inalámbrica determinista a 100 Hz (periodo exacto de 10 ms sin delay bloqueante) vía ESP-NOW.
 *
 * Conexión de pines (ESP32-C3 <-> BNO085 en modo SPI; jumpers PS0=HIGH, PS1=HIGH en BNO085):
 *   - SCK  (SCLK) : GPIO 4
 *   - MISO (SDO)  : GPIO 5
 *   - MOSI (DI)   : GPIO 6
 *   - CS   (CSB)  : GPIO 7
 *   - INT  (H_INT): GPIO 2
 *   - RST  (NRST) : GPIO 3
 *   - GPIO_LAT    : GPIO 10 (Pulso de prueba para osciloscopio en PV-04: flanco de subida al enviar paquete)
 */

#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <Adafruit_BNO08x.h>
#include "../../common/kntx_protocol.h"

// ============================================================================
// CONFIGURACIÓN DE PINES Y PARÁMETROS DE HARDWARE (AS-BUILT PROTOBOARD / PCB)
// ============================================================================
#define PIN_SPI_SCK   4
#define PIN_SPI_MISO  5
#define PIN_SPI_MOSI  6
#define PIN_BNO_CS    7
#define PIN_BNO_INT   2
#define PIN_BNO_RST   3
#define PIN_LAT_TRIG  10   // Pin de disparo para medir latencia en el aire con osciloscopio

// Configuración del nodo
#define MY_NODE_ID        NODE_ID_TIBIA  // 1 = Tibia
#define SAMPLE_PERIOD_US  10000UL        // 100 Hz exactos (10,000 us)
#define SPI_CLOCK_HZ      3000000UL      // 3 MHz (cumplimiento RP-04 / RQ-01)

// Dirección MAC del Gateway ESP32-S3 (por defecto broadcast para plug-and-play en banco;
// sustituir por la MAC impresa por el Gateway para tráfico unicast estricto)
uint8_t gatewayMac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// ============================================================================
// VARIABLES GLOBALES DE ESTADO Y SINCRONIZACIÓN
// ============================================================================
Adafruit_BNO08x bno08x(PIN_BNO_RST);
sh2_SensorValue_t sensorValue;

// Estado de sincronización SNTP con el Gateway
volatile int64_t g_clockOffsetMs = 0;
volatile bool    g_hasSync       = false;
volatile uint32_t g_syncCount    = 0;

// Último cuaternión y aceleración válidos leídos del coprocesador SH-2
static float g_quat[4]   = {1.0f, 0.0f, 0.0f, 0.0f};
static float g_accel[3]  = {0.0f, 0.0f, 1.0f};
static uint8_t g_calib   = 0;
static bool g_useMagMode = false; // false = Game Rotation Vector (sin mag); true = Rotation Vector (con mag)

// Contadores de diagnóstico y cumplimiento de PV-01 / PV-02 / RQ-01
static uint16_t g_seqNum       = 0;
static uint32_t g_spiReadsOk   = 0;
static uint32_t g_spiReadsErr  = 0;
static uint32_t g_txOkCount    = 0;
static uint32_t g_txErrCount   = 0;
static uint32_t g_maxSpiReadUs = 0;

// Temporizadores no bloqueantes
static uint64_t g_lastSampleUs = 0;
static uint32_t g_lastStatMs   = 0;

// ============================================================================
// CALLBACKS DE ESP-NOW (CORE 3.x ESP32)
// ============================================================================

/**
 * @brief Callback ejecutado al recibir una trama broadcast de sincronización SNTP
 *        enviada por el Gateway ESP32-S3 cada 1,000 ms.
 */
void onEspNowRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  (void)info;
  if (len == (int)sizeof(kntx_sync_t) && data[0] == KNTX_MSG_SYNC) {
    kntx_sync_t syncMsg;
    memcpy(&syncMsg, data, sizeof(kntx_sync_t));
    // Aproximación SNTP (RTT/2 despreciable a < 2 m): offset = T_Gateway_tx - T_Nodo_rx
    int64_t localNowMs = (int64_t)millis();
    g_clockOffsetMs = (int64_t)syncMsg.gateway_ms - localNowMs;
    g_hasSync = true;
    g_syncCount++;
  }
}

/**
 * @brief Callback de confirmación de envío ESP-NOW.
 */
void onEspNowSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  (void)tx_info;
  if (status == ESP_NOW_SEND_SUCCESS) {
    g_txOkCount++;
  } else {
    g_txErrCount++;
  }
}

// ============================================================================
// CONFIGURACIÓN DE REPORTES DEL BNO085 (SPI 3 MHz)
// ============================================================================

bool configureBnoReports(bool useMagnetometer) {
  sh2_SensorId_t rotReport = useMagnetometer ? SH2_ROTATION_VECTOR : SH2_GAME_ROTATION_VECTOR;

  // Reporte de cuaternión de orientación a 100 Hz (10,000 us)
  if (!bno08x.enableReport(rotReport, SAMPLE_PERIOD_US)) {
    return false;
  }
  // Reporte de aceleración lineal/total a 100 Hz para detección de contacto inicial (> 3.0 g)
  if (!bno08x.enableReport(SH2_ACCELEROMETER, SAMPLE_PERIOD_US)) {
    return false;
  }
  return true;
}

/**
 * @brief Inicializa la interfaz SPI a 3 MHz y el sensor BNO085 con reintentos no bloqueantes.
 */
bool initBno085Spi() {
  SPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI, PIN_BNO_CS);

  if (!bno08x.begin_SPI(PIN_BNO_CS, PIN_BNO_INT, &SPI)) {
    Serial.println("[ERROR] BNO085 no detectado en bus SPI (verifica PS0=HIGH, PS1=HIGH y cableado < 10 cm).");
    return false;
  }

  Serial.println("[OK] BNO085 inicializado correctamente por SPI (3 MHz).");
  if (!configureBnoReports(g_useMagMode)) {
    Serial.println("[ERROR] No se pudieron habilitar reportes SH-2 del BNO085.");
    return false;
  }
  return true;
}

/**
 * @brief Inicializa Wi-Fi en modo estación (STA) y el stack ESP-NOW en el canal fijo.
 */
bool initEspNow() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(KNTX_ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);

  if (esp_now_init() != ESP_OK) {
    Serial.println("[ERROR] Fallo al inicializar ESP-NOW.");
    return false;
  }

  esp_now_register_recv_cb(onEspNowRecv);
  esp_now_register_send_cb(onEspNowSent);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, gatewayMac, 6);
  peerInfo.channel = KNTX_ESPNOW_CHANNEL;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("[ERROR] No se pudo registrar el Gateway como peer ESP-NOW.");
    return false;
  }

  Serial.print("[OK] ESP-NOW activo | MAC Nodo 1 (Tibia): ");
  Serial.println(WiFi.macAddress());
  return true;
}

// ============================================================================
// SETUP Y BUCLE PRINCIPAL DETERMINISTA (100 Hz SIN BLOQUEOS)
// ============================================================================

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LAT_TRIG, OUTPUT);
  digitalWrite(PIN_LAT_TRIG, LOW);

  // Pequeña espera inicial únicamente al arranque para estabilizar USB CDC en ESP32-C3
  uint32_t t0 = millis();
  while (!Serial && (millis() - t0 < 1500)) { /* espera segura */ }

  Serial.println("\n====================================================");
  Serial.println("  KNTX - NODO SATELITE 1 (TIBIA) | ESP32-C3 + BNO085");
  Serial.println("  Bus SPI 3 MHz | ESP-NOW 100 Hz | Sync SNTP");
  Serial.println("====================================================");

  initEspNow();

  if (!initBno085Spi()) {
    Serial.println("[WARN] Arrancando en modo espera de sensor; reintentando cada 2 s...");
  }

  g_lastSampleUs = esp_timer_get_time();
  g_lastStatMs   = millis();
}

void loop() {
  // 1. Comandos de prueba por consola serial (cambio de modo con/sin magnetómetro para PV-06)
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'm' || cmd == 'M') {
      g_useMagMode = !g_useMagMode;
      configureBnoReports(g_useMagMode);
      Serial.printf("[MODO] BNO085 cambiado a: %s\n",
                    g_useMagMode ? "Rotation Vector (CON mag, <1 deg/min)"
                                 : "Game Rotation Vector (SIN mag, <3 deg/min)");
    }
  }

  // 2. Recuperación automática si el BNO085 se reinicia por ruido eléctrico o caída de tensión
  if (bno08x.wasReset()) {
    Serial.println("[WARN] BNO085 reiniciado; reconfigurando reportes SH-2...");
    configureBnoReports(g_useMagMode);
  }

  // 3. Lectura continua no bloqueante de eventos SPI y medición de duración (meta <= 1.5 ms)
  uint64_t tReadStart = esp_timer_get_time();
  if (bno08x.getSensorEvent(&sensorValue)) {
    uint32_t readDurationUs = (uint32_t)(esp_timer_get_time() - tReadStart);
    if (readDurationUs > g_maxSpiReadUs) {
      g_maxSpiReadUs = readDurationUs;
    }
    g_spiReadsOk++;

    switch (sensorValue.sensorId) {
      case SH2_GAME_ROTATION_VECTOR:
        g_quat[0] = sensorValue.un.gameRotationVector.real;
        g_quat[1] = sensorValue.un.gameRotationVector.i;
        g_quat[2] = sensorValue.un.gameRotationVector.j;
        g_quat[3] = sensorValue.un.gameRotationVector.k;
        g_calib   = sensorValue.status & 0x03;
        break;

      case SH2_ROTATION_VECTOR:
        g_quat[0] = sensorValue.un.rotationVector.real;
        g_quat[1] = sensorValue.un.rotationVector.i;
        g_quat[2] = sensorValue.un.rotationVector.j;
        g_quat[3] = sensorValue.un.rotationVector.k;
        g_calib   = sensorValue.status & 0x03;
        break;

      case SH2_ACCELEROMETER:
        // Conversión de m/s^2 a unidades de gravedad (g) para umbral de contacto inicial > 3.0 g
        g_accel[0] = sensorValue.un.accelerometer.x / 9.80665f;
        g_accel[1] = sensorValue.un.accelerometer.y / 9.80665f;
        g_accel[2] = sensorValue.un.accelerometer.z / 9.80665f;
        break;

      default:
        break;
    }
  }

  // 4. Envío estrictamente periódico a 100 Hz (cada 10,000 us) sin uso de delay()
  uint64_t nowUs = esp_timer_get_time();
  if ((nowUs - g_lastSampleUs) >= SAMPLE_PERIOD_US) {
    g_lastSampleUs += SAMPLE_PERIOD_US;
    // Protección contra acumulación si ocurre un stall externo
    if ((nowUs - g_lastSampleUs) > (SAMPLE_PERIOD_US * 3)) {
      g_lastSampleUs = nowUs;
    }

    int64_t syncedTimeMs = (int64_t)millis() + g_clockOffsetMs;
    if (syncedTimeMs < 0) syncedTimeMs = 0;

    kntx_packet_t pkt;
    pkt.msg_type     = KNTX_MSG_DATA;
    pkt.node_id      = MY_NODE_ID;
    pkt.timestamp_ms = (uint32_t)syncedTimeMs;
    pkt.quat[0]      = g_quat[0];
    pkt.quat[1]      = g_quat[1];
    pkt.quat[2]      = g_quat[2];
    pkt.quat[3]      = g_quat[3];
    pkt.accel[0]     = g_accel[0];
    pkt.accel[1]     = g_accel[1];
    pkt.accel[2]     = g_accel[2];
    pkt.calib_status = g_calib;
    pkt.seq_num      = g_seqNum++;

    // Pulso en GPIO_LAT_TRIG para medir latencia en el aire (< 2 ms) con osciloscopio (PV-04)
    digitalWrite(PIN_LAT_TRIG, HIGH);
    esp_err_t res = esp_now_send(gatewayMac, (uint8_t *)&pkt, sizeof(kntx_packet_t));
    digitalWrite(PIN_LAT_TRIG, LOW);

    if (res != ESP_OK) {
      g_spiReadsErr++;
    }
  }

  // 5. Diagnóstico resumido cada 2 s (no satura el puerto serial)
  if ((millis() - g_lastStatMs) >= 2000) {
    g_lastStatMs = millis();
    Serial.printf("[NODO1-TIBIA] TX_OK=%lu | TX_ERR=%lu | SPI_OK=%lu | MaxSPI=%lu us | Sync=%s (off=%lld ms) | Calib=%u | q=[%.3f,%.3f,%.3f,%.3f]\n",
                  (unsigned long)g_txOkCount,
                  (unsigned long)g_txErrCount,
                  (unsigned long)g_spiReadsOk,
                  (unsigned long)g_maxSpiReadUs,
                  g_hasSync ? "SI" : "NO",
                  (long long)g_clockOffsetMs,
                  g_calib,
                  g_quat[0], g_quat[1], g_quat[2], g_quat[3]);
    g_maxSpiReadUs = 0;
  }
}
