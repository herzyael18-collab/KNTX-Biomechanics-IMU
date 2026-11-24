#!/usr/bin/env python3
"""
kntx_serial_monitor.py
Herramienta rápida para leer salida serial de cualquier placa KNTX (Gateway o Nodos),
enviar comandos opcionales ('c', 'g', 'm', 'r') y verificar funcionamiento en segundos.
"""

import argparse
import sys
import time
import serial
import serial.tools.list_ports


def list_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No hay puertos COM detectados.")
        return
    for p in ports:
        print(f"  {p.device} | {p.description} | HWID={p.hwid}")


def monitor(port: str, baud: int, seconds: float, send_cmd: str):
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 0.5
    ser.dtr = False
    ser.rts = False
    ser.open()
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setRTS(False)
    time.sleep(0.5)
    if send_cmd:
        ser.write(send_cmd.encode("utf-8"))
        print(f"[CMD ENVIADO]: {send_cmd!r}")
    t0 = time.time()
    lines = 0
    try:
        while (time.time() - t0) < seconds:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if raw:
                print(raw)
                lines += 1
    finally:
        ser.close()
    print(f"\n[FIN MONITOR] {lines} lineas leidas en {time.time() - t0:.1f} s.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Serial Rápido KNTX")
    parser.add_argument("--list", action="store_true", help="Listar puertos COM activos")
    parser.add_argument("--port", help="Puerto COM (ej. COM4)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--cmd", default="", help="Comando opcional a enviar (ej. 'g' o 'c')")
    args = parser.parse_args()
    if args.list:
        list_ports()
    elif args.port:
        monitor(args.port, args.baud, args.seconds, args.cmd)
    else:
        list_ports()
