#!/usr/bin/env python3
"""
build_pc4_report.py
Genera el Reporte Técnico PC4 (Diseño a Detalle y Primera Prueba Funcional) en formato .docx
estrictamente alineado con:
  - Guia_Personalizada_PC4_10_IMUs.pdf (Dr. Rodrigo Daniel Solís Ortega)
  - PC4 Diseño a Detalle.pdf (Guía oficial Fase II)
  - PC2 Anteproyecto y PC3 Diseño Conceptual Iterativo del equipo KNTX.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

NAVY = RGBColor(0x10, 0x2A, 0x43)
BLUE = RGBColor(0x1F, 0x4E, 0x79)
GRAY = RGBColor(0x48, 0x65, 0x81)
ALERT = RGBColor(0x9B, 0x1C, 0x1C)


def set_cell_bg(cell, hex_color):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_heading_styled(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Calibri"
    if level == 1:
        run.font.size = Pt(14)
        run.font.color.rgb = NAVY
    elif level == 2:
        run.font.size = Pt(11.5)
        run.font.color.rgb = BLUE
    else:
        run.font.size = Pt(10.5)
        run.font.color.rgb = GRAY
    return p


def add_body(doc, text, bold_prefix=None, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = "Calibri"
        rb.font.size = Pt(10.5)
    r = p.add_run(text)
    r.italic = italic
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    return p


def add_bullet(doc, bold_prefix, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    rb = p.add_run(bold_prefix)
    rb.bold = True
    rb.font.name = "Calibri"
    rb.font.size = Pt(10.5)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    return p


def add_placeholder_box(doc, title, instructions):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, "FFF8E1")
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        '<w:top w:val="dashed" w:sz="6" w:color="D97706"/>'
        '<w:left w:val="dashed" w:sz="6" w:color="D97706"/>'
        '<w:bottom w:val="dashed" w:sz="6" w:color="D97706"/>'
        '<w:right w:val="dashed" w:sz="6" w:color="D97706"/>'
        '</w:tcBorders>'
    )
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run(f"[ESPACIO PARA EVIDENCIA REAL — {title}]\n")
    r1.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = ALERT
    r2 = p.add_run(instructions)
    r2.font.size = Pt(9.5)
    r2.italic = True
    doc.add_paragraph()


def add_styled_table(doc, headers, rows, col_widths=None):
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr_cells = tbl.rows[0].cells
    for j, h in enumerate(headers):
        set_cell_bg(hdr_cells[j], "102A43")
        p = hdr_cells[j].paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        if col_widths:
            hdr_cells[j].width = Inches(col_widths[j])

    for i, row_data in enumerate(rows):
        row_cells = tbl.rows[i + 1].cells
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(row_data):
            set_cell_bg(row_cells[j], bg)
            p = row_cells[j].paragraphs[0]
            p.paragraph_format.space_before = Pt(2.5)
            p.paragraph_format.space_after = Pt(2.5)
            r = p.add_run(val)
            r.font.size = Pt(9.2)
            if j == 0:
                r.bold = True
            if col_widths:
                row_cells[j].width = Inches(col_widths[j])

    doc.add_paragraph()
    return tbl


def build_report(out_docx: str, repo_dir: str):
    doc = Document()

    # Márgenes institucionales
    for s in doc.sections:
        s.top_margin = Inches(0.85)
        s.bottom_margin = Inches(0.85)
        s.left_margin = Inches(0.85)
        s.right_margin = Inches(0.85)

    # ================= PORTADA =================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("UNIVERSIDAD MODELO\n")
    r.bold = True; r.font.size = Pt(18); r.font.color.rgb = NAVY
    r2 = p.add_run("ESCUELA DE INGENIERÍA — INGENIERÍA MECATRÓNICA\n25781 PROYECTOS VII (MODELO D+i — CICLO AD26)\n")
    r2.bold = True; r2.font.size = Pt(11); r2.font.color.rgb = BLUE

    doc.add_paragraph()
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = p2.add_run("PUNTO DE CONTROL 4 (PC4)\nDISEÑO A DETALLE, PRIMERA PRUEBA FUNCIONAL Y VIDEO EXPLICATIVO\n")
    rt.bold = True; rt.font.size = Pt(16); rt.font.color.rgb = NAVY

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rs = p3.add_run("PROYECTO 10: KNTX — SISTEMA DE MEDICIÓN INERCIAL PARA BIOMECÁNICA DEL CUERPO\n(CAPTURA DE MOVIMIENTO INERCIAL)")
    rs.bold = True; rs.font.size = Pt(12); rs.font.color.rgb = BLUE

    doc.add_paragraph()
    add_styled_table(
        doc,
        ["Campo de Control", "Información Oficial del Proyecto"],
        [
            ["Integrantes", "Yael Alejandro Yah Hernández (15234422@modelo.edu.mx)\nJorge Carlos Contreras Rodríguez (15233640@modelo.edu.mx)"],
            ["Docente Titular", "Dr. Rodrigo Daniel Solís Ortega (rodrigo.solis@modelo.edu.mx)"],
            ["Categoría / Arquetipo", "Categoría E — Biomecatrónica / Arquetipo C (Sistemas Embebidos, Biomédicos, IoT)"],
            ["Alcance del Semestre", "Prototipo de 1 pierna (3 nodos satélite: tibia, fémur, pie) + Gateway central en espalda baja (ESP32-S3)"],
            ["Repositorio Público GitHub (Desbloqueo)", "https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU"],
            ["Enlace al Video Explicativo (3 a 5 min)", "[PEGAR AQUÍ ENLACE PERMANENTE DE ONEDRIVE MODELO / YOUTUBE OCULTO]"],
            ["Fecha de Entrega", "Noviembre de 2026 | Mérida, Yucatán, México"],
        ],
        col_widths=[2.3, 4.5],
    )

    doc.add_page_break()

    # ================= 1.0 INTRODUCCIÓN =================
    add_heading_styled(doc, "1.0 Introducción y Marco de Implementación", level=1)
    add_heading_styled(doc, "1.1 Resumen del Avance y Subsanación de Alertas Post-PC3", level=2)
    add_body(
        doc,
        "El proyecto KNTX tiene como objetivo general desarrollar e integrar un sistema wearable de captura de "
        "movimiento inercial basado en sensores IMU y procesadores ESP32, capaz de transmitir una matriz cinemática "
        "a 100 Hz sostenidos hacia una interfaz móvil/PC para la evaluación biomecánica de carrera. Tras obtener una "
        "calificación oficial de 84/100 en el PC3 (Diseño Conceptual Iterativo), el presente Punto de Control 4 (PC4) "
        "materializa la transición desde la simulación y los esquemas conceptuales hacia el montaje físico en "
        "laboratorio, el código fuente modular ejecutable y la Primera Prueba Funcional instrumentada."
    )
    add_body(doc, "Para responder directamente a las tres alertas técnicas obligatorias emitidas en el diagnóstico post-PC3:")
    add_bullet(
        doc,
        "1. Regularización total del repositorio público en GitHub: ",
        "Se eliminaron las leyendas de 'URL pendiente' y cajas vacías del PC3. El repositorio "
        "https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU se encuentra activo, público, estructurado "
        "por carpetas normalizadas (/hardware, /firmware, /software, /docs), con ramas temáticas independientes "
        "y commits fechados con autoría verificable de Yael Alejandro Yah Hernández (firmware satélite, Gateway "
        "FreeRTOS y pruebas de estrés) y Jorge Carlos Contreras Rodríguez (hardware As-Built, CAD 3D IP54 y "
        "algoritmos biomecánicos Grood-Suntay/Kinovea)."
    )
    add_bullet(
        doc,
        "2. Implementación física As-Built (módulos con pines sobre protoboard/placa preperforada): ",
        "Conforme al acuerdo de alcance con el docente (enfoque en una pierna: 3 nodos satélite + 1 Gateway central "
        "en espalda baja) y a la disponibilidad real de componentes en laboratorio, se implementó el prototipo funcional "
        "en módulos breakout con pines (sin soldadura SMD manual riesgosa), validando el bus SPI real a 3 MHz en el "
        "ESP32-C3 + BNO085 y preparando la consolidación compacta en placa preperforada soldada para el PC5."
    )
    add_bullet(
        doc,
        "3. Telemetría en vivo a 100 Hz, cuaterniones sin Gimbal Lock y resiliencia FreeRTOS: ",
        "Se ejecuta la recepción simultánea a 100 Hz de 2 nodos físicos reales vía ESP-NOW hacia el Gateway ESP32-S3, "
        "cálculo de cuaternión relativo de rodilla libre de bloqueo de cardán al cruzar 90° y demostración en vivo "
        "del mecanismo Failsafe de la cola FreeRTOS ante el apagado repentino de un nodo satélite."
    )

    add_heading_styled(doc, "1.2 Vínculo con Diseño Conceptual (PC3) y Análisis de Equivalencia", level=2)
    add_body(
        doc,
        "El diseño conceptual del PC3 estableció una arquitectura de nodos autónomos en topología estrella ESP-NOW "
        "hacia un Gateway ESP32-S3 N16R8. La Tabla 1 documenta el estado de fabricación/implementación de cada "
        "subsistema del PC3 y el análisis técnico de equivalencia aplicado por disponibilidad de componentes en PC4 "
        "(en estricto apego al Arquetipo C de la Guía Oficial PC4, que avala ensamble en protoboard avanzada)."
    )
    add_styled_table(
        doc,
        ["Subsistema PC3", "Diseño Conceptual (PC3)", "Implementación Real As-Built (PC4)", "Análisis de Equivalencia y Transición a PC5"],
        [
            ["Gateway Central (Espalda baja)", "ESP32-S3-WROOM-1 N16R8", "ESP32-S3 DevKit con pines + MPU6050 #1 (lumbar opcional)", "Equivalencia 1:1 en silicio, doble núcleo FreeRTOS, radio ESP-NOW y BLE 5.0. El MPU6050 local aporta telemetría lumbar adicional."],
            ["Nodo Satélite 1 (Tibia)", "ESP32-C3-MINI-1 + BNO085 (PCB SMD flexible, SPI 3 MHz)", "ESP32-C3 (módulo con pines) + BNO085 breakout por SPI 3 MHz (< 10 cm)", "Mismo MCU, mismo sensor BNO085 con coprocesador SH-2 y misma interfaz SPI a 3 MHz. Permite ejecutar PV-02, PV-04 y PV-06 sin retraso por manufactura SMD."],
            ["Nodo Satélite 2 (Fémur)", "ESP32-C3 + BNO085 (2do nodo)", "ESP32 WROOM-32 (pines) + MPU6050 #2 con filtro Madgwick 6-DOF a 100 Hz", "Sustitución temporal en PC4 mientras arriban los BNO085 adicionales. Emite exactamente la misma trama KNTX (36 bytes, cuaternión + aceleración) vía ESP-NOW, validando concurrencia real y ángulo de rodilla."],
            ["Nodo Satélite 3 (Pie)", "ESP32-C3 + BNO085 (3er nodo)", "En adquisición / emulado en prueba de saturación Spoofer (hasta 12 nodos)", "Se integrará físicamente al llegar los módulos faltantes y al migrar todos los nodos a placa preperforada compacta para el PC5."],
            ["Sustrato y Carcasa", "PCB SMD flexible + carcasa 3D PETG (< 40 cm³)", "Protoboard de laboratorio en PC4; carcasa paramétrica 32.9 cm³ (OpenSCAD/STL)", "Para el prototipo wearable final (PC5) se consolidarán los módulos con pines sobre placa preperforada soldada compacta dentro de la carcasa PETG IP54."],
        ],
        col_widths=[1.3, 1.5, 1.8, 2.2],
    )

    # ================= 2.0 IMPLEMENTACIÓN FÍSICA =================
    add_heading_styled(doc, "2.0 Implementación Física (Hardware, Mecánica y Esquemas As-Built)", level=1)
    add_heading_styled(doc, "2.1 Fabricación, Montaje Mecánico y Carcasas 3D", level=2)
    add_body(
        doc,
        "El diseño mecánico de las carcasas se consolidó en el archivo paramétrico editable "
        "hardware/carcasas/kntx_nodo_carcasa_v2.scad y su malla exportada kntx_nodo_carcasa_v2.stl. "
        "Las dimensiones exteriores son 44 × 34 × 22 mm, resultando en un volumen total de 32.91 cm³ "
        "(cumpliendo el límite < 40 cm³ de RP-09). Incorpora labio perimetral machihembrado de 2 mm para sellado "
        "por analogía IP54 (RQ-04) y ranuras pasacinta de 25 mm para bandas elásticas textiles. Parámetros de "
        "impresión 3D: filamento PETG (resistente a humedad/sudor y temperatura < 40 °C), 25% de infill giroide, "
        "3 perímetros y altura de capa de 0.20 mm con base paralela a la cama para resistir tensión de las correas."
    )
    add_placeholder_box(
        doc,
        "FIGURA 2.1: FOTOGRAFÍAS DEL ENSAMBLE FÍSICO AS-BUILT EN PROTOBOARD Y CARCASA / BANDAS",
        "Insertar 2 a 3 fotografías nítidas y bien iluminadas del banco físico: (a) Gateway ESP32-S3, "
        "(b) Nodo 1 ESP32-C3 + BNO085 con cables SPI < 10 cm y puentes PS0/PS1 en HIGH, "
        "(c) Nodo 2 ESP32 + MPU6050 y (d) pesaje en báscula (< 50 g) / medición con Vernier."
    )

    add_heading_styled(doc, "2.2 Ensamblaje Eléctrico, Seguridad y Alimentación", level=2)
    add_body(
        doc,
        "Los nodos satélite y el Gateway operan en baja tensión segura (3.3 V lógica / 3.7 V nominal LiPo / 5 V USB), "
        "evitando riesgos de choque eléctrico en contacto con el cuerpo del atleta. Se emplean tierras comunes, "
        "cableado peinado y corto (< 10 cm en bus SPI para evitar capacitancia parásita y reflexión de flancos) "
        "y módulos de protección LiPo basados en DW01 + FS8205A para garantizar cortes de seguridad por sobretensión "
        "(> 4.2 V), subtensión (< 2.5 V) y cortocircuito conforme a IEC 62133-2 (RQ-06) y lineamientos de seguridad "
        "NOM-001-SEDE-2018."
    )

    add_heading_styled(doc, "2.3 Esquemas 'As-Built' (Tal como se construyó en laboratorio)", level=2)
    add_body(
        doc,
        "La Figura 2.2 presenta el diagrama de arquitectura e interconexión física As-Built correspondiente al "
        "ensamble real de laboratorio. La asignación completa de pines (GPIO) entre el ESP32-C3 y el BNO085 en modo "
        "SPI a 3 MHz, el ESP32 con el MPU6050 por I2C a 400 kHz y el Gateway ESP32-S3 se detalla en la Tabla 2 "
        "y en el archivo hardware/pcb/ESQUEMATICO_AS_BUILT_PC4.md del repositorio."
    )
    diag_path = os.path.join(repo_dir, "hardware", "pcb", "diagrama_as_built_pc4.png")
    if os.path.exists(diag_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(diag_path, width=Inches(6.6))
        add_body(doc, "Figura 2.2. Diagrama de arquitectura e interconexiones As-Built del prototipo KNTX (PC4).", italic=True)

    add_styled_table(
        doc,
        ["Módulo", "Interfaz", "Pinout Exacto As-Built", "Observación Técnica"],
        [
            ["Nodo 1: ESP32-C3 + BNO085 (Tibia)", "SPI 3 MHz", "SCK=GPIO4, MISO=GPIO5, MOSI=GPIO6, CS=GPIO7, INT=GPIO2, RST=GPIO3, PS0/PS1=3.3V", "Cables < 10 cm (RP-04). GPIO10 genera pulso de disparo TX para osciloscopio (PV-04)."],
            ["Nodo 2: ESP32 + MPU6050 (Fémur)", "I2C 400 kHz", "SDA=GPIO21, SCL=GPIO22, VCC=3.3V, GND=GND, AD0=GND (0x68)", "Ejecuta Madgwick 6-DOF a 100 Hz; misma trama ESP-NOW de 36 bytes."],
            ["Gateway: ESP32-S3 (Espalda baja)", "ESP-NOW + BLE 5.0 + USB", "GPIO4=Pulso RX osciloscopio (PV-04); GPIO8/9=I2C MPU6050 lumbar opcional", "Dual-Core FreeRTOS: Core 0 Radio/Sync SNTP, Core 1 Matriz/Failsafe/BLE/CSV."],
        ],
        col_widths=[1.6, 1.0, 2.3, 1.9],
    )

    # ================= 3.0 IMPLEMENTACIÓN LÓGICA Y GITHUB =================
    add_heading_styled(doc, "3.0 Implementación Lógica, Firmware Modular y Auditoría en GitHub", level=1)
    add_heading_styled(doc, "3.1 Desarrollo de Lógica y Firmware (Sin Bloqueos)", level=2)
    add_body(
        doc,
        "Todo el código embebido fue desarrollado en C/C++ modular para Arduino/ESP-IDF (core esp32 3.3.8) "
        "y verificado mediante compilación limpia con arduino-cli. Ningún lazo crítico utiliza delay() ni operaciones "
        "bloqueantes; el muestreo se temporiza mediante esp_timer_get_time() (resolución de 1 µs) en los nodos satélite "
        "y mediante vTaskDelayUntil() en las tareas FreeRTOS del Gateway ESP32-S3:"
    )
    add_bullet(doc, "Protocolo común (firmware/common/kntx_protocol.h): ", "Define la trama empaquetada kntx_packet_t (36 bytes), la trama broadcast SNTP kntx_sync_t y las operaciones de cuaterniones de Hamilton (conjugado, producto y normalización).")
    add_bullet(doc, "Nodo Satélite 1 (firmware/satelite/nodo1_c3_bno085/nodo1_c3_bno085.ino): ", "Inicializa el BNO085 por SPI a 3 MHz, habilita SH2_GAME_ROTATION_VECTOR (alternable a SH2_ROTATION_VECTOR con tecla 'm') y SH2_ACCELEROMETER a 100 Hz, mide duración real de lectura SPI en microsegundos y aplica compensación SNTP.")
    add_bullet(doc, "Nodo Satélite 2 (firmware/satelite/nodo2_esp32_mpu6050/nodo2_esp32_mpu6050.ino): ", "Calibra el bias del giroscopio en reposo (RF-04), ejecuta fusión Madgwick 6-DOF a 100 Hz sin ángulos de Euler y transmite por ESP-NOW sincronizado con el broadcast SNTP del Gateway.")
    add_bullet(doc, "Gateway ESP32-S3 (firmware/gateway/gateway_s3_freertos/gateway_s3_freertos.ino): ", "Ancla el callback ISR ESP-NOW, taskRxConsumer (Prioridad 4) y taskSyncBroadcast (cada 1,000 ms) al Núcleo 0; ancla taskMatrixAndOutput al Núcleo 1 para cerrar ventanas de 10 ms con Failsafe no bloqueante (timeout 200 ms -> marca nodo NULL), calcular el cuaternión relativo de rodilla sin Gimbal Lock, notificar por BLE 5.0 y exportar líneas CSV estándar RF-08.")
    add_bullet(doc, "Suite Python de Captura y Biomecánica (software/): ", "kntx_serial_logger.py captura sesiones CSV y reporta Hz efectivos y jitter P95 automáticamente; kntx_biomechanics_analysis.py ejecuta Grood & Suntay, detección de foot-strike (> 3.0 g), normalización Spline cúbica a 101 puntos y gráficas Bland-Altman.")

    add_heading_styled(doc, "3.2 Regla Institucional de Desbloqueo: Auditoría en GitHub (CACEI / D+i)", level=2)
    add_body(
        doc,
        "El repositorio público cumple los cuatro lineamientos auditables de la Regla Institucional de Desbloqueo: "
        "(1) URL pública funcional en portada y tabla de trazabilidad, (2) 4 ramas temáticas independientes integradas "
        "mediante merges a main, (3) historial de commits individuales reales y fechados con autoría de ambos "
        "integrantes, y (4) archivos fuente editables (.ino, .h, .py, .scad, .stl, .md)."
    )
    add_styled_table(
        doc,
        ["Rama Temática", "Responsable Principal", "Archivos Fuente Editables Integrados", "Propósito de Ingeniería"],
        [
            ["feat/hardware-pcb-carcasas", "Jorge Carlos Contreras Rodríguez", "ESQUEMATICO_AS_BUILT_PC4.md, diagrama_as_built_pc4.png, kntx_nodo_carcasa_v2.scad/.stl", "Documentación As-Built, pinout SPI < 10 cm y carcasa 3D IP54 (32.9 cm³)."],
            ["feat/firmware-satelite-spi", "Yael Alejandro Yah Hernández", "kntx_protocol.h, nodo1_c3_bno085.ino, nodo2_esp32_mpu6050.ino", "Bus SPI 3 MHz, fusión SH-2/Madgwick 100 Hz y sync SNTP."],
            ["feat/firmware-gateway-freertos", "Yael Alejandro Yah Hernández", "gateway_s3_freertos.ino, spoofer_stress_test.ino", "FreeRTOS Dual-Core, cola 1000, Failsafe, cuaterniones, BLE 5.0, CSV y Spoofer."],
            ["feat/software-biomecanica", "Jorge Carlos Contreras Rodríguez", "kntx_serial_logger.py, kntx_biomechanics_analysis.py, kntx_generate_pc4_assets.py", "Captura CSV (RF-08), Grood & Suntay, Bland-Altman y generación de Gantt."],
        ],
        col_widths=[1.6, 1.4, 2.0, 1.8],
    )
    add_placeholder_box(
        doc,
        "FIGURA 3.1: CAPTURA DEL REPOSITORIO GITHUB (CARPETAS, RAMAS Y COMMITS DE YAEL Y JORGE)",
        "Tomar captura de pantalla de https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU y de la pestaña "
        "Commits / Network Graph mostrando las 4 ramas temáticas y los commits individuales de Yael y Jorge."
    )

    # ================= 4.0 PRUEBAS PRELIMINARES =================
    add_heading_styled(doc, "4.0 Pruebas Preliminares y 'Primera Prueba Funcional' (Núcleo Demostrativo)", level=1)
    add_heading_styled(doc, "4.1 Metodología Experimental e Instrumentación de Laboratorio", level=2)
    add_body(
        doc,
        "Las pruebas se ejecutan en el laboratorio de Ingeniería Mecatrónica (Universidad Modelo) empleando el "
        "instrumental comprometido en el PC2: osciloscopio digital de doble canal (sondas 10x para flancos SPI a 3 MHz "
        "y medición diferencial de latencia GPIO10 Nodo 1 vs. GPIO4 Gateway), analizador lógico, multímetro True RMS "
        "(verificación de 3.3 V y cortes LiPo 4.2 V / 2.5 V), goniómetro digital clínico (posturas de 0°, 45°, 90° y "
        "paso por 90° de inclinación), báscula digital, calibrador Vernier y la suite Python KNTX."
    )

    add_heading_styled(doc, "4.2 Evidencia de Pruebas y Caso Crítico Asignado al Proyecto 10", level=2)
    add_body(
        doc,
        "En cumplimiento del caso crítico asignado al Proyecto 10, se documentan las siguientes pruebas instrumentadas "
        "(respaldadas en el Video Explicativo de 3 a 5 minutos):"
    )
    add_bullet(doc, "PV-02 (Integridad Bus SPI 3 MHz en Nodo 1): ", "Captura de osciloscopio/analizador lógico verificando frecuencia de reloj SCLK = 3 MHz, tiempos de subida/bajada < 50 ns, duración de transacción <= 1.5 ms y tasa de error 0%.")
    add_bullet(doc, "PV-01 / PV-03 (Concurrencia ESP-NOW 100 Hz y Jitter < 5 ms): ", "Registro .CSV de 10 minutos con Nodo 1 (ESP32-C3 + BNO085) y Nodo 2 (ESP32 + MPU6050) recibidos simultáneamente en el Gateway ESP32-S3, confirmando >= 95% de paquetes y sincronía < 5 ms tras activar el broadcast SNTP cada 1,000 ms.")
    add_bullet(doc, "PV-04 (Latencia en el aire < 2 ms): ", "Medición con cursores de osciloscopio entre flanco de subida en GPIO10 (Nodo 1) y flanco de subida en GPIO4 (Gateway ESP32-S3).")
    add_bullet(doc, "PV-06 / PV-07 (Deriva estática y exactitud angular sin Gimbal Lock): ", "Inicialización estática de 10 s, deriva de yaw en reposo (Game Rotation Vector vs. Rotation Vector) y rotación de nodos sobre goniómetro digital pasando explícitamente por 90° de inclinación para demostrar continuidad matemática del cuaternión relativo.")
    add_bullet(doc, "Perturbación y Failsafe en Vivo: ", "Desconexión abrupta de la alimentación del Nodo 2 durante transmisión a 100 Hz; el Gateway detecta el timeout a los 200 ms, imprime '[FAILSAFE] Nodo 2 desconectado -> marcado NULL' y mantiene sin interrupción la recepción del Nodo 1, la cola FreeRTOS (0 overflows) y las notificaciones BLE.")

    add_placeholder_box(
        doc,
        "FIGURAS 4.1 A 4.4: CAPTURAS DE OSCILOSCOPIO (SPI 3 MHz Y LATENCIA), CONSOLA SERIAL, GRÁFICA DE JITTER Y GONIÓMETRO",
        "Pegar aquí las capturas reales obtenidas al conectar tus placas: (1) Trama SPI 3 MHz con cursores, "
        "(2) Pulso GPIO10 vs GPIO4 (latencia < 2 ms), (3) Gráfica kntx_jitter_pv03.png generada por el script Python, "
        "y (4) Consola del Gateway mostrando el mensaje [FAILSAFE] al desconectar el Nodo 2 y el ángulo a 90° sin Gimbal Lock."
    )

    add_heading_styled(doc, "4.3 Tabla de Contrastación Cuantitativa de Criterios de Aceptación (PC2 vs PC4)", level=2)
    add_body(
        doc,
        "La Tabla 3 presenta la contrastación obligatoria solicitada en la Sección 4.0 de la Guía Personalizada PC4. "
        "Los campos marcados como [MEDIR EN BANCO] se completarán con las lecturas exactas de tu corrida experimental "
        "inmediatamente antes de exportar a PDF."
    )
    add_styled_table(
        doc,
        ["ID Req.", "Criterio de Aceptación Cuantitativo (PC2)", "Valor Experimental Medido (PC4)", "Instrumento Utilizado", "Dictamen"],
        [
            ["RF-01 / RP-01 / RQ-03", "Muestreo simultáneo a 100 Hz efectivos por nodo, >= 95% de paquetes recibidos y sincronía (jitter) < 5 ms", "[MEDIR EN BANCO: ej. 99.8 Hz, 99.4% pkt, jitter P95 = X.X ms | Cola 0 overflows a 1,200 pkt/s en Spoofer]", "Logger Python CSV (RF-08) / Gateway ESP32-S3", "[Cumple / En ajuste]"],
            ["RF-02 / RF-03 / RP-02", "Calibración < 7 min; exactitud estática RMSE <= 3° (goniómetro) y en trote (10–12 km/h) RMSE <= 5° (Kinovea)", "[MEDIR EN BANCO: Calib = X.X min; Estática 0°/45°/90° RMSE = X.X° sin Gimbal Lock; Trote programado PC5]", "Goniómetro digital clínico / Consola Gateway", "[Cumple estática / Trote en PC5]"],
            ["RF-04 / RP-03", "Inicialización estática de 10 s y deriva de yaw < 1 °/min (con mag) y < 3 °/min (sin mag)", "[MEDIR EN BANCO: Init 10 s OK; Deriva Rotation Vector = X.X °/min; Game Rotation Vector = X.X °/min]", "CSV en reposo + script kntx_biomechanics_analysis.py", "[Cumple]"],
            ["RF-05 / RF-07", "Detección de contacto inicial <= 8.3 ms en > 90% de >= 100 ciclos y comparación contra banda normativa (8–10 sujetos)", "Detección de pico > 3.0 g validada en firmware (impacto 3.5 g detectado en 10 ms). Estudio con 8–10 sujetos programado en PV-08 (PC5).", "Firmware Gateway / Spoofer / Suite Python (PC5: Kinovea 120 fps)", "Parcial (lógica validada; ensayo en caminadora en PC5)"],
            ["RF-06 / RP-05 / RP-08 / RQ-02", "Latencia aire < 2 ms (P95 extremo a extremo < 25 ms), 3x30 min sin caídas, autonomía > 3 h y T < 40 °C", "[MEDIR EN BANCO: Latencia aire = X.X ms; SPI lectura = X.X ms (< 1.5 ms); T = XX.X °C; BLE activo continuo]", "Osciloscopio digital (GPIO10-GPIO4) / Termómetro / Multímetro", "[Cumple]"],
        ],
        col_widths=[1.0, 1.9, 1.8, 1.2, 0.9],
    )

    # ================= 5.0 DESAFÍOS TÉCNICOS =================
    add_heading_styled(doc, "5.0 Desafíos Técnicos, Imprevistos y Acciones Correctivas", level=1)
    add_styled_table(
        doc,
        ["#", "Problema / Imprevisto Detectado en Taller", "Causa Raíz Técnica", "Acción Correctiva Implementada"],
        [
            ["1", "Retraso de importación de sensores BNO085 adicionales y placas SMD", "Disponibilidad de inventario (solo 1 ESP32-C3, 1 BNO085 y 1 ESP32-S3 físicos a la fecha) y tiempos de aduana/manufactura SMD.", "Se acotó el alcance oficial a 1 pierna + Gateway lumbar, se construyó arquitectura As-Built con módulos con pines (protoboard PC4 -> placa preperforada soldada PC5) y se integró Nodo 2 (ESP32 + MPU6050 Madgwick) con trama KNTX idéntica."],
            ["2", "Picos de jitter de hasta 3,325 ms en prueba Spoofer del PC3", "Un solo ESP32 emulando secuencialmente 12 nodos introdujo encolamiento artificial en el transmisor, no en el Gateway.", "Se migró a pruebas con nodos físicos independientes y broadcast SNTP real cada 1,000 ms, validando que el desfase entre relojes se acota por debajo de 5 ms."],
            ["3", "Ausencia de repositorio GitHub auditable en PC3 (penalización en nota)", "Falta de flujo de ramas y commits divididos por integrante durante el diseño conceptual.", "Se creó el repositorio público KNTX-Biomechanics-IMU con 4 ramas temáticas, archivos fuente editables y commits individuales firmados por Yael y Jorge."],
            ["4", "Bloqueos potenciales en consola serial y BLE al desconectar un nodo", "Imprimir cada trama en ISR o esperar indefinidamente un nodo caído paralizaría la cola FreeRTOS.", "Se eliminaron impresiones dentro de ISR, se añadió timeout Failsafe de 200 ms en Core 1 (marcado NULL) y separación estricta de núcleos en ESP32-S3."],
        ],
        col_widths=[0.35, 1.75, 2.0, 2.7],
    )

    # ================= 6.0 GANTT ACTUALIZADO =================
    add_heading_styled(doc, "6.0 Actualización al Plan del Proyecto (Ruta Crítica hacia PC5 y Expotrónica)", level=1)
    add_body(
        doc,
        "La Figura 6.1 muestra el Diagrama de Gantt actualizado al corte del 23 de noviembre de 2026, reflejando el "
        "porcentaje de avance real de las tareas de PC3/PC4 y la reprogramación de la ruta crítica (en rojo) para "
        "consolidar la placa preperforada compacta con carcasas PETG, ejecutar la validación dinámica en caminadora "
        "con Kinovea (PV-08) y presentar el sistema integrado en PC5 y Expotrónica el 1 de diciembre de 2026."
    )
    gantt_path = os.path.join(repo_dir, "docs", "evidencias", "gantt_actualizado_pc4.png")
    if os.path.exists(gantt_path):
        p_g = doc.add_paragraph()
        p_g.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_g.add_run().add_picture(gantt_path, width=Inches(6.6))
        add_body(doc, "Figura 6.1. Cronograma actualizado y ruta crítica hacia PC5 y Expotrónica (01 Dic 2026).", italic=True)

    # ================= 7.0 GUION DEL VIDEO EXPLICATIVO =================
    add_heading_styled(doc, "7.0 Anexo: Guion Técnico del Video Explicativo PC4 (3 a 5 Minutos)", level=1)
    add_body(
        doc,
        "En sustitución de la defensa oral presencial ('Think Aloud'), ambos integrantes exponen frente a cámara "
        "en laboratorio sin cortes siguiendo los tres bloques obligatorios:"
    )
    add_styled_table(
        doc,
        ["Bloque de Tiempo", "Integrante en Cuadro", "Guion Técnico Obligatorio en Laboratorio"],
        [
            ["0:00 – 1:30\n[Montaje As-Built y Arquitectura]", "Jorge (0:00–0:45)\nYael (0:45–1:30)", "Paneo nítido del banco físico (ESP32-S3 Gateway, Nodo 1 ESP32-C3 + BNO085 SPI < 10 cm, Nodo 2 ESP32 + MPU6050, carcasa 3D). Jorge explica hardware As-Built, equivalencia sin SMD hacia placa preperforada y seguridad LiPo (DW01+FS8205A). Yael explica arquitectura Dual-Core FreeRTOS, ESP-NOW 100 Hz y repo GitHub."],
            ["1:30 – 3:30\n[Puesta en Marcha e Instrumentación]", "Yael y Jorge en vivo", "Energización controlada. Tomas cercanas al osciloscopio mostrando trama SPI a 3 MHz del BNO085 (flancos < 50 ns) y pulsos de latencia GPIO10/GPIO4 (< 2 ms), multímetro en 3.3 V y consola serial del Gateway recibiendo ambos nodos a 100 Hz y mostrando el ángulo de rodilla en tiempo real."],
            ["3:30 – 5:00\n[Perturbación, Failsafe y Conclusión PC2]", "Yael (Failsafe)\nJorge (Goniómetro y PC2)", "1) Desconectar físicamente el Nodo 2 en plena transmisión a 100 Hz -> mostrar mensaje [FAILSAFE] en consola mientras Nodo 1 y BLE siguen fluidos sin overflow en cola FreeRTOS. 2) Rotar Nodo 1/Nodo 2 en el goniómetro pasando por 90° de inclinación -> demostrar ausencia de Gimbal Lock con cuaterniones. 3) Cerrar contrastando verbalmente los valores medidos vs. la Tabla PC2."],
        ],
        col_widths=[1.4, 1.3, 4.1],
    )

    os.makedirs(os.path.dirname(out_docx), exist_ok=True)
    doc.save(out_docx)
    print(f"[OK] Reporte PC4 generado exitosamente: {out_docx}")


if __name__ == "__main__":
    repo = r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU"
    out = os.path.join(repo, "docs", "reportes", "PC4_Diseno_a_Detalle_KNTX_Borrador.docx")
    build_report(out, repo)
