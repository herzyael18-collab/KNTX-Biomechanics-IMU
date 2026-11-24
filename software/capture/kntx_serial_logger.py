#!/usr/bin/env python3
"""
kntx_serial_logger.py
Captura telemetría en tiempo real desde el Gateway KNTX (ESP32-S3) vía USB Serial,
guarda un archivo .CSV estandarizado (RF-08) y genera un reporte automático de
métricas para PV-01 (frecuencia efectiva y % de paquetes) y PV-03 (sincronía / jitter < 5 ms).

Uso:
    python kntx_serial_logger.py --port COM4 --duration 600 --out sesion_pv01.csv
"""

import argparse
import csv
import sys
import time
from collections import defaultdict
import numpy as np
import serial


CSV_HEADER = [
    "Timestamp_ms", "Node_ID",
    "Quat_W", "Quat_X", "Quat_Y", "Quat_Z",
    "Accel_X", "Accel_Y", "Accel_Z",
    "Calib_Status", "Knee_Deg"
]


def run_capture(port: str, baud: int, duration_s: float, out_path: str, send_calib: bool):
    print(f"[KNTX] Conectando a {port} @ {baud} bps por {duration_s:.1f} s...")
    ser = serial.Serial(port, baud, timeout=1.0)
    time.sleep(1.5)
    ser.reset_input_buffer()

    if send_calib:
        print("[KNTX] Enviando comando 'c' (calibracion postura neutral)...")
        ser.write(b"c")

    start_time = time.time()
    per_node_ts = defaultdict(list)
    total_rows = 0

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)

        try:
            while (time.time() - start_time) < duration_s:
                raw = ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue
                if raw.startswith("#"):
                    print(raw)
                    continue
                if raw.startswith("Timestamp_ms"):
                    continue

                parts = raw.split(",")
                if len(parts) < 10:
                    continue

                try:
                    ts = int(parts[0])
                    nid = int(parts[1])
                    vals = [float(x) for x in parts[2:9]]
                    calib = int(parts[9])
                    knee = float(parts[10]) if len(parts) > 10 else -1.0
                except ValueError:
                    continue

                writer.writerow([ts, nid] + vals + [calib, knee])
                per_node_ts[nid].append(ts)
                total_rows += 1
        except KeyboardInterrupt:
            print("\n[KNTX] Captura detenida manualmente por el usuario.")
        finally:
            ser.close()

    elapsed = max(time.time() - start_time, 1e-3)
    print("\n================ RESUMEN DE CAPTURA KNTX ================")
    print(f"Archivo guardado : {out_path}")
    print(f"Duracion real    : {elapsed:.2f} s")
    print(f"Filas CSV totales: {total_rows}")
    for nid, ts_list in sorted(per_node_ts.items()):
        arr = np.array(ts_list, dtype=np.float64)
        n = len(arr)
        eff_hz = n / elapsed
        expected = elapsed * 100.0
        pct_rx = min(100.0, (n / max(expected, 1.0)) * 100.0)
        diffs = np.diff(arr) if n > 1 else np.array([10.0])
        jitter_ms = np.abs(diffs - 10.0)
        p95_jitter = float(np.percentile(jitter_ms, 95)) if len(jitter_ms) else 0.0
        print(
            f"  Nodo {nid}: {n} muestras | {eff_hz:.2f} Hz ({pct_rx:.1f}% esperado) | "
            f"Jitter med={np.median(jitter_ms):.2f} ms | P95={p95_jitter:.2f} ms"
        )
    print("=========================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Logger Serial CSV para Gateway KNTX (RF-08)")
    parser.add_argument("--port", required=True, help="Puerto COM del ESP32-S3 (ej. COM4)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (default 115200)")
    parser.add_argument("--duration", type=float, default=60.0, help="Duracion en segundos (600 para PV-01)")
    parser.add_argument("--out", default="kntx_session.csv", help="Ruta del archivo CSV de salida")
    parser.add_argument("--calib", action="store_true", help="Enviar comando 'c' de tara al iniciar")
    args = parser.parse_args()
    run_capture(args.port, args.baud, args.duration, args.out, args.calib)
