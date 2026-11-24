# KNTX — Arquitectura Hardware As-Built (PC4) y Esquemático de Conexiones

**Responsable de Hardware y Manufactura:** Jorge Carlos Contreras Rodríguez (`15233640@modelo.edu.mx`) / Co-integración con Yael Alejandro Yah Hernández (`15234422@modelo.edu.mx`)  
**Alcance PC4 (Primera Prueba Funcional — Arquetipo C):** Implementación en protoboard / placas con pines (breakout) con transición planificada a placa preperforada soldada compacta para el prototipo wearable final del PC5 (sin dependencia de manufactura SMD externa para desbloquear pruebas de laboratorio).

---

## 1. Distribución de Componentes Físicos Disponibles (Estrategia Óptima PC4)

| Rol en Sistema KNTX | Segmento Anatómico | Placa MCU | Sensor IMU | Interfaz Local | Alimentación |
|---|---|---|---|---|---|
| **Gateway Central** | Espalda baja (L4–L5) | `ESP32-S3-WROOM-1 N16R8` (DevKit con pines) | `MPU6050 #1` (opcional lumbar local) | I2C (`GPIO8/9`) + ESP-NOW + BLE 5.0 | USB 5 V / LiPo 3.7 V |
| **Nodo Satélite 1 (Primario)** | Tibia (cara anteromedial distal) | `ESP32-C3` (placa con pines) | `BNO085` (breakout con pines) | **SPI 3 MHz** (< 10 cm, `RP-04`) | USB / LiPo 3.7 V + `DW01+FS8205A` |
| **Nodo Satélite 2 (Secundario)** | Fémur (cara lateral distal) | `ESP32 WROOM-32` (DevKit con pines) | `MPU6050 #2` (breakout con pines) | I2C 400 kHz (< 10 cm) + Madgwick 6-DOF | USB / LiPo 3.7 V + `DW01+FS8205A` |
| **Nodo Satélite 3 (Escalado PC5)** | Pie (empeine) | `ESP32-C3` (por adquirir) | `BNO085` (por adquirir) | SPI 3 MHz (< 10 cm) | LiPo 3.7 V 400 mAh |

> **Justificación de Equivalencia (PC3 -> PC4, Sección 1.2):**  
> En PC3 se diseñó la PCB SMD en EasyEDA (`41 × 36 mm`, pistas SPI ≤ 5 cm, antena libre de cobre `15 × 6.6 mm`). Debido a tiempos de importación de componentes SMD y sensores `BNO085` adicionales, para la Primera Prueba Funcional (PC4) se implementa el circuito en **módulos breakout con pines sobre protoboard** (avalado por el Arquetipo C de la Guía Oficial PC4), manteniendo la topología de estrella ESP-NOW a 100 Hz, el bus SPI real a 3 MHz en el Nodo 1 (`ESP32-C3 + BNO085`) y la arquitectura FreeRTOS Dual-Core en el Gateway (`ESP32-S3`). Para el cierre del PC5, los módulos con pines se consolidarán en una **placa preperforada soldada** compacta encapsulada en carcasa impresa en 3D (PETG).

---

## 2. Tabla de Pinout As-Built (Cableado Directo en Protoboard)

### A) Nodo Satélite 1: `ESP32-C3` + `BNO085` (Modo SPI a 3 MHz)
> **Importante en el módulo BNO085:** Para activar el modo **SPI**, los pines/puentes `PS0` y `PS1` del breakout BNO085 deben estar en **HIGH (`3.3 V`)**. En placas tipo Adafruit BNO085 o GY-BNO08X, soldar o puentear `PS0` y `PS1` a `3.3 V` (o verificar si vienen marcados como `S0/S1`).

