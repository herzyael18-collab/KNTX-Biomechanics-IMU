#!/usr/bin/env python3
"""
kntx_generate_pc4_assets.py
Genera:
  1. Archivo CAD 3D editable (.stl) de la carcasa del nodo satélite KNTX (44x34x22 mm, 32.9 cm^3 < 40 cm^3).
  2. Diagrama esquemático de arquitectura As-Built PC4 (PNG de alta resolución para el reporte).
  3. Diagrama de Gantt actualizado de PC4 hacia PC5 / Expotrónica (PNG + .csv de cronograma).
"""

import os
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime


def write_box_triangles(tris, x0, y0, z0, x1, y1, z1):
    """Agrega los 12 triángulos de un prisma rectangular [x0..x1, y0..y1, z0..z1]."""
    v = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2),  # bottom
        (4, 5, 6), (4, 6, 7),  # top
        (0, 1, 5), (0, 5, 4),  # front
        (2, 3, 7), (2, 7, 6),  # back
        (0, 4, 7), (0, 7, 3),  # left
        (1, 2, 6), (1, 6, 5),  # right
    ]
    for a, b, c in faces:
        tris.append((v[a], v[b], v[c]))


def generate_housing_stl(out_stl: str):
    """Genera el STL binario de la carcasa KNTX (44 x 34 x 22 mm, pared 2 mm, labio IP54)."""
    tris = []
    L, W, H, t = 44.0, 34.0, 20.0, 2.0
    # Fondo
    write_box_triangles(tris, 0, 0, 0, L, W, t)
    # Paredes laterales (hueco interno para placa preperforada/PCB + LiPo)
    write_box_triangles(tris, 0, 0, t, L, t, H)
    write_box_triangles(tris, 0, W - t, t, L, W, H)
    write_box_triangles(tris, 0, t, t, t, W - t, H)
    write_box_triangles(tris, L - t, t, t, L, W - t, H)
    # Labio perimetral IP54 (sobresale 2 mm para machihembrado con tapa)
    write_box_triangles(tris, 1, 1, H, L - 1, 2, H + 2)
    write_box_triangles(tris, 1, W - 2, H, L - 1, W - 1, H + 2)
    write_box_triangles(tris, 1, 2, H, 2, W - 2, H + 2)
    write_box_triangles(tris, L - 2, 2, H, L - 1, W - 2, H + 2)
    # Guías exteriores para banda elástica (pasacintas)
    write_box_triangles(tris, -3.5, 4.5, 0, 0, W - 4.5, 4.5)
    write_box_triangles(tris, L, 4.5, 0, L + 3.5, W - 4.5, 4.5)

    with open(out_stl, "wb") as f:
        header = b"KNTX Node Housing 44x34x22mm IP54 (32.9cm3) - Universidad Modelo".ljust(80, b"\x00")
        f.write(header)
        f.write(struct.pack("<I", len(tris)))
        for p1, p2, p3 in tris:
            u = np.array(p2) - np.array(p1)
            v = np.array(p3) - np.array(p1)
            n = np.cross(u, v)
            norm = np.linalg.norm(n)
            if norm > 0:
                n = n / norm
            f.write(struct.pack("<3f", float(n[0]), float(n[1]), float(n[2])))
            for p in (p1, p2, p3):
                f.write(struct.pack("<3f", float(p[0]), float(p[1]), float(p[2])))
            f.write(struct.pack("<H", 0))
    print(f"[OK] STL generado: {out_stl} ({len(tris)} triángulos)")


