#!/usr/bin/env python3
"""
kntx_live_dashboard.py
Interfaz gráfica en tiempo real (HMI de Laboratorio) para el sistema biomecánico KNTX.
Diseñada para las demostraciones en vivo de PC4 (video 3-5 min), PC5 (auditoría presencial)
y Expotrónica.

Características:
  - Se conecta directo al Gateway ESP32-S3 (COM4 @ 921,600 bps por defecto) sin trabar el CH343.
  - Gráfica en tiempo real del ángulo articular de rodilla (°) con línea roja de referencia en 90°
    para demostrar visualmente la ausencia de Gimbal Lock.
  - Gráfica en vivo de aceleración axial de tibia (g) con línea de umbral de contacto inicial (3.0 g, RF-05).
  - Indicadores tipo LED (VERDE = ACTIVO / ROJO = DESCONECTADO FAILSAFE) para:
      * Nodo 0: Lumbar (ESP32-S3 + MPU6050)
      * Nodo 1: Tibia (ESP32-C3 + BNO085 SPI 3 MHz)
      * Nodo 2: Fémur (ESP32 + MPU6050 Madgwick)
  - Medidores de frecuencia efectiva en Hz por nodo, Cola FreeRTOS (espacios libres / Overflows) y BLE.
  - Botones interactivos:
      * [TARAR 0° (Calibrar)] -> envía 'c' al Gateway y reinicia postura neutral.
      * [GRABAR CSV]          -> guarda sesión estándar RF-08 en docs/evidencias/.
  - Consola de eventos en vivo resaltando mensajes [CALIB] y [FAILSAFE].

Uso:
  python software/capture/kntx_live_dashboard.py
  (o especificar puerto: python software/capture/kntx_live_dashboard.py --port COM4)
"""

import argparse
import csv
import datetime
import os
import queue
import re
import threading
import time
from collections import deque
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import serial
import serial.tools.list_ports


CSV_HEADER = [
    "Timestamp_ms", "Node_ID",
    "Quat_W", "Quat_X", "Quat_Y", "Quat_Z",
    "Accel_X", "Accel_Y", "Accel_Z",
    "Calib_Status", "Knee_Deg"
]