| Pin del BNO085 | Pin del ESP32-C3 | Señal / Función | Longitud máxima recomendada |
|---|---|---|---|
| `VIN` / `3V3` | `3.3V` | Alimentación regulada 3.3 V | < 10 cm |
| `GND` | `GND` | Tierra común | < 10 cm |
| `SCK` / `SCL` | `GPIO 4` | Reloj SPI (3 MHz) | **< 10 cm (RP-04)** |
| `SDO` / `MISO` / `SDA` | `GPIO 5` | Datos IMU → MCU (MISO) | **< 10 cm (RP-04)** |
| `SI` / `MOSI` / `DI` | `GPIO 6` | Datos MCU → IMU (MOSI) | **< 10 cm (RP-04)** |
| `CS` / `CSB` | `GPIO 7` | Chip Select SPI (activo bajo) | **< 10 cm (RP-04)** |
| `INT` / `H_INT` | `GPIO 2` | Interrupción de dato listo SH-2 | < 10 cm |
| `RST` / `NRST` | `GPIO 3` | Reset hardware BNO085 | < 10 cm |
| `PS0` y `PS1` | `3.3V` | Selección obligatoria de modo SPI | Puente directo |
| *(Sonda Osciloscopio)* | `GPIO 10` | Pulso de disparo TX (latencia PV-04) | Conectar a CH1 osciloscopio |

### B) Nodo Satélite 2: `ESP32 WROOM-32` + `MPU6050 #2` (Modo I2C 400 kHz + Madgwick 100 Hz)

| Pin del MPU6050 | Pin del ESP32 WROOM-32 | Señal / Función |
|---|---|---|
| `VCC` | `3.3V` | Alimentación 3.3 V |
| `GND` | `GND` | Tierra común |
| `SDA` | `GPIO 21` | Datos I2C (400 kHz) |
| `SCL` | `GPIO 22` | Reloj I2C (400 kHz) |
| `AD0` | `GND` | Dirección I2C `0x68` |

### C) Gateway Central: `ESP32-S3` (+ `MPU6050 #1` Lumbar Opcional)

| Pin del Gateway ESP32-S3 | Conexión | Función |
|---|---|---|
| `USB-UART / USB-OTG` | PC (Puerto COM) | Telemetría CSV (RF-08) y consola de diagnóstico |
| `GPIO 4` | Sonda CH2 Osciloscopio | Pulso de llegada RX ESP-NOW (mide latencia aire < 2 ms vs. GPIO 10 del Nodo 1) |
| `GPIO 8` (Opcional) | `SDA` de MPU6050 #1 | Sensor lumbar L4–L5 integrado al Gateway |
| `GPIO 9` (Opcional) | `SCL` de MPU6050 #1 | Reloj I2C del sensor lumbar |
| `3.3V` / `GND` (Opcional) | `VCC` / `GND` de MPU6050 #1 | Alimentación del sensor lumbar |

---

## 3. Lista de Materiales As-Built (BOM Real vs. Escalado PC5)

| # | Componente | Cantidad PC4 | Cantidad PC5 (1 pierna + lumbar) | Proveedor / Estado |
|---|---|---|---|---|
| 1 | `ESP32-S3` DevKit (Gateway) | 1 | 1 | En inventario (disponible) |
| 2 | `ESP32-C3` DevKit / SuperMini | 1 | 3 | 1 en inventario + 2 por adquirir |
| 3 | Sensor IMU `BNO085` (breakout) | 1 | 3 | 1 en inventario + 2 por adquirir |
| 4 | `ESP32 WROOM-32` DevKit | 1 | 0 (sustituido por C3) / Spoofer | En inventario (disponible) |
| 5 | Sensor IMU `MPU6050` (breakout) | 2 | 1 (lumbar) o respaldo | En inventario (disponible) |
| 6 | Batería LiPo 3.7 V 400–500 mAh + módulo protección `DW01+FS8205A` / `TP4056` | 2 | 4 | En integración |
| 7 | Placa preperforada fenólica/FR4 + headers | 2 | 4 | Ensamblaje final PC5 |
| 8 | Carcasa 3D en PETG + bandas elásticas textiles | 2 | 4 | Diseño CAD en `/hardware/carcasas` |
