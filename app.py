import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# 1. Danh sách tọa độ các tỉnh thành tiêu biểu tại Việt Nam (có thể mở rộng)
CITIES = {
    "Hà Nội": {"lat": 21.0285, "lon": 105.8542},
    "TP. Hồ Chí Minh": {"lat": 10.8231, "lon": 106.6297},
    "Đà Nẵng": {"lat": 16.0544, "lon": 108.2022},
    "Hải Phòng": {"lat": 20.8449, "lon": 106.6881},
    "Cần Thơ": {"lat": 10.0452, "lon": 105.7469},
    "Nha Trang": {"lat": 12.2388, "lon": 109.1967},
    "Đà Lạt": {"lat": 11.9404, "lon": 108.4583},
    "Huế": {"lat": 16.4637, "lon": 107.5909}
}

st.set_page_config(page_title="Dự báo thời tiết Việt Nam", layout="wide")
st.title("🌤️ Ứng dụng Thời tiết & Bức xạ mặt trời tại Việt Nam")

# --- Thanh công cụ bên trái (Sidebar) ---
st.sidebar.header("Tùy chỉnh tham số")

# Chọn tỉnh thành
selected_city = st.sidebar.selectbox("Chọn Tỉnh/Thành phố:", list(CITIES.keys()))
lat = CITIES[selected_city]["lat"]
lon = CITIES[selected_city]["lon"]

# Chọn loại dữ liệu (Quá khứ / Hiện tại & Dự báo)
mode = st.sidebar.radio("Chọn khoảng thời gian dữ liệu:", ["Hiện tại & Dự báo", "Dữ liệu Quá khứ"])

# Chọn khoảng thời gian hiển thị
granularity = st.sidebar.selectbox("Khung thời gian hiển thị:", ["Theo giờ (Hourly)", "Theo ngày (Daily)"])

# --- Lấy dữ liệu từ Open-Meteo API ---
@st.cache_data(ttl=3600)  # Lưu cache 1 giờ để giảm tải gọi API
def fetch_weather_data(lat, lon, mode, start_date=None, end_date=None):
    if mode == "Hiện tại & Dự báo":
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m"],
            "hourly": ["temperature_2m", "relative_humidity_2m", "shortwave_radiation"],
            "daily": ["temperature_2m_max", "temperature_2m_min", "shortwave_radiation_sum"],
            "timezone": "Asia/Bangkok"
        }
    else:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ["temperature_2m", "relative_humidity_2m", "shortwave_radiation"],
            "daily": ["temperature_2m_max", "temperature_2m_min", "shortwave_radiation_sum"],
            "timezone": "Asia/Bangkok"
        }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# Xử lý thời gian cho dữ liệu Quá khứ
start_date, end_date = None, None
if mode == "Dữ liệu Quá khứ":
    today = datetime.now().date()
    start_date = st.sidebar.date_input("Từ ngày:", today - timedelta(days=7))
    end_date = st.sidebar.date_input("Đến ngày:", today - timedelta(days=1))

data = fetch_weather_data(lat, lon, mode, str(start_date), str(end_date))

# --- Hiển thị kết quả ---
if data:
    # Hiển thị dữ liệu Hiện tại (nếu ở chế độ Dự báo)
    if mode == "Hiện tại & Dự báo" and "current" in data:
        st.subheader(f"📌 Thời tiết hiện tại tại {selected_city}")
        col1, col2 = st.columns(2)
        col1.metric("Nhiệt độ", f"{data['current']['temperature_2m']} °C")
        col2.metric("Độ ẩm", f"{data['current']['relative_humidity_2m']} %")

    st.markdown("---")
    st.subheader(f"📊 Dữ liệu chi tiết ({selected_city})")

    # Xử lý hiển thị dữ liệu Theo Giờ hoặc Theo Ngày
    if granularity == "Theo giờ (Hourly)" and "hourly" in data:
        df = pd.DataFrame({
            "Thời gian": data["hourly"]["time"],
            "Nhiệt độ (°C)": data["hourly"]["temperature_2m"],
            "Độ ẩm (%)": data["hourly"]["relative_humidity_2m"],
            "Bức xạ mặt trời (W/m²)": data["hourly"]["shortwave_radiation"]
        })
        df["Thời gian"] = pd.to_datetime(df["Thời gian"])
        
        # Biểu đồ
        st.line_chart(df.set_index("Thời gian")[["Nhiệt độ (°C)", "Độ ẩm (%)"]])
        st.area_chart(df.set_index("Thời gian")["Bức xạ mặt trời (W/m²)"])
        
        # Bảng dữ liệu
        st.dataframe(df, use_container_width=True)

    elif granularity == "Theo ngày (Daily)" and "daily" in data:
        df = pd.DataFrame({
            "Ngày": data["daily"]["time"],
            "Nhiệt độ Cao nhất (°C)": data["daily"]["temperature_2m_max"],
            "Nhiệt độ Thấp nhất (°C)": data["daily"]["temperature_2m_min"],
            "Tổng Bức xạ mặt trời (MJ/m²)": data["daily"]["shortwave_radiation_sum"]
        })
        
        # Biểu đồ
        st.line_chart(df.set_index("Ngày")[["Nhiệt độ Cao nhất (°C)", "Nhiệt độ Thấp nhất (°C)"]])
        st.bar_chart(df.set_index("Ngày")["Tổng Bức xạ mặt trời (MJ/m²)"])
        
        # Bảng dữ liệu
        st.dataframe(df, use_container_width=True)

else:
    st.error("Không thể lấy dữ liệu từ API. Vui lòng kiểm tra lại kết nối hoặc tham số chọn!")