class KntxLiveDashboard:
    def __init__(self, root: tk.Tk, default_port: str, baud: int):
        self.root = root
        self.root.title("KNTX — Monitor Biomecánico en Tiempo Real (PC4 / PC5)")
        self.root.geometry("1220x780")
        self.root.configure(bg="#0f172a")

        self.baud = baud
        self.ser = None
        self.running = False
        self.reader_thread = None
        self.msg_queue = queue.Queue(maxsize=2000)

        # Estado grabación CSV
        self.recording = False
        self.csv_file = None
        self.csv_writer = None
        self.csv_rows = 0

        # Buffers de gráficas (últimos ~6 segundos a 100 Hz)
        self.max_pts = 500
        self.t_buf = deque(maxlen=self.max_pts)
        self.angle_buf = deque(maxlen=self.max_pts)
        self.accel_buf = deque(maxlen=self.max_pts)
        self.t_start = time.time()

        # Estado en vivo de nodos y salud
        self.last_seen = {0: 0.0, 1: 0.0, 2: 0.0}
        self.pkt_times = {1: deque(maxlen=200), 2: deque(maxlen=200)}
        self.current_angle = 0.0
        self.current_accel = 1.0
        self.health_text = "Cola: 1000/1000 | Overflows: 0 | BLE: ADVERTISING"

        self._build_ui(default_port)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_ui_update()

    def _build_ui(self, default_port: str):
        # Barra superior de conexión y botones
        top = tk.Frame(self.root, bg="#1e293b", pady=8, padx=12)
        top.pack(fill="x")

        tk.Label(top, text="KNTX LIVE HMI", bg="#1e293b", fg="#38bdf8",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=(0, 16))

        tk.Label(top, text="Puerto Gateway:", bg="#1e293b", fg="#e2e8f0",
                 font=("Segoe UI", 10)).pack(side="left")

        ports = [p.device for p in serial.tools.list_ports.comports()]
        if default_port not in ports:
            ports.insert(0, default_port)
        self.port_var = tk.StringVar(value=default_port)
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, values=ports, width=10)
        self.port_combo.pack(side="left", padx=6)

        self.btn_connect = tk.Button(top, text="CONECTAR", bg="#16a34a", fg="white",
                                     font=("Segoe UI", 9, "bold"), padx=12, command=self.toggle_connect)
        self.btn_connect.pack(side="left", padx=6)

        self.btn_tare = tk.Button(top, text="TARAR 0° (Calibrar)", bg="#2563eb", fg="white",
                                  font=("Segoe UI", 9, "bold"), padx=12, command=self.send_tare)
        self.btn_tare.pack(side="left", padx=6)

        self.btn_rec = tk.Button(top, text="● GRABAR CSV", bg="#475569", fg="white",
                                 font=("Segoe UI", 9, "bold"), padx=12, command=self.toggle_record)
        self.btn_rec.pack(side="left", padx=6)

        self.lbl_health = tk.Label(top, text="Desconectado", bg="#1e293b", fg="#94a3b8",
                                   font=("Consolas", 9, "bold"))
        self.lbl_health.pack(side="right", padx=8)

        # Panel de tarjetas de estado (LEDs de nodos + Ángulo grande)
        cards = tk.Frame(self.root, bg="#0f172a", pady=8, padx=12)
        cards.pack(fill="x")

        self.node_cards = {}
        node_defs = [
            (0, "NODO 0 — LUMBAR", "ESP32-S3 + MPU6050"),
            (1, "NODO 1 — TIBIA", "ESP32-C3 + BNO085 (SPI 3MHz)"),
            (2, "NODO 2 — FÉMUR", "ESP32 + MPU6050 (Madgwick)"),
        ]
        for nid, title, sub in node_defs:
            f = tk.Frame(cards, bg="#1e293b", highlightbackground="#334155", highlightthickness=1, padx=12, pady=8)
            f.pack(side="left", expand=True, fill="x", padx=5)
            led = tk.Label(f, text="● OFFLINE", bg="#1e293b", fg="#ef4444", font=("Segoe UI", 10, "bold"))
            led.pack(anchor="w")
            tk.Label(f, text=title, bg="#1e293b", fg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            info = tk.Label(f, text=f"{sub} | 0.0 Hz", bg="#1e293b", fg="#94a3b8", font=("Consolas", 8))
            info.pack(anchor="w")
            self.node_cards[nid] = (led, info, sub)

        # Tarjeta gigante de Ángulo de Rodilla
        af = tk.Frame(cards, bg="#172554", highlightbackground="#3b82f6", highlightthickness=2, padx=16, pady=6)
        af.pack(side="left", expand=True, fill="x", padx=5)
        tk.Label(af, text="ÁNGULO RODILLA (q_rel)", bg="#172554", fg="#93c5fd",
                 font=("Segoe UI", 9, "bold")).pack(anchor="center")
        self.lbl_angle = tk.Label(af, text="0.0°", bg="#172554", fg="#ffffff",
                                  font=("Segoe UI", 24, "bold"))
        self.lbl_angle.pack(anchor="center")

        # Gráficas Matplotlib embebidas
        fig = Figure(figsize=(11.5, 4.6), dpi=100, facecolor="#0f172a")
        self.ax1 = fig.add_subplot(211)
        self.ax2 = fig.add_subplot(212)

        for ax in (self.ax1, self.ax2):
            ax.set_facecolor("#1e293b")
            ax.tick_params(colors="#cbd5e1", labelsize=8)
            for sp in ax.spines.values():
                sp.set_color("#334155")
            ax.grid(True, color="#334155", alpha=0.5)

        self.ax1.set_title("Ángulo Articular Relativo de Rodilla en Tiempo Real (Sin Gimbal Lock al cruzar 90°)",
                           color="#f8fafc", fontsize=10, fontweight="bold")
        self.ax1.set_ylabel("Ángulo [°]", color="#e2e8f0", fontsize=9)
        self.ax1.set_ylim(-5, 145)
        self.ax1.axhline(90.0, color="#ef4444", linestyle="--", lw=1.4, label="90° (Zona Gimbal Lock)")
        self.line_angle, = self.ax1.plot([], [], color="#38bdf8", lw=2.2, label="Rodilla q_rel (°)")
        self.ax1.legend(loc="upper right", facecolor="#0f172a", edgecolor="#334155", labelcolor="white", fontsize=8)

        self.ax2.set_title("Aceleración Resultante en Tibia (Detección de Contacto Inicial > 3.0 g — RF-05)",
                           color="#f8fafc", fontsize=10, fontweight="bold")
        self.ax2.set_ylabel("|a| [g]", color="#e2e8f0", fontsize=9)
        self.ax2.set_xlabel("Tiempo [s]", color="#e2e8f0", fontsize=9)
        self.ax2.set_ylim(0, 4.5)
        self.ax2.axhline(3.0, color="#f59e0b", linestyle="--", lw=1.4, label="Umbral Foot-Strike (3.0 g)")
        self.line_accel, = self.ax2.plot([], [], color="#4ade80", lw=1.8, label="Aceleración Tibia (g)")
        self.ax2.legend(loc="upper right", facecolor="#0f172a", edgecolor="#334155", labelcolor="white", fontsize=8)
        fig.tight_layout(pad=1.6)

        self.canvas = FigureCanvasTkAgg(fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(2, 4))

        # Consola inferior de eventos en vivo (CALIB, FAILSAFE, SALUD)
        log_frame = tk.Frame(self.root, bg="#0f172a", padx=12, pady=6)
        log_frame.pack(fill="x")
        tk.Label(log_frame, text="Eventos del Gateway ESP32-S3 (FreeRTOS / Failsafe / Calibración):",
                 bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.txt_log = tk.Text(log_frame, height=5, bg="#020617", fg="#e2e8f0",
                               font=("Consolas", 8.5), relief="flat")
        self.txt_log.pack(fill="x")
        self.txt_log.tag_config("fail", foreground="#f87171", font=("Consolas", 9, "bold"))
        self.txt_log.tag_config("ok", foreground="#4ade80")
        self.txt_log.tag_config("info", foreground="#38bdf8")

    def log_event(self, text: str, tag: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert("end", f"[{ts}] {text}\n", tag)
        self.txt_log.see("end")

    def toggle_connect(self):
        if self.running:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_var.get().strip()
        try:
            ser = serial.Serial()
            ser.port = port
            ser.baudrate = self.baud
            ser.timeout = 0.2
            ser.dtr = False
            ser.rts = False
            ser.open()
            # Pulso limpio EN en CH343 sin entrar a bootloader
            ser.setDTR(False)
            ser.setRTS(True)
            time.sleep(0.1)
            ser.setRTS(False)
            self.ser = ser
            self.running = True
            self.t_start = time.time()
            self.btn_connect.config(text="DESCONECTAR", bg="#dc2626")
            self.log_event(f"Conectado a Gateway {port} @ {self.baud} bps.", "ok")
            self.reader_thread = threading.Thread(target=self._serial_loop, daemon=True)
            self.reader_thread.start()
        except Exception as e:
            self.log_event(f"Error al abrir {port}: {e}", "fail")

    def _disconnect(self):
        self.running = False
        if self.recording:
            self.toggle_record()
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
        self.btn_connect.config(text="CONECTAR", bg="#16a34a")
        self.lbl_health.config(text="Desconectado", fg="#94a3b8")
        self.log_event("Puerto serial cerrado.", "info")

    def send_tare(self):
        if self.ser and self.running:
            try:
                self.ser.write(b"c")
                self.log_event("Comando 'c' enviado -> Tarando postura neutral a 0°...", "ok")
            except Exception as e:
                self.log_event(f"Error enviando tara: {e}", "fail")

    def toggle_record(self):
        if not self.recording:
            os.makedirs(os.path.join("docs", "evidencias"), exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = os.path.join("docs", "evidencias", f"kntx_live_{stamp}.csv")
            self.csv_file = open(fname, "w", newline="", encoding="utf-8")
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(CSV_HEADER)
            self.csv_rows = 0
            self.recording = True
            self.btn_rec.config(text="■ DETENER CSV", bg="#dc2626")
            self.log_event(f"Grabando telemetría CSV en: {fname}", "ok")
        else:
            self.recording = False
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
            self.btn_rec.config(text="● GRABAR CSV", bg="#475569")
            self.log_event(f"Grabación detenida ({self.csv_rows} filas guardadas).", "info")

    def _serial_loop(self):
        while self.running and self.ser:
            try:
                raw = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if raw:
                    try:
                        self.msg_queue.put_nowait((time.time(), raw))
                    except queue.Full:
                        pass
            except Exception:
                break

    def _schedule_ui_update(self):
        processed = 0
        now = time.time()
        while not self.msg_queue.empty() and processed < 250:
            ts_rx, line = self.msg_queue.get_nowait()
            processed += 1
            if line.startswith("#"):
                if "FAILSAFE" in line:
                    self.log_event(line, "fail")
                elif "CALIB" in line or "[OK]" in line:
                    self.log_event(line, "ok")
                elif "SALUD KNTX" in line:
                    self.health_text = line.replace("# [SALUD KNTX] ", "")
                    m = re.search(r"NodosMask=0x([0-9A-Fa-f]+)", line)
                    if m and (int(m.group(1), 16) & 0x01):
                        self.last_seen[0] = now
                continue
            if line.startswith("Timestamp_ms"):
                continue

            parts = line.split(",")
            if len(parts) >= 11:
                try:
                    nid = int(parts[1])
                    ax, ay, az = float(parts[6]), float(parts[7]), float(parts[8])
                    knee = float(parts[10])
                except ValueError:
                    continue

                if self.recording and self.csv_writer:
                    self.csv_writer.writerow(parts[:11])
                    self.csv_rows += 1

                if nid in self.last_seen:
                    self.last_seen[nid] = now
                if nid in self.pkt_times:
                    self.pkt_times[nid].append(now)

                if nid == 1:
                    self.current_accel = (ax*ax + ay*ay + az*az) ** 0.5
                    if knee >= 0.0:
                        self.current_angle = knee
                        self.t_buf.append(ts_rx - self.t_start)
                        self.angle_buf.append(knee)
                        self.accel_buf.append(self.current_accel)

        # Actualizar indicadores visuales
        if self.running:
            self.lbl_health.config(text=self.health_text, fg="#38bdf8")
            self.lbl_angle.config(text=f"{self.current_angle:5.1f}°")

            for nid, (led, info, sub) in self.node_cards.items():
                age = now - self.last_seen[nid]
                online = (self.last_seen[nid] > 0) and (age < (2.8 if nid == 0 else 0.5))
                if online:
                    led.config(text="● ONLINE", fg="#4ade80")
                else:
                    led.config(text="● OFFLINE / FAILSAFE", fg="#ef4444")

                if nid in self.pkt_times:
                    dq = self.pkt_times[nid]
                    # Contar paquetes en el último segundo
                    recent = sum(1 for t in dq if (now - t) <= 1.0)
                    info.config(text=f"{sub} | {recent:3d} Hz")
                else:
                    info.config(text=f"{sub} | {'OK' if online else 'WAIT'}")

            # Refrescar curvas
            if len(self.t_buf) > 2:
                xs = list(self.t_buf)
                self.line_angle.set_data(xs, list(self.angle_buf))
                self.line_accel.set_data(xs, list(self.accel_buf))
                xmax = xs[-1]
                xmin = max(0.0, xmax - 6.0)
                self.ax1.set_xlim(xmin, max(6.0, xmax))
                self.ax2.set_xlim(xmin, max(6.0, xmax))
                self.canvas.draw_idle()

        self.root.after(40, self._schedule_ui_update)

    def _on_close(self):
        self._disconnect()
        self.root.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dashboard en vivo KNTX (PC4/PC5)")
    parser.add_argument("--port", default="COM4", help="Puerto COM del Gateway ESP32-S3")
    parser.add_argument("--baud", type=int, default=921600)
    args = parser.parse_args()

    app_root = tk.Tk()
    app = KntxLiveDashboard(app_root, args.port, args.baud)
    app_root.mainloop()
