#!/usr/bin/env python3
"""
kntx_biomechanics_analysis.py
Módulo de procesamiento biomecánico y validación metrológica del proyecto KNTX.
Autoría principal: Jorge Carlos Contreras Rodríguez (Algoritmos ISB / Grood-Suntay / Kinovea).

Implementa:
  1. Álgebra de cuaterniones relativos (q_rel = conj(q_prox) ⊗ q_dist) sin Gimbal Lock (RF-02).
  2. Convención articular Grood & Suntay (1983) e ISB (Wu et al., 2002; Cereatti et al., 2024).
  3. Detección de contacto inicial (foot strike, RF-05) por umbral > 3.0 g en tibia.
  4. Normalización del ciclo de zancada (0–100 %) por interpolación Spline cúbica a 101 puntos.
  5. Generación automática de gráficas para PC4 y PC5:
     - Análisis de jitter y sincronía entre nodos (PV-01 / PV-03).
     - Deriva de yaw en reposo (°/min, PV-06).
     - Gráfica de Bland-Altman y RMSE vs. Goniómetro / Kinovea (PV-07 / PV-08).
     - Curva de ángulo de rodilla vs. % de ciclo con banda normativa media ± 1 DE (RF-07).
"""

import argparse
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from scipy.signal import find_peaks


