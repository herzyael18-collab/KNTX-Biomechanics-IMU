#!/usr/bin/env python3
"""
build_sensor_change_memo.py
Nota Técnica Ejecutiva de 1 página exacta (Universidad Modelo) para aval docente del cambio
a Arquitectura Sensorial Híbrida: 1 BNO085 (Tibia) + 3 BMI160 Bosch (Fémur, Pie y Lumbar).
"""

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
    p.paragraph_format.space_before = Pt(5.5)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title)
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(10.2)
    r.font.color.rgb = BLUE


def add_p(doc, text, bold_pre=None, size=8.9):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.07
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
        r.font.size = Pt(8.3)
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
            p.paragraph_format.line_spacing = 1.04
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(8.0)
            if j == 0:
                r.bold = True
                r.font.color.rgb = NAVY


def build_memo(out_path):
    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(0.42)
        s.bottom_margin = Inches(0.42)
        s.left_margin = Inches(0.58)
        s.right_margin = Inches(0.58)

    # Encabezado institucional
    hdr = doc.add_table(rows=1, cols=1)
    hdr.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = hdr.cell(0, 0)
    shade(cell, "102A43")
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run("UNIVERSIDAD MODELO • ESCUELA DE INGENIERÍA • PROYECTOS VII (AD26)\n")
    r1.bold = True; r1.font.name = "Calibri"; r1.font.size = Pt(9.5); r1.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
    r2 = p.add_run("NOTA TÉCNICA: ADOPCIÓN DE SENSOR BOSCH BMI160 EN ARQUITECTURA HÍBRIDA KNTX (PC4 → PC5)")
    r2.bold = True; r2.font.name = "Calibri"; r2.font.size = Pt(11); r2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(3.5)
    p_meta.paragraph_format.space_after = Pt(2.5)
    for k, v in [
        ("Proyecto: ", "Proyecto 10 — KNTX (1 pierna: 3 nodos satélite + Gateway espalda baja)   |   "),
        ("Fecha: ", "24 de noviembre de 2026\n"),
        ("Equipo: ", "Yael Alejandro Yah Hernández & Jorge Carlos Contreras Rodríguez   |   "),
        ("Docente: ", "Dr. Rodrigo Daniel Solís Ortega"),
    ]:
        rk = p_meta.add_run(k); rk.bold = True; rk.font.name = "Calibri"; rk.font.size = Pt(8.6); rk.font.color.rgb = NAVY
        rv = p_meta.add_run(v); rv.font.name = "Calibri"; rv.font.size = Pt(8.6); rv.font.color.rgb = DARK

    # 1. Decisión y contexto de mercado
    add_sec(doc, "1. Decisión de Ingeniería y Justificación de Mercado (Sustitución Parcial del BNO085 por Bosch BMI160)")
    add_p(
        doc,
        "En PC2/PC3 se presupuestó el BNO085 en $380 MXN/unidad; sin embargo, al adquirir los 3 sensores restantes en noviembre "
        "de 2026 el BNO085 original presenta desabasto local en Mérida, tiempos de importación incompatibles con el cierre del "
        "1 de diciembre y un incremento hasta ~$1,000 MXN/pza (+163%, ~$3,000 MXN extra). Por ello, conservamos nuestro BNO085 "
        "físico en el Nodo 1 (Tibia, segmento de impacto > 3.0 g) y seleccionamos el sensor Bosch BMI160 ($74.25 MXN/pza con "
        "entrega Full en 24 h a Mérida; $223 MXN por 3 piezas = 92% de ahorro) para equipar Fémur, Pie y Lumbar."
    )

    # 2. Por qué BMI160 y por qué descartamos el magnetómetro
    add_sec(doc, "2. ¿Por qué Bosch BMI160 y por qué se descarta el Magnetómetro (6-DOF vs. 9-DOF)?")
    add_p(
        doc,
        "A diferencia del MPU-6050 (solo I2C) o del MPU-9250 (descontinuado/EOL, $360–$433 MXN y con clones frecuentes), el "
        "BMI160 pertenece a la misma línea Bosch Sensortec de grado wearable que el BNO085: incorpora bus SPI nativo hasta 10 MHz "
        "(preservando íntegros RP-04 y RQ-01 a 3 MHz con pistas < 10 cm y lectura <= 1.5 ms), acelerómetro hasta ±16 g (apto para "
        "impactos de carrera), bajo ruido de giroscopio y consumo ultrabajo (~0.9 mA, favoreciendo autonomía > 3 h de RP-08).",
        bold_pre="Ventaja técnica del BMI160: "
    )
    add_p(
        doc,
        "El BMI160 es una IMU de 6-DOF (sin magnetómetro), decisión respaldada directamente por la bibliografía del PC2 "
        "(Ceriola et al., 2026) y la Decisión 2 del PC3: durante la validación dinámica en caminadora (PV-08), el motor eléctrico "
        "y el chasis metálico generan distorsiones ferromagnéticas que provocan errores de yaw > 30° en magnetómetros. Por esta "
        "razón, incluso el BNO085 se opera obligatoriamente sin magnetómetro (modo Game Rotation Vector, criterio RP-03 < 3 °/min). "
        "En consecuencia, eliminar el magnetómetro evita corrupción magnética, reduce costo y simplifica la calibración previa.",
        bold_pre="Justificación de descarte del magnetómetro: "
    )

    # 3. Cómo se superó la limitación de CPU del PC3
    add_sec(doc, "3. ¿Cómo logramos Fusión Madgwick en CPU a 100 Hz sin colapsar el ESP32-C3 (Logro Real PC4)?")
    add_p(
        doc,
        "En el PC3 (Decisión 1 v1) la fusión por software falló al saturar la CPU y perder paquetes ESP-NOW. En las pruebas "
        "físicas de laboratorio del PC4 comprobamos que el cuello de botella no era la potencia del MCU (ESP32-C3 RISC-V 160 MHz), "
        "sino bloqueos de software (Serial a 115,200 bps por paquete, polling SPI sin pin INT y delay()). Tras optimizar el "
        "firmware —temporización con esp_timer_get_time() (1 µs), Madgwick 6-DOF compacto (~120 µs/ciclo = 1.2% de la ventana de "
        "10 ms), lectura SPI por pin INT (reducción de 8.99 ms a 1.39 ms) y Gateway Dual-Core a 921,600 bps con cola g_csvQueue— "
        "validamos en corrida continua de 60 s (12,016 muestras): Nodo 1 (BNO085) = 99.94 Hz (P95 jitter = 1.0 ms, deriva = "
        "0.021 °/min) y Nodo 2 (MPU-6050 + Madgwick) = 100.21 Hz (P95 jitter = 0.0 ms, deriva = 0.977 °/min), 0 overflows y cruce "
        "continuo por 90° (hasta 136.4°) sin Gimbal Lock."
    )

    # 4. Tabla comparativa
    add_sec(doc, "4. Matriz Comparativa de Opciones Evaluadas y Cumplimiento de Requisitos PC2")
    add_tbl(
        doc,
        ["Sensor Evaluado", "Bus / DOF", "Precio (3 pzas)", "Cumplimiento frente a requisitos PC2", "Dictamen"],
        [
            ["Bosch BMI160\n(ML Full — 24 h)", "SPI 3 MHz\n6-DOF", "$223 MXN\n($74.25 c/u)",
             "CUMPLE 100%: SPI 3 MHz (RP-04/RQ-01), ±16 g, 100 Hz + Madgwick en ESP32-C3, deriva < 3 °/min, consumo 0.9 mA (>3 h), inmune a perturbación magnética en caminadora.",
             "SELECCIONADO\n(Fémur, Pie, Lumbar)"],
            ["MPU-9250 / 6500\n(EOL / genérico)", "SPI / I2C\n9-DOF*", "$1,077–$1,298\n($359–$433 c/u)",
             "Descontinuado (EOL), costo 5× mayor al BMI160, alto riesgo de clones sin magnetómetro real y mayor ruido/consumo.",
             "DESCARTADO\n(Costo / EOL)"],
            ["MPU-6050 (GY-521)\n(Respaldo actual)", "Solo I2C\n6-DOF", "$100–$140\n(ya tenemos 2)",
             "Validado hoy a 100.21 Hz, jitter 0.0 ms y deriva 0.977 °/min; NO tiene bus SPI (usa I2C local < 5 cm). Se conserva como respaldo.",
             "RESPALDO\n(Validado en PC4)"],
            ["BNO085 adicional\n(Importación)", "SPI 3 MHz\n9-DOF", "~$3,000 MXN\n(~$1,000 c/u)",
             "Sobrecosto +163% y entrega tardía fuera del calendario del 1 de dic. Se conserva la pieza física ya operativa en Tibia (Nodo 1).",
             "CONSERVAR 1 PZA\nEN TIBIA (NODO 1)"],
        ],
        [1.45, 0.72, 0.95, 2.93, 1.25],
    )

    # 5. Plan cerrado PC5
    add_sec(doc, "5. Configuración Final Propuesta para Aprobación (PC5 y Expotrónica — 1 de Diciembre)")
    add_p(
        doc,
        "• Arquitectura Híbrida Homogénea en Protocolo: 1× ESP32-C3 + BNO085 (Tibia, SPI 3 MHz) + 2× ESP32-C3 + BMI160 "
        "(Fémur y Pie, SPI 3 MHz, Madgwick 6-DOF) + 1× Gateway ESP32-S3 + BMI160 (Espalda baja), transmitiendo todos la "
        "misma trama KNTX de 36 bytes a 100 Hz vía ESP-NOW.  • Ensamble final en placas preperforadas soldadas compactas dentro "
        "de carcasas PETG (< 40 cm³, IP54) y registro formal en el Expediente de Desviaciones y Cierre Presupuestal del PC5.",
        size=8.6,
    )

    p_f = doc.add_paragraph()
    p_f.paragraph_format.space_before = Pt(4)
    p_f.paragraph_format.space_after = Pt(0)
    rf = p_f.add_run(
        "Repositorio público auditado y evidencias reales (12,016 muestras + Dashboard HMI Python): "
        "https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU"
    )
    rf.italic = True; rf.font.name = "Calibri"; rf.font.size = Pt(8.1); rf.font.color.rgb = BLUE

    doc.save(out_path)
    print("[OK] Nota tecnica BMI160 generada:", out_path)


if __name__ == "__main__":
    build_memo(r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU\docs\reportes\Nota_Tecnica_Cambio_Sensores_KNTX.docx")
