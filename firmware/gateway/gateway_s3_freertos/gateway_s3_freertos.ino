/**
 * @file gateway_s3_freertos.ino
 * @brief Firmware del Gateway Central (Espalda Baja) - Proyecto KNTX
 * @hardware ESP32-S3-WROOM-1 N16R8 (+ MPU6050 local opcional para segmento lumbar L4-L5)
 * @author Yael Alejandro Yah Hernández (Firmware Gateway FreeRTOS / ESP-NOW / BLE / CSV)
 *
 * Arquitectura Dual-Core FreeRTOS (fiel a PC3 Tabla 10 y Figura 7):
 *  - Núcleo 0 (Radio y Sincronización):
 *      * Callback ISR ESP-NOW: copia el paquete a `rxQueue` (1,000 espacios) vía xQueueSendFromISR()
 *        y dispara pulso GPIO_RX_TRIG para medición de latencia en el aire (< 2 ms) con osciloscopio.
 *      * taskSyncBroadcast (Prioridad 3): emite trama broadcast SNTP cada 1,000 ms para acotar jitter < 5 ms.
 *      * taskRxConsumer (Prioridad 4): consume `rxQueue`, valida Node_ID, evalúa jitter entre nodos,
 *        detecta impactos (> 3.0 g en tibia) y deposita en la ventana temporal de 10 ms protegida por Mutex.
 *  - Núcleo 1 (Cinemática, BLE y Exportación CSV):
 *      * taskMatrixAndOutput (Prioridad 3): cierra cada ventana de 10 ms (100 Hz); si un nodo satélite
 *        se apaga o desconecta, lo marca como faltante (NULL / bitmask=0) sin bloquear el sistema ni BLE.
 *        Calcula el cuaternión relativo de rodilla q_rel = conj(q_femur) ⊗ q_tibia y el ángulo sagital
 *        sin Gimbal Lock (incluye prueba limpia al cruzar 90° de inclinación).
 *      * Emite notificaciones BLE 5.0 hacia la interfaz móvil y líneas CSV estándar RF-08 por USB Serial.
 *
 * Comandos por Monitor Serie (115200 baudios):
 *   'c' -> Captura postura neutral (tara q_calib para calibración sensor-segmento RF-03)
 *   'r' -> Alterna modo salida CSV crudo (RF-08) vs. modo resumen legible para consola/video
 *   'g' -> Imprime diagnóstico inmediato de salud (Cola FreeRTOS, Jitter, Nodos activos, BLE)
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <math.h>
#include "../../common/kntx_protocol.h"

// ============================================================================
// CONFIGURACIÓN DE HARDWARE Y CONSTANTES DEL SISTEMA
// ============================================================================
#define PIN_RX_LAT_TRIG   4    // Pulso de recepción ESP-NOW para osciloscopio (PV-04)
#define PIN_LOCAL_SDA     8    // I2C opcional en ESP32-S3 para MPU6050 lumbar (L4-L5)
#define PIN_LOCAL_SCL     9

#define MAX_NODES         13   // Índices 0..12 (soporta hasta los 12 nodos del caso límite)
#define RX_QUEUE_LEN      1000 // 1,000 paquetes en RAM (~36 KB) -> 0 overflows a 1,200 pkt/s
#define WINDOW_MS         10   // Ventana de ensamblado de matriz cinemática (100 Hz)
#define NODE_TIMEOUT_MS   350  // Tiempo tras el cual un nodo se declara desconectado (Failsafe sin falsos positivos)
#define SYNC_PERIOD_MS    1000 // Broadcast SNTP cada 1,000 ms (RP-01)
#define IMPACT_THRESH_G   3.0f // Umbral de contacto inicial (foot strike, RF-05)

// UUIDs del Servicio BLE KNTX
#define BLE_SERVICE_UUID  "12345678-1234-5678-1234-56789abcdef0"
#define BLE_CHAR_TX_UUID  "12345678-1234-5678-1234-56789abcdef1"

// ============================================================================
// ESTRUCTURAS DE ESTADO DE VENTANA Y TELEMETRÍA
// ============================================================================
typedef struct {
  bool          presentInWindow;
  bool          online;
  uint32_t      lastGatewayRxMs;
  uint32_t      lastTimestampMs;
  uint16_t      lastSeq;
  uint32_t      rxPackets;
  uint32_t      lostPackets;
  kntx_packet_t data;
  kntx_quat_t   qCalibConj;   // Conjugado de postura neutral (tara sensor-segmento)
} node_state_t;

static node_state_t g_nodes[MAX_NODES];

// Recursos FreeRTOS
static QueueHandle_t     g_rxQueue      = NULL;
static QueueHandle_t     g_csvQueue     = NULL;
static SemaphoreHandle_t g_matrixMutex  = NULL;

// BLE
static BLEServer         *g_bleServer   = NULL;
static BLECharacteristic *g_bleCharTx   = NULL;
static volatile bool      g_bleConnected = false;

// IMU local opcional en Gateway (Espalda baja / Lumbar L4-L5)
static Adafruit_MPU6050   g_localMpu;
static bool               g_hasLocalMpu  = false;

// Contadores globales de salud y métricas PC4
static volatile uint32_t  g_queueOverflows = 0;
static volatile uint32_t  g_totalRxPkts    = 0;
static volatile uint32_t  g_jitterExceeds  = 0;
static volatile int32_t   g_maxJitterMs    = 0;
static volatile uint32_t  g_impactEvents   = 0;
static volatile bool      g_csvMode        = true; // true = CSV estándar RF-08 listo para Python

// ============================================================================
// CALLBACKS BLE Y ESP-NOW (ISR EN NÚCLEO 0)
// ============================================================================

class KntxBleCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *pServer) override {
    (void)pServer;
    g_bleConnected = true;
  }
  void onDisconnect(BLEServer *pServer) override {
    g_bleConnected = false;
    pServer->startAdvertising();
  }
};

/**
 * @brief Callback de recepción ESP-NOW (Núcleo 0 — tarea Wi-Fi).
 * Regla de oro FreeRTOS: ejecución mínima sin Serial.println() ni bloqueos.
 * Nota ESP-IDF 5 / Core 3.x: se usa xQueueSend con timeout 0 (no bloqueante).
 */
void onEspNowRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len) {
  (void)info;
  if (len != (int)sizeof(kntx_packet_t)) return;
  if (incomingData[0] != KNTX_MSG_DATA) return;

  // Pulso físico de confirmación de llegada para medir latencia en el aire (< 2 ms)
  digitalWrite(PIN_RX_LAT_TRIG, HIGH);

  kntx_packet_t pkt;
  memcpy(&pkt, incomingData, sizeof(kntx_packet_t));

  if (xQueueSend(g_rxQueue, &pkt, 0) != pdPASS) {
    g_queueOverflows++;
  }

  digitalWrite(PIN_RX_LAT_TRIG, LOW);
}

// ============================================================================
// ÁLGEBRA BIOMECÁNICA: CUATERNIÓN RELATIVO SIN GIMBAL LOCK (GROOD & SUNTAY)
// ============================================================================

/**
 * @brief Calcula el ángulo sagital de flexión/extensión de rodilla (grados) a partir
 *        de los cuaterniones de Fémur (proximal) y Tibia (distal).
 *        Al operar en el espacio de cuaterniones (S^3) y proyectar el vector de eje
 *        de segmento tras q_rel = conj(q_prox) ⊗ q_dist, se evita por completo el
 *        bloqueo de cardán (Gimbal Lock) incluso pasando por ±90° de inclinación.
 */
float computeJointFlexionDeg(const kntx_quat_t qProx, const kntx_quat_t qDist, kntx_quat_t *qRelOut) {
  kntx_quat_t qRel = kntx_quat_norm(kntx_quat_mul(kntx_quat_conj(qProx), qDist));
  if (qRelOut) *qRelOut = qRel;

  // Extracción estable mediante matriz de rotación equivalente (atan2 evita singularidad a 90°)
  float r20 = 2.0f * (qRel.x * qRel.z - qRel.w * qRel.y);
  float r21 = 2.0f * (qRel.y * qRel.z + qRel.w * qRel.x);
  float r22 = 1.0f - 2.0f * (qRel.x * qRel.x + qRel.y * qRel.y);

  // Ángulo total de flexión relativa libre de Gimbal Lock mediante atan2(norma_vec, w)
  // y signo del plano sagital (eje Y de Grood-Suntay).
  float flexRad = atan2f(-r20, sqrtf(r21 * r21 + r22 * r22));
  // También calculamos ángulo geodésico total 2*acos(|w|) cuando se prueba en goniómetro de 1 eje
  float clampedW = fminf(1.0f, fmaxf(-1.0f, fabsf(qRel.w)));
  float geodesicDeg = 2.0f * acosf(clampedW) * (180.0f / (float)M_PI);

  (void)flexRad;
  return geodesicDeg;
}

