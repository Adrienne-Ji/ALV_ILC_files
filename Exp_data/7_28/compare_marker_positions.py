"""
compare_marker_positions.py
---------------------------
Visually compares marker positions and derived geometry across all 7_28 trials.

Figure 1 — Phase-averaged overlay (averaged_cycle.csv):
    twist / height / volume / pressure for every trial on the same axes.

Figure 2 — Raw marker distance time-series (processed_markers_full.csv):
    dist_Pink_Green, dist_Pink_Midpoint, dist_Green_Midpoint
    height_mm, twist_deg, volume_mL, rBase_mm

Figure 3 — Centred marker XYZ time-series (processed_markers_full.csv):
    Pink, Green, Purple centred X/Y/Z positions.

Outputs: compare_phase_avg.png, compare_marker_distances.png,
         compare_marker_xyz.png  (saved in the 7_28 directory)
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Discover trial sub-folders (any folder containing averaged_cycle.csv) ─────
trial_dirs = sorted(
    d for d in glob.glob(os.path.join(BASE_DIR, "*"))
    if os.path.isdir(d) and os.path.exists(os.path.join(d, "averaged_cycle.csv"))
)

if not trial_dirs:
    raise FileNotFoundError(f"No trial sub-folders with averaged_cycle.csv found in {BASE_DIR}")

trial_names = [os.path.basename(d) for d in trial_dirs]
n_trials    = len(trial_dirs)
CMAP        = plt.cm.tab10
colours     = [CMAP(i / max(n_trials - 1, 1)) for i in range(n_trials)]

print(f"Found {n_trials} trials: {trial_names}")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 1 — Phase-averaged overlay
# ══════════════════════════════════════════════════════════════════════════════
AVG_COLS = [
    ("twist",    "Twist (deg)",     "darkorchid"),
    ("height",   "Height (mm)",     "steelblue"),
    ("volume",   "Volume (mL)",     "seagreen"),
    ("pressure", "Pressure (mmHg)", "tomato"),
]

fig1, axes1 = plt.subplots(len(AVG_COLS), 1, figsize=(12, 10), sharex=True)
fig1.suptitle("Phase-averaged geometry & pressure — all 7_28 trials", fontsize=13, fontweight="bold")

for trial_dir, name, clr in zip(trial_dirs, trial_names, colours):
    path = os.path.join(trial_dir, "averaged_cycle.csv")
    df   = pd.read_csv(path)
    phase = np.linspace(0, 1, len(df), endpoint=False)
    for ax, (col, ylabel, _) in zip(axes1, AVG_COLS):
        if col in df.columns:
            ax.plot(phase, df[col].values, color=clr, lw=1.8, label=name)

for ax, (col, ylabel, _col_colour) in zip(axes1, AVG_COLS):
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, lw=0.3, alpha=0.5)

axes1[0].legend(fontsize=8, loc="upper right", ncol=min(n_trials, 4))
axes1[-1].set_xlabel("Normalised phase (0→1)", fontsize=9)
plt.tight_layout()
out1 = os.path.join(BASE_DIR, "compare_phase_avg.png")
fig1.savefig(out1, dpi=150, bbox_inches="tight")
plt.close(fig1)
print(f"Saved -> {out1}")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 2 — Raw marker distances & derived geometry time-series
# ══════════════════════════════════════════════════════════════════════════════
DIST_COLS = [
    ("dist_Pink_Green",     "Pink–Green dist (m)",    "crimson"),
    ("dist_Pink_Midpoint",  "Pink–Midpoint dist (m)", "darkorange"),
    ("dist_Green_Midpoint", "Green–Midpoint dist (m)", "goldenrod"),
    ("height_mm",           "Height (mm)",             "steelblue"),
    ("twist_deg",           "Twist (deg)",             "darkorchid"),
    ("volume_mL",           "Volume (mL)",             "seagreen"),
    ("rBase_mm",            "rBase (mm)",              "teal"),
]

# Only keep columns that exist in at least one trial
available_dist_cols = []
for col_info in DIST_COLS:
    col = col_info[0]
    for td in trial_dirs:
        p = os.path.join(td, "processed_markers_full.csv")
        if os.path.exists(p):
            hdr = pd.read_csv(p, nrows=0).columns.tolist()
            if col in hdr:
                available_dist_cols.append(col_info)
                break

n_dc = len(available_dist_cols)
fig2, axes2 = plt.subplots(n_dc, 1, figsize=(14, 2.5 * n_dc), sharex=False)
if n_dc == 1:
    axes2 = [axes2]
fig2.suptitle("Raw marker distances & derived geometry — all 7_28 trials", fontsize=13, fontweight="bold")

for trial_dir, name, clr in zip(trial_dirs, trial_names, colours):
    path = os.path.join(trial_dir, "processed_markers_full.csv")
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found, skipping")
        continue
    df = pd.read_csv(path)
    t  = df["abs_time_s"].values if "abs_time_s" in df.columns else df["Time_s"].values
    for ax, (col, ylabel, _) in zip(axes2, available_dist_cols):
        if col in df.columns:
            ax.plot(t, df[col].values, color=clr, lw=0.9, alpha=0.85, label=name)

for ax, (col, ylabel, _) in zip(axes2, available_dist_cols):
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel("Elapsed time (s)", fontsize=8)
    ax.grid(True, lw=0.3, alpha=0.5)

axes2[0].legend(fontsize=8, loc="upper right", ncol=min(n_trials, 4))
plt.tight_layout()
out2 = os.path.join(BASE_DIR, "compare_marker_distances.png")
fig2.savefig(out2, dpi=150, bbox_inches="tight")
plt.close(fig2)
print(f"Saved -> {out2}")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 3 — Centred marker XYZ time-series
# ══════════════════════════════════════════════════════════════════════════════
XYZ_MARKERS = ["Pink", "Green", "Purple"]
AXES_LABELS = ["X (m)", "Y (m)", "Z (m)"]

# Build list of (marker, axis) pairs that exist
xyz_panels = []
for marker in XYZ_MARKERS:
    for ax_lbl, suffix in zip(AXES_LABELS, ["X", "Y", "Z"]):
        col = f"{marker}_centered_{suffix}"
        for td in trial_dirs:
            p = os.path.join(td, "processed_markers_full.csv")
            if os.path.exists(p):
                hdr = pd.read_csv(p, nrows=0).columns.tolist()
                if col in hdr:
                    xyz_panels.append((col, f"{marker} centred {ax_lbl}"))
                    break

n_xyz = len(xyz_panels)
if n_xyz > 0:
    fig3, axes3 = plt.subplots(n_xyz, 1, figsize=(14, 2.0 * n_xyz), sharex=False)
    if n_xyz == 1:
        axes3 = [axes3]
    fig3.suptitle("Centred marker XYZ positions — all 7_28 trials", fontsize=13, fontweight="bold")

    for trial_dir, name, clr in zip(trial_dirs, trial_names, colours):
        path = os.path.join(trial_dir, "processed_markers_full.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        t  = df["abs_time_s"].values if "abs_time_s" in df.columns else df["Time_s"].values
        for ax, (col, ylabel) in zip(axes3, xyz_panels):
            if col in df.columns:
                ax.plot(t, df[col].values, color=clr, lw=0.9, alpha=0.85, label=name)

    for ax, (col, ylabel) in zip(axes3, xyz_panels):
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_xlabel("Elapsed time (s)", fontsize=8)
        ax.grid(True, lw=0.3, alpha=0.5)

    axes3[0].legend(fontsize=8, loc="upper right", ncol=min(n_trials, 4))
    plt.tight_layout()
    out3 = os.path.join(BASE_DIR, "compare_marker_xyz.png")
    fig3.savefig(out3, dpi=150, bbox_inches="tight")
    plt.close(fig3)
    print(f"Saved -> {out3}")
else:
    print("  No centred XYZ columns found — skipping Figure 3")
