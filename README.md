# 🚦 Traffic_Web: Travel Risk Assessment Web Application

**Traffic_Web** is a web application designed to **assess travel risks** for a given route. The risk assessment considers factors such as **weather conditions, past accident data, and road conditions** to calculate a risk coefficient, helping users make informed travel decisions.

---

## 🌍 How It Works

### 1️⃣ Route Selection
- The user enters a **start and end location** (e.g., "Street, City, Country").
- An optional **departure time** can be specified (**currently in UTC**).
- **Nominatim (geopy)** determines the coordinates. Some cities may not be recognized (e.g., Omer, Israel).
- The **openrouteservice** API generates the route.
- The route consists of **multiple waypoints** with latitude and longitude.

---

### 2️⃣ Route Data Processing
Each route segment is enriched with:
- **Distance** (calculated using `geodesic.rm` from geopy).
- **Average Speed** (default: 60 km/h, adjusted using openrouteservice data if available).
- **Travel Time** (calculated from segment distance & speed).
- **Estimated Arrival Time** (considering user-defined departure time).
- **Cumulative Distance** (total distance traveled up to each point).
- **Accident Severity** (initially set to zero).

#### 🔢 Route-Wide Metrics:
- **Total Duration (`sec_route`)** in seconds.
- **Total Distance (`dist`)** in kilometers.
- **Total Travel Time (`time`)**.
- **Number of Route Points (`count`)**.

---

### 3️⃣ Weather Forecast Integration 🌦️
Weather data is fetched from **OpenWeatherMap API**:
- To optimize **API requests**:
  - Forecasts are **cached** during the session.
  - If points are **within 10 km**, they share the same forecast.
- Extracted weather parameters:
  - **Weather Condition:** `Clear` or `Rainy`
  - **Road Condition:** `Dry` or `Wet`
  - **Sunrise/Sunset Times** (to determine daytime or nighttime travel).

---

### 4️⃣ Accident Data Integration 🚨
Accident data is retrieved from **Google BigQuery (`traffic.accident_analysis` table)**.
If a route point has accident data:
- **Accident Count** is recorded.
- **Speed Limit & District Weights** are assigned based on the latest data.
- **Serious Accidents Count** (severity > 1).
- **Weather & Road Condition Weights** are applied if they match past accident conditions.
- **Day/Night & Day-of-Week Weights** are set if they match past accidents.
- The **most recent accident at each point** is logged.

---

### 5️⃣ Assigning Weights for Points Without Accidents
If a point has no accident data, default weights are assigned:
| Condition         | Weight |
|------------------|--------|
| **Weather** 
| **Weather** 
| **Road**
| **Road** 
| **Sunday** 
| **Monday** 
| **Tuesday** 
| **Wednesday** 
| **Thursday**
| **Friday** 
| **Saturday** 

---

### 6️⃣ Risk Calculation ⚖️
- **Total Weight** at each point = Sum of:
  - Weather, road, day/night, day-of-week, district, speed limit, and severity weights.
- **Final Risk Coefficient Calculation**:
  - Sum of all segment weights **multiplied by travel duration**.
  - Overall **Risk Score** = **(Total Weight ÷ Total Route Duration)**.
  - **Final Risk Coefficient** = **(Total Weight ÷ 60)**.
  
⚠️ **Next Steps:** Define **threshold values** for a traffic-light risk indicator (Green, Yellow, Red).

---

### 7️⃣ Risk Trend Analysis 📈
- To visualize **risk distribution**, the coefficient from step 6 is computed for **each point**, marking segment endpoints.
- This allows for **route-specific risk mapping**.

---

## 🔧 Future Improvements
✅ Implement a **traffic-light risk system** (Green, Yellow, Red).  
✅ Allow users to input **local time zones** instead of UTC.  
✅ Improve accident weight selection logic.  
✅ Handle unrecognized cities in the geolocation API.  

---

## 📦 Installation & Setup

### 🔹 Prerequisites
- Python 3.8+
- `geopy`, `openrouteservice`, `requests`, `pandas`
- API keys for:
  - **OpenWeatherMap** (`api_id` in `mete0.py`)
  - **OpenRouteService** (`api_key` in `road.py`)
  - **Google BigQuery** (accident data)

### 🔹 Installation
```bash
git clone https://github.com/your-repo/traffic_web.git
cd traffic_web
pip install -r requirements.txt
```

### 🔹 Running the Application
```bash
python main_traffic.py
```

---

## 🛠 Technologies Used
- **Python** (Backend)
- **Flask** (Web API)
- **geopy** (Geolocation)
- **openrouteservice** (Routing)
- **OpenWeatherMap API** (Weather Forecasts)
- **Google BigQuery** (Accident Data)
- **Pandas** (Data Processing)

---

## 📜 License
MIT License - Free to use and modify.

---

## 📢 Contact & Contributions
- Found a bug? Open an **issue**!
- Want to contribute? Fork the repo and submit a **pull request**.
- Questions? Reach out via **GitHub Discussions**.

🚀 **Stay safe on the roads!** 🚦