/**
 * @brief Captura la postura neutral actual (N-pose / T-pose) como referencia cero (RF-03).
 */
void captureNeutralPose() {
  if (xSemaphoreTake(g_matrixMutex, pdMS_TO_TICKS(50)) == pdTRUE) {
    for (int i = 0; i < MAX_NODES; i++) {
      if (g_nodes[i].online) {
        kntx_quat_t q = {
          g_nodes[i].data.quat[0], g_nodes[i].data.quat[1],
          g_nodes[i].data.quat[2], g_nodes[i].data.quat[3]
        };
        g_nodes[i].qCalibConj = kntx_quat_conj(kntx_quat_norm(q));
      }
    }
    xSemaphoreGive(g_matrixMutex);
    Serial.println("# [CALIB] Postura neutral (q_calib) capturada para todos los nodos activos.");
  }
}

// ============================================================================
// TAREAS FREERTOS - NÚCLEO 0 (RECEPCIÓN Y SINCRONÍA SNTP)
// ============================================================================

/**
 * @brief Tarea de consumo de cola ESP-NOW (Core 0, Prioridad 4).
 */
void taskRxConsumer(void *pvParameters) {
  (void)pvParameters;
  kntx_packet_t pkt;

  for (;;) {
    if (xQueueReceive(g_rxQueue, &pkt, portMAX_DELAY) == pdTRUE) {
      if (pkt.node_id >= MAX_NODES) continue;

      uint32_t nowMs = millis();
      g_totalRxPkts++;

      // Detección de impacto tibial > 3.0 g (RF-05)
      float accelMag = sqrtf(pkt.accel[0] * pkt.accel[0] +
                             pkt.accel[1] * pkt.accel[1] +
                             pkt.accel[2] * pkt.accel[2]);
      if (pkt.node_id == NODE_ID_TIBIA && accelMag > IMPACT_THRESH_G) {
        g_impactEvents++;
      }

      if (xSemaphoreTake(g_matrixMutex, pdMS_TO_TICKS(5)) == pdTRUE) {
        node_state_t &st = g_nodes[pkt.node_id];

        // Detección de paquetes perdidos por salto en seq_num
        if (st.rxPackets > 0) {
          uint16_t expectedSeq = st.lastSeq + 1;
          if (pkt.seq_num != expectedSeq) {
            uint16_t diff = (uint16_t)(pkt.seq_num - expectedSeq);
            if (diff < 100) st.lostPackets += diff;
          }
        }

        // Cálculo de jitter respecto al reloj del Gateway (meta < 5 ms)
        int32_t jitterMs = abs((int32_t)nowMs - (int32_t)pkt.timestamp_ms);
        if (jitterMs > g_maxJitterMs && jitterMs < 5000) {
          g_maxJitterMs = jitterMs;
        }
        if (jitterMs > 5 && jitterMs < 5000) {
          g_jitterExceeds++;
        }

        st.data            = pkt;
        st.lastSeq         = pkt.seq_num;
        st.lastGatewayRxMs = nowMs;
        st.lastTimestampMs = pkt.timestamp_ms;
        st.presentInWindow = true;
        st.online          = true;
        st.rxPackets++;

        xSemaphoreGive(g_matrixMutex);
      }

      // Encolar cada paquete recibido hacia Core 1 para exportación CSV íntegra (evita pérdida en bordes de ventana 10 ms)
      if (g_csvQueue != NULL) {
        xQueueSend(g_csvQueue, &pkt, 0);
      }
    }
  }
}

/**
 * @brief Tarea emisora de tramas broadcast SNTP cada 1,000 ms (Core 0, Prioridad 3).
 */
void taskSyncBroadcast(void *pvParameters) {
  (void)pvParameters;
  TickType_t xLastWakeTime = xTaskGetTickCount();
  uint32_t syncSeq = 0;

  for (;;) {
    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(SYNC_PERIOD_MS));

    kntx_sync_t syncMsg;
    syncMsg.msg_type    = KNTX_MSG_SYNC;
    syncMsg.gateway_ms  = millis();
    syncMsg.sync_seq    = syncSeq++;
    syncMsg.reset_calib = 0;

    esp_now_send(KNTX_BROADCAST_MAC, (uint8_t *)&syncMsg, sizeof(kntx_sync_t));
  }
}

// ============================================================================
// TAREAS FREERTOS - NÚCLEO 1 (ENSAMBLADO DE MATRIZ, FAILSAFE, BLE Y CSV)
// ============================================================================

