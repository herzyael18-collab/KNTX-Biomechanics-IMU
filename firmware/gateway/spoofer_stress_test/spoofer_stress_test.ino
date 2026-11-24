/**
 * @file spoofer_stress_test.ino
 * @brief Emulador de tráfico masivo (1,200 pkt/s) e inyección de fallas para Caso Límite (PC3/PC4).
 * @hardware ESP32 WROOM-32 clásico
 * @author Yael Alejandro Yah Hernández
 *
 * Comandos por Monitor Serie (115200 baudios):
 *   'A' -> Simula apagado repentino del Nodo 5 durante 2 segundos (prueba Failsafe FreeRTOS).
 *   'B' -> Inyecta pico de impacto axial de 3.5 g (> 3.0 g) en el Nodo 1 (Tibia) para probar RF-05.
 *   'N' -> Alterna entre modo 3 nodos (300 pkt/s nominal) y 12 nodos (1,200 pkt/s caso límite).
 */

#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include "../../common/kntx_protocol.h"

uint8_t gatewayAddress[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

static bool     g_simulateNodeLoss = false;
static uint32_t g_lossStartMs      = 0;
static bool     g_simulateImpact   = false;
static uint8_t  g_numVirtualNodes  = 12; // 12 nodos * 100 Hz = 1,200 pkt/s
static uint16_t g_seqPerNode[13]   = {0};
static volatile int64_t g_clockOffsetMs = 0;

void onSyncRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  (void)info;
  if (len == (int)sizeof(kntx_sync_t) && data[0] == KNTX_MSG_SYNC) {
    kntx_sync_t syncMsg;
    memcpy(&syncMsg, data, sizeof(kntx_sync_t));
    g_clockOffsetMs = (int64_t)syncMsg.gateway_ms - (int64_t)millis();
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(KNTX_ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);

  if (esp_now_init() != ESP_OK) {
    Serial.println("[ERROR] Fallo inicializando ESP-NOW en Spoofer.");
    return;
  }
  esp_now_register_recv_cb(onSyncRecv);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, gatewayAddress, 6);
  peerInfo.channel = KNTX_ESPNOW_CHANNEL;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  Serial.println("=====================================================");
  Serial.println("  KNTX SPOOFER - GENERADOR DE TRAFICO (1,200 pkt/s)");
  Serial.println("  Comandos: 'A'=Apagar Nodo 5 (2s) | 'B'=Impacto 3.5g | 'N'=3/12 nodos");
  Serial.println("=====================================================");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'A' || cmd == 'a') {
      g_simulateNodeLoss = true;
      g_lossStartMs = millis();
      Serial.println("--> [FALLO INYECTADO]: Nodo 5 apagado por 2 segundos.");
    } else if (cmd == 'B' || cmd == 'b') {
      g_simulateImpact = true;
      Serial.println("--> [IMPACTO INYECTADO]: Pico de 3.5 g en Nodo 1 (Tibia).");
    } else if (cmd == 'N' || cmd == 'n') {
      g_numVirtualNodes = (g_numVirtualNodes == 12) ? 3 : 12;
      Serial.printf("--> [MODO] Nodos virtuales activos: %u (%u pkt/s)\n",
                    g_numVirtualNodes, g_numVirtualNodes * 100);
    }
  }

  if (g_simulateNodeLoss && (millis() - g_lossStartMs >= 2000)) {
    g_simulateNodeLoss = false;
    Serial.println("--> [RECUPERACION]: Nodo 5 reconectado.");
  }

  uint64_t tStartUs = esp_timer_get_time();
  int64_t syncedNowMs = (int64_t)millis() + g_clockOffsetMs;
  if (syncedNowMs < 0) syncedNowMs = 0;

  for (uint8_t id = 1; id <= g_numVirtualNodes; id++) {
    if (g_simulateNodeLoss && id == 5) continue;

    kntx_packet_t pkt;
    pkt.msg_type     = KNTX_MSG_DATA;
    pkt.node_id      = id;
    pkt.timestamp_ms = (uint32_t)syncedNowMs;
    // Simular inclinación de 90° en nodo 1 para probar ausencia de Gimbal Lock
    if (id == 1) {
      pkt.quat[0] = 0.7071f; pkt.quat[1] = 0.0f; pkt.quat[2] = 0.7071f; pkt.quat[3] = 0.0f;
    } else {
      pkt.quat[0] = 1.0f; pkt.quat[1] = 0.0f; pkt.quat[2] = 0.0f; pkt.quat[3] = 0.0f;
    }

    if (g_simulateImpact && id == 1) {
      pkt.accel[0] = 0.2f; pkt.accel[1] = 0.1f; pkt.accel[2] = 3.5f;
      g_simulateImpact = false;
    } else {
      pkt.accel[0] = 0.0f; pkt.accel[1] = 0.0f; pkt.accel[2] = 1.0f;
    }

    pkt.calib_status = 3;
    pkt.seq_num      = g_seqPerNode[id]++;

    esp_now_send(gatewayAddress, (uint8_t *)&pkt, sizeof(kntx_packet_t));
  }

  // Mantener periodo estricto de 10 ms (100 Hz)
  uint64_t elapsedUs = esp_timer_get_time() - tStartUs;
  if (elapsedUs < 10000ULL) {
    delayMicroseconds((uint32_t)(10000ULL - elapsedUs));
  }
}
