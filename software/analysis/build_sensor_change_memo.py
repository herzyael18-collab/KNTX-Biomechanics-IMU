#!/usr/bin/env python3
"""
build_sensor_change_memo.py
Genera:
  1. Un diagrama limpio, claro y SIN mezclar conceptos (fig_nota_bmi160_resumen.png):
     Muestra únicamente la Arquitectura Sensorial Híbrida Propuesta para PC5
     (1x Bosch BNO085 + 3x Bosch BMI160 por SPI 3 MHz) y un mini-esquema visual de cómo
     funciona la fusión Madgwick 6-DOF (Gyro + Acel -> Cuaternión 36 B).
  2. La Nota Técnica Ejecutiva de 1 página exacta (Nota_Tecnica_Bosch_BMI160_Visual.docx),
     separando con total claridad lo YA medido hoy (BNO085 + MPU-6050 con Madgwick)
     de lo que se consolida mañana al integrar los Bosch BMI160.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

REPO = r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU"
EVID = os.path.join(REPO, "docs", "evidencias")
NAVY = RGBColor(0x10, 0x2A, 0x43)
BLUE = RGBColor(0x1F, 0x4E, 0x79)
DARK = RGBColor(0x1E, 0x29, 0x3B)


def make_clean_architecture_graphic(out_png: str):
    """Diagrama 100% claro: izquierda = Arquitectura Híbrida PC5; derecha = Cómo funciona Madgwick 6-DOF."""
    fig = plt.figure(figsize=(11.5, 3.45), dpi=180)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 3.45)
    ax.axis("off")

    # Marco izquierdo: Arquitectura propuesta para PC5
    ax.add_patch(patches.FancyBboxPatch((0.12, 0.12), 7.20, 3.20, boxstyle="round,pad=0.06",
                                        facecolor="#f8fafc", edgecolor="#cbd5e1", lw=1.2))
    ax.text(3.72, 3.16, "ARQUITECTURA SENSORIAL HÍBRIDA PROPUESTA PARA PC5 (TODOS EN SPI 3 MHz)",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color="#102a43")

    def nbox(x, y, w, h, title, sub, fc, ec):
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                            facecolor=fc, edgecolor=ec, lw=1.5))
        ax.text(x + w/2, y + h - 0.12, title, ha="center", va="top", fontsize=7.6, fontweight="bold", color="#102a43")
        ax.text(x + w/2, y + 0.12, sub, ha="center", va="bottom", fontsize=6.7, color="#334155")

    nbox(0.28, 2.22, 3.15, 0.72, "NODO 1 — TIBIA (Impacto >3g)", "ESP32-C3 + Bosch BNO085 | Fusión HW SH-2", "#dbeafe", "#1d4ed8")
    nbox(0.28, 1.28, 3.15, 0.72, "NODO 2 — FÉMUR (6-DOF)", "ESP32-C3 + Bosch BMI160 | Madgwick en CPU", "#dcfce7", "#15803d")
    nbox(0.28, 0.34, 3.15, 0.72, "NODO 3 — PIE (6-DOF)", "ESP32-C3 + Bosch BMI160 | Madgwick en CPU", "#dcfce7", "#15803d")

    nbox(4.42, 0.52, 2.72, 2.22, "GATEWAY — ESPALDA BAJA",
         "ESP32-S3 + Bosch BMI160\n\n• Core 0: ESP-NOW 100 Hz\n  + Sync SNTP cada 1,000 ms\n• Core 1: Cuaternión q_rel\n  (Sin Gimbal Lock) + Failsafe\n• Salida: BLE 5.0 + CSV",
         "#fff7ed", "#c2410c")

    for ys, ye, col in [(2.58, 2.25, "#1d4ed8"), (1.64, 1.64, "#15803d"), (0.70, 1.05, "#15803d")]:
        ax.annotate("", xy=(4.36, ye), xytext=(3.48, ys),
                    arrowprops=dict(arrowstyle="-|>", lw=1.7, color=col, mutation_scale=12))
    ax.text(3.92, 2.75, "ESP-NOW\n36 Bytes\n100 Hz", ha="center", va="center", fontsize=6.8, fontweight="bold", color="#102a43")

    # Marco derecho: Cómo funciona Madgwick 6-DOF en el ESP32-C3
    ax.add_patch(patches.FancyBboxPatch((7.55, 0.12), 3.82, 3.20, boxstyle="round,pad=0.06",
                                        facecolor="#f0fdf4", edgecolor="#15803d", lw=1.4))
    ax.text(9.46, 3.16, "¿CÓMO FUNCIONA MADGWICK 6-DOF?",
            ha="center", va="center", fontsize=8.4, fontweight="bold", color="#14532d")

    nbox(7.72, 2.25, 1.62, 0.65, "Giroscopio", "Vel. angular (rad/s)\nSuave, pero deriva", "#ffffff", "#64748b")
    nbox(9.58, 2.25, 1.62, 0.65, "Acelerómetro", "Vector gravedad (g)\nSin deriva, con ruido", "#ffffff", "#64748b")

    nbox(7.85, 1.18, 3.22, 0.72, "Filtro Madgwick (Descenso Gradiente)", "Corrige deriva del gyro con gravedad (β=0.12)\nSolo ~0.12 ms en CPU (1.2% del ciclo 10 ms)", "#bbf7d0", "#15803d")
    nbox(7.85, 0.28, 3.22, 0.58, "Salida: Cuaternión [w, x, y, z]", "Misma trama 36 B que BNO085 | Sin Gimbal Lock", "#102a43", "#102a43")
    # Texto blanco para la caja oscura inferior
    for txt in ax.texts[-2:]:
        txt.set_color("white")

    ax.annotate("", xy=(8.65, 1.94), xytext=(8.53, 2.22), arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#15803d"))
    ax.annotate("", xy=(10.25, 1.94), xytext=(10.39, 2.22), arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#15803d"))
    ax.annotate("", xy=(9.46, 0.90), xytext=(9.46, 1.15), arrowprops=dict(arrowstyle="-|>", lw=1.7, color="#102a43"))

    plt.savefig(out_png)
    plt.close()
    print("[OK] Grafico limpio generado:", out_png)


def shade(cell, hex_c):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_c}"/>'))


def add_sec(doc, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title)
    r.bold = True; r.font.name = "Calibri"; r.font.size = Pt(10.3); r.font.color.rgb = BLUE


def add_bullet(doc, bold_pre, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2.0)
    p.paragraph_format.line_spacing = 1.06
    rb = p.add_run(bold_pre)
    rb.bold = True; rb.font.name = "Calibri"; rb.font.size = Pt(8.9); rb.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.name = "Calibri"; r.font.size = Pt(8.9); r.font.color.rgb = DARK


def build_memo(out_docx: str, fig_png: str):
    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(0.40)
        s.bottom_margin = Inches(0.40)
        s.left_margin = Inches(0.55)
        s.right_margin = Inches(0.55)

    # Banner
    hdr = doc.add_table(rows=1, cols=1)
    hdr.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = hdr.cell(0, 0)
    shade(c, "102A43")
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3.5); p.paragraph_format.space_after = Pt(3.5)
    r1 = p.add_run("UNIVERSIDAD MODELO • INGENIERÍA MECATRÓNICA • PROYECTOS VII (AD26)\n")
    r1.bold = True; r1.font.name = "Calibri"; r1.font.size = Pt(9.0); r1.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
    r2 = p.add_run("RESUMEN EJECUTIVO: ARQUITECTURA HÍBRIDA CON BOSCH BMI160 Y VALIDACIÓN EN BANCO (PC4 → PC5)")
    r2.bold = True; r2.font.name = "Calibri"; r2.font.size = Pt(10.8); r2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    pm = doc.add_paragraph()
    pm.paragraph_format.space_before = Pt(3.5); pm.paragraph_format.space_after = Pt(2.5)
    for k, v in [
        ("Proyecto 10 — KNTX  |  ", "Yael A. Yah Hernández & Jorge C. Contreras Rodríguez  |  "),
        ("Docente: ", "Dr. Rodrigo Daniel Solís Ortega  |  24 Nov 2026"),
    ]:
        rk = pm.add_run(k); rk.bold = True; rk.font.name = "Calibri"; rk.font.size = Pt(8.6); rk.font.color.rgb = NAVY
        rv = pm.add_run(v); rv.font.name = "Calibri"; rv.font.size = Pt(8.6); rv.font.color.rgb = DARK

    # Diagrama limpio (Arquitectura propuesta + Cómo funciona Madgwick)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(1); p_img.paragraph_format.space_after = Pt(2)
    p_img.add_run().add_picture(fig_png, width=Inches(7.3))

    # Sección 1: Cambio de sensores
    add_sec(doc, "1. Propuesta de Sustitución Parcial: Bosch BMI160 (Entrega confirmada: mañana)")
    add_bullet(doc, "Motivo (cadena de suministro y costo): ", "Los 3 BNO085 faltantes presentan tiempos de importación incompatibles con el cierre del 1 de diciembre y un sobreprecio elevado (~$1,000 MXN/pza). Conservamos nuestro BNO085 físico en la Tibia (impacto > 3.0 g) e integramos Bosch BMI160 en Fémur, Pie y Lumbar.")
    add_bullet(doc, "Por qué Bosch BMI160 (y no MPU-6050 / MPU-9250): ", "Pertenece a la misma familia Bosch Sensortec de grado wearable, ofrece bus SPI nativo hasta 10 MHz (mantiene RP-04/RQ-01 a 3 MHz en todos los nodos), rango ±16 g y consumo ultrabajo (0.9 mA, favoreciendo autonomía > 3 h).")
    add_bullet(doc, "Por qué descartamos el magnetómetro (6-DOF): ", "Conforme al PC2 (Ceriola et al., 2026) y PC3 (Decisión 2), el motor y chasis metálico de la caminadora inducen errores de yaw > 30° en magnetómetros; incluso el BNO085 debe operarse en modo 6-DOF sin magnetómetro (Game Rotation Vector, meta < 3 °/min).")

    # Sección 2: Logro real en banco HOY (con separación transparente!)
    add_sec(doc, "2. Evidencia Ya Validada HOY en Banco (Pruebas Reales con BNO085 + MPU-6050 corriendo Madgwick)")
    add_bullet(doc, "Superación del límite de CPU de PC3: ", "En PC3 el filtro por software colapsó por código bloqueante (delay(), Serial a 115.2 kbps y polling SPI sin INT). Al reescribir el firmware con esp_timer (1 µs), Madgwick compacto (~0.12 ms/ciclo = 1.2% del CPU), SPI por pin INT y Gateway Dual-Core a 921,600 bps, la fusión en CPU opera estable a 100 Hz.")
    add_bullet(doc, "Por qué esto respalda al BMI160: ", "Si el algoritmo Madgwick ya superó las metas del PC2 usando un MPU-6050 básico por I2C (Tabla 1), al migrar mañana al Bosch BMI160 por SPI 3 MHz conservamos exactamente el mismo protocolo de 36 bytes y ganamos menor ruido, SPI nativo y mayor rango dinámico (±16 g).")

    # Tabla comparativa honesta: Medido HOY vs. Mejora al poner BMI160 mañana
    tbl = doc.add_table(rows=5, cols=4)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Criterio PC2", "Ya Medido HOY en Banco (60 s reales)", "Evaluado con", "Mejora al integrar Bosch BMI160 (PC5)"]
    rows = [
        ["RP-04 (SPI 3 MHz ≤1.5 ms)", "1.39 ms (bajó de 8.99 ms con pin INT)", "ESP32-C3 + BNO085", "Todos los nodos pasan a SPI 3 MHz (eliminando I2C del MPU-6050)"],
        ["RF-01 / RP-01 (100 Hz, <5 ms)", "99.94 Hz (P95 1.0 ms) y 100.21 Hz (P95 0.0 ms)", "BNO085 + MPU-6050", "Misma trama ESP-NOW 36 B a 100 Hz y 0 Overflows en FreeRTOS"],
        ["RF-02 / RP-03 (Sin Gimbal Lock)", "Cruce 90° -> 136.4°; deriva 0.02 y 0.98 °/min", "BNO085 + MPU-6050", "Menor ruido de giroscopio Bosch -> menor deriva 6-DOF (< 3 °/min)"],
        ["Failsafe / Consumo / Carcasa", "Desconexión detectada en 359 ms + reconexión", "Gateway ESP32-S3", "0.9 mA del BMI160 ayuda a > 3 h en placa preperforada + PETG 32.9 cm³"],
    ]
    widths = [1.55, 2.05, 1.25, 2.45]
    for j, h in enumerate(headers):
        cell = tbl.rows[0].cells[j]
        shade(cell, "102A43")
        cell.width = Inches(widths[j])
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(1.5); p.paragraph_format.space_after = Pt(1.5)
        r = p.add_run(h); r.bold = True; r.font.size = Pt(8.2); r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for i, rdata in enumerate(rows):
        bg = "F8FAFC" if i % 2 else "FFFFFF"
        for j, val in enumerate(rdata):
            cell = tbl.rows[i + 1].cells[j]
            shade(cell, bg)
            cell.width = Inches(widths[j])
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1.5); p.paragraph_format.space_after = Pt(1.5)
            r = p.add_run(val); r.font.size = Pt(8.0)
            if j == 0: r.bold = True; r.font.color.rgb = NAVY

    pf = doc.add_paragraph()
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.paragraph_format.space_before = Pt(5); pf.paragraph_format.space_after = Pt(0)
    rf = pf.add_run("Repositorio Público GitHub (código, evidencias reales y Dashboard HMI): https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU")
    rf.italic = True; rf.font.size = Pt(8.1); rf.font.color.rgb = BLUE

    doc.save(out_docx)
    print("[OK] Nota clara y sin ambiguedad generada:", out_docx)


if __name__ == "__main__":
    fig_p = os.path.join(EVID, "fig_nota_bmi160_resumen.png")
    out_d = os.path.join(REPO, "docs", "reportes", "Nota_Tecnica_Bosch_BMI160_Final.docx")
    make_clean_architecture_graphic(fig_p)
    build_memo(out_d, fig_p)
