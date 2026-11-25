#!/usr/bin/env python3
"""
generate_pc4_vertical_diagrams.py
Genera diagramas en FORMATO VERTICAL DE PÁGINA COMPLETA (proporción Carta 8.5 x 11, alta resolución)
sin ningún texto encimado ni recortado, atendiendo las indicaciones del docente:
  1. fig_conexiones_vertical_fullpage.png   -> Mapa visual vertical de los 3 circuitos reales con cajas grandes.
  2. fig_arquitectura_vertical_fullpage.png -> Arquitectura As-Built + transición híbrida Bosch BMI160 en vertical.
  3. fig_flujo_paquetes_vertical_fullpage.png -> Flujo vertical paso a paso de paquetes ESP-NOW, SNTP y FreeRTOS.
  4. fig_modelo_analitico_spi_tiempos.png   -> Modelo analítico RC de flancos SPI 3 MHz + tiempos reales esp_timer (1 us).
  5. gantt_actualizado_pc4.png              -> Gantt actualizado al 24 Nov 2026 incluyendo arribo de Bosch BMI160 (25 Nov).
"""

import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

REPO = r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU"
EVID = os.path.join(REPO, "docs", "evidencias")


def load_img_cropped(path, crop_frac, target_w=640):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    l, t, r, b = crop_frac
    img = img.crop((int(w * l), int(h * t), int(w * r), int(h * b)))
    ratio = target_w / img.width
    return img.resize((target_w, int(img.height * ratio)), Image.Resampling.LANCZOS)