def generate_as_built_diagram(out_png: str):
    """Genera diagrama de arquitectura As-Built PC4 limpio y profesional."""
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=180)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    ax.text(6.0, 6.15, "ARQUITECTURA AS-BUILT KNTX (PC4) — RED ESTRELLA ESP-NOW 100 Hz + SPI 3 MHz",
            ha="center", va="center", fontsize=12, fontweight="bold", color="#102a43")

    def draw_box(x, y, w, h, title, body, fc, ec="#1f4e79"):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                                      facecolor=fc, edgecolor=ec, linewidth=1.8)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="top",
                fontsize=9.5, fontweight="bold", color="#102a43")
        ax.text(x + w / 2, y + h / 2 - 0.18, body, ha="center", va="center",
                fontsize=8.2, color="#243b53", linespacing=1.35)

    # Nodo 1
    draw_box(0.3, 3.3, 3.4, 2.3,
             "NODO SATÉLITE 1 — TIBIA",
             "MCU: ESP32-C3 (DevKit / pines)\nIMU: BNO085 (Coprocesador SH-2)\nBus: SPI 3 MHz (< 10 cm, RP-04)\nGPIO4=SCK, 5=MISO, 6=MOSI, 7=CS\nGPIO2=INT, 3=RST, 10=Trig Latencia\nFusión HW: Game / Rotation Vector",
             "#e6f2ff", "#1f4e79")

    # Nodo 2
    draw_box(0.3, 0.5, 3.4, 2.3,
             "NODO SATÉLITE 2 — FÉMUR",
             "MCU: ESP32 WROOM-32 (pines)\nIMU: MPU6050 #2 (Breakout)\nBus: I2C 400 kHz (GPIO21/22)\nFusión: Madgwick 6-DOF a 100 Hz\nCalibración estática bias (RF-04)\nTrama estándar KNTX (36 bytes)",
             "#eef7ee", "#2e7d32")

    # Gateway
    draw_box(4.6, 1.5, 3.7, 3.7,
             "GATEWAY CENTRAL — ESPALDA BAJA",
             "MCU: ESP32-S3-WROOM-1 N16R8\nIMU Local Opcional: MPU6050 #1 (Lumbar)\n\n• CORE 0 (Radio & Sync):\n  ISR ESP-NOW -> Cola FreeRTOS (1000)\n  Broadcast SNTP cada 1,000 ms (jitter<5ms)\n  GPIO4 = Pulso RX (medición latencia <2ms)\n\n• CORE 1 (Cinemática & Salida):\n  Ventana 10 ms tolerante a fallos (Failsafe)\n  Cuaternión relativo q_rel (sin Gimbal Lock)\n  BLE 5.0 + Exportación CSV estándar RF-08",
             "#fff8e6", "#b45309")

    # PC / Movil
    draw_box(9.0, 3.4, 2.7, 2.1,
             "INTERFAZ MÓVIL (BLE 5.0)",
             "Recepción tiempo real\nEstado de nodos activos\nÁngulo de rodilla (deg)\nBanda normativa ±1 DE",
             "#f3e8ff", "#6b21a8")

    draw_box(9.0, 0.7, 2.7, 2.2,
             "PC / SUITE PYTHON (USB)",
             "Logger CSV (RF-08)\nAnálisis Jitter / PV-01..04\nGrood & Suntay (ISB)\nBland-Altman & Kinovea",
             "#f0f4f8", "#334e68")

    # Flechas
    arrow_kw = dict(arrowstyle="-|>", lw=1.8, color="#1f4e79", mutation_scale=14)
    ax.annotate("", xy=(4.55, 4.1), xytext=(3.78, 4.4), arrowprops=arrow_kw)
    ax.annotate("", xy=(4.55, 2.5), xytext=(3.78, 1.7), arrowprops=arrow_kw)
    ax.text(4.15, 4.65, "ESP-NOW\n100 Hz", ha="center", fontsize=7.8, fontweight="bold", color="#1f4e79")
    ax.text(4.15, 1.45, "ESP-NOW\n100 Hz", ha="center", fontsize=7.8, fontweight="bold", color="#2e7d32")

    # Flecha Sync broadcast
    ax.annotate("", xy=(3.78, 3.65), xytext=(4.55, 3.45),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, ls="--", color="#c00000", mutation_scale=12))
    ax.text(4.15, 3.25, "SNTP Sync\n(1,000 ms)", ha="center", fontsize=7.4, color="#c00000")

    # Salidas Gateway
    ax.annotate("", xy=(8.95, 4.4), xytext=(8.38, 3.9),
                arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#6b21a8", mutation_scale=14))
    ax.text(8.67, 4.42, "BLE 5.0", ha="center", fontsize=7.8, fontweight="bold", color="#6b21a8")

    ax.annotate("", xy=(8.95, 1.8), xytext=(8.38, 2.3),
                arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#334e68", mutation_scale=14))
    ax.text(8.67, 1.65, "USB CSV", ha="center", fontsize=7.8, fontweight="bold", color="#334e68")

    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()
    print(f"[OK] Diagrama As-Built generado: {out_png}")


def generate_updated_gantt(out_png: str):
    """Genera Diagrama de Gantt actualizado al 23 Nov 2026 con ruta crítica hacia PC5 y Expotrónica."""
    tasks = [
        ("1. Diseño Hardware PC3 + Carcasas 3D", "2026-10-01", "2026-10-31", 100, "Jorge / Yael", "#1f4e79"),
        ("2. Firmware Base ESP-NOW & FreeRTOS",  "2026-10-01", "2026-10-20", 100, "Yael",         "#1f4e79"),
        ("3. Caso Límite 1,200 pkt/s (Spoofer)", "2026-10-13", "2026-10-20", 100, "Yael",         "#1f4e79"),
        ("4. Regularización GitHub & Firmware PC4", "2026-11-18", "2026-11-24", 95, "Ambos",      "#2e7d32"),
        ("5. Ensamble As-Built Proto (C3+BNO+S3+MPU)", "2026-11-22", "2026-11-25", 70, "Ambos",   "#d97706"),
        ("6. Pruebas PC4 (SPI 3MHz, PV-01..07, Video)", "2026-11-24", "2026-11-26", 30, "Ambos",  "#c00000"),
        ("7. Migración a Placa Preperforada + Carcasas", "2026-11-26", "2026-11-28", 15, "Jorge", "#c00000"),
        ("8. Validación Dinámica Caminadora/Kinovea (PC5)", "2026-11-28", "2026-11-30", 0, "Ambos", "#c00000"),
        ("9. Cierre Presupuestal, PC5 y Expotrónica", "2026-11-30", "2026-12-01", 0, "Ambos",     "#7c3aed"),
    ]

    t0 = datetime(2026, 10, 1)
    fig, ax = plt.subplots(figsize=(11.5, 5.4), dpi=170)

    y_pos = np.arange(len(tasks))[::-1]
    for idx, (name, start_s, end_s, pct, owner, color) in enumerate(tasks):
        y = y_pos[idx]
        s = (datetime.strptime(start_s, "%Y-%m-%d") - t0).days
        e = (datetime.strptime(end_s, "%Y-%m-%d") - t0).days
        dur = max(1, e - s + 1)
        ax.barh(y, dur, left=s, height=0.58, color=color, alpha=0.28, edgecolor=color, linewidth=1.2)
        if pct > 0:
            ax.barh(y, dur * (pct / 100.0), left=s, height=0.58, color=color, alpha=0.88)
        ax.text(s + dur + 0.6, y, f"{pct}% ({owner})", va="center", ha="left", fontsize=8.2, color="#102a43")

    # Línea de corte actual (23 Nov 2026)
    today_x = (datetime(2026, 11, 23) - t0).days
    ax.axvline(today_x, color="#c00000", linestyle="--", linewidth=1.6, label="Fecha corte PC4 (23 Nov 2026)")

    ax.set_yticks(y_pos)
    ax.set_yticklabels([t[0] for t in tasks], fontsize=8.8)
    xticks = [0, 14, 31, 45, 53, 61]
    xlabels = ["01 Oct", "15 Oct", "01 Nov", "15 Nov", "23 Nov", "01 Dic"]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, fontsize=8.8)
    ax.set_xlim(0, 74)
    ax.set_title("Cronograma Actualizado KNTX (PC4 -> Ruta Crítica hacia PC5 y Expotrónica 01 Dic 2026)",
                 fontsize=10.5, fontweight="bold", color="#102a43")
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower left", fontsize=8.5)
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()
    print(f"[OK] Gantt actualizado generado: {out_png}")


if __name__ == "__main__":
    base = r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU"
    generate_housing_stl(os.path.join(base, "hardware", "carcasas", "kntx_nodo_carcasa_v2.stl"))
    generate_as_built_diagram(os.path.join(base, "hardware", "pcb", "diagrama_as_built_pc4.png"))
    generate_updated_gantt(os.path.join(base, "docs", "evidencias", "gantt_actualizado_pc4.png"))
