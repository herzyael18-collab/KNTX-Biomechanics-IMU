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
    # Foto panorámica real del banco físico (los 3 circuitos armados y encendidos)
    banco_path = os.path.join(repo_dir, "docs", "evidencias", "foto_banco_completo.jpg")
    if os.path.exists(banco_path):
        p_b = doc.add_paragraph()
        p_b.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_b.add_run().add_picture(banco_path, width=Inches(4.1))
        add_body(
            doc,
            "Figura 2.1. Vista panorámica real del banco físico As-Built KNTX operando en laboratorio: "
            "Gateway ESP32-S3 N16R8 con MPU6050 lumbar (arriba derecha), Nodo 1 ESP32-C3 SuperMini + GY-BNO08X "
            "por SPI a 3 MHz (izquierda) y Nodo 2 ESP32 WROOM-32 + MPU6050 (abajo).",
            italic=True
        )

    cables_path = os.path.join(repo_dir, "docs", "evidencias", "fig_infografia_cables_senales.png")
    if os.path.exists(cables_path):
        p_c = doc.add_paragraph()
        p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_c.add_run().add_picture(cables_path, width=Inches(6.65))
        add_body(
            doc,
            "Figura 2.2. Mapa visual cable-por-cable con fotografías reales de los tres circuitos físicos As-Built, "
            "detallando cada hilo físico, su pin GPIO y la señal eléctrica/lógica que transporta.",
            italic=True
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
        "La Figura 2.3 presenta el flujo visual completo de paquetes y telemetría desde los sensores inerciales "
        "hasta la interfaz de visualización, explicando cómo viajan las tramas ESP-NOW de 36 bytes a 100 Hz, "
        "el broadcast de retorno SNTP cada 1,000 ms, la separación Dual-Core de FreeRTOS y la salida por BLE 5.0 "
        "y USB-CSV. La Figura 2.4 y la Tabla 2 consolidan la arquitectura técnica formal y el pinout exacto."
    )
    flujo_path = os.path.join(repo_dir, "docs", "evidencias", "fig_infografia_flujo_paquetes.png")
    if os.path.exists(flujo_path):
        p_fl = doc.add_paragraph()
        p_fl.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_fl.add_run().add_picture(flujo_path, width=Inches(6.65))
        add_body(doc, "Figura 2.3. Infografía de flujo de paquetes en tiempo real: SPI 3 MHz -> ESP-NOW 36 B -> SNTP -> FreeRTOS Dual-Core -> BLE/CSV.", italic=True)

    diag_path = os.path.join(repo_dir, "hardware", "pcb", "diagrama_as_built_pc4.png")
    if os.path.exists(diag_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(diag_path, width=Inches(6.5))
        add_body(doc, "Figura 2.4. Diagrama de arquitectura e interconexiones As-Built del prototipo KNTX (PC4).", italic=True)

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
    gh_path = os.path.join(repo_dir, "docs", "evidencias", "foto_github_repo.jpg")
    if os.path.exists(gh_path):
        p_gh = doc.add_paragraph()
        p_gh.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_gh.add_run().add_picture(gh_path, width=Inches(6.55))
        add_body(
            doc,
            "Figura 3.1. Captura real del repositorio público en GitHub (KNTX-Biomechanics-IMU) mostrando "
            "estructura normalizada (/docs, /firmware, /hardware, /software), 5 ramas activas, 20 commits "
            "y 2 contribuidores verificados (Yael Alejandro Yah Hernández y Jorge Carlos Contreras Rodríguez).",
            italic=True
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

    add_heading_styled(doc, "4.2 Evidencia de Pruebas, Correcciones en Banco y Caso Crítico Asignado", level=2)
    add_body(
        doc,
        "Las pruebas en laboratorio se ejecutaron con los 3 módulos físicos operando de forma simultánea "
        "(Gateway ESP32-S3 MAC E0:72:A1:F4:EB:D8 + MPU6050 lumbar, Nodo 1 ESP32-C3 + BNO085 por SPI a 3 MHz "
        "y Nodo 2 ESP32 + MPU6050 con Madgwick 6-DOF a 100 Hz). Durante la puesta en marcha real se identificaron "
        "y corrigieron cuatro fallos técnicos documentados en la Figura 4.1 y la Figura 4.2:"
    )

    def insert_fig(filename, caption, width_in=6.55):
        fpath = os.path.join(repo_dir, "docs", "evidencias", filename)
        if os.path.exists(fpath):
            p_f = doc.add_paragraph()
            p_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_f.add_run().add_picture(fpath, width=Inches(width_in))
            add_body(doc, caption, italic=True)

    insert_fig(
        "fig_consola_antes_despues.png",
        "Figura 4.1. Comparativa de logs reales capturados en laboratorio: fallos iniciales detectados en banco "
        "(MaxSPI=8.99 ms, Core 0 panic, falso Failsafe por underflow uint32 y saturación UART 115.2 kbps) frente "
        "a la telemetría validada tras las correcciones de ingeniería."
    )
    insert_fig(
        "fig_mejora_spi_uart.png",
        "Figura 4.2. Impacto cuantitativo de las correcciones: (A) reducción de 6.4× en lectura SPI del BNO085 "
        "(8.99 ms -> 1.39 ms <= 1.5 ms, RP-04) mediante sincronización por pin INT; (B) desbloqueo de frecuencia "
        "multi-nodo de 69 Hz a 99.9 / 100.2 Hz mediante UART a 921,600 baudios y cola dedicada g_csvQueue."
    )
    insert_fig(
        "fig_pv01_pv03_jitter_60s.png",
        "Figura 4.3. Resultados experimentales PV-01 y PV-03 (60.04 s continuos, 12,016 muestras reales, 0 overflows): "
        "Nodo 1 = 99.94 Hz (99.9%, Jitter P95 = 1.00 ms) y Nodo 2 = 100.21 Hz (100.0%, Jitter P95 = 0.00 ms)."
    )
    insert_fig(
        "fig_pv06_deriva_yaw_60s.png",
        "Figura 4.4. Prueba de estabilidad y deriva de yaw en reposo (PV-06, 60 s): BNO085 en modo Game Rotation "
        "Vector registró 0.021 °/min y MPU6050 Madgwick registró 0.977 °/min, ambos muy por debajo de 3.0 °/min."
    )
    insert_fig(
        "fig_pv07_gimballock_failsafe.png",
        "Figura 4.5. Caso Crítico PC4 ejecutado en vivo: cruce continuo por 90° de inclinación (hasta 136.4°) sin "
        "Gimbal Lock y desconexión física del Nodo 2 en t = 17.2 s -> disparo de Failsafe (marcado NULL en 359 ms) "
        "mientras Nodo 1 mantiene 100 Hz ininterrumpidos, BLE activo y reconexión automática a t = 30.0 s."
    )
    insert_fig(
        "fig_prueba_flexiones_signo.png",
        "Figura 4.6. Validación cíclica de flexiones en vivo desde el Dashboard HMI (61.7 s, 12,344 muestras: "
        "6,171 Nodo 1 + 6,173 Nodo 2 = 100%). Comparativa del ángulo geodésico sin signo 2·acos(|w|) frente a la "
        "corrección por descomposición Twist con signo 2·atan2(q_eje, w): demuestra repetición a +90°, cruce suave "
        "hasta +166.95° sin Gimbal Lock, discriminación de flexión inversa (-88.23° y -16.5°) y retorno exacto a 0.0°."
    )

    add_placeholder_box(
        doc,
        "FIGURA 4.7 (COMPLEMENTO EN LABORATORIO): CAPTURAS DE OSCILOSCOPIO (FLANCOS SPI 3 MHz Y LATENCIA GPIO10-GPIO4)",
        "Insertar aquí las 2 fotos de la pantalla del osciloscopio tomadas al grabar el video en el laboratorio de "
        "Mecatrónica: (a) flanco de subida/bajada SCLK a 3 MHz (< 50 ns) y (b) diferencia entre pulso GPIO10 del "
        "Nodo 1 y GPIO4 del Gateway (latencia en el aire < 2 ms), más lectura en goniómetro digital clínico."
    )

    add_heading_styled(doc, "4.3 Tabla de Contrastación Cuantitativa de Criterios de Aceptación (PC2 vs PC4)", level=2)
    add_body(
        doc,
        "La Tabla 3 presenta la contrastación obligatoria de la Sección 4.0 de la Guía Personalizada PC4, "
        "poblada con los datos experimentales reales capturados del hardware KNTX en banco de pruebas."
    )
    add_styled_table(
        doc,
        ["ID Req.", "Criterio de Aceptación Cuantitativo (PC2)", "Valor Experimental Medido (PC4)", "Instrumento Utilizado", "Dictamen"],
        [
            ["RF-01 / RP-01 / RQ-03", "Muestreo simultáneo a 100 Hz efectivos por nodo, >= 95% de paquetes recibidos y sincronía (jitter) < 5 ms", "Corrida 60.04 s (12,016 filas CSV): Nodo 1 = 99.94 Hz (99.9%, Jitter med=0.0 ms, P95=1.0 ms); Nodo 2 = 100.21 Hz (100.0%, P95=0.0 ms); 0 overflows en cola FreeRTOS (1000/1000 libres).", "Gateway ESP32-S3 + Logger Python CSV (RF-08)", "Cumple"],
            ["RF-02 / RF-03 / RP-02", "Calibración < 7 min; exactitud estática RMSE <= 3° (goniómetro) y en trote (10–12 km/h) RMSE <= 5° (Kinovea)", "Calibración neutral < 15 s ('c'). Cruce continuo por 90° (máx. 136.4°) demostrado sin Gimbal Lock con cuaternión relativo q_rel. Verificación formal en goniómetro clínico y trote (Kinovea) en cierre de banco/PC5.", "Gateway ESP32-S3 / Goniómetro digital (cierre video)", "Cumple sin Gimbal Lock (Trote en PC5)"],
            ["RF-04 / RP-03", "Inicialización estática de 10 s y deriva de yaw < 1 °/min (con mag) y < 3 °/min (sin mag)", "Inicialización estática ejecutada (Calib_Status = 3). Deriva medida en reposo (60 s sin magnetómetro): BNO085 = 0.021 °/min; MPU6050 = 0.977 °/min (< 3.0 °/min).", "CSV 60 s + kntx_biomechanics_analysis.py", "Cumple"],
            ["RF-05 / RF-07", "Detección de contacto inicial <= 8.3 ms en > 90% de >= 100 ciclos y comparación contra banda normativa (8–10 sujetos)", "Lógica de detección de pico axial > 3.0 g validada en firmware (impacto 3.5 g capturado en ventana 10 ms) y algoritmo Spline 101 pts en Python. Ensayo con 8–10 corredores programado en PV-08 (PC5).", "Firmware Gateway / Spoofer / Suite Python", "Parcial (lógica validada; PV-08 en PC5)"],
            ["RF-06 / RP-04 / RP-05 / RP-08 / RQ-02", "SPI 3 MHz <= 1.5 ms; latencia aire < 2 ms (P95 < 25 ms), 3x30 min sin caídas, autonomía > 3 h y T < 40 °C", "Lectura SPI BNO085 medida en MCU: 1.37–1.40 ms (<= 1.5 ms, 0 errores TX); BLE 5.0 continuo sin caídas; Failsafe ante desconexión de Nodo 2 en 359 ms + reconexión automática. Osciloscopio GPIO10-GPIO4 y autonomía 3 h en cierre de laboratorio.", "Contadores esp_timer (us) / Consola Gateway / Osciloscopio", "Cumple SPI y Failsafe (Autonomía en PC5)"],
        ],
        col_widths=[1.0, 1.85, 2.05, 1.1, 0.8],
    )

    # ================= 5.0 DESAFÍOS TÉCNICOS =================
    add_heading_styled(doc, "5.0 Desafíos Técnicos, Imprevistos y Acciones Correctivas", level=1)
    add_styled_table(
        doc,
        ["#", "Problema / Imprevisto Real Detectado en Banco", "Causa Raíz Técnica Verificada", "Acción Correctiva Implementada y Resultado"],
        [
            ["1", "Lectura SPI del BNO085 alcanzaba 7.99–8.99 ms (incumpliendo RP-04 <= 1.5 ms)", "Llamado continuo de bno08x.getSensorEvent() por polling sin verificar el pin de interrupción hardware INT.", "Se condicionó la lectura SPI a digitalRead(PIN_BNO_INT) == LOW. Resultado: reducción de 6.4× a 1.37–1.40 ms (<= 1.5 ms)."],
            ["2", "Guru Meditation Error: Core 0 panic en el Gateway ESP32-S3 al iniciar sincronía", "Stack de 2,048 bytes insuficiente en taskSyncBroadcast para el stack Wi-Fi/ESP-NOW y uso de xQueueSendFromISR() en callback de tarea Wi-Fi (Core 3.x).", "Se amplió stack a 4,096 B (8,192 B en Core 1) y se migró a xQueueSend(..., 0). Resultado: 0 reinicios y 0 overflows."],
            ["3", "Falsos disparos de [FAILSAFE] cada ~30 ms con el Nodo 1 operando normalmente", "Condición de carrera entre Core 0 y Core 1: resta sin signo uint32_t (nowMs - lastGatewayRxMs) producía underflow (~4.29×10^9 ms > timeout).", "Se convirtió a aritmética con signo int32_t dentro del Mutex y timeout de 350 ms. Resultado: 0 falsos positivos y disparo real exacto a 359 ms."],
            ["4", "Tasa multi-nodo limitada a ~69 Hz y jitter P95 = 10 ms en corrida inicial", "Saturación del puerto UART a 115,200 bps (flujo CSV de 2 nodos = ~150 kbps) + pérdida de muestras en bordes de ventana de 10 ms.", "Se elevó el UART a 921,600 bps (buffer TX 4 KB) y se añadió cola dedicada g_csvQueue. Resultado: salto a 99.94 Hz / 100.21 Hz y jitter P95 <= 1.0 ms."],
            ["5", "Retraso de importación de BNO085 adicionales y placas SMD", "Disponibilidad real de 1 ESP32-C3, 1 BNO085 y 1 ESP32-S3 a la fecha.", "Implementación As-Built con módulos con pines (protoboard PC4 -> placa preperforada soldada PC5) + Nodo 2 equivalente (ESP32 + MPU6050) con trama KNTX idéntica."],
        ],
        col_widths=[0.3, 1.75, 2.0, 2.75],
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