def generate_vertical_connections():
    """Página completa vertical (8.5 x 11.2 in): 3 tarjetas horizontales enormes apiladas verticalmente."""
    fig = plt.figure(figsize=(8.6, 11.4), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0, 11.4)
    ax.axis("off")

    # Encabezado superior
    ax.add_patch(patches.Rectangle((0, 10.65), 8.6, 0.75, facecolor="#102a43", edgecolor="none"))
    ax.text(4.3, 11.12, "MAPA VISUAL DE CONEXIONES FÍSICAS AS-BUILT (PC4)",
            ha="center", va="center", fontsize=13.2, fontweight="bold", color="white")
    ax.text(4.3, 10.82, "Fotografías reales de los 3 módulos físicos, pines GPIO y señal eléctrica/digital por cada conductor",
            ha="center", va="center", fontsize=8.8, color="#cbd5e1")

    def draw_module_card(y_bot, height, header_c, title, subtitle, img_path, crop_f, img_zoom, caption, wires):
        x0, w = 0.22, 8.16
        # Marco principal
        ax.add_patch(patches.FancyBboxPatch((x0, y_bot), w, height, boxstyle="round,pad=0.05",
                                            facecolor="#f8fafc", edgecolor=header_c, lw=2.0))
        # Barra de título de tarjeta
        hh = 0.52
        ax.add_patch(patches.FancyBboxPatch((x0, y_bot + height - hh), w, hh, boxstyle="round,pad=0.03",
                                            facecolor=header_c, edgecolor="none"))
        ax.text(x0 + 0.16, y_bot + height - 0.19, title, va="center", ha="left",
                fontsize=10.4, fontweight="bold", color="white")
        ax.text(x0 + 0.16, y_bot + height - 0.39, subtitle, va="center", ha="left",
                fontsize=7.9, color="#e2e8f0")

        # Foto grande a la izquierda
        im = load_img_cropped(img_path, crop_f, target_w=620)
        oi = OffsetImage(im, zoom=img_zoom)
        img_cx = 2.02
        img_cy = y_bot + (height - hh) * 0.56
        ax.add_artist(AnnotationBbox(oi, (img_cx, img_cy), frameon=True,
                                     bboxprops=dict(edgecolor=header_c, lw=1.6, facecolor="white")))
        ax.text(img_cx, y_bot + 0.21, caption, ha="center", va="center",
                fontsize=7.3, style="italic", color="#334e68", linespacing=1.18)

        # Lista de cables grande y espaciada a la derecha
        wx = 3.82
        top_y = y_bot + height - hh - 0.28
        step_y = (height - hh - 0.38) / max(len(wires), 1)
        for idx, (wcol, wtitle, wdesc) in enumerate(wires):
            wy = top_y - idx * step_y
            ax.plot([wx, wx + 0.32], [wy, wy], color=wcol, lw=4.2, solid_capstyle="round")
            ax.text(wx + 0.42, wy + 0.07, wtitle, va="center", ha="left",
                    fontsize=8.6, fontweight="bold", color="#102a43")
            ax.text(wx + 0.42, wy - 0.11, wdesc, va="center", ha="left",
                    fontsize=7.7, color="#475569")

    # Tarjeta Superior: Nodo 1 (Tibia)
    draw_module_card(
        y_bot=7.12, height=3.35, header_c="#1f4e79",
        title="1. NODO SATÉLITE 1 — TIBIA (Referencia de Impacto y Bus SPI)",
        subtitle="ESP32-C3 SuperMini (MAC 38:44:BE:43:19:14) + Bosch GY-BNO08X | Bus SPI Local a 3 MHz (< 5 cm)",
        img_path=os.path.join(EVID, "foto_nodo1_c3_bno085.jpg"),
        crop_f=(0.18, 0.24, 0.86, 0.90), img_zoom=0.35,
        caption="Circuito real Nodo 1: cables SPI < 5 cm\n(cumple RP-04 < 10 cm)",
        wires=[
            ("#dc2626", "3V3 -> VCC  |  G -> GND", "Alimentación regulada 3.3 V DC y tierra común libre de lazos"),
            ("#ea580c", "PS0 y PS1 -> 3.3V (HIGH)", "Configura el coprocesador SH-2 del BNO085 en modo SPI nativo"),
            ("#2563eb", "GPIO 4 -> SCL (SCK SPI)", "Reloj maestro síncrono a 3.0 MHz (periodo 333.3 ns)"),
            ("#16a34a", "GPIO 5 <- SDA (MISO SPI)", "Recibe cuaternión [w,x,y,z] + aceleración [g] desde el BNO085"),
            ("#9333ea", "GPIO 6 -> ADD (MOSI) | GPIO 7 -> CS", "Comandos de configuración SH-2 y habilitación Chip Select"),
            ("#0891b2", "GPIO 2 <- INT  |  GPIO 3 -> RST", "Interrupción dato listo (redujo lectura de 8.99 ms a 1.39 ms)"),
        ]
    )

    # Tarjeta Media: Nodo 2 (Fémur)
    draw_module_card(
        y_bot=3.62, height=3.32, header_c="#15803d",
        title="2. NODO SATÉLITE 2 — FÉMUR (Equivalencia Funcional PC4 -> BMI160 en PC5)",
        subtitle="ESP32 WROOM-32 (MAC 00:70:07:82:EB:4C) + MPU-6050 (GY-521) | Fusión Madgwick 6-DOF a 100 Hz",
        img_path=os.path.join(EVID, "foto_nodo2_esp32_mpu6050.jpg"),
        crop_f=(0.08, 0.14, 0.83, 0.89), img_zoom=0.35,
        caption="Circuito real Nodo 2: opera a 100.21 Hz (deriva 0.98 °/min)",
        wires=[
            ("#dc2626", "3V3 -> VCC  |  GND -> GND", "Alimentación regulada 3.3 V DC para el transceptor y el IMU"),
            ("#16a34a", "GPIO 21 <-> SDA (Datos I2C)", "Transfiere lecturas crudas de giroscopio (rad/s) y acelerómetro (g)"),
            ("#2563eb", "GPIO 22 -> SCL (Reloj 400 kHz)", "Reloj Fast-Mode I2C local (< 4 cm, lectura en ~0.45 ms)"),
            ("#334155", "AD0 -> GND (Dirección 0x68)", "Fija dirección física del esclavo en el bus local"),
            ("#7c3aed", "Fusión Madgwick 6-DOF en CPU", "Calcula cuaternión [w,x,y,z] en 0.12 ms (1.2% CPU) sin Gimbal Lock"),
        ]
    )

    # Tarjeta Inferior: Gateway Central (Espalda baja)
    draw_module_card(
        y_bot=0.16, height=3.28, header_c="#b45309",
        title="3. GATEWAY CENTRAL — ESPALDA BAJA (L4–L5) | MAC: E0:72:A1:F4:EB:D8",
        subtitle="ESP32-S3-WROOM-1 N16R8 Dual-Core FreeRTOS + MPU-6050 Lumbar Local + BLE 5.0 + USB 921,600 bps",
        img_path=os.path.join(EVID, "foto_gateway_s3_lumbar.jpg"),
        crop_f=(0.04, 0.14, 0.73, 0.80), img_zoom=0.35,
        caption="Circuito real Gateway ESP32-S3 + sensor lumbar integrado",
        wires=[
            ("#dc2626", "3V3 -> VCC  |  GND -> GND", "Energiza el sensor inercial local del segmento lumbar (Node_ID = 0)"),
            ("#16a34a", "GPIO 8 <-> SDA | GPIO 9 -> SCL", "Bus I2C dedicado en Core 1 para referencia pélvica/lumbar"),
            ("#7c3aed", "Antena 2.4 GHz (Core 0 / Core 1)", "Recibe ESP-NOW (100 Hz/nodo), emite Sync SNTP (1 s) y BLE 5.0"),
            ("#ea580c", "GPIO 4 (Pulso RX Trigger)", "Salida digital de instrumentación para medir latencia aire (< 2 ms)"),
            ("#0891b2", "USB-UART CH343 @ 921,600 bps", "Enlace de alta velocidad hacia Dashboard HMI Python y logger .CSV"),
        ]
    )

    out = os.path.join(EVID, "fig_conexiones_vertical_fullpage.png")
    plt.savefig(out)
    plt.close()
    print("[OK]", out)


