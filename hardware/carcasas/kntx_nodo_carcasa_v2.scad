// ============================================================================
// KNTX — Carcasa Biomecánica Paramétrica para Nodo Satélite (PC4 / PC5)
// Archivo fuente editable OpenSCAD (.scad) exportable a .STL / .STEP
// Autor: Jorge Carlos Contreras Rodríguez (Diseño Mecánico / Carcasas 3D)
//
// Cumplimiento de requisitos PC2:
//  - RP-09: Volumen exterior < 40 cm^3 (44 x 34 x 22 mm = 32.9 cm^3) y masa < 50 g.
//  - RQ-04: Labio perimetral de cierre tipo machihembrado para protección IP54.
//  - RF-09: Ranuras laterales pasacinta para banda elástica de 25 mm (colocación < 5 min).
//
// Parámetros de impresión recomendados (PC4 Sección 2.1):
//  - Filamento: PETG (resistente a sudor y temperatura < 40 °C)
//  - Infill: 25% giroide | Perímetros: 3 | Altura de capa: 0.20 mm
//  - Orientación: Base plana sobre cama (capas paralelas al plano de sujeción)
// ============================================================================

$fn = 32;

// Dimensiones exteriores (mm) -> Volumen = 44 * 34 * 22 = 32,912 mm^3 = 32.91 cm^3 (< 40 cm^3)
ext_len = 44.0;
ext_wid = 34.0;
ext_hgt = 22.0;
wall    = 2.0;
fillet  = 3.0;

// Ranuras para banda elástica textil (ancho 25 mm, espesor 2.5 mm)
strap_w = 25.0;
strap_t = 2.6;

module rounded_box(l, w, h, r) {
    hull() {
        for (x = [-l/2 + r, l/2 - r])
            for (y = [-w/2 + r, w/2 - r])
                translate([x, y, 0])
                    cylinder(h = h, r = r);
    }
}

module kntx_base_housing() {
    difference() {
        union() {
            // Cuerpo principal redondeado (ergonómico sobre prominencias óseas)
            rounded_box(ext_len, ext_wid, ext_hgt - 4.0, fillet);
            // Labio superior para sellado IP54 contra salpicaduras
            translate([0, 0, ext_hgt - 4.0])
                rounded_box(ext_len - wall, ext_wid - wall, 2.0, fillet - 0.5);
        }
        // Cavidad interna para placa preperforada/PCB (ESP32-C3 + BNO085 + LiPo 400 mAh)
        translate([0, 0, wall])
            rounded_box(ext_len - 2*wall, ext_wid - 2*wall, ext_hgt, max(1.0, fillet - wall));
        // Ranura pasacinta izquierda y derecha (sujeción sin rotación sobre piel)
        for (sx = [-ext_len/2 + 4.0, ext_len/2 - 4.0]) {
            translate([sx, 0, 3.0])
                cube([strap_t, strap_w, 4.0], center = true);
        }
        // Puerto USB-C / carga con tapa elastomérica IP54
        translate([ext_len/2 - wall/2, 0, 7.5])
            cube([wall + 2.0, 9.5, 4.0], center = true);
    }
}

module kntx_lid() {
    translate([0, ext_wid + 8.0, 0])
    difference() {
        rounded_box(ext_len, ext_wid, 4.0, fillet);
        translate([0, 0, 2.0])
            rounded_box(ext_len - wall + 0.3, ext_wid - wall + 0.3, 2.2, fillet - 0.5);
    }
}

// Renderizar base y tapa lado a lado para impresión 3D
kntx_base_housing();
kntx_lid();
