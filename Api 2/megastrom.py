import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
from datetime import datetime

app = FastAPI(
    title="SolarSentinel - MagStorm Shield Backend",
    description="Stage 5: Production-Grade Response Setup with Robust Error Fallbacks & RAM Caching",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TelemetrySchema(BaseModel):
    speed: str
    kp_index: float

class StormMetadataSchema(BaseModel):
    storm_class: str
    severity_color: str
    eta_seconds: int
    formatted_eta: str

class HeatmapTriggerSchema(BaseModel):
    lat: float
    lng: float
    region: str
    alert_level: str
    value: float

class AviationAlertSchema(BaseModel):
    route_id: str
    status: str
    action: str

class MagStormShieldResponse(BaseModel):
    timestamp: str
    pipeline_status: str
    simulation_active: bool
    live_telemetry: TelemetrySchema
    storm_metadata: StormMetadataSchema
    grid_heatmap_triggers: List[HeatmapTriggerSchema]
    automated_actions: List[str]
    aviation_alerts: List[AviationAlertSchema]

# ==========================================
# STAGE 5 CORE: Global RAM Cache Protection
# ==========================================
# Agar internet chala jaye, toh ye default safe values system ko crash hone se bachayengi
cached_space_weather_state = {
    "solar_wind_speed": 450.0,
    "kp_index": 2.5,
    "pipeline_status": "HEALTHY",
    "last_successful_fetch": None
}

async def track_space_weather_pipeline():
    global cached_space_weather_state
    NOAA_PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
    NOAA_KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
    
    while True:
        try:
            # Timeout ko 8.0 seconds set kiya hai taaki slow internet par pipeline hange na ho
            async with httpx.AsyncClient(timeout=8.0) as client:
                plasma_response = await client.get(NOAA_PLASMA_URL)
                if plasma_response.status_code == 200:
                    plasma_data = plasma_response.json()
                    for reading in reversed(plasma_data):
                        try:
                            extracted_speed = float(reading[2])
                            if extracted_speed > 0:
                                # Data milte hi RAM Cache instantly update hoga
                                cached_space_weather_state["solar_wind_speed"] = round(extracted_speed, 2)
                                break
                        except (ValueError, IndexError, TypeError):
                            continue

                kp_response = await client.get(NOAA_KP_URL)
                if kp_response.status_code == 200:
                    kp_data = kp_response.json()
                    for entry in reversed(kp_data):
                        try:
                            if isinstance(entry, list):
                                for item in entry:
                                    try:
                                        val = float(item)
                                        if 0.0 <= val <= 9.0:
                                            cached_space_weather_state["kp_index"] = round(val, 1)
                                            raise StopIteration
                                    except ValueError:
                                        continue
                            elif isinstance(entry, dict):
                                for key in ["kp_index", "kp", "observed_kp"]:
                                    if key in entry:
                                        cached_space_weather_state["kp_index"] = round(float(entry[key]), 1)
                                        raise StopIteration
                        except (ValueError, IndexError, TypeError):
                            continue
                        except StopIteration:
                            break
                
                # Fetch successful hote hi status HEALTHY ho jayega
                cached_space_weather_state["pipeline_status"] = "HEALTHY"
                cached_space_weather_state["last_successful_fetch"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [SYNC SUCCESS] Speed: {cached_space_weather_state['solar_wind_speed']} | Kp: {cached_space_weather_state['kp_index']}")
        
        except Exception as e:
            # STAGE 5 CRASH PROTECTION: Agar net down hua, toh loop crash nahi hoga, cache activate ho jayega
            cached_space_weather_state["pipeline_status"] = "USING_CACHE_FALLBACK"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [NETWORK WARN] Live fetch failed, serving from internal cache: {e}")
            
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(track_space_weather_pipeline())

@app.get("/api/v1/infrastructure/impact", response_model=MagStormShieldResponse)
async def get_infrastructure_impact(mode: str = "live"):
    if mode == "simulation":
        speed = 1200.0
        kp = 9.0
        is_simulated = True
    else:
        # Normal mode mein data direct global RAM cache se uthaya jayega
        speed = cached_space_weather_state["solar_wind_speed"]
        kp = cached_space_weather_state["kp_index"]
        is_simulated = False

    eta_seconds = int(1500000 / speed)
    minutes = eta_seconds // 60
    seconds = eta_seconds % 60
    formatted_eta = f"{minutes} Min {seconds} Sec"

    if kp < 5.0:
        s_class = "Nominal"
        s_color = "#00FF00"
        grid_triggers = [
            {"lat": 28.7041, "lng": 77.1025, "region": "Delhi NCR", "alert_level": "GREEN", "value": 0.1},
            {"lat": 26.1445, "lng": 91.7362, "region": "Northeast Grid", "alert_level": "GREEN", "value": 0.1}
        ]
        actions = ["All grids operational. Systems nominal."]
        aviation = [{"route_id": "IN-US-POLAR", "status": "NOMINAL", "action": "Proceed with planned flight path"}]
    else:
        if 5.0 <= kp < 7.0:
            s_class = "G1-G2 (Moderate Storm)"
            s_color = "#FFA500"
            alert_status = "YELLOW"
            grid_val = 0.5
            action_text = "Monitor transformer temperatures closely."
            flight_status = "MONITOR"
            flight_action = "Expect minor HF propagation delay."
        else:
            s_class = "G4-G5 (Catastrophic Storm)"
            s_color = "#8B0000"
            alert_status = "RED"
            grid_val = 1.0
            action_text = "CRITICAL RISK: Isolate Northern transformer links. Reduce Delhi grid load by 30% NOW."
            flight_status = "RE-ROUTED"
            flight_action = "Polar route closed. Divert flights to Mid-Latitude track."

        grid_triggers = [
            {"lat": 28.7041, "lng": 77.1025, "region": "Delhi NCR", "alert_level": alert_status, "value": grid_val},
            {"lat": 26.1445, "lng": 91.7362, "region": "Northeast Grid", "alert_level": alert_status, "value": grid_val}
        ]
        actions = [
            f"[GRID ALERT] {action_text}",
            "[INDUCED CURRENT] Geomagnetically Induced Currents (GIC) spiking above 45 Amps."
        ]
        aviation = [{"route_id": "IN-US-POLAR", "status": flight_status, "action": flight_action}]

    return {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline_status": cached_space_weather_state["pipeline_status"], # Frontend yahan se light status padhega
        "simulation_active": is_simulated,
        "live_telemetry": {"speed": f"{speed} km/s", "kp_index": kp},
        "storm_metadata": {
            "storm_class": s_class,
            "severity_color": s_color,
            "eta_seconds": eta_seconds,
            "formatted_eta": formatted_eta
        },
        "grid_heatmap_triggers": grid_triggers,
        "automated_actions": actions,
        "aviation_alerts": aviation
    }