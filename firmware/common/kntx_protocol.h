#ifndef KNTX_PROTOCOL_H
#define KNTX_PROTOCOL_H

#include <stdint.h>

/**
 * @file kntx_protocol.h
 * @brief Definición de estructuras de trama ESP-NOW y sincronización temporal SNTP
 *        para el sistema biomecánico inercial KNTX (Proyecto 10 - Universidad Modelo).
 *
 * Cumple con los requisitos:
 *  - RF-01 / RP-01: 100 Hz efectivos por nodo, jitter < 5 ms.
 *  - RF-08: Exportación CSV con Timestamp, Node_ID, Quat_W..Z, Accel_X..Z, Calib_Status.
 *  - RF-05: Detección de impacto (> 3.0 g) en tibia.
 */

// Tipos de trama en el bus inalámbrico ESP-NOW
#define KNTX_MSG_DATA  0x01  // Paquete cinemático desde nodo satélite hacia Gateway
#define KNTX_MSG_SYNC  0x02  // Trama broadcast de sincronización SNTP desde Gateway

// Identificadores anatómicos de nodos (alcance pierna derecha + lumbar)
#define NODE_ID_LUMBAR 0     // Gateway ESP32-S3 (Espalda baja L4-L5, IMU local opcional)
#define NODE_ID_TIBIA  1     // Nodo Satélite 1: ESP32-C3 + BNO085 (SPI 3 MHz)
#define NODE_ID_FEMUR  2     // Nodo Satélite 2: ESP32 + MPU6050 (Fusión Madgwick 100 Hz)
#define NODE_ID_PIE    3     // Nodo Satélite 3: Expansión (Pie / Empeine)

// Canal Wi-Fi fijo compartido entre Gateway y nodos para minimizar latencia (< 2 ms)
#define KNTX_ESPNOW_CHANNEL 1

// Dirección MAC por defecto del Gateway ESP32-S3 (actualizar con la MAC real de la placa)
// Se puede usar broadcast {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF} en pruebas de banco
// o la MAC específica del ESP32-S3 para transmisión unicast determinista.
static const uint8_t KNTX_BROADCAST_MAC[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

/**
 * @brief Paquete cinemático estándar KNTX (36 bytes empaquetados; 33 bytes base + metadatos).
 * Se mantiene compatibilidad exacta con el formato CSV de RF-08.
 */
typedef struct __attribute__((packed)) {
  uint8_t  msg_type;      // KNTX_MSG_DATA (0x01)
  uint8_t  node_id;       // Identificador del segmento (1=Tibia, 2=Fémur, 3=Pie, 0=Lumbar)
  uint32_t timestamp_ms;  // Sello de tiempo sincronizado con el reloj del Gateway (ms)
  float    quat[4];       // Cuaternión unitario [w, x, y, z]
  float    accel[3];      // Aceleración lineal/axial [ax, ay, az] en g
  uint8_t  calib_status;  // 0..3 (BNO085 accuracy / MPU6050 bias calibrated flag)
  uint16_t seq_num;       // Contador secuencial de paquete para auditoría de pérdida (%)
} kntx_packet_t;

/**
 * @brief Trama broadcast de sincronización temporal emitida por el Gateway cada 1,000 ms.
 * Permite al nodo satélite estimar su desfase: offset = t_gateway_tx - t_node_rx.
 */
typedef struct __attribute__((packed)) {
  uint8_t  msg_type;       // KNTX_MSG_SYNC (0x02)
  uint32_t gateway_ms;     // Reloj maestro del Gateway al momento de transmitir (ms)
  uint32_t sync_seq;       // Secuencia de pulso de sincronía
  uint8_t  reset_calib;    // 1 = Solicitar recalibración/tara de postura neutral
} kntx_sync_t;

/**
 * @brief Estructura de cuaternión para álgebra de Hamilton sin Gimbal Lock.
 */
typedef struct {
  float w;
  float x;
  float y;
  float z;
} kntx_quat_t;

// Conjugado de un cuaternión unitario (inverso rotacional)
static inline kntx_quat_t kntx_quat_conj(const kntx_quat_t q) {
  kntx_quat_t r = { q.w, -q.x, -q.y, -q.z };
  return r;
}

// Producto de Hamilton: q_rel = q1 ⊗ q2
static inline kntx_quat_t kntx_quat_mul(const kntx_quat_t a, const kntx_quat_t b) {
  kntx_quat_t r;
  r.w = a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z;
  r.x = a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y;
  r.y = a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x;
  r.z = a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w;
  return r;
}

// Normalización segura de cuaternión para evitar deriva numérica
static inline kntx_quat_t kntx_quat_norm(kntx_quat_t q) {
  float norm = sqrtf(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
  if (norm > 1e-6f) {
    float inv = 1.0f / norm;
    q.w *= inv; q.x *= inv; q.y *= inv; q.z *= inv;
  } else {
    q.w = 1.0f; q.x = 0.0f; q.y = 0.0f; q.z = 0.0f;
  }
  return q;
}

#endif // KNTX_PROTOCOL_H
