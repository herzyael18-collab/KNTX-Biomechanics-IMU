#!/usr/bin/env python3
"""
build_sensor_change_memo.py
Genera una Nota Técnica Ejecutiva de 1 página (formato institucional Universidad Modelo)
para presentar hoy al Dr. Rodrigo Daniel Solís Ortega:
  - Justificación técnico-financiera de sustitución parcial de BNO085 (sobrecosto +163% / desabasto).
  - Explicación de cómo se superó la limitación de CPU de PC3 para correr fusión Madgwick a 100 Hz.
  - Tabla de cumplimiento real (qué cumple y qué cambia con MPU-6050 vs. BMI160/MPU-9250).
  - Propuesta formal de Arquitectura Híbrida para aval del PC5.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

NAVY = RGBColor(0x10, 0x2A, 0x43)
BLUE = RGBColor(0x1F, 0x4E, 0x79)
DARK = RGBColor(0x1E, 0x29, 0x3B)


def shade(cell, hex_c):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_c}"/>'))


def add_sec(doc, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title)
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.color.rgb = BLUE


def add_p(doc, text, bold_pre=None, size=9.2):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.08
    if bold_pre:
        rb = p.add_run(bold_pre)
        rb.bold = True
        rb.font.name = "Calibri"
        rb.font.size = Pt(size)
        rb.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(size)
    r.font.color.rgb = DARK


def add_tbl(doc, headers, rows, widths):
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        c = tbl.rows[0].cells[j]
        shade(c, "102A43")
        c.width = Inches(widths[j])
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(1.5)
        p.paragraph_format.space_after = Pt(1.5)
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Calibri"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for i, rdata in enumerate(rows):
        bg = "F8FAFC" if i % 2 else "FFFFFF"
        for j, val in enumerate(rdata):
            c = tbl.rows[i + 1].cells[j]
            shade(c, bg)
            c.width = Inches(widths[j])
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.05
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(8.2)
            if j == 0:
                r.bold = True
                r.font.color.rgb = NAVY


def build_memo(out_path):
    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(0.45)
        s.bottom_margin = Inches(0.45)
        s.left_margin = Inches(0.6)
        s.right_margin = Inches(0.6)

    # Encabezado institucional compacto
    hdr = doc.add_table(rows=1, cols=1)
    hdr.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = hdr.cell(0, 0)
    shade(cell, "102A43")
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run("UNIVERSIDAD MODELO • ESCUELA DE INGENIERÍA • PROYECTOS VII (AD26)\n")
    r1.bold = True; r1.font.name = "Calibri"; r1.font.size = Pt(10); r1.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
    r2 = p.add_run("NOTA TÉCNICA DE EQUIVALENCIA SENSORIAL Y VALIDACIÓN DE ARQUITECTURA HÍBRIDA (PC4 → PC5)")
    r2.bold = True; r2.font.name = "Calibri"; r2.font.size = Pt(11.5); r2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(4)
    p_meta.paragraph_format.space_after = Pt(3)
    for k, v in [
        ("Proyecto: ", "Proyecto 10 — KNTX (1 pierna: 3 nodos satélite + Gateway espalda baja)   |   "),
        ("Fecha: ", "24 de noviembre de 2026\n"),
        ("Equipo: ", "Yael Alejandro Yah Hernández & Jorge Carlos Contreras Rodríguez   |   "),
        ("Para: ", "Dr. Rodrigo Daniel Solís Ortega"),
    ]:
        rk = p_meta.add_run(k); rk.bold = True; rk.font.name = "Calibri"; rk.font.size = Pt(8.8); rk.font.color.rgb = NAVY
        rv = p_meta.add_run(v); rv.font.name = "Calibri"; rv.font.size = Pt(8.8); rv.font.color.rgb = DARK

    # 1. Contexto y justificación económica
    add_sec(doc, "1. Justificación Técnico-Financiera de Sustitución Parcial de Sensores (Cadena de Suministro)")
    add_p(
        doc,
        "En el PC2/PC3 se cotizó el sensor BNO085 en $380 MXN/unidad para equipar 3 nodos satélite + 1 referencia lumbar. "
        "Al ejecutar la compra final en noviembre de 2026, el BNO085 original presenta desabasto local en Mérida, tiempos de "
        "importación incompatibles con el cierre del semestre (1 de diciembre) y un incremento de precio hasta ~$1,000 MXN por "
        "pieza (+163% de sobrecosto, elevando 3 módulos faltantes a ~$3,000 MXN). Dado que ya contamos con 1 BNO085 operativo "
        "(validado en SPI a 3 MHz) y 2 ESP32-C3 adicionales disponibles localmente, se propone adoptar una Arquitectura Sensorial "
        "Híbrida: conservar el BNO085 en la Tibia (nodo crítico de impacto > 3.0 g y referencia metrológica SPI) y emplear sensores "
        "disponibles en Mérida/entrega 24 h en los 3 nodos restantes (Fémur, Pie y Lumbar)."
    )

    # 2. Cómo se superó el cuello de botella de CPU de PC3
    add_sec(doc, "2. ¿Cómo se logró ejecutar Fusión Madgwick a 100 Hz sin colapsar el microcontrolador?")
    add_p(
        doc,
        "En PC3 (Anexo A, Decisión 1 v1) se descartó inicialmente la fusión por software porque saturó el CPU y provocó "
        "pérdida de paquetes ESP-NOW. Durante la implementación real en banco del PC4 identificamos que el cuello de botella no era "
        "la capacidad de cómputo del procesador (ESP32-C3 RISC-V 160 MHz / ESP32 240 MHz), sino la arquitectura bloqueante "
        "(impresión Serial por paquete a 115,200 bps, polling SPI continuo sin pin INT y uso de delay()). Al corregir estos cuatro "
        "factores —temporización no bloqueante con esp_timer_get_time() (1 µs), filtro Madgwick 6-DOF compacto (~120 µs por ciclo, "
        "solo 1.2% del CPU de la ventana de 10 ms), diagnósticos a 0.5 Hz, lectura SPI por interrupción INT (bajó de 8.99 ms a 1.39 ms) "
        "y telemetría Gateway a 921,600 bps con cola dedicada g_csvQueue— el sistema alcanzó en pruebas reales de 60 s: Nodo 1 "
        "(BNO085) = 99.94 Hz (P95 jitter = 1.0 ms, deriva = 0.021 °/min) y Nodo 2 (MPU-6050 + Madgwick) = 100.21 Hz (P95 jitter = "
        "0.0 ms, deriva = 0.977 °/min), ambos con 0 overflows y cruce continuo por 90° (hasta 136.4°) sin Gimbal Lock."
    )

    # 3. Comparativa de sensores alternativos disponibles en Mérida
    add_sec(doc, "3. Evaluación de Alternativas Disponibles (Mérida / Envío 24 h) y Matriz de Cumplimiento PC2")
    add_tbl(
        doc,
        ["Alternativa (3 pzas faltantes)", "Bus", "Costo est. (MXN)", "Cumplimiento frente a requisitos PC2", "Recomendación"],
        [
            ["Opción A (Preferida):\nBMI160 / MPU-9250 (6500)\n(Av. 60 Norte / ML Full 24h)", "SPI 3 MHz\ne I2C", "$110–$220 c/u\n(~$450–$660 total)",
             "CUMPLE 100% incluyendo bus SPI a 3 MHz (RP-04/RQ-01), rango ±16 g, bajo ruido y 100 Hz con Madgwick en ESP32-C3. Sin cambios al diseño SPI.",
             "MEJOR OPCIÓN\n(si hay stock hoy/mañana)"],
            ["Opción B (Respaldo inmediato):\nMPU-6050 (GY-521)\n(Ya tenemos 2; stock Mérida)", "Solo I2C\n400 kHz", "$50–$70 c/u\n(~$100–$140 total)",
             "CUMPLE 100 Hz (100.21 Hz medidos), jitter 0.0 ms, deriva 0.977 °/min (< 3 °/min), cuaterniones sin Gimbal Lock y trama idéntica de 36 B.\nNO CUMPLE: bus SPI (usa I2C local < 5 cm, 0.45 ms/lectura) ni magnetómetro (que igual se desactiva en caminadora).",
             "VIABLE 100%\n(avalado en prueba real de 60 s)"],
            ["Referencia original:\nBNO085 adicional (3 pzas)", "SPI 3 MHz", "~$1,000 c/u\n(~$3,000 total)",
             "Cumple todos los requisitos pero excede el presupuesto (+163%) y tiempos de entrega impiden completar validación dinámica PC5 (1 dic).",
             "DESESTIMADO\n(conservar 1 pza en Tibia)"],
        ],
        [1.75, 0.65, 1.0, 2.75, 1.15],
    )

    # 4. Acuerdo solicitado hoy al docente
    add_sec(doc, "4. Propuesta Concreta para Aprobación del Prototipo Final (PC5 — 1 de Diciembre)")
    add_p(
        doc,
        "1) Conservar el BNO085 en el Nodo 1 (Tibia) para garantizar detección de contacto inicial (> 3.0 g) y validación metrológica "
        "del bus SPI a 3 MHz (1.39 ms <= 1.5 ms).  "
        "2) Equipar los nodos Fémur, Pie y Lumbar con BMI160/MPU-9250 (preferente por soporte SPI) o MPU-6050 (ya validado hoy a "
        "100.21 Hz y 0.977 °/min de deriva), emitiendo todos exactamente la misma trama binaria KNTX (36 bytes) vía ESP-NOW hacia "
        "el Gateway ESP32-S3.  "
        "3) Consolidar los módulos con pines sobre placas preperforadas soldadas compactas dentro de las carcasas 3D PETG (32.9 cm³ < 40 cm³) "
        "y documentar formalmente el análisis de mercado y equivalencia en el Expediente de Desviaciones y Cierre Presupuestal del PC5.",
        size=8.9,
    )

    # Línea de visto bueno
    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.space_before = Pt(6)
    p_sig.paragraph_format.space_after = Pt(0)
    r_sig = p_sig.add_run(
        "Evidencia en vivo disponible en repositorio público: https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU  |  "
        "Dashboard HMI Python y 12,016 muestras reales verificadas en banco."
    )
    r_sig.italic = True; r_sig.font.name = "Calibri"; r_sig.font.size = Pt(8.2); r_sig.font.color.rgb = BLUE

    doc.save(out_path)
    print("[OK] Nota tecnica generada:", out_path)


if __name__ == "__main__":
    out = r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU\docs\reportes\Nota_Tecnica_Cambio_Sensores_KNTX.docx"
    build_memo(out)