def generate_vertical_architecture():
    """Página completa vertical (8.5 x 11.2 in): Arquitectura As-Built PC4 + Evolución a Bosch BMI160 PC5."""
    fig = plt.figure(figsize=(8.6, 11.2), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0, 11.2)
    ax.axis("off")

    ax.add_patch(patches.Rectangle((0, 10.45), 8.6, 0.75, facecolor="#102a43", edgecolor="none"))
    ax.text(4.3, 10.92, "ARQUITECTURA GENERAL DEL SISTEMA KNTX (FORMATO VERTICAL)",
            ha="center", va="center", fontsize=13.0, fontweight="bold", color="white")
    ax.text(4.3, 10.62, "Topología Estrella ESP-NOW 100 Hz, Procesamiento Dual-Core FreeRTOS y Evolución Sensorial hacia PC5",
            ha="center", va="center", fontsize=8.6, color="#cbd5e1")

    def box(x, y, w, h, title, body, fc, ec, tc="#102a43", fs_title=9.6, fs_body=8.1):
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                            facecolor=fc, edgecolor=ec, lw=1.9))
        ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="top",
                fontsize=fs_title, fontweight="bold", color=tc)
        ax.text(x + w / 2, y + (h - 0.30) / 2, body, ha="center", va="center",
                fontsize=fs_body, color="#1e293b", linespacing=1.35)

    # NIVEL 1: CAPA DE SENSADO INERCIAL (ARRIBA)
    ax.text(4.3, 10.18, "NIVEL 1 — CAPA DE NODOS SATÉLITE EN EXTREMIDAD INFERIOR (MUESTREO SÍNCRONO A 100 Hz)",
            ha="center", va="center", fontsize=9.2, fontweight="bold", color="#1f4e79")

    box(0.28, 8.05, 2.52, 1.92,
        "NODO 1 — TIBIA\n(Implementado PC4 & PC5)",
        "MCU: ESP32-C3 (160 MHz)\nIMU: Bosch BNO085\nBus: SPI 3 MHz (< 5 cm)\nLectura por pin INT: 1.39 ms\nFusión HW SH-2 (6-DOF)\nImpacto tibial > 3.0 g",
        "#e0f2fe", "#0284c7", "#0c4a6e", fs_title=8.9, fs_body=7.7)

    box(3.04, 8.05, 2.52, 1.92,
        "NODO 2 — FÉMUR\n(PC4: MPU6050 -> PC5: BMI160)",
        "PC4: ESP32 + MPU-6050 (I2C)\nPC5: ESP32-C3 + Bosch BMI160\nBus PC5: SPI 3 MHz nativo\nFusión: Madgwick 6-DOF\n(0.12 ms CPU | 0.98 °/min)\nRango dinámico ±16 g",
        "#dcfce7", "#16a34a", "#14532d", fs_title=8.9, fs_body=7.7)

    box(5.80, 8.05, 2.52, 1.92,
        "NODO 3 — PIE\n(Escalado Final PC5)",
        "MCU: ESP32-C3 (160 MHz)\nIMU: Bosch BMI160 (6-DOF)\nBus: SPI 3 MHz (< 5 cm)\nConsumo IMU: 0.9 mA\nPlaca preperforada soldada\nCarcasa PETG 32.9 cm³",
        "#f0fdf4", "#15803d", "#14532d", fs_title=8.9, fs_body=7.7)

    # NIVEL 2: RED INALÁMBRICA ESP-NOW (ENLACE AIRE)
    ax.add_patch(patches.FancyBboxPatch((0.60, 6.72), 7.40, 0.88, boxstyle="round,pad=0.06",
                                        facecolor="#fefce8", edgecolor="#ca8a04", lw=1.6, ls="--"))
    ax.text(4.3, 7.36, "NIVEL 2 — ENLACE INALÁMBRICO MAC-A-MAC ESP-NOW (CANAL WI-FI 1 — 2.4 GHz)",
            ha="center", va="center", fontsize=8.9, fontweight="bold", color="#854d0e")
    ax.text(4.3, 6.98, "Subida: Tramas kntx_packet_t de 36 Bytes @ 100 Hz por nodo (Latencia aire < 2 ms)\n"
                       "Bajada (Broadcast): Trama kntx_sync_t de 10 Bytes cada 1,000 ms (SNTP -> Jitter P95 ≤ 1.0 ms)",
            ha="center", va="center", fontsize=7.9, color="#422006", linespacing=1.3)

    for x_arrow in [1.54, 4.30, 7.06]:
        ax.annotate("", xy=(x_arrow, 7.64), xytext=(x_arrow, 8.02),
                    arrowprops=dict(arrowstyle="-|>", lw=2.0, color="#1f4e79", mutation_scale=14))
        ax.annotate("", xy=(x_arrow, 6.26), xytext=(x_arrow, 6.68),
                    arrowprops=dict(arrowstyle="-|>", lw=2.0, color="#b45309", mutation_scale=14))

    # NIVEL 3: GATEWAY CENTRAL ESP32-S3 (CENTRO)
    ax.add_patch(patches.FancyBboxPatch((0.35, 2.85), 7.90, 3.38, boxstyle="round,pad=0.08",
                                        facecolor="#fff7ed", edgecolor="#c2410c", lw=2.2))
    ax.text(4.3, 6.02, "NIVEL 3 — GATEWAY CENTRAL ESP32-S3-WROOM-1 N16R8 (ESPALDA BAJA L4–L5)",
            ha="center", va="center", fontsize=9.8, fontweight="bold", color="#9a3412")
    ax.text(4.3, 5.76, "MAC Real: E0:72:A1:F4:EB:D8  |  IMU Lumbar Local Integrado (PC4: MPU-6050 -> PC5: Bosch BMI160)",
            ha="center", va="center", fontsize=8.0, color="#7c2d12")

    box(0.58, 3.10, 3.55, 2.45,
        "NÚCLEO 0 (PRO_CPU)\nRecepción Radio & Reloj Maestro",
        "• onEspNowRecv(): Encola paquete en\n  g_rxQueue (1,000 espacios = 36 KB RAM)\n  sin bloqueos -> 0 Overflows.\n• taskRxConsumer (Prio 4): Valida secuencia,\n  mide jitter, detecta pico > 3.0 g en tibia y\n  transfiere copia íntegra a g_csvQueue.\n• taskSyncBroadcast (Prio 3): Emite reloj\n  maestro cada 1,000 ms a todos los nodos.",
        "#ffedd5", "#ea580c", "#9a3412", fs_title=8.8, fs_body=7.6)

    box(4.47, 3.10, 3.55, 2.45,
        "NÚCLEO 1 (APP_CPU)\nCinemática, Failsafe & Salidas",
        "• taskMatrixAndOutput (Prio 3, cada 10 ms):\n• FAILSAFE (Timeout 350 ms, aritm. int32):\n  Marca NULL al nodo caído sin detener el\n  sistema + reconexión automática en caliente.\n• Álgebra de Cuaterniones (Sin Gimbal Lock):\n  q_rel = conj(q_femur) ⊗ q_tibia\n  θ_rodilla = 2·atan2(q_eje, w)  [con signo ±].\n• Notifica BLE 5.0 y drena g_csvQueue.",
        "#fef3c7", "#d97706", "#92400e", fs_title=8.8, fs_body=7.6)

    ax.annotate("", xy=(4.44, 4.32), xytext=(4.16, 4.32),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#9a3412", mutation_scale=15))

    # NIVEL 4: CAPA DE VISUALIZACIÓN Y ANÁLISIS BIOMECÁNICO (ABAJO)
    ax.annotate("", xy=(2.25, 2.32), xytext=(2.85, 2.82),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#7e22ce", mutation_scale=15))
    ax.annotate("", xy=(6.35, 2.32), xytext=(5.75, 2.82),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#0369a1", mutation_scale=15))

    box(0.35, 0.30, 3.75, 1.98,
        "NIVEL 4A — INTERFAZ MÓVIL (BLE 5.0)",
        "Perfil GATT: KNTX_Gateway_S3 (2M PHY)\n• Visualización inalámbrica en tiempo real\n• Estado activo/Failsafe por nodo (bitmask)\n• Curva articular frente a banda ± 1 DE",
        "#faf5ff", "#7e22ce", "#581c87", fs_title=9.0, fs_body=7.9)

    box(4.50, 0.30, 3.75, 1.98,
        "NIVEL 4B — SUITE PYTHON & HMI (USB)",
        "Enlace Serial Alta Velocidad: 921,600 bps\n• kntx_live_dashboard.py: Gráficas ±180° y |a|,\n  LEDs Online/Failsafe y botón de Tara 0°\n• Exportación .CSV (RF-08), Grood & Suntay,\n  Spline 101 pts y Bland-Altman (Kinovea)",
        "#f0f9ff", "#0369a1", "#0c4a6e", fs_title=9.0, fs_body=7.9)

    out = os.path.join(EVID, "fig_arquitectura_vertical_fullpage.png")
    plt.savefig(out)
    plt.close()
    print("[OK]", out)


def generate_vertical_packet_flow():
    """Página completa vertical (8.5 x 11.2 in): Diagrama vertical paso a paso del flujo de paquetes."""
    fig = plt.figure(figsize=(8.6, 11.2), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0, 11.2)
    ax.axis("off")

    ax.add_patch(patches.Rectangle((0, 10.45), 8.6, 0.75, facecolor="#102a43", edgecolor="none"))
    ax.text(4.3, 10.92, "FLUJO VERTICAL DE TELEMETRÍA Y ESTRUCTURA DE PAQUETES KNTX",
            ha="center", va="center", fontsize=12.8, fontweight="bold", color="white")
    ax.text(4.3, 10.62, "Trazabilidad completa del dato desde el registro físico del IMU hasta la gráfica biomecánica y archivo .CSV",
            ha="center", va="center", fontsize=8.5, color="#cbd5e1")

    steps = [
        ("ETAPA 1 — ADQUISICIÓN FÍSICA Y FUSIÓN LOCAL EN CADA NODO (CADA 10,000 µs = 100 Hz)",
         "• Nodo 1 (Tibia): Pin físico INT cae a LOW -> ESP32-C3 ejecuta lectura SPI a 3 MHz del BNO085 en 1.39 ms (≤ 1.5 ms).\n"
         "• Nodo 2 (Fémur): Lectura rápida de giroscopio y acelerómetro -> ejecuta filtro Madgwick 6-DOF en 0.12 ms (1.2% CPU).\n"
         "• Ambos nodos corrigen su marca de tiempo local sumando la constante de sincronía:  t_sync = millis() + offset_SNTP.",
         "#eff6ff", "#1d4ed8", "#1e3a8a"),

        ("ETAPA 2 — EMPAQUETADO BINARIO DETERMINISTA (kntx_packet_t = 36 BYTES EMPAQUETADOS)",
         "  [Byte 0]      msg_type = 0x01 (DATA)          |  [Bytes 6..21]  quat[4] = {w, x, y, z} (4 × float32 = 16 B)\n"
         "  [Byte 1]      node_id  = 1 (Tibia), 2 (Fémur) |  [Bytes 22..33] accel[3]= {ax, ay, az} en g (3 × float32 = 12 B)\n"
         "  [Bytes 2..5]  timestamp_ms (uint32 = 4 B)     |  [Bytes 34..36] calib_status (1 B) + seq_num (uint16 = 2 B)",
         "#fefce8", "#ca8a04", "#854d0e"),

        ("ETAPA 3 — TRANSMISIÓN AIRE ESP-NOW Y RETORNO DE SINCRONÍA SNTP (2.4 GHz, CANAL 1)",
         "• Envío Unicast directo a la MAC del Gateway (E0:72:A1:F4:EB:D8) sin overhead TCP/IP -> tiempo en aire < 2 ms.\n"
         "• En sentido inverso, cada 1,000 ms el Gateway emite un broadcast kntx_sync_t (10 Bytes) con su reloj maestro T_S3;\n"
         "  todos los nodos actualizan simultáneamente su offset_SNTP, manteniendo el Jitter P95 en 0.00 – 1.00 ms (< 5 ms).",
         "#f0fdf4", "#15803d", "#14532d"),

        ("ETAPA 4 — ENCOLAMIENTO NO BLOQUEANTE Y AUDITORÍA EN NÚCLEO 0 (ESP32-S3)",
         "• El callback Wi-Fi deposita cada paquete en g_rxQueue (capacidad = 1,000 paquetes) en microsegundos (0 Overflows).\n"
         "• taskRxConsumer verifica continuidad de seq_num, registra impactos tibiales > 3.0 g (RF-05), actualiza la tabla\n"
         "  compartida protegida por Mutex y empuja una copia exacta a g_csvQueue (256 paquetes) para evitar pérdida en bordes.",
         "#fff7ed", "#ea580c", "#9a3412"),

        ("ETAPA 5 — ÁLGEBRA TWIST SIN GIMBAL LOCK Y VIGILANCIA FAILSAFE EN NÚCLEO 1",
         "• Cada 10 ms se calcula el cuaternión relativo q_rel = conj(q_femur) ⊗ q_tibia y el ángulo con signo:\n"
         "  θ_rodilla = 2 · atan2(q_eje, w) · (180/π)  -> continuo en ±90° (validado de -88.2° a +167.0° con retorno a 0.0°).\n"
         "• Si (t_actual - lastRxMs) > 350 ms, dispara # [FAILSAFE], marca el nodo NULL y mantiene activos los demás nodos y BLE.",
         "#fef2f2", "#dc2626", "#991b1b"),

        ("ETAPA 6 — SALIDA SIMULTÁNEA A INTERFAZ EN VIVO Y ARCHIVO ABIERTO .CSV (RF-08)",
         "• Puerto USB-UART a 921,600 bps (92 KB/s reales, sin cuello de botella): alimenta el Dashboard KNTX en tiempo real\n"
         "  y escribe las 11 columnas oficiales: Timestamp_ms, Node_ID, Quat_W..Z, Accel_X..Z, Calib_Status, Knee_Deg.\n"
         "• Radio BLE 5.0: notifica la cadena compacta con máscara de nodos activos, ángulo y cuaternión relativo hacia el móvil.",
         "#f5f3ff", "#7c3aed", "#4c1d95"),
    ]

    y_top = 10.22
    box_h = 1.38
    gap = 0.28
    for i, (stitle, sbody, fc, ec, tc) in enumerate(steps):
        yb = y_top - (i + 1) * box_h - i * gap
        ax.add_patch(patches.FancyBboxPatch((0.35, yb), 7.90, box_h, boxstyle="round,pad=0.06",
                                            facecolor=fc, edgecolor=ec, lw=1.8))
        ax.text(0.55, yb + box_h - 0.19, stitle, ha="left", va="top",
                fontsize=8.9, fontweight="bold", color=tc)
        ax.text(0.55, yb + (box_h - 0.26) / 2, sbody, ha="left", va="center",
                fontsize=7.85, family="DejaVu Sans", color="#1e293b", linespacing=1.34)
        if i < len(steps) - 1:
            ax.annotate("", xy=(4.3, yb - gap + 0.03), xytext=(4.3, yb - 0.02),
                        arrowprops=dict(arrowstyle="-|>", lw=2.4, color="#102a43", mutation_scale=16))

    out = os.path.join(EVID, "fig_flujo_paquetes_vertical_fullpage.png")
    plt.savefig(out)
    plt.close()
    print("[OK]", out)


def generate_spi_analytical_model():
    """
    Genera figura técnica honesta y rigurosa para PV-02 / PV-04:
      Panel A: Modelo analítico RC de integridad de señal del bus SPI a 3 MHz (< 5 cm, tr < 10 ns << 50 ns).
      Panel B: Cronograma de transacción SPI medido con temporizador interno esp_timer (1.39 ms <= 1.5 ms)
               + presupuesto temporal de ventana de 10 ms (100 Hz).
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.8, 7.2), dpi=190)

    # Panel A: Modelo RC de flanco de subida SCLK a 3 MHz (pista/cable < 5 cm)
    # R_drv ESP32-C3 ~ 35 Ohm, C_load = C_pin_BNO (6 pF) + C_wire_5cm (5 pF) + C_pad (4 pF) = 15 pF (y caso peor protoboard 45 pF)
    t_ns = np.linspace(0, 333.3, 1000)  # 1 periodo completo a 3 MHz = 333.3 ns (semiperiodo = 166.7 ns)
    tau_pcb = 35.0 * 15e-3   # ns (0.525 ns)
    tau_proto = 40.0 * 65e-3 # ns (2.6 ns considerando capacitancia parásita de protoboard ~65 pF)

    def pulse_rc(t, tau):
        y = np.zeros_like(t)
        up = t <= 166.67
        y[up] = 3.3 * (1.0 - np.exp(-t[up] / tau))
        v_peak = 3.3 * (1.0 - np.exp(-166.67 / tau))
        y[~up] = v_peak * np.exp(-(t[~up] - 166.67) / tau)
        return y

    v_proto = pulse_rc(t_ns, tau_proto)
    tr_10_90 = 2.197 * tau_proto  # ~5.7 ns

    ax1.plot(t_ns, v_proto, color="#1d4ed8", lw=2.2,
             label=f"Modelo RC As-Built Protoboard (<5 cm, C_par≈65 pF): t_r(10-90%) = {tr_10_90:.1f} ns")
    ax1.axvspan(0, 50.0, color="#dcfce7", alpha=0.55, label="Ventana máxima permitida de flanco RP-04 (< 50 ns)")
    ax1.axvline(50.0, color="#16a34a", ls="--", lw=1.5)
    ax1.axhline(3.3 * 0.9, color="#64748b", ls=":", lw=1.0)
    ax1.axhline(3.3 * 0.1, color="#64748b", ls=":", lw=1.0)
    ax1.set_xlim(-5, 335)
    ax1.set_ylim(-0.2, 3.8)
    ax1.set_xlabel("Tiempo dentro de 1 ciclo SCLK a 3.0 MHz [ns]", fontweight="bold")
    ax1.set_ylabel("Tensión lógica [V]", fontweight="bold")
    ax1.set_title("A) Modelo RC de Integridad SPI a 3 MHz (RP-04: flancos < 50 ns)",
                  fontweight="bold", color="#102a43", fontsize=9.6)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right", fontsize=8.2)

    # Panel B: Presupuesto real medido de la ventana de 10 ms (100 Hz) con esp_timer (1 us)
    stages = [
        ("1. Lectura SPI BNO085\n(medido esp_timer COM7)", 0.0, 1.39, "#1d4ed8"),
        ("2. Empaquetado + SNTP\n(ESP32-C3 160 MHz)", 1.39, 0.08, "#7c3aed"),
        ("3. Aire ESP-NOW (36 B)\n(Unicast -> Gateway S3)", 1.47, 0.85, "#ea580c"),
        ("4. Core 0/1 + Twist + UART\n(ESP32-S3 @ 921.6 kbps)", 2.32, 0.45, "#16a34a"),
        ("5. Margen Libre CPU/Radio\n(72.3% holgura en ciclo 10 ms)", 2.77, 7.23, "#cbd5e1"),
    ]
    y_idx = np.arange(len(stages))[::-1]
    for y, (lbl, start_ms, dur_ms, col) in zip(y_idx, stages):
        ax2.barh(y, dur_ms, left=start_ms, height=0.56, color=col, edgecolor="#102a43", lw=1.0)
        txt_x = start_ms + dur_ms + 0.14 if dur_ms < 5 else start_ms + dur_ms / 2
        ha = "left" if dur_ms < 5 else "center"
        ax2.text(txt_x, y, f"{dur_ms:.2f} ms", va="center", ha=ha, fontsize=8.5, fontweight="bold", color="#102a43")

    ax2.axvline(1.50, color="#dc2626", ls="--", lw=1.5, label="Límite lectura SPI RP-04 (1.50 ms)")
    ax2.axvline(10.0, color="#102a43", ls="-", lw=1.6, label="Cierre de ventana 100 Hz (10.00 ms)")
    ax2.set_yticks(y_idx)
    ax2.set_yticklabels([s[0] for s in stages], fontsize=8.3)
    ax2.set_xlim(0, 10.7)
    ax2.set_xlabel("Tiempo dentro del periodo de muestreo de 10 ms [ms]", fontweight="bold")
    ax2.set_title("B) Presupuesto Temporal de Ciclo de 10 ms (esp_timer Real 1 µs + Enlace ESP-NOW)",
                  fontweight="bold", color="#102a43", fontsize=9.6)
    ax2.grid(axis="x", alpha=0.3)
    ax2.legend(loc="upper right", fontsize=8.1)

    plt.tight_layout()
    out = os.path.join(EVID, "fig_modelo_analitico_spi_tiempos.png")
    plt.savefig(out)
    plt.close()
    print("[OK]", out)


def generate_updated_gantt():
    """Actualiza el Gantt al 24 Nov 2026 incluyendo arribo Bosch BMI160 (25 Nov) y ruta crítica PC5."""
    tasks = [
        ("1. Diseño Conceptual PC3 y Carcasas CAD", "2026-10-01", "2026-10-31", 100, "Jorge / Yael", "#1f4e79"),
        ("2. Firmware Base ESP-NOW & FreeRTOS", "2026-10-01", "2026-10-20", 100, "Yael", "#1f4e79"),
        ("3. Caso Límite 1,200 pkt/s (Spoofer)", "2026-10-13", "2026-10-20", 100, "Yael", "#1f4e79"),
        ("4. Repositorio GitHub, HMI y Código PC4", "2026-11-18", "2026-11-24", 100, "Ambos", "#16a34a"),
        ("5. Primera Prueba Funcional y Reporte PC4", "2026-11-22", "2026-11-24", 95, "Ambos", "#16a34a"),
        ("6. Arribo Bosch BMI160 y Port SPI 3 MHz", "2026-11-25", "2026-11-26", 0, "Yael", "#dc2626"),
        ("7. Soldadura en Placa Preperforada + PETG", "2026-11-26", "2026-11-28", 15, "Jorge", "#dc2626"),
        ("8. Pruebas Osciloscopio, Caminadora y Kinovea", "2026-11-28", "2026-11-30", 0, "Ambos", "#dc2626"),
        ("9. Entrega PC5, Cierre y Expotrónica", "2026-11-30", "2026-12-01", 0, "Ambos", "#7c3aed"),
    ]
    t0 = datetime(2026, 10, 1)
    fig, ax = plt.subplots(figsize=(10.8, 5.2), dpi=190)
    y_pos = np.arange(len(tasks))[::-1]
    for idx, (name, s_str, e_str, pct, owner, col) in enumerate(tasks):
        y = y_pos[idx]
        s = (datetime.strptime(s_str, "%Y-%m-%d") - t0).days
        e = (datetime.strptime(e_str, "%Y-%m-%d") - t0).days
        dur = max(1, e - s + 1)
        ax.barh(y, dur, left=s, height=0.58, color=col, alpha=0.25, edgecolor=col, lw=1.3)
        if pct > 0:
            ax.barh(y, dur * (pct / 100.0), left=s, height=0.58, color=col, alpha=0.90)
        ax.text(s + dur + 0.5, y, f"{pct}% ({owner})", va="center", ha="left", fontsize=8.2, color="#102a43")

    today_x = (datetime(2026, 11, 24) - t0).days
    ax.axvline(today_x, color="#dc2626", ls="--", lw=1.7, label="Corte Entrega PC4 (24 Nov 2026)")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([t[0] for t in tasks], fontsize=8.8)
    ax.set_xticks([0, 14, 31, 45, 54, 61])
    ax.set_xticklabels(["01 Oct", "15 Oct", "01 Nov", "15 Nov", "24 Nov", "01 Dic"], fontsize=8.8)
    ax.set_xlim(0, 75)
    ax.set_title("Cronograma Actualizado KNTX — Corte PC4 (24 Nov) y Ruta Crítica hacia PC5 / Expotrónica (01 Dic)",
                 fontsize=10.0, fontweight="bold", color="#102a43")
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower left", fontsize=8.5)
    plt.tight_layout()
    out = os.path.join(EVID, "gantt_actualizado_pc4.png")
    plt.savefig(out)
    plt.close()
    print("[OK]", out)


if __name__ == "__main__":
    generate_vertical_connections()
    generate_vertical_architecture()
    generate_vertical_packet_flow()
    generate_spi_analytical_model()
    generate_updated_gantt()