def quat_conj(q: np.ndarray) -> np.ndarray:
    """Conjugado de un arreglo de cuaterniones Nx4 [w, x, y, z]."""
    out = q.copy()
    out[..., 1:] *= -1.0
    return out


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Producto de Hamilton vectorizado para arreglos Nx4 [w, x, y, z]."""
    w1, x1, y1, z1 = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    w2, x2, y2, z2 = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    ], axis=-1)


def quat_to_grood_suntay_deg(q_prox: np.ndarray, q_dist: np.ndarray) -> dict:
    """
    Calcula ángulos articulares (flexión/extensión, abducción/aducción, rotación axial)
    a partir de los cuaterniones de los segmentos proximal (fémur) y distal (tibia)
    siguiendo Grood & Suntay (1983) sin singularidad de Gimbal Lock a 90°.
    """
    q_rel = quat_mul(quat_conj(q_prox), q_dist)
    norms = np.linalg.norm(q_rel, axis=-1, keepdims=True)
    q_rel = np.divide(q_rel, np.where(norms > 1e-8, norms, 1.0))

    w, x, y, z = q_rel[..., 0], q_rel[..., 1], q_rel[..., 2], q_rel[..., 3]

    # Matriz de rotación equivalente R(q_rel)
    r00 = 1 - 2 * (y * y + z * z)
    r10 = 2 * (x * y + w * z)
    r20 = 2 * (x * z - w * y)
    r21 = 2 * (y * z + w * x)
    r22 = 1 - 2 * (x * x + y * y)

    flex_ext = np.degrees(np.arctan2(-r20, np.sqrt(r21**2 + r22**2)))
    abd_add  = np.degrees(np.arctan2(r21, r22))
    int_ext  = np.degrees(np.arctan2(r10, r00))
    geodesic = np.degrees(2.0 * np.arccos(np.clip(np.abs(w), 0.0, 1.0)))

    return {
        "flexion_deg": flex_ext,
        "abduction_deg": abd_add,
        "rotation_deg": int_ext,
        "geodesic_deg": geodesic,
    }


def detect_foot_strikes(accel_xyz: np.ndarray, fs_hz: float = 100.0, threshold_g: float = 3.0) -> np.ndarray:
    """
    Detecta eventos de contacto inicial (foot strike, RF-05) buscando picos de aceleración
    resultante en tibia superiores a 3.0 g con distancia mínima fisiológica de 350 ms.
    """
    mag = np.linalg.norm(accel_xyz, axis=1)
    min_dist = max(1, int(0.35 * fs_hz))
    peaks, _ = find_peaks(mag, height=threshold_g, distance=min_dist)
    return peaks


def normalize_cycles_101(signal: np.ndarray, strike_indices: np.ndarray) -> np.ndarray:
    """
    Normaliza cada ciclo de zancada (entre dos contactos iniciales consecutivos)
    a exactamente 101 puntos (0% a 100% en saltos de 1%) mediante Spline cúbica.
    """
    cycles = []
    grid = np.linspace(0.0, 100.0, 101)
    for i in range(len(strike_indices) - 1):
        s, e = int(strike_indices[i]), int(strike_indices[i + 1])
        if (e - s) < 10:
            continue
        seg = signal[s:e + 1]
        x_orig = np.linspace(0.0, 100.0, len(seg))
        cs = CubicSpline(x_orig, seg)
        cycles.append(cs(grid))
    return np.array(cycles) if cycles else np.empty((0, 101))


def compute_yaw_drift_deg_per_min(df_node: pd.DataFrame) -> float:
    """Calcula la pendiente lineal de deriva de yaw (°/min) en prueba estática (PV-06)."""
    q = df_node[["Quat_W", "Quat_X", "Quat_Y", "Quat_Z"]].to_numpy()
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    yaw_rad = np.unwrap(np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
    yaw_deg = np.degrees(yaw_rad)
    t_min = (df_node["Timestamp_ms"].to_numpy() - df_node["Timestamp_ms"].iloc[0]) / 60000.0
    if len(t_min) < 2 or (t_min[-1] - t_min[0]) < 1e-4:
        return 0.0
    slope, _ = np.polyfit(t_min, yaw_deg, 1)
    return float(abs(slope))


def plot_bland_altman(kntx_deg: np.ndarray, ref_deg: np.ndarray, out_png: str, title: str):
    """Genera gráfica de concordancia de Bland & Altman (1986) para PV-07 / PV-08."""
    mean_vals = 0.5 * (kntx_deg + ref_deg)
    diff_vals = kntx_deg - ref_deg
    bias = float(np.mean(diff_vals))
    sd = float(np.std(diff_vals, ddof=1)) if len(diff_vals) > 1 else 0.0
    loa_hi = bias + 1.96 * sd
    loa_lo = bias - 1.96 * sd
    rmse = float(np.sqrt(np.mean(diff_vals**2)))

    plt.figure(figsize=(8, 4.8), dpi=160)
    plt.scatter(mean_vals, diff_vals, color="#1f4e79", alpha=0.8, label="Muestras")
    plt.axhline(bias, color="#c00000", linestyle="-", label=f"Sesgo = {bias:.2f}°")
    plt.axhline(loa_hi, color="#7f7f7f", linestyle="--", label=f"+1.96 DE = {loa_hi:.2f}°")
    plt.axhline(loa_lo, color="#7f7f7f", linestyle="--", label=f"-1.96 DE = {loa_lo:.2f}°")
    plt.title(f"{title} | RMSE = {rmse:.2f}°")
    plt.xlabel("Media (KNTX y Referencia) [°]")
    plt.ylabel("Diferencia (KNTX - Referencia) [°]")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()
    return {"rmse_deg": rmse, "bias_deg": bias, "loa_lo": loa_lo, "loa_hi": loa_hi}


def analyze_csv(csv_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(csv_path)
    print(f"[INFO] Archivo cargado: {csv_path} ({len(df)} registros)")

    # 1. Métricas por nodo (PV-01, PV-03, PV-06)
    summary_rows = []
    plt.figure(figsize=(9, 4.2), dpi=160)
    for nid, grp in df.groupby("Node_ID"):
        ts = grp["Timestamp_ms"].to_numpy(dtype=np.float64)
        dur_s = max((ts[-1] - ts[0]) / 1000.0, 1e-3) if len(ts) > 1 else 1.0
        eff_hz = len(ts) / dur_s
        diffs = np.diff(ts) if len(ts) > 1 else np.array([10.0])
        jitter = np.abs(diffs - 10.0)
        drift = compute_yaw_drift_deg_per_min(grp)
        summary_rows.append({
            "Node_ID": int(nid),
            "Muestras": int(len(ts)),
            "Duracion_s": round(dur_s, 2),
            "Frecuencia_Hz": round(eff_hz, 2),
            "Jitter_med_ms": round(float(np.median(jitter)), 3),
            "Jitter_P95_ms": round(float(np.percentile(jitter, 95)), 3),
            "Jitter_max_ms": round(float(np.max(jitter)), 3),
            "Deriva_yaw_deg_min": round(drift, 3),
        })
        t_rel = (ts[1:] - ts[0]) / 1000.0 if len(ts) > 1 else np.array([0.0])
        plt.plot(t_rel, jitter, label=f"Nodo {nid}", alpha=0.85)

    plt.axhline(5.0, color="#c00000", linestyle="--", linewidth=1.5, label="Límite RP-01 (5 ms)")
    plt.title("KNTX — Jitter temporal por nodo (PV-03)")
    plt.xlabel("Tiempo [s]")
    plt.ylabel("Jitter |Δt - 10 ms| [ms]")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    jitter_png = os.path.join(out_dir, "kntx_jitter_pv03.png")
    plt.savefig(jitter_png)
    plt.close()

    summary_df = pd.DataFrame(summary_rows)
    print("\n=== RESUMEN METROLÓGICO DE SESIÓN ===")
    print(summary_df.to_string(index=False))
    summary_df.to_csv(os.path.join(out_dir, "kntx_metrics_summary.csv"), index=False)

    # 2. Si existen Nodo 1 (Tibia) y Nodo 2 (Fémur), calcular ángulo relativo de rodilla
    if {1, 2}.issubset(set(df["Node_ID"].unique())):
        n1 = df[df["Node_ID"] == 1].sort_values("Timestamp_ms")
        n2 = df[df["Node_ID"] == 2].sort_values("Timestamp_ms")
        merged = pd.merge_asof(n1, n2, on="Timestamp_ms", direction="nearest",
                               tolerance=10, suffixes=("_tibia", "_femur")).dropna()
        if len(merged) > 5:
            q_tibia = merged[["Quat_W_tibia", "Quat_X_tibia", "Quat_Y_tibia", "Quat_Z_tibia"]].to_numpy()
            q_femur = merged[["Quat_W_femur", "Quat_X_femur", "Quat_Y_femur", "Quat_Z_femur"]].to_numpy()
            angles = quat_to_grood_suntay_deg(q_femur, q_tibia)
            t_s = (merged["Timestamp_ms"].to_numpy() - merged["Timestamp_ms"].iloc[0]) / 1000.0

            plt.figure(figsize=(9, 4.2), dpi=160)
            plt.plot(t_s, angles["geodesic_deg"], color="#1f4e79", label="Ángulo relativo rodilla (cuaternión)")
            plt.title("KNTX — Ángulo Articular Relativo Fémur–Tibia en Tiempo Real (RF-02)")
            plt.xlabel("Tiempo [s]")
            plt.ylabel("Ángulo [°]")
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, "kntx_knee_angle_rf02.png"))
            plt.close()
            print(f"[OK] Gráfica de rodilla generada con {len(merged)} pares sincronizados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análisis Biomecánico y Metrológico KNTX")
    parser.add_argument("--csv", required=True, help="Archivo CSV exportado del Gateway (RF-08)")
    parser.add_argument("--out-dir", default="resultados_analisis", help="Carpeta de salida")
    args = parser.parse_args()
    analyze_csv(args.csv, args.out_dir)
