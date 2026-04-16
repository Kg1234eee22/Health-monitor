import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# =========================================================
# CONFIGURATION
# =========================================================
st.set_page_config(page_title="Transformer Insulation Digital Twin", layout="wide")
st.title(" Transformer Insulation Digital Twin EE-447")
st.caption("Accelerated-life mode | Full life ≈ 300 days")

SIM_DAYS_PER_TICK = 1.0  # 1 real second = 1 simulated day
FAILURE_HI = 38.0
LIFE_ACCEL = 36.0  # ⬅️ LIFE COMPRESSION FACTOR

# =========================================================
# INITIALIZATION
# =========================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True

    st.session_state.time_days = 0.0
    st.session_state.HI = 100.0
    st.session_state.time_hist = [0.0]
    st.session_state.HI_hist = [100.0]

    st.session_state.event_log = []

    st.session_state.base_temp = 75.0
    st.session_state.base_moisture = 2.0
    st.session_state.base_PD = 15.0
    st.session_state.base_BDV = 60.0
    st.session_state.base_elec_stress = 1.0

    st.session_state.Tx_temp = 75.0
    st.session_state.Tx_moisture = 2.0
    st.session_state.Tx_PD = 15.0
    st.session_state.BDV = 60.0
    st.session_state.elec_stress = 1.0

    st.session_state.cum_PD_damage = 0.0
    st.session_state.cum_ox_damage = 0.0

    st.session_state.fault_days = 0.0
    st.session_state.rain_days = 0.0
    st.session_state.fan_days = 0.0
    st.session_state.pd_days = 0.0

    st.session_state.failed = False
    st.session_state.report_finalized = False

# =========================================================
# HEALTH STATUS FUNCTION
# =========================================================
def health_status(HI):
    if HI >= 80:
        return " HEALTHY", "success"
    elif HI >= 65:
        return " MODERATE", "info"
    elif HI >= 50:
        return " DEGRADING", "warning"
    elif HI > FAILURE_HI:
        return " NEEDS MAINTENANCE", "error"
    else:
        return " FAILURE", "error"

# =========================================================
# SIDEBAR — BASELINE CONTROLS
# =========================================================
st.sidebar.header("Baseline Operating Conditions")

st.session_state.base_temp = st.sidebar.slider("Hot-spot Temperature (°C)", 60, 120, 75)
st.session_state.base_moisture = st.sidebar.slider("Moisture Content (%)", 0.5, 6.0, 2.0)
st.session_state.base_PD = st.sidebar.slider("Baseline PD Level (pC)", 5, 50, 15)
st.session_state.base_BDV = st.sidebar.slider("Oil BDV (kV)", 40, 70, 60)
st.session_state.base_elec_stress = st.sidebar.slider("Electrical Stress (p.u.)", 0.8, 1.5, 1.0)

# =========================================================
# SIDEBAR — EVENTS
# =========================================================
st.sidebar.header("Trigger Events")

PD_event_level = st.sidebar.slider("PD Activity Level (pC)", 20, 600, 100)

if st.sidebar.button(" Fault (1 ms)") and st.session_state.fault_days <= 0:
    st.session_state.fault_days = 10 / 864000000
    st.session_state.event_log.append(f"Day {st.session_state.time_days:.2f}: Fault occurred (5 s)")

if st.sidebar.button(" Rain (4 h)") and st.session_state.rain_days <= 0:
    st.session_state.rain_days = 4 / 24
    st.session_state.event_log.append(f"Day {st.session_state.time_days:.2f}: Rain started (4 h)")

if st.sidebar.button(" Fan Failure (1 day)") and st.session_state.fan_days <= 0:
    st.session_state.fan_days = 1.0
    st.session_state.event_log.append(f"Day {st.session_state.time_days:.2f}: Cooling fan failed (1 day)")

if st.sidebar.button("⚡ PD Activity (6 h)") and st.session_state.pd_days <= 0:
    st.session_state.pd_days = 6 / 24
    st.session_state.event_log.append(
        f"Day {st.session_state.time_days:.2f}: PD activity started ({PD_event_level} pC, 6 h)"
    )

st.sidebar.markdown("---")

if st.sidebar.button(" End Simulation & Generate Report"):
    st.session_state.report_finalized = True
    st.session_state.event_log.append(f"Day {st.session_state.time_days:.2f}: Simulation terminated by user")

