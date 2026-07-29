"""
marker_3d_interactive.py
------------------------
Interactive 3D Plotly figure comparing marker positions across all 7_28 trials.

Left subplot  — Heart markers (Pink, Green, Purple, Midpoint) home position
Right subplot — Reference markers (Tag1, Tag2) home position

"Home position" = mean of first 50 frames (actuators at rest, same every trial).
Colour gradient: blue (itr0) → red (last trial).

Buttons toggle between:
  • Home position  (mean point per marker per trial)
  • Full cardiac cycle  (every 5th frame of a representative mid-recording window)
"""

import os, glob
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE        = os.path.dirname(os.path.abspath(__file__))
HEART_MK    = ["Pink", "Green", "Purple", "Midpoint"]
REF_MK      = ["Tag1", "Tag2"]
SYMBOLS     = {"Pink": "circle", "Green": "diamond", "Purple": "cross",
               "Midpoint": "square", "Tag1": "x", "Tag2": "x"}
SIZES       = {"Pink": 10, "Green": 10, "Purple": 8, "Midpoint": 9,
               "Tag1": 8,  "Tag2": 8}

trial_dirs  = sorted([
    d for d in glob.glob(os.path.join(BASE, "*"))
    if os.path.isdir(d) and
       os.path.exists(os.path.join(d, "processed_markers_full.csv"))
])
trial_names = [os.path.basename(d) for d in trial_dirs]
n           = len(trial_dirs)

def rgba(i, total, a=1.0):
    r = int(220 * i / max(total-1,1))
    b = int(220 * (1 - i / max(total-1,1)))
    return f"rgba({r},80,{b},{a})"

fig = make_subplots(
    rows=1, cols=2,
    specs=[[{"type": "scene"}, {"type": "scene"}]],
    subplot_titles=["Heart markers — Pink / Green / Purple / Midpoint",
                    "Reference markers — Tag1 / Tag2  (should NOT move)"],
    horizontal_spacing=0.05,
)

HOME_N   = 50      # frames for home average
CYCLE_N  = 200     # frames per cycle window for full view
STRIDE   = 3

all_traces     = []
home_visible   = []
cycle_visible  = []

def add(trace, is_home_trace):
    fig.add_trace(trace[0], row=1, col=trace[1])
    all_traces.append(is_home_trace)

