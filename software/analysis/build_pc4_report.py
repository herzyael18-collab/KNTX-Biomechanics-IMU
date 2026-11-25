#!/usr/bin/env python3
"""
build_pc4_report.py
Genera el Reporte Maestro Final del Punto de Control 4 (PC4):
  docs/reportes/PC4_Diseno_a_Detalle_KNTX_FINAL.docx

Características de calidad editorial y cumplimiento 100% de rúbrica:
  - Hipervínculos reales clicables (<w:hyperlink>) al repositorio público en Portada y Sección 3.3.
  - Diagramas de Conexiones Físicas, Arquitectura General y Flujo de Paquetes en FORMATO VERTICAL
    DE PÁGINA COMPLETA (1 figura por hoja entera para máxima legibilidad).
  - Cero recuadros pendientes vacíos; único campo por pegar por el alumno: URL del video en Portada.
  - Trazabilidad completa de las 5 corridas experimentales reales (48,670 muestras en archivos .CSV
    auditables en GitHub), fórmulas empleadas, comparativas Antes vs. Después y análisis del modelo
    analítico RC de integridad SPI + temporizador hardware esp_timer (1 µs).
  - Justificación técnica y de cadena de suministro de la transición a Bosch BMI160 (6-DOF SPI 3 MHz)
    acordada con el docente hacia el PC5.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

NAVY = RGBColor(0x10, 0x2A, 0x43)
BLUE = RGBColor(0x1F, 0x4E, 0x79)
DARK = RGBColor(0x1E, 0x29, 0x3B)
GRAY = RGBColor(0x47, 0x55, 0x69)

GITHUB_URL = "https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU"


def set_cell_bg(cell, hex_color: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_hyperlink(paragraph, url: str, text: str, font_size_pt: float = 10.0, bold: bool = True):
    """Inserta un hipervínculo clicable nativo de Word (<w:hyperlink>)."""
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Calibri")
    rFonts.set(qn("w:hAnsi"), "Calibri")
    rPr.append(rFonts)

    c = OxmlElement("w:color")
    c.set(qn("w:val"), "1D4ED8")
    rPr.append(c)

    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)

    if bold:
        rPr.append(OxmlElement("w:b"))

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(font_size_pt * 2)))
    rPr.append(sz)

    new_run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def add_h(doc, text: str, level: int = 1):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(12 if level == 1 else (9 if level == 2 else 6))
    p.paragraph_format.space_after = Pt(4 if level == 1 else 3)
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Calibri"
    if level == 1:
        r.font.size = Pt(13.5)
        r.font.color.rgb = NAVY
    elif level == 2:
        r.font.size = Pt(11.5)
        r.font.color.rgb = BLUE
    else:
        r.font.size = Pt(10.5)
        r.font.color.rgb = DARK
    return p


def add_p(doc, text: str, bold_prefix: str = None, italic: bool = False, align=None, size: float = 10.2):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4.5)
    p.paragraph_format.line_spacing = 1.15
    if align is not None:
        p.alignment = align
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.bold = True
        rb.font.name = "Calibri"
        rb.font.size = Pt(size)
        rb.font.color.rgb = NAVY
    r = p.add_run(text)
    r.italic = italic
    r.font.name = "Calibri"
    r.font.size = Pt(size)
    r.font.color.rgb = GRAY if italic else DARK
    return p


def add_bullet(doc, bold_prefix: str, text: str, size: float = 10.0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.12
    rb = p.add_run(bold_prefix)
    rb.bold = True
    rb.font.name = "Calibri"
    rb.font.size = Pt(size)
    rb.font.color.rgb = NAVY
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(size)
    r.font.color.rgb = DARK
    return p


def add_table_caption(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(9.5)
    r.font.color.rgb = NAVY
    return p


def add_table(doc, headers, rows, widths=None, font_pt: float = 8.9):
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    for j, h in enumerate(headers):
        c = tbl.rows[0].cells[j]
        set_cell_bg(c, "102A43")
        if widths:
            c.width = Inches(widths[j])
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Calibri"
        r.font.size = Pt(font_pt + 0.3)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for i, rdata in enumerate(rows):
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(rdata):
            c = tbl.rows[i + 1].cells[j]
            set_cell_bg(c, bg)
            if widths:
                c.width = Inches(widths[j])
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2.5)
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.line_spacing = 1.08
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(font_pt)
            r.font.color.rgb = NAVY if j == 0 else DARK
            if j == 0:
                r.bold = True

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(3)
    return tbl


def add_figure(doc, img_path: str, caption: str, width_in: float = 6.65, full_page: bool = False):
    if not os.path.exists(img_path):
        add_p(doc, f"[Imagen no encontrada: {img_path}]", italic=True)
        return
    if full_page:
        doc.add_page_break()
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(2)
    p_img.paragraph_format.space_after = Pt(3)
    p_img.paragraph_format.keep_with_next = True
    p_img.add_run().add_picture(img_path, width=Inches(width_in))
    add_p(doc, caption, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=9.2)
    if full_page:
        doc.add_page_break()


def build_final_pc4(out_docx: str, repo_dir: str):
    evid = os.path.join(repo_dir, "docs", "evidencias")
    doc = Document()

    for s in doc.sections:
        s.top_margin = Inches(0.68)
        s.bottom_margin = Inches(0.68)
        s.left_margin = Inches(0.72)
        s.right_margin = Inches(0.72)

    # =========================================================================
    # PORTADA OFICIAL CON HIPERVÍNCULOS ACTIVOS
    # =========================================================================
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(10)
    r = p_top.add_run("UNIVERSIDAD MODELO — CAMPUS MÉRIDA\n")
    r.bold = True; r.font.name = "Calibri"; r.font.size = Pt(17); r.font.color.rgb = NAVY
    r2 = p_top.add_run("ESCUELA DE INGENIERÍA • INGENIERÍA MECATRÓNICA\n25781 PROYECTOS VII (FASE II: MODELO D+i — CICLO AD26)\n")
    r2.bold = True; r2.font.name = "Calibri"; r2.font.size = Pt(11); r2.font.color.rgb = BLUE

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(10)
    rt = p_title.add_run("PUNTO DE CONTROL 4 (PC4)\nDISEÑO A DETALLE, PRIMERA PRUEBA FUNCIONAL Y VIDEO EXPLICATIVO\n\n")
    rt.bold = True; rt.font.name = "Calibri"; rt.font.size = Pt(15.5); rt.font.color.rgb = NAVY
    rs = p_title.add_run("PROYECTO 10: KNTX — SISTEMA DE MEDICIÓN INERCIAL PARA BIOMECÁNICA DEL CUERPO\n(CAPTURA DE MOVIMIENTO INERCIAL)")
    rs.bold = True; rs.font.name = "Calibri"; rs.font.size = Pt(12); rs.font.color.rgb = BLUE

    # Tabla de ficha técnica de portada
    tbl_cov = add_table(
        doc,
        ["Campo de Identificación Institucional", "Información Oficial Registrada del Proyecto"],
        [
            ["Integrantes y Correos Institucionales",
             "• Yael Alejandro Yah Hernández (15234422@modelo.edu.mx)\n• Jorge Carlos Contreras Rodríguez (15233640@modelo.edu.mx)"],
            ["Docente Titular Evaluador", "Dr. Rodrigo Daniel Solís Ortega (rodrigo.solis@modelo.edu.mx)"],
            ["Categoría y Arquetipo Tecnológico", "Categoría E — Biomecatrónica / Arquetipo C (Sistemas Embebidos, Biomédicos e IoT)"],
            ["Alcance Físico Acordado (Semestre 1)",
             "1 Extremidad Inferior (3 nodos satélite: Tibia, Fémur y Pie) + 1 Gateway Central con sensor lumbar en Espalda Baja (L4–L5)"],
            ["Calificación Previa PC3", "84 / 100 — Diseño Conceptual Iterativo (Subsanación 100% de repositorio GitHub en esta entrega)"],
            ["Fecha y Sede de Entrega", "24 de noviembre de 2026 | Mérida, Yucatán, México"],
        ],
        widths=[2.45, 4.55],
        font_pt=9.4,
    )
    _ = tbl_cov

    # Caja destacada de Enlaces de Desbloqueo (GitHub activo clicable + Enlace de Video)
    link_box = doc.add_table(rows=2, cols=2)
    link_box.style = "Table Grid"
    link_box.alignment = WD_TABLE_ALIGNMENT.CENTER

    c00, c01 = link_box.rows[0].cells[0], link_box.rows[0].cells[1]
    set_cell_bg(c00, "102A43"); set_cell_bg(c01, "EFF6FF")
    c00.width = Inches(2.45); c01.width = Inches(4.55)
    r_l1 = c00.paragraphs[0].add_run("Repositorio Público GitHub\n(Regla de Desbloqueo Activa)")
    r_l1.bold = True; r_l1.font.name = "Calibri"; r_l1.font.size = Pt(9.5); r_l1.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p_gh_cov = c01.paragraphs[0]
    p_gh_cov.paragraph_format.space_before = Pt(4); p_gh_cov.paragraph_format.space_after = Pt(4)
    add_hyperlink(p_gh_cov, GITHUB_URL, GITHUB_URL, font_size_pt=9.8, bold=True)

    c10, c11 = link_box.rows[1].cells[0], link_box.rows[1].cells[1]
    set_cell_bg(c10, "1F4E79"); set_cell_bg(c11, "FFFBEB")
    c10.width = Inches(2.45); c11.width = Inches(4.55)
    r_l2 = c10.paragraphs[0].add_run("Video Explicativo PC4\n(3 a 5 min — Sustituye Think Aloud)")
    r_l2.bold = True; r_l2.font.name = "Calibri"; r_l2.font.size = Pt(9.5); r_l2.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p_vid = c11.paragraphs[0]
    p_vid.paragraph_format.space_before = Pt(4); p_vid.paragraph_format.space_after = Pt(4)
    rv = p_vid.add_run("[PEGAR AQUÍ ENLACE PERMANENTE DE ONEDRIVE MODELO / YOUTUBE OCULTO ANTES DE EXPORTAR A PDF]")
    rv.bold = True; rv.font.name = "Calibri"; rv.font.size = Pt(9.2); rv.font.color.rgb = RGBColor(0xB4, 0x53, 0x09)

    doc.add_page_break()

    # =========================================================================
    # ÍNDICE ESTRUCTURADO DE CONTENIDO, TABLAS Y FIGURAS
    # =========================================================================
    add_h(doc, "Índice General del Reporte Técnico PC4", level=1)
    toc_items = [
        ("1.0 Introducción y Marco de Implementación", "Resumen del avance post-PC3, subsanación de las 3 alertas obligatorias, análisis de equivalencia As-Built y adopción justificada del sensor Bosch BMI160."),
        ("2.0 Implementación Física (Hardware, Mecánica y Esquemas As-Built)", "Carcasas CAD 3D (32.91 cm³ < 40 cm³, IP54), presupuesto de masa (< 50 g), seguridad eléctrica y diagramas verticales de página completa (Conexiones físicas, Arquitectura y Flujo de paquetes)."),
        ("3.0 Implementación Lógica, Firmware Modular y Auditoría en GitHub", "Protocolo binario de 36 bytes, filtro Madgwick 6-DOF optimizado (1.2% CPU), arquitectura FreeRTOS Dual-Core con álgebra Twist con signo, modelo analítico RC SPI 3 MHz y trazabilidad GitHub."),
        ("4.0 Pruebas Preliminares y 'Primera Prueba Funcional' (Núcleo Demostrativo)", "Trazabilidad de las 5 corridas experimentales reales (48,670 muestras .CSV), diagnóstico Antes vs. Después, PV-01/PV-03 (100 Hz, jitter ≤ 1 ms), PV-06 (deriva), Caso Crítico (90° + Failsafe) y Tabla PC2 vs. PC4."),
        ("5.0 Desafíos Técnicos, Imprevistos y Acciones Correctivas", "Bitácora analítica de los 6 problemas reales detectados en taller/firmware, causa raíz verificada y solución implementada."),
        ("6.0 Actualización al Plan del Proyecto (Ruta Crítica hacia PC5 y Expotrónica)", "Cronograma reprogramado al corte del 24 de noviembre de 2026 rumbo al cierre del 1 de diciembre."),
        ("7.0 Protocolo del Video Explicativo (3 a 5 min) y 8.0 Referencias APA 7", "Estructura minuto a minuto de la demostración en laboratorio y bibliografía normativa/técnica."),
    ]
    add_table(doc, ["Sección Oficial", "Alcance Documentado en este Entregable"], toc_items, widths=[2.4, 4.6], font_pt=8.9)

    add_h(doc, "Relación de Figuras y Tablas Principales", level=2)
    add_bullet(doc, "Figuras de Implementación Física (Página Completa Vertical): ",
               "Figura 2.1 (Banco físico real completo), Figura 2.2 (Mapa visual vertical de conexiones físicas y señales por cable), "
               "Figura 2.3 (Arquitectura general vertical KNTX PC4->PC5) y Figura 2.4 (Flujo vertical de paquetes ESP-NOW, SNTP y FreeRTOS).")
    add_bullet(doc, "Figuras de Lógica, Simulación y GitHub: ",
               "Figura 3.1 (Modelo analítico RC de integridad SPI 3 MHz + presupuesto temporal de 10 ms) y Figura 3.2 (Captura real del repositorio público en GitHub).")
    add_bullet(doc, "Figuras Experimentales Obtenidas de Datos Crudos (.CSV): ",
               "Figura 4.1 (Logs reales Antes vs. Después), Figura 4.2 (Mejora SPI 6.4× y desbloqueo UART 100 Hz), Figura 4.3 (PV-01/PV-03 en 60 s: 12,016 muestras), "
               "Figura 4.4 (PV-06 Deriva de yaw en reposo), Figura 4.5 (Caso Crítico: cruce >90° sin Gimbal Lock + Failsafe y reconexión), "
               "Figura 4.6 (Comparativa ángulo sin signo vs. Twist con signo, 12,344 muestras), Figura 4.7 (Ensayo multi-patrón de 86.9 s, 17,387 muestras) y Figura 6.1 (Gantt actualizado).")

    doc.add_page_break()

    # =========================================================================
    # 1.0 INTRODUCCIÓN Y MARCO DE IMPLEMENTACIÓN
    # =========================================================================
    add_h(doc, "1.0 Introducción y Marco de Implementación", level=1)
    add_h(doc, "1.1 Resumen del Avance y Subsanación de Alertas Técnicas Post-PC3", level=2)
    add_p(
        doc,
        "El proyecto KNTX tiene como objetivo general desarrollar e integrar un sistema wearable de captura de movimiento "
        "inercial capaz de adquirir, sincronizar y transmitir una matriz cinemática articular a 100 Hz sostenidos hacia una "
        "interfaz móvil y de computadora para el análisis biomecánico de la carrera atlética. Conforme al alcance semestral "
        "acordado en el PC3 (Sección 1.2), el sistema físico se delimita a una extremidad inferior instrumentada (3 nodos "
        "satélite: Tibia, Fémur y Pie) más un concentrador central (Gateway) ubicado en la espalda baja (vértebras L4–L5)."
    )
    add_p(
        doc,
        "En la evaluación oficial del PC3 (84/100), el docente titular reconoció la profundidad del diseño electrónico, los "
        "algoritmos de sincronía SNTP y el modelado mecánico, señalando tres alertas técnicas obligatorias para este PC4, "
        "las cuales han sido subsanadas al 100% como se detalla a continuación:"
    )
    add_bullet(
        doc, "1. Regularización integral de GitHub (Regla Institucional de Desbloqueo): ",
        "Se eliminó toda leyenda de 'URL pendiente'. El repositorio público https://github.com/herzyael18-collab/KNTX-Biomechanics-IMU "
        "alberga el código fuente modular (.h, .ino, .py), modelos CAD editables (.scad, .stl), esquemas As-Built y 48,670 muestras "
        "experimentales crudas (.csv), organizadas en 4 ramas temáticas con commits individuales verificados de Yael Alejandro Yah "
        "Hernández y Jorge Carlos Contreras Rodríguez."
    )
    add_bullet(
        doc, "2. Transición física As-Built libre de fallos de soldadura SMD: ",
        "En estricto apego al Arquetipo C de la Guía Oficial PC4 (que faculta la validación sobre ensamble limpio en protoboard "
        "avanzada o primera placa), se implementó el banco funcional empleando módulos breakout con pines e interconexiones "
        "ultracortas (< 5 cm), verificando continuidad e integridad del bus SPI a 3 MHz en el sensor BNO085 sin riesgo térmico "
        "de soldadura SMD manual. Para el cierre integrado del PC5, los módulos con pines se consolidarán sobre placas "
        "preperforadas soldadas compactas alojadas dentro de las carcasas impresas en 3D (PETG)."
    )
    add_bullet(
        doc, "3. Demostración experimental a 100 Hz, cuaterniones sin Gimbal Lock y resiliencia FreeRTOS: ",
        "Se ejecutó y documentó con datos reales la recepción concurrente a 100 Hz de múltiples nodos físicos vía ESP-NOW hacia "
        "el Gateway ESP32-S3 (0 overflows en cola de 1,000 paquetes), el cruce continuo por ±90° hasta +166.95° y -88.23° sin "
        "bloqueo de cardán mediante descomposición Twist de cuaterniones, y la respuesta Failsafe no bloqueante (359 ms) ante la "
        "desconexión física en vivo de un nodo satélite."
    )

    add_h(doc, "1.2 Vínculo con PC3, Análisis de Equivalencia y Selección del Sensor Bosch BMI160", level=2)
    add_p(
        doc,
        "Todo componente implementado responde a la arquitectura aprobada en PC3; aquellas sustituciones motivadas por tiempos "
        "de cadena de suministro y sobrecosto internacional se respaldan con el siguiente análisis de equivalencia ingenieril "
        "(revisado con el docente titular):"
    )
    add_bullet(
        doc, "Justificación técnico-económica de la Arquitectura Sensorial Híbrida (Bosch BNO085 + Bosch BMI160): ",
        "En PC2/PC3 se contemplaron sensores BNO085 para todos los segmentos. No obstante, en noviembre de 2026 las unidades "
        "adicionales de BNO085 presentan desabasto local, plazos de importación posteriores al 1 de diciembre y un incremento "
        "de precio cercano a $1,000 MXN por unidad (+163% respecto a la cotización base). En consecuencia, el equipo conserva el "
        "BNO085 físico disponible en el Nodo 1 (Tibia — segmento crítico sometido a los picos de impacto > 3.0 g del contacto "
        "inicial RF-05 y referencia metrológica SPI) y adopta el sensor industrial Bosch Sensortec BMI160 (con arribo confirmado "
        "el 25 de noviembre) para los tres segmentos restantes (Fémur, Pie y Lumbar)."
    )
    add_bullet(
        doc, "Idoneidad técnica del Bosch BMI160 y descarte fundamentado del magnetómetro (6-DOF vs. 9-DOF): ",
        "El BMI160 pertenece a la misma familia MEMS de grado wearable de Bosch que el BNO085: incorpora interfaz SPI nativa de "
        "hasta 10 MHz (cumpliendo sin modificaciones el requisito RP-04 y RQ-01 a 3 MHz con pistas < 10 cm y lectura <= 1.5 ms), "
        "rango acelerométrico de ±16 g y consumo ultrabajo de 0.9 mA (favoreciendo la meta de autonomía > 3 h de RP-08). La "
        "ausencia de magnetómetro en el BMI160 (6-DOF) está plenamente respaldada por la literatura base del PC2 (Ceriola et al., "
        "2026) y la Decisión 2 del PC3: en pruebas sobre caminadora eléctrica (PV-08), el motor y el chasis ferromagnético "
        "distorsionan el campo magnético local generando errores de rumbo (yaw) superiores a 30°, razón por la cual incluso el "
        "BNO085 debe operarse con el magnetómetro deshabilitado (modo Game Rotation Vector, criterio RP-03 < 3 °/min)."
    )
    add_bullet(
        doc, "Equivalencia del Nodo 2 en la Primera Prueba Funcional PC4 (ESP32 + MPU-6050 con Fusión Madgwick): ",
        "Para ejecutar de forma inmediata las pruebas multi-nodo de este PC4 previo al montaje final de los BMI160 mañana, se "
        "implementó el Nodo 2 (Fémur) con un ESP32 WROOM-32 y un IMU MPU-6050 de 6-DOF ejecutando nuestro filtro de descenso de "
        "gradiente Madgwick a 100 Hz en CPU (~0.12 ms por muestra = 1.2% de carga de procesador) y transmitiendo exactamente la "
        "misma estructura binaria kntx_packet_t de 36 bytes vía ESP-NOW. Haber superado todos los umbrales del PC2 (100.21 Hz, "
        "jitter P95 = 0.00 ms y deriva = 0.977 °/min) con un MPU-6050 garantiza un margen aún mayor al migrar al Bosch BMI160 por SPI."
    )

    add_table_caption(doc, "Tabla 1. Vínculo con diseño conceptual (PC3), equivalencia As-Built (PC4) y consolidación final (PC5).")
    add_table(
        doc,
        ["Subsistema", "Diseño Conceptual (PC3)", "Implementación As-Built (PC4)", "Consolidación Final (PC5 — 01 Dic)"],
        [
            ["Gateway Central\n(Espalda baja L4–L5)", "ESP32-S3-WROOM-1 N16R8", "ESP32-S3-N16R8 DevKit + IMU Lumbar local (MPU-6050 I2C)", "ESP32-S3-N16R8 + Bosch BMI160 en placa preperforada + carcasa"],
            ["Nodo Satélite 1\n(Tibia — Impacto)", "ESP32-C3 + BNO085\n(PCB flexible SPI 3 MHz)", "ESP32-C3 SuperMini + GY-BNO08X por SPI 3 MHz (< 5 cm, pin INT)", "Mismo hardware soldado en placa preperforada + carcasa PETG IP54"],
            ["Nodo Satélite 2\n(Fémur — Rodilla)", "ESP32-C3 + BNO085\n(SPI 3 MHz)", "ESP32 WROOM-32 + MPU-6050 (Madgwick 6-DOF @ 100 Hz, trama 36 B)", "ESP32-C3 SuperMini + Bosch BMI160 por SPI 3 MHz + carcasa PETG"],
            ["Nodo Satélite 3\n(Pie — Tobillo)", "ESP32-C3 + BNO085\n(SPI 3 MHz)", "Validado a escala de red con Spoofer (hasta 12 nodos / 1,200 pkt/s)", "ESP32-C3 SuperMini + Bosch BMI160 por SPI 3 MHz + carcasa PETG"],
            ["Visualización y\nRegistro (RF-06/08)", "Mockup móvil BLE +\nexportación .CSV", "BLE 5.0 activo + Dashboard HMI Python en vivo (921.6 kbps) + .CSV", "Interfaz unificada con banda normativa ±1 DE + estudio Kinovea"],
        ],
        widths=[1.35, 1.55, 2.05, 2.05],
        font_pt=8.6,
    )

    # =========================================================================
    # 2.0 IMPLEMENTACIÓN FÍSICA (CON DIAGRAMAS VERTICALES DE PÁGINA COMPLETA)
    # =========================================================================
    add_h(doc, "2.0 Implementación Física (Hardware, Mecánica y Esquemas As-Built)", level=1)
    add_h(doc, "2.1 Diseño Mecánico CAD 3D, Presupuesto de Masa y Montaje en Banco", level=2)
    add_p(
        doc,
        "El encapsulado mecánico de cada nodo satélite fue parametrizado en OpenSCAD (hardware/carcasas/kntx_nodo_carcasa_v2.scad) "
        "y exportado a malla cerrada .STL lista para manufactura aditiva FDM en PETG (material seleccionado por su resistencia "
        "química al sudor, tenacidad ante impacto y estabilidad dimensional por encima de 70 °C, cumpliendo ampliamente RQ-02 < 40 °C). "
        "Las dimensiones exteriores son 44.0 × 34.0 × 22.0 mm, arrojando un volumen geométrico bruto de 32.91 cm³ (< 40 cm³ exigido "
        "por RP-09), con espesor de pared de 2.0 mm, 3 perímetros, relleno giroide al 25%, capas de 0.20 mm paralelas al plano de "
        "tracción de las correas elásticas de 25 mm y labio perimetral machihembrado de 2.0 mm para protección contra salpicaduras "
        "grado IP54 (IEC 60529, RQ-04). La Tabla 2 verifica el cumplimiento del presupuesto de masa por nodo (< 50 g, RP-09)."
    )

    add_table_caption(doc, "Tabla 2. Presupuesto másico y volumétrico por nodo satélite encapsulado (verificación RP-09 < 50 g y < 40 cm³).")
    add_table(
        doc,
        ["Componente Físico del Nodo Satélite", "Especificación / Material", "Masa Unitaria (g)", "Fuente de Verificación"],
        [
            ["Microcontrolador ESP32-C3 SuperMini / MINI-1", "Módulo con antena cerámica/PCB", "2.4 g", "Hoja de datos / pesaje módulo"],
            ["Sensor IMU (Bosch BNO085 / Bosch BMI160)", "Breakout compacto con pines", "1.8 g", "Hoja de datos fabricante"],
            ["Placa preperforada FR4 recortada + soldadura", "Sustrato 40 × 30 × 1.6 mm", "4.6 g", "Cálculo volumétrico FR4 (1.85 g/cm³)"],
            ["Batería LiPo 3.7 V, 400 mAh + DW01/FS8205A", "Celda polímero de litio 602035", "8.5 g", "Ficha técnica proveedor (Steren/uElec)"],
            ["Carcasa impresa en 3D (Base + Tapa IP54)", "PETG (ρ = 1.27 g/cm³, infill 25%)", "14.2 g", " Propiedades físicas malla STL"],
            ["TOTAL NODO ENCAPSULADO (Meta RP-09 < 50 g)", "Volumen exterior = 32.91 cm³ (< 40 cm³)", "31.5 g", "CUMPLE (Margen libre de 18.5 g = 37%)"],
        ],
        widths=[2.35, 1.85, 1.15, 1.65],
        font_pt=8.7,
    )

    add_figure(
        doc,
        os.path.join(evid, "foto_banco_completo.jpg"),
        "Figura 2.1. Fotografía real del banco físico As-Built KNTX energizado y operando de forma concurrente: "
        "Gateway ESP32-S3-N16R8 + MPU-6050 lumbar (derecha superior), Nodo 1 ESP32-C3 SuperMini + GY-BNO08X en SPI 3 MHz "
        "(izquierda) y Nodo 2 ESP32 WROOM-32 + MPU-6050 (inferior).",
        width_in=3.85,
        full_page=False,
    )

    add_h(doc, "2.2 Ensamblaje Eléctrico, Seguridad y Mapa Visual de Conexiones Físicas", level=2)
    add_p(
        doc,
        "El subsistema eléctrico opera íntegramente en régimen de Muy Baja Tensión de Seguridad (SELV: 3.3 V DC en buses lógicos, "
        "3.7 V nominales en celdas LiPo y 5.0 V DC en puerto USB), eliminando riesgos eléctricos sobre la piel del deportista en "
        "concordancia con NOM-001-SEDE-2018. El diseño de alimentación autónoma contempla celdas LiPo de 400–500 mAh protegidas "
        "por el circuito integrado DW01A + doble MOSFET FS8205A conforme a IEC 62133-2 (RQ-06: corte por sobretensión > 4.2 V, "
        "subtensión < 2.5 V y sobrecorriente/cortocircuito). En la página siguiente, la Figura 2.2 presenta en formato vertical "
        "de página completa el mapa visual detallado de los tres circuitos construidos y qué señal viaja por cada conductor."
    )

    # PÁGINA COMPLETA VERTICAL 1: CONEXIONES FÍSICAS
    add_figure(
        doc,
        os.path.join(evid, "fig_conexiones_vertical_fullpage.png"),
        "Figura 2.2. Mapa visual vertical de página completa de las conexiones físicas As-Built (Nodo 1 Tibia, Nodo 2 Fémur y Gateway Lumbar).",
        width_in=6.95,
        full_page=True,
    )

    add_h(doc, "2.3 Esquemas 'As-Built' y Diagramas Verticales de Arquitectura y Flujo de Paquetes", level=2)
    add_p(
        doc,
        "Para garantizar máxima claridad técnica y visual, en las dos páginas completas siguientes se despliegan en orientación "
        "vertical: (1) la Figura 2.3 con la Arquitectura General del Sistema KNTX estructurada en cuatro niveles jerárquicos "
        "(incluyendo la transición a Bosch BMI160 hacia PC5), y (2) la Figura 2.4 con el Flujo Vertical Paso a Paso de Telemetría "
        "y la estructura exacta byte por byte de los paquetes inalámbricos."
    )

    # PÁGINA COMPLETA VERTICAL 2: ARQUITECTURA GENERAL
    add_figure(
        doc,
        os.path.join(evid, "fig_arquitectura_vertical_fullpage.png"),
        "Figura 2.3. Diagrama vertical de página completa de la Arquitectura General As-Built del sistema KNTX y escalado hacia PC5.",
        width_in=6.95,
        full_page=True,
    )

    # PÁGINA COMPLETA VERTICAL 3: FLUJO DE PAQUETES
    add_figure(
        doc,
        os.path.join(evid, "fig_flujo_paquetes_vertical_fullpage.png"),
        "Figura 2.4. Infografía vertical de página completa del flujo de datos y estructura binaria de paquetes desde el IMU hasta el archivo .CSV.",
        width_in=6.95,
        full_page=True,
    )

    # =========================================================================
    # 3.0 IMPLEMENTACIÓN LÓGICA, SIMULACIÓN SPI Y AUDITORÍA EN GITHUB
    # =========================================================================
    add_h(doc, "3.0 Implementación Lógica, Integridad de Señal y Auditoría en GitHub", level=1)
    add_h(doc, "3.1 Arquitectura Modular de Firmware y Algoritmos Cinemáticos (Sin Bloqueos)", level=2)
    add_p(
        doc,
        "El software embebido se programó en C/C++ modular sobre el núcleo oficial Espressif Arduino/ESP-IDF v3.3.8, "
        "erradicando cualquier instrucción bloqueante (delay()) dentro de los lazos de muestreo y comunicación:"
    )
    add_bullet(
        doc, "Protocolo Binario Común (firmware/common/kntx_protocol.h): ",
        "Define mediante __attribute__((packed)) la trama cinemática kntx_packet_t (36 bytes: tipo 0x01, node_id, timestamp_ms "
        "sincronizado de 32 bits, cuaternión unitario quat[4] en IEEE-754 float32, aceleración accel[3] en unidades g, estado de "
        "calibración y contador secuencial seq_num de 16 bits para auditar pérdida de paquetes) y la trama de sincronía kntx_sync_t "
        "(10 bytes), además de las funciones inline de conjugado, producto de Hamilton y normalización segura."
    )
    add_bullet(
        doc, "Nodo Satélite 1 — SPI 3 MHz por Interrupción (nodo1_c3_bno085.ino): ",
        "Configura el bus SPI del ESP32-C3 a 3.0 MHz y habilita los reportes SH2_GAME_ROTATION_VECTOR y SH2_ACCELEROMETER cada "
        "10,000 µs (100 Hz) en el coprocesador SH-2 del BNO085. Al condicionar la transacción SPI a digitalRead(PIN_BNO_INT) == LOW, "
        "el tiempo máximo de lectura se redujo a 1.37–1.40 ms (cumpliendo RP-04 <= 1.5 ms). El disparo de paquetes ESP-NOW se "
        "gobierna con el temporizador hardware esp_timer_get_time() (resolución de 1 µs)."
    )
    add_bullet(
        doc, "Nodo Satélite 2 — Fusión Madgwick 6-DOF en CPU (nodo2_esp32_mpu6050.ino): ",
        "Ejecuta al arranque una calibración estática de 250 muestras para sustraer el offset (bias) de los tres ejes del "
        "giroscopio (RF-04). En cada ventana de 10,000 µs integra la derivada de cuaternión por velocidad angular y aplica un "
        "paso de descenso de gradiente con el vector gravitacional normalizado (β = 0.12), requiriendo únicamente sumas, "
        "productos y dos raíces cuadradas rápidas (~0.12 ms = 1.2% del presupuesto de CPU), demostrando por qué el ESP32-C3 "
        "puede ejecutar esta misma rutina sobre los sensores Bosch BMI160 en el PC5 sin afectar la pila ESP-NOW."
    )
    add_bullet(
        doc, "Gateway Dual-Core FreeRTOS y Descomposición Twist Con Signo (gateway_s3_freertos.ino): ",
        "Ancla la recepción Wi-Fi/ESP-NOW (g_rxQueue de 1,000 elementos), el consumidor de paquetes (Prioridad 4) y el transmisor "
        "SNTP periódico cada 1,000 ms (Prioridad 3) al Núcleo 0; y ancla el cierre de matriz cinemática, vigilancia Failsafe "
        "(timeout 350 ms con aritmética con signo int32_t), notificaciones BLE 5.0 y vaciado de la cola g_csvQueue por UART a "
        "921,600 bps al Núcleo 1. El ángulo articular se extrae proyectando la componente axial del cuaternión relativo "
        "q_rel = conj(q_prox) ⊗ q_dist mediante θ = 2·atan2(q_eje, w)·(180/π), preservando signo (±180°) y eliminando por "
        "completo el bloqueo de cardán (Gimbal Lock) en ±90°."
    )

    add_h(doc, "3.2 Modelo Analítico de Integridad de Señal SPI (3 MHz) y Presupuesto de Ciclo", level=2)
    add_p(
        doc,
        "Para respaldar analíticamente el requisito RP-04 previo a la captura presencial con osciloscopio en la fase final, "
        "se modeló la línea de reloj SCLK (3.0 MHz, periodo T = 333.3 ns) como una red RC de parámetros concentrados "
        "considerando la impedancia de salida CMOS del ESP32-C3 (R_out ≈ 40 Ω) y la capacitancia parásita combinada del caso "
        "más desfavorable en protoboard con conductores de < 5 cm (C_par = C_pin_MCU + C_protoboard + C_cable + C_pin_IMU ≈ 65 pF). "
        "La constante de tiempo resultante es τ = R_out · C_par = 2.60 ns, lo que arroja un tiempo de subida/bajada (10% a 90%) "
        "de t_r = 2.197 · τ = 5.71 ns, casi nueve veces inferior al umbral máximo de 50 ns fijado en RP-04 (en placa soldada "
        "C_par cae a ~15 pF, reduciendo t_r a ~1.3 ns). En la Figura 3.1 se grafica dicha respuesta transitoria junto con el "
        "presupuesto real de tiempos dentro de la ventana de 10 ms medido con el contador hardware esp_timer (1 µs)."
    )

    add_figure(
        doc,
        os.path.join(evid, "fig_modelo_analitico_spi_tiempos.png"),
        "Figura 3.1. (A) Modelo analítico RC de flancos SPI a 3 MHz sobre cableado As-Built < 5 cm (t_r = 5.7 ns < 50 ns); "
        "(B) Presupuesto temporal real del ciclo de 10 ms combinando la lectura SPI medida por esp_timer (1.39 ms) y el enlace ESP-NOW.",
        width_in=6.55,
        full_page=False,
    )

    add_h(doc, "3.3 Regla Institucional de Desbloqueo: Auditoría de Repositorio GitHub", level=2)
    p_repo = doc.add_paragraph()
    p_repo.paragraph_format.space_after = Pt(4)
    rb_r = p_repo.add_run("Enlace Directo al Repositorio Público Auditable: ")
    rb_r.bold = True; rb_r.font.name = "Calibri"; rb_r.font.size = Pt(10.2); rb_r.font.color.rgb = NAVY
    add_hyperlink(p_repo, GITHUB_URL, GITHUB_URL, font_size_pt=10.2, bold=True)

    add_p(
        doc,
        "La Tabla 3 documenta las ramas temáticas independientes y una muestra representativa de los hashes SHA-1 reales "
        "(verificables en vivo en la pestaña Commits / Insights -> Network del repositorio), acreditando la autoría técnica "
        "equitativa de ambos integrantes."
    )

    add_table_caption(doc, "Tabla 3. Registro auditable de ramas temáticas y hashes SHA-1 reales por integrante en GitHub.")
    add_table(
        doc,
        ["Hash SHA-1 Real", "Rama / Integración", "Autor Verificado en Git", "Descripción Técnica de la Contribución"],
        [
            ["df4b97c / 2540e0d", "feat/hardware-pcb-carcasas", "Jorge Carlos Contreras Rodríguez\n<15233640@modelo.edu.mx>", "Esquemático As-Built PC4, BOM y carcasa paramétrica IP54 (32.91 cm³) en OpenSCAD y malla .STL."],
            ["1f17e38 / 4ed491b", "feat/firmware-satelite-spi", "Yael Alejandro Yah Hernández\n<15234422@modelo.edu.mx>", "Protocolo binario kntx_protocol.h (36 B) y firmware Nodo 1 ESP32-C3 + BNO085 SPI 3 MHz + SNTP."],
            ["bd24ebf / 000efc7", "feat/firmware-satelite-spi", "Yael Alejandro Yah Hernández\n<15234422@modelo.edu.mx>", "Firmware Nodo 2 Madgwick 6-DOF @ 100 Hz y optimización SPI por pin INT (8.99 ms -> 1.39 ms)."],
            ["fb829ef / f3b2881", "feat/firmware-gateway-freertos", "Yael Alejandro Yah Hernández\n<15234422@modelo.edu.mx>", "Gateway Dual-Core FreeRTOS ESP32-S3, fix stack 4KB, Failsafe int32, UART 921.6 kbps y g_csvQueue."],
            ["0aece37 / 8cdb5a9", "feat/software-biomecanica", "Jorge Carlos Contreras Rodríguez\n<15233640@modelo.edu.mx>", "Logger serial Python CSV (RF-08), Grood & Suntay, detección foot-strike, Spline 101 pts y Bland-Altman."],
            ["9b3ff33 / b362b18", "feat/software-biomecanica", "Jorge Carlos Contreras Rodríguez\n<15233640@modelo.edu.mx>", "Dashboard HMI en vivo (Tkinter/Matplotlib), infografías y respaldo de datasets .CSV reales."],
            ["21ac405 / c5cb5fd", "main (consolidado)", "Yael Alejandro Yah Hernández\n<15234422@modelo.edu.mx>", "Descomposición Twist con signo (±180°) en Gateway y validación multi-patrón de 17,387 muestras."],
        ],
        widths=[1.15, 1.55, 1.80, 2.50],
        font_pt=8.3,
    )

    add_figure(
        doc,
        os.path.join(evid, "foto_github_repo.jpg"),
        "Figura 3.2. Captura real del repositorio público KNTX-Biomechanics-IMU en GitHub mostrando estructura normalizada "
        "(/docs, /firmware, /hardware, /software), 5 ramas activas, historial progresivo de commits y 2 contribuidores.",
        width_in=6.55,
        full_page=False,
    )

    # =========================================================================
    # 4.0 PRUEBAS PRELIMINARES Y PRIMERA PRUEBA FUNCIONAL (TRAZABILIDAD TOTAL)
    # =========================================================================
    add_h(doc, "4.0 Pruebas Preliminares y 'Primera Prueba Funcional' (Núcleo Demostrativo)", level=1)
    add_h(doc, "4.1 Metodología Experimental y Trazabilidad de Archivos Fuente Crudos (.CSV)", level=2)
    add_p(
        doc,
        "Todas las tablas y gráficas reportadas en esta sección provienen exclusivamente de mediciones reales ejecutadas "
        "sobre los tres módulos físicos KNTX operando en el banco de pruebas (24 de noviembre de 2026, temperatura ambiente "
        "26 °C), acumulando un total auditable de 48,670 filas de telemetría cruda almacenadas en la carpeta docs/evidencias/ "
        "del repositorio GitHub. La Tabla 4 detalla el origen exacto, duración, tamaño muestral y ecuaciones aplicadas a cada "
        "conjunto de datos."
    )

    add_table_caption(doc, "Tabla 4. Trazabilidad de corridas experimentales y archivos fuente crudos (.CSV) en el repositorio (48,670 muestras).")
    add_table(
        doc,
        ["ID Corrida", "Archivo Fuente en GitHub (docs/evidencias/)", "Duración / Muestras", "Condición Experimental Evaluada", "Métricas y Figuras Derivadas"],
        [
            ["EXP-01\n(Línea base v1)", "evidencia_antes_uart115200.csv\n+ bitácora serial COM7/COM4", "15.03 s\n2,071 filas CSV", "Operación inicial previa a ajustes: polling SPI sin pin INT y puerto UART a 115,200 bps.", "Detectó cuello de botella SPI (8.99 ms) y saturación UART (68.9 Hz, P95=10 ms) -> Figuras 4.1 y 4.2."],
            ["EXP-02\n(Estática 60 s)", "pv01_pv03_pv06_reposo_60s.csv\n+ kntx_metrics_summary.csv", "60.04 s\n12,016 filas CSV\n(6,000 N1 + 6,016 N2)", "Sensores inmóviles tras optimización (SPI por INT, UART 921.6 kbps, g_csvQueue y SNTP 1 s).", "PV-01 (99.94 / 100.21 Hz), PV-03 (Jitter P95 = 1.0 / 0.0 ms) y PV-06 (Deriva 0.021 y 0.977 °/min) -> Fig. 4.3 y 4.4."],
            ["EXP-03\n(Caso Crítico)", "pv07_gimballock_failsafe_oficial.csv\n+ pv07_..._consola.log", "30.60 s\n4,852 filas CSV", "Giro pasando por 90° (0–15 s), desconexión física USB de Nodo 2 en t=17.2 s y reconexión en t=30.0 s.", "Cruce limpio a 136.36° sin Gimbal Lock + disparo [FAILSAFE] en 359 ms + 0 overflows -> Figura 4.5."],
            ["EXP-04\n(Signo Twist)", "kntx_live_20261124_114104.csv", "61.72 s\n12,344 filas CSV\n(6,171 N1 + 6,173 N2)", "Secuencia desde Dashboard HMI: 3 flexiones a +90°, 1 a +167°, 1 a +90° y 2 inversas (-88° y -16.5°).", "Demostró ambigüedad de signo en 2·acos(|w|) y validó descomposición Twist 2·atan2(q_z, w) -> Figura 4.6."],
            ["EXP-05\n(Multi-patrón)", "kntx_live_20261124_115539.csv", "86.91 s\n17,387 filas CSV\n(8,695 N1 + 8,692 N2)", "Prueba integral con Gateway ya actualizado con Twist con signo: inversas, ráfagas rápidas y escalones >90°.", "100.0% de paquetes recibidos en 86.9 s, rango -83.87° a +157.34° y retorno exacto a 0.0° -> Figura 4.7."],
        ],
        widths=[0.95, 1.75, 1.15, 1.65, 1.50],
        font_pt=8.2,
    )

    add_h(doc, "4.2 Análisis Detallado de Evidencias Experimentales y Caso Crítico", level=2)

    # Sub-bloque A: Antes vs Después
    add_p(
        doc,
        "En la corrida inicial EXP-01 se identificaron cuatro limitaciones reales en banco: (1) llamar continuamente a "
        "bno08x.getSensorEvent() sin consultar el pin físico INT retenía el bus SPI hasta 8,990 µs (8.99 ms > 1.5 ms); "
        "(2) la tarea taskSyncBroadcast con 2 KB de stack generaba un reinicio Core 0 panic al invocar al driver Wi-Fi; "
        "(3) la resta sin signo uint32_t entre núcleos producía underflow disparando falsos avisos [FAILSAFE]; y (4) transmitir "
        "dos líneas CSV cada 10 ms (~15,000 B/s ≈ 150 kbps) sobre un UART a 115,200 bps saturaba el buffer serie limitando la "
        "tasa registrada a 68.91 Hz (Nodo 1) y 68.84 Hz (Nodo 2). Tras aplicar la lectura guiada por pin INT, ampliar los stacks "
        "a 4 KB / 8 KB, usar aritmética con signo int32_t e incrementar el UART a 921,600 bps con la cola dedicada g_csvQueue, "
        "la lectura SPI cayó 6.4 veces hasta 1.37–1.40 ms y la tasa subió al 100% nominal (Figuras 4.1 y 4.2).",
        bold_prefix="A) Diagnóstico y Corrección en Banco (Origen: EXP-01 vs. EXP-02): "
    )

    add_figure(
        doc,
        os.path.join(evid, "fig_consola_antes_despues.png"),
        "Figura 4.1. Comparativa directa de salidas reales de consola capturadas en los puertos COM7 (Nodo 1) y COM4 (Gateway): "
        "estado inicial con fallos en banco (izquierda, EXP-01) frente a telemetría depurada (derecha, EXP-02 y EXP-03).",
        width_in=6.60,
    )
    add_figure(
        doc,
        os.path.join(evid, "fig_mejora_spi_uart.png"),
        "Figura 4.2. Mejora cuantitativa medida tras las correcciones de firmware: (A) tiempo máximo de lectura SPI en ESP32-C3 + BNO085 "
        "(8.99 ms -> 1.39 ms <= 1.5 ms); (B) frecuencia efectiva multi-nodo registrada en archivo .CSV (69.3 Hz -> 99.94 / 100.21 Hz).",
        width_in=6.55,
    )

    # Sub-bloque B: PV-01, PV-03 y PV-06 (60 s)
    add_p(
        doc,
        "A partir del archivo pv01_pv03_pv06_reposo_60s.csv (60.04 s de reloj de pared; 12,016 registros totales), el script "
        "kntx_biomechanics_analysis.py calculó para cada nodo la diferencia entre marcas consecutivas Δt_k = t_k - t_{k-1} y el "
        "jitter instantáneo J_k = |Δt_k - 10 ms| en régimen permanente sincronizado por SNTP. El Nodo 1 registró 6,000 muestras "
        "(99.94 Hz, 99.9% de los paquetes esperados, Jitter mediano = 0.00 ms, P95 = 1.00 ms) y el Nodo 2 registró 6,016 muestras "
        "(100.21 Hz, 100.0%, Jitter mediano = 0.00 ms, P95 = 0.00 ms), manteniendo 1,000/1,000 espacios libres en g_rxQueue "
        "(0 overflows). Sobre ese mismo dataset estático se extrajo el ángulo de guiñada desenvuelto ψ(t) = unwrap(atan2(2(wz+xy), "
        "1-2(y²+z²))) y se ajustó por mínimos cuadrados su pendiente lineal en grados por minuto, obteniendo 0.021 °/min para el "
        "BNO085 (Game Rotation Vector) y 0.977 °/min para el MPU-6050 (Madgwick 6-DOF), cumpliendo holgadamente RP-03 (< 3 °/min) "
        "(Tabla 5, Figura 4.3 y Figura 4.4).",
        bold_prefix="B) Validación de Red 100 Hz, Sincronía SNTP y Deriva Estática (Origen: EXP-02, 12,016 muestras): "
    )

    add_table_caption(doc, "Tabla 5. Estadísticos metrológicos medidos en corrida estática continua EXP-02 (60.04 s, 12,016 muestras).")
    add_table(
        doc,
        ["Nodo Evaluado (EXP-02)", "Muestras (60.04 s)", "Frecuencia Efectiva", "% Paquetes Recibidos", "Jitter Mediana / P95", "Deriva Yaw (PV-06)"],
        [
            ["Nodo 1 — Tibia (ESP32-C3 + BNO085 SPI)", "6,000", "99.94 Hz", "99.9% (meta ≥ 95%)", "0.00 ms / 1.00 ms (< 5 ms)", "0.021 °/min (< 3 °/min)"],
            ["Nodo 2 — Fémur (ESP32 + MPU-6050 Madgwick)", "6,016", "100.21 Hz", "100.0% (meta ≥ 95%)", "0.00 ms / 0.00 ms (< 5 ms)", "0.977 °/min (< 3 °/min)"],
        ],
        widths=[1.85, 0.95, 1.00, 1.05, 1.15, 1.00],
        font_pt=8.4,
    )

    add_figure(
        doc,
        os.path.join(evid, "fig_pv01_pv03_jitter_60s.png"),
        "Figura 4.3. Gráfica generada desde pv01_pv03_pv06_reposo_60s.csv (EXP-02): (Superior) Jitter instantáneo |Δt - 10 ms| por debajo "
        "del umbral rojo de 5.0 ms (P95 = 1.00 ms y 0.00 ms); (Inferior) Frecuencia efectiva segundo a segundo clavada en 100 Hz.",
        width_in=6.55,
    )
    add_figure(
        doc,
        os.path.join(evid, "fig_pv06_deriva_yaw_60s.png"),
        "Figura 4.4. Evolución temporal del ángulo Yaw en reposo durante 60 s (EXP-02, PV-06): pendiente de deriva de 0.021 °/min en BNO085 "
        "y 0.977 °/min en MPU-6050 con Madgwick, ambas dentro de la banda permitida sin magnetómetro (±3.0 °/min).",
        width_in=6.55,
    )

    # Sub-bloque C: Caso crítico (90° + Failsafe) y pruebas con signo desde HMI
    add_p(
        doc,
        "En la corrida EXP-03 (pv07_gimballock_failsafe_oficial.csv, 4,852 muestras) se ejecutó el Caso Crítico obligatorio del "
        "Proyecto 10: primero se rotó el Nodo 1 sosteniendo ~87°–90° y cruzando continuamente hasta 136.36° sin presentar bloqueo "
        "de cardán; posteriormente, en t = 17.2 s se desconectó físicamente la alimentación USB del Nodo 2. Como registra "
        "pv07_gimballock_failsafe_consola.log, exactamente 359 ms después el Gateway emitió '# [FAILSAFE] Nodo 2 desconectado -> "
        "marcado NULL (BLE/FreeRTOS continuo)', actualizó la máscara activa de 0x07 a 0x03 y mantuvo al Nodo 1 transmitiendo a "
        "100.0 Hz exactos con 0 overflows hasta que el Nodo 2 fue reconectado en caliente en t = 30.0 s, reintegrándose de forma "
        "automática (Figura 4.5).",
        bold_prefix="C) Caso Crítico: Cruce por 90° sin Gimbal Lock, Apagado en Vivo (Failsafe) y Reconexión (Origen: EXP-03): "
    )

    add_figure(
        doc,
        os.path.join(evid, "fig_pv07_gimballock_failsafe.png"),
        "Figura 4.5. Caso Crítico PC4 (EXP-03): cruce continuo por 90° hasta 136.4° sin Gimbal Lock, desconexión física del Nodo 2 "
        "en t = 17.2 s con activación de Failsafe en 359 ms (franja amarilla: Nodo 1 sigue a 100 pkt/s sin interrupción) y reconexión en t = 30.0 s.",
        width_in=6.55,
    )

    add_p(
        doc,
        "Finalmente, usando el Dashboard HMI (kntx_live_dashboard.py) se ejecutaron dos ensayos cinemáticos adicionales: en EXP-04 "
        "(kntx_live_20261124_114104.csv, 12,344 muestras) se detectó que la fórmula geodésica inicial 2·arccos(|w|) reflejaba las "
        "flexiones inversas (-90°) como positivas (+90°). Al sustituirla en el firmware del Gateway por la descomposición Twist "
        "alrededor del eje articular θ = 2·atan2(q_eje, w) (Figura 4.6) y validarla en tiempo real durante 86.91 s continuos en "
        "EXP-05 (kntx_live_20261124_115539.csv, 17,387 muestras, 100.0% de paquetes sin pérdidas), el sistema discriminó con "
        "precisión flexiones positivas (+90° a +157.34°), flexiones inversas (-83.87°), ráfagas rápidas a 100 Hz y retorno "
        "exacto a 0.0° sin acumulación de deriva (Figura 4.7).",
        bold_prefix="D) Refinamiento de Signo Articular (Twist Quaternion) y Ensayo Multi-Patrón en Vivo (Origen: EXP-04 y EXP-05): "
    )

    add_figure(
        doc,
        os.path.join(evid, "fig_prueba_flexiones_signo.png"),
        "Figura 4.6. Análisis de EXP-04 (61.7 s, 12,344 muestras): comparación entre el ángulo sin signo 2·acos(|w|) (panel superior) "
        "y la proyección Twist con signo 2·atan2(q_z, w) (panel inferior), discriminando +166.95° y flexión inversa a -88.23°.",
        width_in=6.55,
    )
    add_figure(
        doc,
        os.path.join(evid, "fig_multiples_pruebas_reciente.png"),
        "Figura 4.7. Ensayo prolongado multi-patrón EXP-05 con el firmware Twist ya cargado en el Gateway (86.91 s, 17,387 muestras, "
        "100.0% de recepción en ambos nodos): flexiones negativas (-83.87°), oscilaciones rápidas, cruces >90° (+157.34°) y aceleración tibial.",
        width_in=6.55,
    )

    # =========================================================================
    # 4.3 TABLA OFICIAL DE CONTRASTACIÓN PC2 VS PC4 Y ARQUETIPO C
    # =========================================================================
    add_h(doc, "4.3 Tabla Oficial de Contrastación Cuantitativa de Criterios de Aceptación (PC2 vs PC4)", level=2)
    add_table_caption(doc, "Tabla 6. Contrastación cuantitativa oficial de magnitudes experimentales medidas en PC4 frente a los umbrales del PC2.")
    add_table(
        doc,
        ["ID Req.", "Criterio de Aceptación Cuantitativo (PC2)", "Valor Experimental Medido en PC4", "Instrumento / Fuente Verificable", "Dictamen PC4"],
        [
            ["RF-01 / RP-01 /\nRQ-03",
             "Muestreo simultáneo a 100 Hz efectivos por nodo, ≥ 95% de paquetes recibidos y sincronía (jitter) < 5 ms",
             "EXP-02 (60 s) y EXP-05 (86.9 s): Nodo 1 = 99.94 Hz (99.9%–100.0% pkt, Jitter med=0.0 ms, P95=1.0 ms); Nodo 2 = 100.21 Hz (100.0% pkt, P95=0.0 ms); 0 overflows (1000/1000 libres).",
             "Gateway ESP32-S3 + Archivos CSV EXP-02 y EXP-05",
             "CUMPLE\nSATISFACTORIAMENTE"],
            ["RF-02 / RF-03 /\nRP-02",
             "Calibración < 7 min; exactitud estática RMSE ≤ 3° (goniómetro) y en trote (10–12 km/h) RMSE ≤ 5° (Kinovea)",
             "Tara neutral ('c') completada en < 15 s (< 7 min). Rango continuo validado de -88.23° a +166.95° sin Gimbal Lock y retorno a 0.00° ± 0.2°. Contrastación con goniómetro clínico y Kinovea programada en PC5.",
             "Dashboard HMI Python + CSV EXP-03/04/05 (PC5: Goniómetro y Kinovea)",
             "CUMPLE CALIBRACIÓN Y SIN GIMBAL LOCK\n(Kinovea en PC5)"],
            ["RF-04 / RP-03",
             "Inicialización estática de 10 s y deriva de yaw < 1 °/min (con mag) y < 3 °/min (sin mag)",
             "Inicialización estática verificada (Calib_Status = 3). Deriva medida en reposo (60 s, 6-DOF sin mag): BNO085 = 0.021 °/min; MPU-6050 Madgwick = 0.977 °/min (ambos < 3.0 °/min).",
             "CSV EXP-02 + regresión lineal en kntx_biomechanics_analysis.py",
             "CUMPLE\nSATISFACTORIAMENTE"],
            ["RF-05 / RF-07",
             "Detección de contacto inicial ≤ 8.3 ms en > 90% de ≥ 100 ciclos y comparación contra banda normativa (8–10 sujetos)",
             "Umbral axial > 3.0 g operativo en Gateway/HMI (pico 3.5 g detectado en ventana de 10 ms) y normalización Spline cúbica a 101 puntos lista en Python. Muestra de corredores corresponde a PV-08 (PC5).",
             "Firmware Gateway / Spoofer / Suite Python (PC5: Caminadora + 120 fps)",
             "AVANCE LÓGICO COMPLETO\n(Ensayo PV-08 en PC5)"],
            ["RF-06 / RP-04 /\nRP-05 / RP-08 /\nRQ-02",
             "SPI 3 MHz ≤ 1.5 ms (<50 ns); latencia aire < 2 ms (P95 < 25 ms), 3×30 min sin caídas, autonomía > 3 h y T < 40 °C",
             "Lectura SPI BNO085 medida con esp_timer (1 µs): 1.37–1.40 ms (≤ 1.5 ms, 18,775 lecturas con BER = 0%); modelo RC t_r = 5.7 ns (< 50 ns); Failsafe en 359 ms + BLE continuo. Captura en osciloscopio y descarga LiPo 3 h programadas en PC5.",
             "Temporizador hardware esp_timer (1 µs) + Modelo RC (PC5: Osciloscopio)",
             "CUMPLE SPI Y FAILSAFE\n(Osciloscopio y 3 h en PC5)"],
        ],
        widths=[0.95, 1.75, 2.05, 1.25, 1.00],
        font_pt=8.1,
    )

    add_h(doc, "4.4 Verificación de Requisitos Específicos del Arquetipo C (Guía Oficial PC4)", level=2)
    add_bullet(doc, "(1) Ensamble físico limpio en protoboard avanzada: ", "Cumplido con los 3 módulos armados con cableado peinado < 5 cm (Figuras 2.1 y 2.2).")
    add_bullet(doc, "(2) Adquisición limpia de variables físicas en tiempo real a 100 Hz: ", "Cumplido con 48,670 muestras reales vía ESP-NOW sin pérdidas en EXP-02 y EXP-05.")
    add_bullet(doc, "(3) Procesamiento embebido en tiempo real: ", "Cumplido mediante fusión SH-2 / Madgwick 6-DOF en satélites y descomposición Twist de cuaterniones relativos en el Gateway.")
    add_bullet(doc, "(4) Mecanismo de resiliencia ante pérdida de enlace: ", "Cumplido y demostrado en vivo en EXP-03 con detección Failsafe en 359 ms, cola FreeRTOS con 0 overflows y reconexión automática.")

    # =========================================================================
    # 5.0 DESAFÍOS TÉCNICOS Y ACCIONES CORRECTIVAS
    # =========================================================================
    add_h(doc, "5.0 Desafíos Técnicos, Imprevistos y Acciones Correctivas", level=1)
    add_table_caption(doc, "Tabla 7. Bitácora de resolución de problemas de ingeniería detectados durante la implementación y pruebas de PC4.")
    add_table(
        doc,
        ["#", "Problema / Imprevisto Real en Taller", "Causa Raíz Técnica Identificada", "Acción Correctiva Aplicada y Verificación"],
        [
            ["1", "Duración de lectura SPI del BNO085 de hasta 8.99 ms en primera prueba", "Sondeo continuo (polling) de bno08x.getSensorEvent() sin sincronizar con la línea física de interrupción H_INTN.", "Se condicionó la transacción SPI a digitalRead(PIN_BNO_INT) == LOW; el tiempo máximo cayó 6.4× a 1.37–1.40 ms (≤ 1.5 ms)."],
            ["2", "Reinicio Guru Meditation Error (Core 0 panic) al arrancar Gateway", "Pila (stack) de 2,048 B insuficiente en taskSyncBroadcast para llamadas ESP-NOW y uso de API ISR dentro de contexto de tarea Wi-Fi (Core 3.x).", "Se incrementó el stack a 4,096 B (8,192 B en Core 1) y se empleó xQueueSend(..., 0); se lograron 0 reinicios y 0 overflows."],
            ["3", "Falsas alertas [FAILSAFE] cada ~30 ms con nodos activos", "Condición de carrera entre núcleos: resta sin signo uint32_t (nowMs - lastRxMs) producía underflow (~4.29×10⁹ ms) cuando Core 0 actualizaba 1 ms después.", "Conversión a resta con signo int32_t protegida por Mutex y umbral de 350 ms; 0 falsos disparos y detección real exacta en 359 ms."],
            ["4", "Frecuencia limitada a ~69 Hz y jitter P95 = 10 ms en EXP-01", "Cuello de botella físico en UART a 115,200 bps (~150 kbps requeridos para 2 nodos CSV) y descarte en bordes de ventana de 10 ms.", "Migración a 921,600 bps (buffer TX 4 KB) + cola dedicada g_csvQueue (256 ítems); la tasa subió a 99.94 / 100.21 Hz con P95 ≤ 1.0 ms."],
            ["5", "Flexión inversa (-90°) se reportaba como positiva (+90°) en EXP-04", "La distancia geodésica 2·arccos(|w|) es estrictamente no negativa y pierde el sentido de giro articular.", "Implementación de descomposición Twist con signo θ = 2·atan2(q_eje, w); validada en EXP-05 de -83.87° a +157.34° con retorno a 0.0°."],
            ["6", "Desabasto y sobrecosto (+163%, ~$1,000 MXN/u) de sensores BNO085 extra", "Restricción de inventario internacional e importación incompatible con el cierre del 1 de diciembre.", "Adopción aprobada de Arquitectura Híbrida: conservar BNO085 en Tibia e integrar 3× Bosch BMI160 (SPI 3 MHz, 6-DOF, ±16 g) en placas preperforadas para PC5."],
        ],
        widths=[0.30, 1.75, 2.20, 2.75],
        font_pt=8.2,
    )

    # =========================================================================
    # 6.0 ACTUALIZACIÓN AL PLAN DEL PROYECTO (GANTT HACIA PC5)
    # =========================================================================
    add_h(doc, "6.0 Actualización al Plan del Proyecto (Ruta Crítica hacia PC5 y Expotrónica)", level=1)
    add_p(
        doc,
        "La Figura 6.1 y la Tabla 8 presentan la reprogramación realista de la ruta crítica al corte del 24 de noviembre de "
        "2026: mañana 25 de noviembre arriban los sensores Bosch BMI160 para portar el driver SPI a 3 MHz sobre los dos "
        "ESP32-C3 adicionales; del 26 al 28 de noviembre se ejecuta la soldadura definitiva en placas preperforadas compactas "
        "y el cierre de las carcasas impresas en PETG con bandas textiles; y del 28 al 30 de noviembre se completan las "
        "capturas de osciloscopio en laboratorio, las pruebas dinámicas en caminadora con Kinovea (PV-08) y el cierre "
        "documental/presupuestal del PC5 previo a Expotrónica (1 de diciembre de 2026)."
    )

    add_table_caption(doc, "Tabla 8. Cronograma reprogramado y ruta crítica hacia el Punto de Control 5 y Expotrónica.")
    add_table(
        doc,
        ["Etapa / Actividad Crítica", "Periodo Reprogramado", "% Avance", "Responsable", "Entregable / Meta de Cierre"],
        [
            ["4–5. Firmware Dual-Core, HMI Python, Pruebas y Reporte PC4", "18 nov – 24 nov 2026", "95%–100%", "Ambos", "GitHub activo, 48,670 muestras CSV, PC4 y Video 3–5 min"],
            ["6. Recepción Bosch BMI160 e integración SPI 3 MHz en ESP32-C3", "25 nov – 26 nov 2026", "0% (Ruta Crítica)", "Yael", "3 nodos satélite + lumbar operando en SPI 3 MHz a 100 Hz"],
            ["7. Soldadura en placa preperforada, LiPo DW01 y carcasas PETG", "26 nov – 28 nov 2026", "15% (Ruta Crítica)", "Jorge", "4 módulos compactos < 50 g / < 40 cm³, prueba IP54 y cortes LiPo"],
            ["8. Osciloscopio en sitio + Validación en caminadora y Kinovea", "28 nov – 30 nov 2026", "0% (Ruta Crítica)", "Ambos", "Oscilogramas SPI/GPIO, Bland-Altman, ICC > 0.85 y SUS > 75"],
            ["9. Entrega Reporte Final PC5, Auditoría Viva y Expotrónica", "30 nov – 01 dic 2026", "0%", "Ambos", "Matriz de Cumplimiento 100%, cierre presupuestal y demostración"],
        ],
        widths=[2.15, 1.25, 0.90, 0.80, 1.90],
        font_pt=8.2,
    )

    add_figure(
        doc,
        os.path.join(evid, "gantt_actualizado_pc4.png"),
        "Figura 6.1. Cronograma actualizado del Proyecto KNTX al 24 de noviembre de 2026 mostrando el avance ejecutado y la ruta crítica en rojo hacia PC5.",
        width_in=6.60,
    )

    # =========================================================================
    # 7.0 PROTOCOLO DEL VIDEO EXPLICATIVO Y 8.0 REFERENCIAS APA 7
    # =========================================================================
    add_h(doc, "7.0 Estructura del Video Explicativo de la Primera Prueba Funcional (3 a 5 min)", level=1)
    add_table_caption(doc, "Tabla 9. Guion técnico minuto a minuto del Video Explicativo obligatorio (sustituye protocolo Think Aloud).")
    add_table(
        doc,
        ["Segmento Temporal", "Expositor en Cuadro", "Contenido Técnico Demostrado en Laboratorio (Sin Cortes Fraudulentos)"],
        [
            ["0:00 – 1:30\n[Montaje As-Built y Arquitectura]", "Jorge C. Contreras\ny Yael A. Yah", "Paneo en primer plano de los 3 módulos físicos en protoboard (< 5 cm en SPI), explicación de correspondencia con los diagramas As-Built, justificación de transición a Bosch BMI160 + placa preperforada y muestra del repositorio GitHub."],
            ["1:30 – 3:30\n[Puesta en Marcha y Telemetría Viva]", "Yael A. Yah y\nJorge C. Contreras", "Energización en tiempo real y conexión al Dashboard HMI Python (921.6 kbps): visualización simultánea de los 3 indicadores en verde (100 Hz), tara instantánea a 0.0° y muestra de las secciones clave de código no bloqueante (SPI INT y FreeRTOS)."],
            ["3:30 – 5:00\n[Perturbación, 90° y Contrastación PC2]", "Ambos integrantes", "1) Flexiones positivas (+90°, >135°) e inversas (-85°) demostrando ausencia total de Gimbal Lock con descomposición Twist; 2) Desconexión en vivo del Nodo 2 mostrando alerta roja [FAILSAFE] en 359 ms mientras el Nodo 1 sigue a 100 Hz con 0 overflows y reconexión automática; 3) Cierre verbal contrastando métricas contra el PC2."],
        ],
        widths=[1.35, 1.25, 4.40],
        font_pt=8.4,
    )

    add_h(doc, "8.0 Referencias Técnicas y Normativas (Formato APA 7)", level=1)
    refs = [
        "Bosch Sensortec. (2020). BMI160: Small, low power inertial measurement unit — Data sheet (BST-BMI160-DS000-09).",
        "Cereatti, A., Gurchiek, R., Mündermann, A., Fantozzi, S., Horak, F., Delp, S., & Aminian, K. (2024). ISB recommendations on the definition, estimation, and reporting of joint kinematics in human motion analysis applications using wearable inertial measurement technology. Journal of Biomechanics, 173, 112225.",
        "Ceriola, L., Molinaro, L., Taborri, J., Patanè, F., & Mileti, I. (2026). IMU- and vision-based measurement techniques for joint kinematics: A narrative review. Sensors, 26(16), 5063.",
        "CEVA / Hillcrest Labs. (2020). BNO080 / BNO085 / BNO086 9-axis System in Package (SiP) Data Sheet (1000-3927 v1.16).",
        "Espressif Systems. (2023). ESP32-C3 Series Datasheet & ESP32-S3-WROOM-1 Datasheet; ESP-NOW User Guide.",
        "Grood, E. S., & Suntay, W. J. (1983). A joint coordinate system for the clinical description of three-dimensional motions: Application to the knee. Journal of Biomechanical Engineering, 105(2), 136–144.",
        "International Electrotechnical Commission. (2013/2017). IEC 60529 (Degrees of protection IP Code) & IEC 62133-2 (Safety requirements for portable sealed secondary lithium cells).",
        "Madgwick, S. O. H., Harrison, A. J. L., & Vaidyanathan, R. (2011). Estimation of IMU and MARG orientation using a gradient descent algorithm. IEEE International Conference on Rehabilitation Robotics, 1–7.",
        "Secretaría de Energía. (2018). Norma Oficial Mexicana NOM-001-SEDE-2018, Instalaciones Eléctricas (utilización).",
    ]
    for rf in refs:
        p_rf = doc.add_paragraph()
        p_rf.paragraph_format.left_indent = Inches(0.32)
        p_rf.paragraph_format.first_line_indent = Inches(-0.32)
        p_rf.paragraph_format.space_after = Pt(3)
        p_rf.paragraph_format.line_spacing = 1.08
        r_rf = p_rf.add_run(rf)
        r_rf.font.name = "Calibri"
        r_rf.font.size = Pt(9.0)
        r_rf.font.color.rgb = DARK

    os.makedirs(os.path.dirname(out_docx), exist_ok=True)
    doc.save(out_docx)
    print("[OK] Reporte Maestro PC4 FINAL generado exitosamente:", out_docx)


if __name__ == "__main__":
    repo = r"c:\Proyectos\Proyectos 7\KNTX-Biomechanics-IMU"
    out = os.path.join(repo, "docs", "reportes", "PC4_Diseno_a_Detalle_KNTX_FINAL.docx")
    build_final_pc4(out, repo)
