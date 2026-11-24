#!/usr/bin/env python3
"""
generate_visual_infographics.py
Crea 2 infografías de alta claridad y calidad editorial usando las fotos REALES
de los circuitos armados en laboratorio:
  1. fig_infografia_cables_senales.png:
     Muestra cada circuito físico real (Nodo 1 C3+BNO085, Nodo 2 ESP32+MPU6050 y Gateway S3+Lumbar)
     con mapa explícito cable-por-cable de QUÉ SEÑAL viaja por cada hilo físico (SPI 3 MHz, INT, RST,
     I2C 400 kHz, 3.3V/GND, pulsos de osciloscopio).
  2. fig_infografia_flujo_paquetes.png:
     Explica visualmente de forma intuitiva cómo fluye la telemetría completa desde los sensores
     hasta el teléfono/PC: qué paquetes entran por ESP-NOW (36 B @ 100 Hz), cómo regresa el pulso
     SNTP cada 1,000 ms, qué hace el Núcleo 0 vs Núcleo 1 de FreeRTOS, qué ocurre si se apaga un nodo
     (Failsafe) y cómo sale por BLE 5.0 y USB-CSV (921,600 bps).
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

REPO = r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU"
EVID = os.path.join(REPO, "docs", "evidencias")


def load_cropped(path, crop_box_frac=None, max_w=700):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if crop_box_frac:
        l, t, r, b = crop_box_frac
        img = img.crop((int(w*l), int(h*t), int(w*r), int(h*b)))
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), Image.Resampling.LANCZOS)
    return img


def make_cables_infographic():
    fig = plt.figure(figsize=(14, 9.2), dpi=180)
    fig.patch.set_facecolor("#f8fafc")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9.2)
    ax.axis("off")

    # Banner superior
    ax.add_patch(patches.Rectangle((0, 8.45), 14, 0.75, facecolor="#102a43", edgecolor="none"))
    ax.text(7.0, 8.88, "KNTX — MAPA VISUAL DE CONEXIONES FÍSICAS Y SEÑALES POR CABLE (AS-BUILT PC4)",
            ha="center", va="center", fontsize=13.5, fontweight="bold", color="white")
    ax.text(7.0, 8.58, "Identificación física real de componentes, pines GPIO, buses locales (< 10 cm) y qué información viaja por cada hilo",
            ha="center", va="center", fontsize=9.2, color="#cbd5e1")

    def card(x, y, w, h, title, subtitle, header_color):
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                            facecolor="white", edgecolor=header_color, linewidth=2.0))
        ax.add_patch(patches.FancyBboxPatch((x, y + h - 0.62), w, 0.62, boxstyle="round,pad=0.04",
                                            facecolor=header_color, edgecolor="none"))
        ax.text(x + 0.18, y + h - 0.22, title, va="center", ha="left", fontsize=10.5, fontweight="bold", color="white")
        ax.text(x + 0.18, y + h - 0.46, subtitle, va="center", ha="left", fontsize=8.1, color="#e2e8f0")

    def cable_row(x, y, wire_color, wire_name, pins, what_passes):
        # Línea de color representando el cable físico
        ax.plot([x, x + 0.36], [y, y], color=wire_color, lw=4.0, solid_capstyle="round")
        ax.text(x + 0.46, y + 0.08, f"{wire_name}  ({pins})", va="center", ha="left",
                fontsize=8.3, fontweight="bold", color="#102a43")
        ax.text(x + 0.46, y - 0.12, what_passes, va="center", ha="left",
                fontsize=7.6, color="#475569")

    # ================= TARJETA 1: NODO 1 (C3 + BNO085) =================
    card(0.25, 4.35, 6.65, 3.9,
         "1. NODO SATÉLITE 1 — TIBIA (Alta Precisión)",
         "ESP32-C3 SuperMini + GY-BNO08X (Coprocesador SH-2) | Bus SPI 3 MHz (< 5 cm)",
         "#1f4e79")

    img1 = load_cropped(os.path.join(EVID, "foto_nodo1_c3_bno085.jpg"), (0.18, 0.25, 0.85, 0.90), max_w=420)
    ib1 = OffsetImage(img1, zoom=0.41)
    ax.add_artist(AnnotationBbox(ib1, (1.65, 6.22), frameon=True,
                                 bboxprops=dict(edgecolor="#1f4e79", lw=1.4)))
    ax.text(1.65, 4.72, "Foto real: cables SPI ultracortos\n(< 5 cm, cumple RP-04 < 10 cm)",
            ha="center", va="center", fontsize=7.6, style="italic", color="#334e68")

    rx1 = 3.10
    cable_row(rx1, 7.30, "#dc2626", "3.3V y GND", "3V3->VCC | G->GND", "Energía lógica regulada 3.3 V + referencia común")
    cable_row(rx1, 6.80, "#ea580c", "PS0 y PS1 -> 3.3V", "Puentes HIGH", "Obliga al BNO085 a arrancar en modo SPI (no I2C)")
    cable_row(rx1, 6.30, "#2563eb", "SCK (Reloj SPI)", "GPIO4 -> SCL", "Pulso maestro a 3 MHz (flancos < 50 ns)")
    cable_row(rx1, 5.80, "#16a34a", "MISO (Datos IMU)", "GPIO5 <- SDA", "Cuaterniones [w,x,y,z] + Acel [g] del SH-2")
    cable_row(rx1, 5.30, "#9333ea", "MOSI + CS", "GPIO6->ADD | GPIO7->CS", "Comandos SH-2 y selección de chip SPI")
    cable_row(rx1, 4.80, "#0891b2", "INT + RST", "GPIO2<-INT | GPIO3->RST", "INT avisa dato listo -> baja lectura de 8.99 a 1.39 ms")

    # ================= TARJETA 2: NODO 2 (ESP32 + MPU6050) =================
    card(7.10, 4.35, 6.65, 3.9,
         "2. NODO SATÉLITE 2 — FÉMUR (Equivalencia As-Built PC4)",
         "ESP32 WROOM-32 + MPU6050 (GY-521) | Bus I2C 400 kHz + Fusión Madgwick 100 Hz",
         "#15803d")

    img2 = load_cropped(os.path.join(EVID, "foto_nodo2_esp32_mpu6050.jpg"), (0.08, 0.14, 0.82, 0.88), max_w=420)
    ib2 = OffsetImage(img2, zoom=0.42)
    ax.add_artist(AnnotationBbox(ib2, (8.55, 6.22), frameon=True,
                                 bboxprops=dict(edgecolor="#15803d", lw=1.4)))
    ax.text(8.55, 4.72, "Foto real: ESP32 WROOM-32\n+ MPU6050 listo para prueba Failsafe",
            ha="center", va="center", fontsize=7.6, style="italic", color="#334e68")

    rx2 = 9.95
    cable_row(rx2, 7.25, "#dc2626", "Alimentación", "3V3->VCC | GND->GND", "Alimentación limpia 3.3 V desde regulador ESP32")
    cable_row(rx2, 6.68, "#16a34a", "SDA (Datos I2C)", "GPIO21 <-> SDA", "Lectura cruda Gyro (rad/s) y Acel (g) a 400 kHz")
    cable_row(rx2, 6.11, "#2563eb", "SCL (Reloj I2C)", "GPIO22 -> SCL", "Sincroniza muestreo exacto cada 10 ms (100 Hz)")
    cable_row(rx2, 5.54, "#334155", "AD0 -> GND", "Dirección 0x68", "Fija dirección I2C estándar del MPU6050")
    cable_row(rx2, 4.95, "#7c3aed", "Proceso en CPU", "Madgwick 6-DOF", "Convierte Gyro+Acel a Cuaternión 36B idéntico a Nodo 1")

    # ================= TARJETA 3: GATEWAY ESP32-S3 + LUMBAR =================
    card(0.25, 0.25, 13.50, 3.85,
         "3. GATEWAY CENTRAL — ESPALDA BAJA (L4–L5) | MAC REAL: E0:72:A1:F4:EB:D8",
         "ESP32-S3-WROOM-1 N16R8 Dual-Core FreeRTOS + MPU6050 Lumbar Local + Antena 2.4 GHz (ESP-NOW & BLE 5.0) + USB 921,600 bps",
         "#b45309")

    img3 = load_cropped(os.path.join(EVID, "foto_gateway_s3_lumbar.jpg"), (0.04, 0.14, 0.72, 0.78), max_w=480)
    ib3 = OffsetImage(img3, zoom=0.42)
    ax.add_artist(AnnotationBbox(ib3, (2.25, 2.08), frameon=True,
                                 bboxprops=dict(edgecolor="#b45309", lw=1.4)))
    ax.text(2.25, 0.62, "Foto real: Gateway ESP32-S3 N16R8\nconectado por USB-UART (CH343) + MPU6050",
            ha="center", va="center", fontsize=7.8, style="italic", color="#334e68")

    rx3 = 4.45
    cable_row(rx3, 3.05, "#dc2626", "Energía Lumbar", "3V3->VCC | GND->GND", "Alimenta el sensor MPU6050 #1 integrado en el Gateway")
    cable_row(rx3, 2.50, "#16a34a", "I2C Lumbar Local", "GPIO8=SDA | GPIO9=SCL", "Lee aceleración/orientación de espalda baja (Node_ID = 0)")
    cable_row(rx3, 1.95, "#ea580c", "Pulso Osciloscopio", "GPIO4 (RX Trigger)", "Sube a HIGH al llegar paquete ESP-NOW (mide latencia aire < 2 ms)")
    cable_row(rx3, 1.40, "#0891b2", "Puerto USB-C (UART)", "CH343 @ 921,600 bps", "Exporta filas CSV (RF-08) y telemetría en vivo hacia Python")
    cable_row(rx3, 0.85, "#7c3aed", "Antena PCB 2.4 GHz", "ESP-NOW + BLE 5.0", "Recibe Nodos 1 y 2 a 100 Hz (Core 0) y emite BLE al móvil (Core 1)")

    # Recuadro derecho resumen del Gateway
    ax.add_patch(patches.FancyBboxPatch((9.55, 0.55), 3.95, 2.78, boxstyle="round,pad=0.10",
                                        facecolor="#fffbeb", edgecolor="#d97706", linewidth=1.6))
    ax.text(11.52, 3.08, "¿POR QUÉ FUNCIONA SIN TRABARSE?", ha="center", va="center",
            fontsize=9.2, fontweight="bold", color="#92400e")
    bullets = (
        "• Core 0 (Radio): Solo recibe ESP-NOW\n"
        "  y guarda en Cola de 1,000 paquetes.\n"
        "• Broadcast SNTP: Envía la hora del S3\n"
        "  cada 1,000 ms para alinear relojes.\n"
        "• Core 1 (Cinemática): Calcula q_rel\n"
        "  (rodilla sin Gimbal Lock) y vigila\n"
        "  Failsafe (si un nodo calla > 350 ms,\n"
        "  lo marca NULL sin detener BLE/CSV)."
    )
    ax.text(9.72, 2.82, bullets, va="top", ha="left", fontsize=8.0, color="#451a03", linespacing=1.35)

    out = os.path.join(EVID, "fig_infografia_cables_senales.png")
    plt.savefig(out)
    plt.close()
    print("[OK]", out)


def make_packet_flow_infographic():
    """Diagrama visual súper intuitivo de QUÉ PAQUETES VIAJAN POR CADA ENLACE y CÓMO OPERA EL SISTEMA."""
    fig = plt.figure(figsize=(14, 7.6), dpi=180)
    fig.patch.set_facecolor("#ffffff")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.6)
    ax.axis("off")

    ax.add_patch(patches.Rectangle((0, 6.85), 14, 0.75, facecolor="#102a43", edgecolor="none"))
    ax.text(7.0, 7.30, "KNTX — FLUJO DE TELEMETRÍA Y PAQUETES EN TIEMPO REAL (EXPLICACIÓN GRÁFICA)",
            ha="center", va="center", fontsize=13.2, fontweight="bold", color="white")
    ax.text(7.0, 7.00, "Paso a paso: cómo nace un dato en el sensor, viaja por ESP-NOW, se sincroniza con SNTP, se procesa en FreeRTOS y llega a la pantalla",
            ha="center", va="center", fontsize=8.8, color="#cbd5e1")

    def box(x, y, w, h, title, text, fc, ec, title_c="#102a43"):
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.10",
                                            facecolor=fc, edgecolor=ec, linewidth=1.8))
        ax.text(x + w/2, y + h - 0.22, title, ha="center", va="top", fontsize=9.2, fontweight="bold", color=title_c)
        ax.text(x + w/2, y + h/2 - 0.16, text, ha="center", va="center", fontsize=7.9, color="#1e293b", linespacing=1.32)

    # Columna 1: Sensores (Nodos)
    box(0.30, 4.15, 2.95, 2.35,
        "PASO 1A: NODO 1 (TIBIA)",
        "BNO085 fusiona 9-DOF a 400 Hz\n"
        "↓ Pin INT avisa (lectura 1.39 ms)\n"
        "ESP32-C3 lee por SPI a 3 MHz\n"
        "↓ Suma desfase SNTP al reloj\n"
        "Empaqueta 36 bytes cada 10 ms\n"
        "(100 paquetes/s exactos)",
        "#eff6ff", "#1d4ed8", "#1e3a8a")

    box(0.30, 1.35, 2.95, 2.35,
        "PASO 1B: NODO 2 (FÉMUR)",
        "MPU6050 lee Gyro + Acel (I2C)\n"
        "↓ Bias calibrado en reposo\n"
        "ESP32 corre filtro Madgwick 6-DOF\n"
        "↓ Suma desfase SNTP al reloj\n"
        "Empaqueta los MISMOS 36 bytes\n"
        "(100 paquetes/s exactos)",
        "#f0fdf4", "#15803d", "#14532d")

    # Columna 2: Medio inalámbrico (Estructura del paquete)
    ax.add_patch(patches.FancyBboxPatch((3.80, 4.05), 2.55, 2.45, boxstyle="round,pad=0.08",
                                        facecolor="#fefce8", edgecolor="#ca8a04", linewidth=1.8, linestyle="--"))
    ax.text(5.07, 6.28, "PAQUETE ESP-NOW (36 Bytes)", ha="center", va="top", fontsize=8.8, fontweight="bold", color="#854d0e")
    pkt_fields = (
        "• msg_type (1B): 0x01 DATA\n"
        "• node_id  (1B): 1=Tibia, 2=Fémur\n"
        "• timestamp(4B): ms sincronizado\n"
        "• quat[4] (16B): [w, x, y, z]\n"
        "• accel[3](12B): [ax, ay, az] en g\n"
        "• calib+seq(3B): estado + contador\n"
        "Canal Wi-Fi 1 | Aire < 2 ms"
    )
    ax.text(3.92, 5.95, pkt_fields, va="top", ha="left", fontsize=7.4, color="#422006", linespacing=1.32)

    # Bloque regreso SNTP
    ax.add_patch(patches.FancyBboxPatch((3.80, 1.65), 2.55, 1.65, boxstyle="round,pad=0.08",
                                        facecolor="#fef2f2", edgecolor="#dc2626", linewidth=1.6, linestyle="--"))
    ax.text(5.07, 3.12, "REGRESO: SYNC SNTP (10 B)", ha="center", va="top", fontsize=8.6, fontweight="bold", color="#991b1b")
    ax.text(5.07, 2.30, "Gateway envía broadcast cada\n1,000 ms con su reloj T_S3.\nCada nodo ajusta:\noffset = T_S3 - millis()\n-> Logra Jitter P95 ≤ 1.0 ms",
            ha="center", va="center", fontsize=7.5, color="#7f1d1d", linespacing=1.28)

    # Columna 3: Gateway ESP32-S3 (Core 0 y Core 1)
    ax.add_patch(patches.FancyBboxPatch((6.95, 1.15), 3.65, 5.45, boxstyle="round,pad=0.10",
                                        facecolor="#fff7ed", edgecolor="#c2410c", linewidth=2.2))
    ax.text(8.77, 6.42, "PASO 2: GATEWAY ESP32-S3 (DUAL-CORE)", ha="center", va="top",
            fontsize=9.3, fontweight="bold", color="#9a3412")

    box(7.15, 4.30, 3.25, 1.80,
        "NÚCLEO 0 — Radio & Sincronía",
        "1) Callback ESP-NOW -> g_rxQueue (1000)\n"
        "2) taskRxConsumer valida Node_ID,\n"
        "   detecta impacto > 3.0 g (RF-05)\n"
        "   y envía copia a g_csvQueue\n"
        "3) taskSyncBroadcast cada 1,000 ms",
        "#ffedd5", "#ea580c", "#9a3412")

    box(7.15, 1.40, 3.25, 2.55,
        "NÚCLEO 1 — Cinemática & Failsafe",
        "1) Cierra ventana cada 10 ms (100 Hz)\n"
        "2) FAILSAFE: si un nodo calla > 350 ms\n"
        "   lo marca NULL sin trabar el sistema\n"
        "3) Calcula Cuaternión Relativo:\n"
        "   q_rel = conj(q_femur) ⊗ q_tibia\n"
        "   (Ángulo rodilla SIN Gimbal Lock a 90°)\n"
        "4) Emite BLE 5.0 y vacía g_csvQueue",
        "#fef3c7", "#d97706", "#92400e")

    # Columna 4: Salidas finales
    box(11.15, 4.20, 2.55, 2.25,
        "PASO 3A: INTERFAZ MÓVIL",
        "Enlace BLE 5.0 (2M PHY)\n"
        "Servicio: KNTX_Gateway_S3\n"
        "Recibe máscara de nodos,\n"
        "ángulo de rodilla en vivo\n"
        "y banda normativa ± 1 DE",
        "#faf5ff", "#7e22ce", "#581c87")

    box(11.15, 1.35, 2.55, 2.40,
        "PASO 3B: PC / PYTHON LIVE",
        "USB-UART @ 921,600 bps\n"
        "1) Dashboard en vivo:\n"
        "   Gráfica rodilla + LEDs\n"
        "   + Alerta Failsafe + Tara\n"
        "2) Archivo .CSV (RF-08):\n"
        "   Grood-Suntay / Bland-Altman",
        "#f0f9ff", "#0369a1", "#0c4a6e")

    # Flechas entre bloques
    ak = dict(arrowstyle="-|>", lw=2.2, color="#1d4ed8", mutation_scale=15)
    ax.annotate("", xy=(3.78, 5.45), xytext=(3.28, 5.45), arrowprops=ak)
    ax.annotate("", xy=(3.78, 4.65), xytext=(3.28, 3.05), arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#15803d", mutation_scale=15))
    ax.annotate("", xy=(6.92, 5.20), xytext=(6.38, 5.20), arrowprops=dict(arrowstyle="-|>", lw=2.4, color="#b45309", mutation_scale=16))

    # Flecha retorno SNTP
    ax.annotate("", xy=(6.38, 2.45), xytext=(7.12, 4.45), arrowprops=dict(arrowstyle="-|>", lw=1.6, ls="--", color="#dc2626", mutation_scale=13))
    ax.annotate("", xy=(3.28, 4.30), xytext=(3.78, 2.65), arrowprops=dict(arrowstyle="-|>", lw=1.6, ls="--", color="#dc2626", mutation_scale=13))
    ax.annotate("", xy=(3.28, 2.35), xytext=(3.78, 2.35), arrowprops=dict(arrowstyle="-|>", lw=1.6, ls="--", color="#dc2626", mutation_scale=13))

    # Flecha Core 0 -> Core 1
    ax.annotate("", xy=(8.77, 3.98), xytext=(8.77, 4.28), arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#9a3412", mutation_scale=14))

    # Flechas salida Gateway -> Móvil y PC
    ax.annotate("", xy=(11.12, 5.25), xytext=(10.42, 3.30), arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#7e22ce", mutation_scale=15))
    ax.annotate("", xy=(11.12, 2.55), xytext=(10.42, 2.55), arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#0369a1", mutation_scale=15))

    # Pie informativo en 2 líneas centradas
    ax.add_patch(patches.FancyBboxPatch((0.30, 0.18), 13.40, 0.72, boxstyle="round,pad=0.06",
                                        facecolor="#f1f5f9", edgecolor="#64748b", linewidth=1.2))
    ax.text(7.0, 0.54,
            "MÉTRICAS REALES VALIDADAS EN BANCO:  SPI = 1.39 ms (≤1.5 ms)  |  Nodo 1 = 99.94 Hz (P95 Jitter 1.0 ms)  |  Nodo 2 = 100.21 Hz (P95 Jitter 0.0 ms)\n"
            "Cruce por 90° hasta 136.4° sin Gimbal Lock  |  Deriva Yaw BNO085 = 0.021 °/min  |  Failsafe real = 359 ms + Reconexión automática (0 Overflows)",
            ha="center", va="center", fontsize=8.0, fontweight="bold", color="#0f172a", linespacing=1.4)

    out = os.path.join(EVID, "fig_infografia_flujo_paquetes.png")
    plt.savefig(out)
    plt.close()
    print("[OK]", out)


if __name__ == "__main__":
    make_cables_infographic()
    make_packet_flow_infographic()
