import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://xmbexrqduwdqgktbstyn.supabase.co"
ANON_KEY     = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhtYmV4cnFkdXdkcWdrdGJzdHluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwNzk1NzksImV4cCI6MjA5MzY1NTU3OX0.-MOHehvYV6l5zUs8SnO0ahWYwrN_5QbNHCcVCrqcqGo"
HEADERS      = {"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"}

CITIES = ["Chandigarh", "Delhi", "Mumbai", "Bengaluru", "Shillong"]

AQI_LABELS = {1:"Good",2:"Satisfactory",3:"Moderate",4:"Poor",5:"Very Poor",6:"Severe"}
AQI_COLORS = {1:"#00C853",2:"#76FF03",3:"#FFD600",4:"#FF6D00",5:"#D50000",6:"#7B1FA2"}

WEATHER_ICONS = {
    "clear sky":"☀️","few clouds":"🌤️","scattered clouds":"⛅",
    "broken clouds":"🌥️","overcast clouds":"☁️","light rain":"🌦️",
    "moderate rain":"🌧️","heavy intensity rain":"🌧️","shower rain":"🌧️",
    "thunderstorm":"⛈️","snow":"❄️","mist":"🌫️","haze":"🌫️","fog":"🌫️",
}

st.set_page_config(page_title="Live Weather Dashboard", page_icon="🌤️",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');

* { font-family: 'Outfit', sans-serif !important; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0e1a !important;
    color: #e8eaf0 !important;
}
[data-testid="stAppViewContainer"] { background: #0a0e1a !important; }
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { background: #0d1120 !important; }

.hero-card {
    background: linear-gradient(135deg, #FF6B2B 0%, #FF8C42 50%, #e55a1c 100%);
    border-radius: 24px;
    padding: 28px;
    position: relative;
    overflow: hidden;
    min-height: 200px;
    box-shadow: 0 8px 32px rgba(255,107,43,0.35);
}
.hero-card::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 160px; height: 160px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}
.hero-city { font-size: 15px; font-weight: 600; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase; }
.hero-updated { font-size: 12px; opacity: 0.75; }
.hero-temp { font-size: 56px; font-weight: 800; line-height: 1; margin: 16px 0 6px; }
.hero-desc { font-size: 16px; opacity: 0.9; font-weight: 400; text-transform: capitalize; }
.hero-icon { font-size: 64px; position: absolute; top: 20px; right: 28px; }

.metric-card {
    background: #141929;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 18px 20px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: rgba(255,107,43,0.4); }
.metric-icon { font-size: 22px; margin-bottom: 6px; }
.metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #8892a4; font-weight: 600; }
.metric-value { font-size: 26px; font-weight: 700; color: #fff; margin-top: 4px; }

.section-card {
    background: #141929;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 22px;
}
.section-title { font-size: 14px; font-weight: 600; color: #8892a4; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }

.forecast-card {
    background: #1a2035;
    border-radius: 14px;
    padding: 14px 10px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.06);
}
.forecast-day { font-size: 11px; color: #8892a4; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.forecast-icon { font-size: 24px; margin: 6px 0; }
.forecast-temp { font-size: 18px; font-weight: 700; color: #fff; }

.aqi-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 8px;
}
.pollutant-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.pollutant-name { font-size: 12px; color: #8892a4; }
.pollutant-val { font-size: 18px; font-weight: 700; color: #fff; }

.city-btn button {
    background: #1a2035 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e8eaf0 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
div[data-testid="stSelectbox"] > div {
    background: #141929 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #e8eaf0 !important;
}
</style>
""", unsafe_allow_html=True)


# ── DATA FETCH ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch(table, city, limit=1, order="recorded_at.desc"):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*&city=eq.{city}&order={order}&limit={limit}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    return r.json() if r.status_code == 200 else []

@st.cache_data(ttl=300)
def fetch_history(table, city, limit=144):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*&city=eq.{city}&order=recorded_at.desc&limit={limit}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    return r.json() if r.status_code == 200 else []

@st.cache_data(ttl=300)
def fetch_forecast(city):
    url = f"{SUPABASE_URL}/rest/v1/forecastdata?select=*&city=eq.{city}&order=forecast_date.asc&limit=7"
    r = requests.get(url, headers=HEADERS, timeout=10)
    return r.json() if r.status_code == 200 else []


# ── HEADER ───────────────────────────────────────────────────────────────────
col_title, col_city, col_refresh = st.columns([3, 2, 1])
with col_title:
    st.markdown("### 🌤️ Live Weather Dashboard — India")
with col_city:
    selected_city = st.selectbox("", CITIES, label_visibility="collapsed")
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ── FETCH DATA ────────────────────────────────────────────────────────────────
weather_rows  = fetch("weatherdata", selected_city, limit=1)
aqi_rows      = fetch("aqidata",     selected_city, limit=1)
wx_history    = fetch_history("weatherdata", selected_city, limit=144)
aqi_history   = fetch_history("aqidata",     selected_city, limit=144)
forecast_rows = fetch_forecast(selected_city)

if not weather_rows:
    st.error(f"No data found for {selected_city}. Check your database connection.")
    st.stop()

w   = weather_rows[0]
aqi = aqi_rows[0] if aqi_rows else {}

temp      = w.get("temperature", 0)
humidity  = w.get("humidity", 0)
pressure  = w.get("pressure", 0)
wind      = w.get("wind_speed", 0)
desc      = w.get("weather_desc", "clear sky").lower()
recorded  = w.get("recorded_at", "")
sunrise   = w.get("sunrise", "N/A")
sunset    = w.get("sunset",  "N/A")

aqi_val   = aqi.get("aqi",   0)
pm25      = aqi.get("pm2_5", 0)
pm10      = aqi.get("pm10",  0)
no2       = aqi.get("no2",   0)
o3        = aqi.get("o3",    0)

try:
    dt_obj   = datetime.fromisoformat(recorded.replace("Z",""))
    last_upd = dt_obj.strftime("%d %b, %I:%M %p")
except:
    last_upd = recorded[:16] if recorded else "N/A"

wx_icon   = WEATHER_ICONS.get(desc, "🌡️")
aqi_label = AQI_LABELS.get(aqi_val, "N/A")
aqi_color = AQI_COLORS.get(aqi_val, "#888")


# ── ROW 1 ─────────────────────────────────────────────────────────────────────
r1c1, r1c2, r1c3 = st.columns([1.4, 2, 1.2])

# Hero card
with r1c1:
    st.markdown(f"""
    <div class="hero-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
                <div class="hero-city">📍 {selected_city}</div>
                <div class="hero-updated">Last Updated, {last_upd}</div>
            </div>
        </div>
        <div class="hero-icon">{wx_icon}</div>
        <div class="hero-temp">{temp:.1f} °C</div>
        <div class="hero-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

# Forecast strip
with r1c2:
    st.markdown('<div class="section-card"><div class="section-title">7-Day Forecast</div>', unsafe_allow_html=True)
    if forecast_rows:
        cols = st.columns(len(forecast_rows[:7]))
        for i, row in enumerate(forecast_rows[:7]):
            day  = row.get("day_name", "")[:3]
            t    = row.get("temp", 0)
            fdesc= row.get("weather_desc","clear sky").lower()
            icon = WEATHER_ICONS.get(fdesc, "🌡️")
            with cols[i]:
                st.markdown(f"""
                <div class="forecast-card">
                    <div class="forecast-day">{day}</div>
                    <div class="forecast-icon">{icon}</div>
                    <div class="forecast-temp">{t:.0f}°</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("No forecast data available.")
    st.markdown('</div>', unsafe_allow_html=True)

# Sunrise/Sunset
with r1c3:
    st.markdown(f"""
    <div class="section-card" style="height:100%">
        <div class="section-title">Sunrise & Sunset</div>
        <div style="padding:10px 0">
            <div style="font-size:28px">🌅</div>
            <div style="color:#8892a4;font-size:12px;margin-top:4px">Sunrise</div>
            <div style="font-size:22px;font-weight:700">{sunrise}</div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.06);margin:12px 0">
        <div style="padding:10px 0">
            <div style="font-size:28px">🌇</div>
            <div style="color:#8892a4;font-size:12px;margin-top:4px">Sunset</div>
            <div style="font-size:22px;font-weight:700">{sunset}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── ROW 2: METRICS ────────────────────────────────────────────────────────────
metrics = [
    ("💧", "Humidity",    f"{humidity} %"),
    ("🌬️", "Wind Speed",  f"{wind:.1f} m/s"),
    ("👁️", "Visibility",  "N/A"),
    ("🌡️", "Pressure",    f"{pressure} hPa"),
    ("☀️", "UV Index",    "N/A"),
    ("🌧️", "Precipitation","N/A"),
]
m_cols = st.columns(6)
for i, (icon, label, val) in enumerate(metrics):
    with m_cols[i]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{val}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── ROW 3: CHARTS ─────────────────────────────────────────────────────────────
r3c1, r3c2, r3c3 = st.columns([2, 1.3, 1.2])

# Temperature trend
with r3c1:
    st.markdown('<div class="section-card"><div class="section-title">Temperature Trend (Last 24h)</div>', unsafe_allow_html=True)
    if wx_history:
        df_wx = pd.DataFrame(wx_history)
        df_wx["recorded_at"] = pd.to_datetime(df_wx["recorded_at"])
        df_wx = df_wx.sort_values("recorded_at")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_wx["recorded_at"], y=df_wx["temperature"],
            mode="lines+markers",
            line=dict(color="#FF6B2B", width=2.5),
            marker=dict(size=4, color="#FF6B2B"),
            fill="tozeroy",
            fillcolor="rgba(255,107,43,0.08)",
        ))
        fig.update_layout(
            height=200, margin=dict(l=0,r=0,t=0,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, color="#8892a4", tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#8892a4", tickfont=dict(size=10)),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# AQI gauge + pollutants
with r3c2:
    st.markdown('<div class="section-card"><div class="section-title">Air Quality Overview</div>', unsafe_allow_html=True)
    if aqi_val:
        gauge_col, poll_col = st.columns([1,1])
        with gauge_col:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=aqi_val,
                number={"font":{"size":28,"color":"#fff"}},
                gauge={
                    "axis":{"range":[0,6],"tickcolor":"#8892a4","tickfont":{"size":9}},
                    "bar":{"color":aqi_color,"thickness":0.25},
                    "bgcolor":"rgba(0,0,0,0)",
                    "steps":[
                        {"range":[0,1],"color":"rgba(0,200,83,0.15)"},
                        {"range":[1,2],"color":"rgba(118,255,3,0.15)"},
                        {"range":[2,3],"color":"rgba(255,214,0,0.15)"},
                        {"range":[3,4],"color":"rgba(255,109,0,0.15)"},
                        {"range":[4,5],"color":"rgba(213,0,0,0.15)"},
                        {"range":[5,6],"color":"rgba(123,31,162,0.15)"},
                    ],
                },
                domain={"x":[0,1],"y":[0,1]},
            ))
            fig_g.update_layout(
                height=160, margin=dict(l=10,r=10,t=10,b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color":"#fff"},
            )
            st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar":False})
            st.markdown(f"<div style='text-align:center;font-size:13px;font-weight:700;color:{aqi_color}'>{aqi_label}</div>", unsafe_allow_html=True)

        with poll_col:
            for name, val in [("PM2.5", pm25), ("PM10", pm10), ("NO2", no2), ("O3", o3)]:
                st.markdown(f"""
                <div class="pollutant-row">
                    <span class="pollutant-name">{name}</span>
                    <span class="pollutant-val">{val:.0f}</span>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("No AQI data.")
    st.markdown('</div>', unsafe_allow_html=True)

# AQI trend
with r3c3:
    st.markdown('<div class="section-card"><div class="section-title">AQI Trend</div>', unsafe_allow_html=True)
    if aqi_history:
        df_aqi = pd.DataFrame(aqi_history)
        df_aqi["recorded_at"] = pd.to_datetime(df_aqi["recorded_at"])
        df_aqi = df_aqi.sort_values("recorded_at")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_aqi["recorded_at"], y=df_aqi["aqi"],
            mode="lines",
            line=dict(color=aqi_color, width=2.5),
            fill="tozeroy",
            fillcolor=f"rgba(255,107,43,0.08)",
        ))
        fig2.update_layout(
            height=200, margin=dict(l=0,r=0,t=0,b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, color="#8892a4", tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#8892a4",
                       tickfont=dict(size=9), range=[0,6]),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#3a4155;font-size:12px;padding:10px">
    Data updates every 10 minutes via Azure Functions → Supabase PostgreSQL
</div>
""", unsafe_allow_html=True)