# =========================================================
# FINAL REPORT
# =========================================================
if st.session_state.report_finalized:
    st.warning(" SIMULATION TERMINATED – FINAL REPORT")

    st.metric("Final Health Index (%)", f"{st.session_state.HI:.2f}")
    st.metric("Total Operating Time (days)", f"{st.session_state.time_days:.2f}")

    st.subheader(" Event History")
    for e in st.session_state.event_log:
        st.write(e)

    fig, ax = plt.subplots()
    ax.plot(st.session_state.time_hist, st.session_state.HI_hist)
    ax.set_xlabel("Days")
    ax.set_ylabel("HI (%)")
    ax.grid(True)
    st.pyplot(fig)

    st.stop()

# =========================================================
# RESET TO BASELINE + EVENTS
# =========================================================
st.session_state.Tx_temp = st.session_state.base_temp
st.session_state.Tx_moisture = st.session_state.base_moisture
st.session_state.Tx_PD = st.session_state.base_PD
st.session_state.BDV = st.session_state.base_BDV
st.session_state.elec_stress = st.session_state.base_elec_stress

if st.session_state.fault_days > 0:
    st.session_state.Tx_temp += 30
    st.session_state.Tx_PD += 400
    st.session_state.elec_stress += 0.2
    st.session_state.fault_days -= SIM_DAYS_PER_TICK

if st.session_state.rain_days > 0:
    st.session_state.Tx_moisture += 0.05
    st.session_state.BDV -= 1.0
    st.session_state.Tx_PD += 20
    st.session_state.rain_days -= SIM_DAYS_PER_TICK

if st.session_state.fan_days > 0:
    st.session_state.Tx_temp += 15
    st.session_state.fan_days -= SIM_DAYS_PER_TICK

if st.session_state.pd_days > 0:
    st.session_state.Tx_PD += PD_event_level
    st.session_state.Tx_temp += 5
    st.session_state.pd_days -= SIM_DAYS_PER_TICK

# =========================================================
# AGING MODEL (ACCELERATED)
# =========================================================
FAA = np.exp((15000 / 383) - (15000 / (st.session_state.Tx_temp + 273)))
F_M = 1 + 0.5 * (st.session_state.Tx_moisture - 0.8)
F_PD = 1 + 0.6 * (st.session_state.Tx_PD / 20)
F_E = st.session_state.elec_stress

PD_erosion = 0.0005 * (st.session_state.Tx_PD / 100) ** 1.2
OX_rate = 0.0003 * np.exp(0.03 * (st.session_state.Tx_temp - 90))

st.session_state.cum_PD_damage += PD_erosion
st.session_state.cum_ox_damage += OX_rate

base_damage = 0.002 * FAA * F_M * F_PD * F_E + PD_erosion
damage = LIFE_ACCEL * base_damage   # ⬅️ ACCELERATION APPLIED HERE

st.session_state.HI -= damage
st.session_state.HI = max(st.session_state.HI, 0)

# =========================================================
# UPDATE TIME
# =========================================================
st.session_state.time_days += SIM_DAYS_PER_TICK
st.session_state.time_hist.append(st.session_state.time_days)
st.session_state.HI_hist.append(st.session_state.HI)

# =========================================================
# STATUS BAR
# =========================================================
status_text, status_type = health_status(st.session_state.HI)
st.subheader(" Transformer Health Status")
getattr(st, status_type)(status_text)

# =========================================================
# PRIMARY METRICS
# =========================================================
m1, m2, m3 = st.columns(3)
m1.metric("Health Index (%)", f"{st.session_state.HI:.2f}")
m2.metric("Elapsed Time (days)", f"{st.session_state.time_days:.1f}")
m3.metric("Total Degradation (%)", f"{100 - st.session_state.HI:.1f}")

# =========================================================
# LIVE METERS
# =========================================================
st.subheader("Live Condition Meters")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Temperature (°C)", f"{st.session_state.Tx_temp:.1f}")
c2.metric("Electrical Stress (p.u.)", f"{st.session_state.elec_stress:.2f}")
c3.metric("FAA", f"{FAA:.2f}")
c4.metric("PD Erosion (%)", f"{min(st.session_state.cum_PD_damage*100,100):.1f}")
c5.metric("Oxidation (%)", f"{min(st.session_state.cum_ox_damage*100,100):.1f}")

# =========================================================
# HEALTH GRAPH
# =========================================================
st.subheader(" Health Index vs Time")

fig, ax = plt.subplots()
ax.plot(st.session_state.time_hist, st.session_state.HI_hist)
ax.set_xlabel("Days")
ax.set_ylabel("HI (%)")
ax.set_ylim(0, 100)
ax.grid(True)
st.pyplot(fig)

# =========================================================
# CLOCK
# =========================================================
time.sleep(1)
st.rerun()