for ti, (td, name) in enumerate(zip(trial_dirs, trial_names)):
    mk  = pd.read_csv(os.path.join(td, "processed_markers_full.csv"))
    clr = rgba(ti, n)

    # ── HOME: mean position of first HOME_N frames ────────────────────────────
    home = mk.iloc[:HOME_N]

    for col_idx, marker_list in enumerate([HEART_MK, REF_MK], start=1):
        for marker in marker_list:
            if f"{marker}_X" not in mk.columns:
                continue
            hx = home[f"{marker}_X"].mean()*1000
            hy = home[f"{marker}_Y"].mean()*1000
            hz = home[f"{marker}_Z"].mean()*1000
            tr = go.Scatter3d(
                x=[hx], y=[hy], z=[hz],
                mode="markers+text",
                marker=dict(size=SIZES.get(marker,8), color=clr,
                            symbol=SYMBOLS.get(marker,"circle"), opacity=0.95,
                            line=dict(width=1, color="white")),
                text=[marker], textposition="top center",
                textfont=dict(size=9, color=clr),
                name=name,
                legendgroup=name,
                showlegend=(marker == "Pink" and col_idx == 1),
                visible=True,
                hovertemplate=(f"<b>{name}</b><br>{marker}<br>"
                               f"({hx:.1f}, {hy:.1f}, {hz:.1f}) mm"
                               "<extra></extra>"),
            )
            fig.add_trace(tr, row=1, col=col_idx)
            home_visible.append(True)
            cycle_visible.append(False)

    # Draw heart outline (Pink→Midpoint→Green) for home position
    pts = []
    for mk_name in ["Pink", "Midpoint", "Green"]:
        if f"{mk_name}_X" in mk.columns:
            pts.append([home[f"{mk_name}_X"].mean()*1000,
                        home[f"{mk_name}_Y"].mean()*1000,
                        home[f"{mk_name}_Z"].mean()*1000])
    if len(pts) == 3:
        px,py,pz = zip(*pts)
        tr = go.Scatter3d(x=list(px), y=list(py), z=list(pz),
                          mode="lines",
                          line=dict(color=clr, width=4),
                          name=name, legendgroup=name, showlegend=False,
                          visible=True,
                          hovertemplate=f"<b>{name}</b> outline<extra></extra>")
        fig.add_trace(tr, row=1, col=1)
        home_visible.append(True)
        cycle_visible.append(False)

    # Tag1-Tag2 line for home
    t1x = home["Tag1_X"].mean()*1000 if "Tag1_X" in mk.columns else None
    t1y = home["Tag1_Y"].mean()*1000 if "Tag1_X" in mk.columns else None
    t1z = home["Tag1_Z"].mean()*1000 if "Tag1_X" in mk.columns else None
    t2x = home["Tag2_X"].mean()*1000 if "Tag2_X" in mk.columns else None
    t2y = home["Tag2_Y"].mean()*1000 if "Tag2_X" in mk.columns else None
    t2z = home["Tag2_Z"].mean()*1000 if "Tag2_X" in mk.columns else None
    if None not in [t1x, t2x]:
        d = np.sqrt((t2x-t1x)**2+(t2y-t1y)**2+(t2z-t1z)**2)
        tr = go.Scatter3d(x=[t1x,t2x], y=[t1y,t2y], z=[t1z,t2z],
                          mode="lines",
                          line=dict(color=clr, width=4),
                          name=name, legendgroup=name, showlegend=False,
                          visible=True,
                          hovertemplate=(f"<b>{name}</b><br>Tag1–Tag2 = {d:.2f} mm"
                                         "<extra></extra>"))
        fig.add_trace(tr, row=1, col=2)
        home_visible.append(True)
        cycle_visible.append(False)

    # ── FULL CYCLE: pick a mid-recording window ───────────────────────────────
    mid = len(mk) // 2
    window = mk.iloc[mid:mid + CYCLE_N:STRIDE]

    for col_idx, marker_list in enumerate([HEART_MK, REF_MK], start=1):
        for marker in marker_list:
            if f"{marker}_X" not in mk.columns:
                continue
            cx = window[f"{marker}_X"].values*1000
            cy = window[f"{marker}_Y"].values*1000
            cz = window[f"{marker}_Z"].values*1000
            tr = go.Scatter3d(
                x=cx, y=cy, z=cz,
                mode="markers",
                marker=dict(size=4, color=clr,
                            symbol=SYMBOLS.get(marker,"circle"), opacity=0.55),
                name=name,
                legendgroup=name,
                showlegend=False,
                visible=False,
                hovertemplate=(f"<b>{name}</b><br>{marker}<br>"
                               "(%{x:.1f}, %{y:.1f}, %{z:.1f}) mm"
                               "<extra></extra>"),
            )
            fig.add_trace(tr, row=1, col=col_idx)
            home_visible.append(False)
            cycle_visible.append(True)

n_traces = len(home_visible)

# ── Buttons ───────────────────────────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text=("7_28 — All trials marker positions<br>"
              "<sup>Colour: <b style='color:blue'>blue</b> = itr0  →  "
              "<b style='color:red'>red</b> = last trial  |  "
              "Right panel: Tag1/Tag2 must NOT move between trials</sup>"),
        font=dict(size=14),
    ),
    legend=dict(title="Trial", x=0.46, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
    updatemenus=[dict(
        type="buttons",
        direction="left",
        x=0.5, xanchor="center", y=1.12, yanchor="top",
        buttons=[
            dict(label="Home position (mean of first 50 frames)",
                 method="update",
                 args=[{"visible": home_visible}]),
            dict(label="Mid-recording cardiac cycle",
                 method="update",
                 args=[{"visible": cycle_visible}]),
        ],
        showactive=True,
    )],
    height=700,
    scene=dict(aspectmode="data",
               xaxis_title="X (mm)", yaxis_title="Y (mm)", zaxis_title="Z (mm)"),
    scene2=dict(aspectmode="data",
                xaxis_title="X (mm)", yaxis_title="Y (mm)", zaxis_title="Z (mm)"),
)

out = os.path.join(BASE, "marker_3d_interactive.html")
fig.write_html(out, include_plotlyjs="cdn")
print(f"Saved -> {out}")

import webbrowser
webbrowser.open(f"file:///{out.replace(os.sep, '/')}")