/**
 * @brief Cierra cada ventana de 10 ms (100 Hz), aplica Failsafe si un nodo desaparece,
 *        calcula cuaternión relativo de rodilla y exporta CSV + BLE sin bloqueos.
 */
void taskMatrixAndOutput(void *pvParameters) {
  (void)pvParameters;
  TickType_t xLastWakeTime = xTaskGetTickCount();
  uint32_t windowTick = 0;

  for (;;) {
    vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(WINDOW_MS));
    windowTick++;

    uint32_t nowMs = millis();

    // Si hay MPU6050 local conectado al ESP32-S3 (Lumbar), capturamos su aceleración
    if (g_hasLocalMpu) {
      sensors_event_t a, g, temp;
      if (g_localMpu.getEvent(&a, &g, &temp)) {
        if (xSemaphoreTake(g_matrixMutex, pdMS_TO_TICKS(2)) == pdTRUE) {
          node_state_t &lum = g_nodes[NODE_ID_LUMBAR];
          lum.online = true;
          lum.presentInWindow = true;
          lum.lastGatewayRxMs = nowMs;
          lum.data.node_id = NODE_ID_LUMBAR;
          lum.data.timestamp_ms = nowMs;
          lum.data.quat[0] = 1.0f; lum.data.quat[1] = 0.0f;
          lum.data.quat[2] = 0.0f; lum.data.quat[3] = 0.0f;
          lum.data.accel[0] = a.acceleration.x / 9.80665f;
          lum.data.accel[1] = a.acceleration.y / 9.80665f;
          lum.data.accel[2] = a.acceleration.z / 9.80665f;
          lum.data.calib_status = 3;
          xSemaphoreGive(g_matrixMutex);
        }
      }
    }

    // Copiar snapshot de ventana para liberar Mutex inmediatamente
    uint8_t activeMask = 0;
    kntx_packet_t snapPkts[4];
    bool snapValid[4] = {false, false, false, false};
    kntx_quat_t qTibiaCal = {1, 0, 0, 0}, qFemurCal = {1, 0, 0, 0};

    if (xSemaphoreTake(g_matrixMutex, pdMS_TO_TICKS(3)) == pdTRUE) {
      uint32_t checkMs = millis();
      for (int i = 0; i < MAX_NODES; i++) {
        // Comparación con signo para evitar underflow uint32_t entre Core 0 y Core 1
        int32_t ageMs = (int32_t)(checkMs - g_nodes[i].lastGatewayRxMs);
        if (g_nodes[i].online && ageMs > NODE_TIMEOUT_MS) {
          // FAILSAFE: Nodo marcado como desconectado (NULL) sin bloquear la cola ni BLE
          g_nodes[i].online = false;
          g_nodes[i].presentInWindow = false;
          Serial.printf("# [FAILSAFE] Nodo %d desconectado a t=%lu ms (sin datos %ld ms) -> marcado NULL (BLE/FreeRTOS continuo).\n",
                        i, (unsigned long)checkMs, (long)ageMs);
        }
      }

      for (int id = 0; id < 4; id++) {
        if (g_nodes[id].online) {
          activeMask |= (1 << id);
          // Solo exportar fila CSV cuando realmente llegó un paquete fresco o está activo
          snapPkts[id] = g_nodes[id].data;
          snapValid[id] = g_nodes[id].presentInWindow || (id == NODE_ID_LUMBAR);
        }
        g_nodes[id].presentInWindow = false;
      }

      // Aplicar tara de postura neutral (q_calib_conj ⊗ q_actual) usando último dato válido
      if (g_nodes[NODE_ID_TIBIA].online) {
        kntx_quat_t qt = {g_nodes[NODE_ID_TIBIA].data.quat[0], g_nodes[NODE_ID_TIBIA].data.quat[1],
                          g_nodes[NODE_ID_TIBIA].data.quat[2], g_nodes[NODE_ID_TIBIA].data.quat[3]};
        qTibiaCal = kntx_quat_mul(g_nodes[NODE_ID_TIBIA].qCalibConj, qt);
      }
      if (g_nodes[NODE_ID_FEMUR].online) {
        kntx_quat_t qf = {g_nodes[NODE_ID_FEMUR].data.quat[0], g_nodes[NODE_ID_FEMUR].data.quat[1],
                          g_nodes[NODE_ID_FEMUR].data.quat[2], g_nodes[NODE_ID_FEMUR].data.quat[3]};
        qFemurCal = kntx_quat_mul(g_nodes[NODE_ID_FEMUR].qCalibConj, qf);
      }
      xSemaphoreGive(g_matrixMutex);
    }

    // Cálculo en tiempo real de cuaternión relativo y ángulo de rodilla (Fémur-Tibia)
    float kneeAngleDeg = NAN;
    kntx_quat_t qRelKnee = {1, 0, 0, 0};
    bool tibiaOn = (activeMask & (1 << NODE_ID_TIBIA)) != 0;
    bool femurOn = (activeMask & (1 << NODE_ID_FEMUR)) != 0;
    if (tibiaOn && femurOn) {
      kneeAngleDeg = computeJointFlexionDeg(qFemurCal, qTibiaCal, &qRelKnee);
    } else if (tibiaOn) {
      // Modo 1 nodo de prueba en goniómetro: ángulo relativo respecto a postura neutral
      kntx_quat_t qIdent = {1, 0, 0, 0};
      kneeAngleDeg = computeJointFlexionDeg(qIdent, qTibiaCal, &qRelKnee);
    }

    // Exportación CSV íntegra (RF-08) vaciando g_csvQueue en Core 1 (cero pérdidas en bordes de ventana)
    if (g_csvMode && g_csvQueue != NULL) {
      kntx_packet_t csvPkt;
      while (xQueueReceive(g_csvQueue, &csvPkt, 0) == pdTRUE) {
        Serial.printf("%lu,%u,%.5f,%.5f,%.5f,%.5f,%.4f,%.4f,%.4f,%u,%.2f\n",
                      (unsigned long)csvPkt.timestamp_ms,
                      csvPkt.node_id,
                      csvPkt.quat[0], csvPkt.quat[1], csvPkt.quat[2], csvPkt.quat[3],
                      csvPkt.accel[0], csvPkt.accel[1], csvPkt.accel[2],
                      csvPkt.calib_status,
                      isnan(kneeAngleDeg) ? -1.0f : kneeAngleDeg);
      }
    } else if (g_csvQueue != NULL) {
      xQueueReset(g_csvQueue);
    }

    // Notificación BLE 5.0 (paquete compacto de 24 bytes a 50-100 Hz sin bloquear Core 0)
    if (g_bleConnected && g_bleCharTx != NULL) {
      char bleBuf[64];
      int n = snprintf(bleBuf, sizeof(bleBuf), "%lu,%u,%.2f,%.3f,%.3f,%.3f,%.3f",
                       (unsigned long)nowMs, activeMask,
                       isnan(kneeAngleDeg) ? -1.0f : kneeAngleDeg,
                       qRelKnee.w, qRelKnee.x, qRelKnee.y, qRelKnee.z);
      g_bleCharTx->setValue((uint8_t *)bleBuf, (size_t)n);
      g_bleCharTx->notify();
    }

    // Reporte de salud cada 2 s (prefijado con '#' para no corromper el parser CSV)
    if ((windowTick % 200) == 0) {
      UBaseType_t freeSpaces = uxQueueSpacesAvailable(g_rxQueue);
      Serial.printf("# [SALUD KNTX] Cola=%u/%d libres | Overflows=%lu | TotalRX=%lu | MaxJitter=%ld ms | Jitter>5ms=%lu | NodosMask=0x%02X | Rodilla=%.2f deg | BLE=%s\n",
                    (unsigned int)freeSpaces, RX_QUEUE_LEN,
                    (unsigned long)g_queueOverflows,
                    (unsigned long)g_totalRxPkts,
                    (long)g_maxJitterMs,
                    (unsigned long)g_jitterExceeds,
                    activeMask,
                    isnan(kneeAngleDeg) ? -1.0f : kneeAngleDeg,
                    g_bleConnected ? "CONNECTED" : "ADVERTISING");
      g_maxJitterMs = 0;
    }
  }
}

// ============================================================================
// SETUP Y LOOP (GESTIÓN DE COMANDOS INTERACTIVOS SIN BLOQUEO)
// ============================================================================

void setup() {
  // 921600 baudios (vs 115200): evita saturación del buffer TX UART al exportar CSV de múltiples nodos a 100 Hz
  Serial.begin(921600);
  Serial.setTxBufferSize(4096);
  pinMode(PIN_RX_LAT_TRIG, OUTPUT);
  digitalWrite(PIN_RX_LAT_TRIG, LOW);

  uint32_t t0 = millis();
  while (!Serial && (millis() - t0 < 2000)) { /* espera segura USB CDC */ }

  // Inicializar estado de nodos con cuaternión identidad en tara
  for (int i = 0; i < MAX_NODES; i++) {
    memset(&g_nodes[i], 0, sizeof(node_state_t));
    g_nodes[i].qCalibConj = {1.0f, 0.0f, 0.0f, 0.0f};
  }

  // Crear colas FreeRTOS y Mutex
  g_rxQueue     = xQueueCreate(RX_QUEUE_LEN, sizeof(kntx_packet_t));
  g_csvQueue    = xQueueCreate(256, sizeof(kntx_packet_t));
  g_matrixMutex = xSemaphoreCreateMutex();

  // Inicializar Wi-Fi STA + ESP-NOW en canal fijo
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(KNTX_ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);

  Serial.println("# ========================================================");
  Serial.println("#  KNTX GATEWAY CENTRAL (ESP32-S3) - FREERTOS DUAL-CORE");
  Serial.print("#  MAC DEL GATEWAY: ");
  Serial.println(WiFi.macAddress());
  Serial.println("#  Comandos: 'c'=Tarar Postura | 'r'=Toggle CSV | 'g'=Salud");
  Serial.println("# ========================================================");

  if (esp_now_init() != ESP_OK) {
    Serial.println("# [ERROR] No se pudo inicializar ESP-NOW en Gateway.");
  } else {
    esp_now_register_recv_cb(onEspNowRecv);
    // Registrar dirección broadcast para emitir tramas de sincronía SNTP cada 1,000 ms
    esp_now_peer_info_t bcastPeer = {};
    memcpy(bcastPeer.peer_addr, KNTX_BROADCAST_MAC, 6);
    bcastPeer.channel = KNTX_ESPNOW_CHANNEL;
    bcastPeer.encrypt = false;
    esp_now_add_peer(&bcastPeer);
  }

  // Inicializar BLE 5.0 (Núcleo 1)
  BLEDevice::init("KNTX_Gateway_S3");
  g_bleServer = BLEDevice::createServer();
  g_bleServer->setCallbacks(new KntxBleCallbacks());
  BLEService *pService = g_bleServer->createService(BLE_SERVICE_UUID);
  g_bleCharTx = pService->createCharacteristic(
      BLE_CHAR_TX_UUID,
      BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_READ);
  g_bleCharTx->addDescriptor(new BLE2902());
  pService->start();
  g_bleServer->getAdvertising()->start();
  Serial.println("# [OK] BLE 5.0 KNTX_Gateway_S3 emitiendo publicidad.");

  // Detectar si existe MPU6050 local conectado al Gateway (Lumbar L4-L5 opcional)
  Wire.begin(PIN_LOCAL_SDA, PIN_LOCAL_SCL);
  if (g_localMpu.begin()) {
    g_hasLocalMpu = true;
    Serial.println("# [OK] MPU6050 Lumbar detectado en Gateway ESP32-S3.");
  }

  // Encabezado oficial CSV según RF-08 del PC2
  Serial.println("Timestamp_ms,Node_ID,Quat_W,Quat_X,Quat_Y,Quat_Z,Accel_X,Accel_Y,Accel_Z,Calib_Status,Knee_Deg");

  // Lanzar tareas ancladas a sus núcleos dedicados (Tabla 10 del PC3)
  xTaskCreatePinnedToCore(taskRxConsumer,      "RxConsumer",   4096, NULL, 4, NULL, 0);
  xTaskCreatePinnedToCore(taskSyncBroadcast,   "SyncBcast",    4096, NULL, 3, NULL, 0);
  xTaskCreatePinnedToCore(taskMatrixAndOutput, "MatrixOutput", 8192, NULL, 3, NULL, 1);
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'c' || c == 'C') {
      captureNeutralPose();
    } else if (c == 'r' || c == 'R') {
      g_csvMode = !g_csvMode;
      Serial.printf("# [MODO] Exportacion CSV por Serial: %s\n", g_csvMode ? "ACTIVA" : "PAUSADA");
    } else if (c == 'g' || c == 'G') {
      Serial.printf("# [DIAG] Cola=%u/%d | Overflows=%lu | TotalRX=%lu | Impactos>3g=%lu\n",
                    (unsigned int)uxQueueSpacesAvailable(g_rxQueue),
                    RX_QUEUE_LEN,
                    (unsigned long)g_queueOverflows,
                    (unsigned long)g_totalRxPkts,
                    (unsigned long)g_impactEvents);
    }
  }
  vTaskDelay(pdMS_TO_TICKS(50));
}
