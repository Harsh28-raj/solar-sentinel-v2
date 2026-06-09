import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
from datetime import datetime

app = FastAPI(
    title="SolarSentinel - MagStorm Shield Backend",
    description="Stage 5.3: 14-Node Advanced Grid Heatmap & Multi-Route Aviation Infrastructure Pipeline",
    version="5.3.0"
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
            async with httpx.AsyncClient(timeout=8.0) as client:
                plasma_response = await client.get(NOAA_PLASMA_URL)
                if plasma_response.status_code == 200:
                    plasma_data = plasma_response.json()
                    for reading in reversed(plasma_data):
                        try:
                            extracted_speed = float(reading[2])
                            if extracted_speed > 0:
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
                
                cached_space_weather_state["pipeline_status"] = "HEALTHY"
                cached_space_weather_state["last_successful_fetch"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [SYNC SUCCESS] Speed: {cached_space_weather_state['solar_wind_speed']} | Kp: {cached_space_weather_state['kp_index']}")
        
        except Exception as e:
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
        
        # 14 Full Active Grids Mapping (All Green in Nominal Mode)
        grid_triggers = [
            {"lat": 28.7041, "lng": 77.1025, "region": "Northern Grid (Delhi NCR)", "alert_level": "GREEN", "value": 0.1},
            {"lat": 26.1445, "lng": 91.7362, "region": "Northeastern Grid (Guwahati)", "alert_level": "GREEN", "value": 0.1},
            {"lat": 19.0760, "lng": 72.8777, "region": "Western Grid (Mumbai)", "alert_level": "GREEN", "value": 0.12},
            {"lat": 12.9716, "lng": 77.5946, "region": "Southern Grid (Bengaluru)", "alert_level": "GREEN", "value": 0.08},
            {"lat": 22.5726, "lng": 88.3639, "region": "Eastern Grid (Kolkata)", "alert_level": "GREEN", "value": 0.15},
            {"lat": 17.3850, "lng": 78.4867, "region": "Central Grid (Hyderabad)", "alert_level": "GREEN", "value": 0.11},
            {"lat": 34.0837, "lng": 74.7973, "region": "Kashmir Sub-Grid (Srinagar)", "alert_level": "GREEN", "value": 0.05},
            {"lat": 13.0827, "lng": 80.2707, "region": "Tamil Nadu Link (Chennai)", "alert_level": "GREEN", "value": 0.07},
            {"lat": 23.0225, "lng": 72.5714, "region": "Gujarat Corridor (Ahmedabad)", "alert_level": "GREEN", "value": 0.1},
            {"lat": 20.2961, "lng": 85.8245, "region": "Odisha Coastal Node (Bhubaneswar)", "alert_level": "GREEN", "value": 0.12},
            {"lat": 26.1158, "lng": 91.7086, "region": "Assam Hub Grid (Dispur)", "alert_level": "GREEN", "value": 0.09},
            {"lat": 32.7266, "lng": 74.8570, "region": "Duggar Sector Grid (Jammu)", "alert_level": "GREEN", "value": 0.06},
            {"lat": 11.6234, "lng": 92.7265, "region": "Bay of Bengal Telemetry (Port Blair)", "alert_level": "GREEN", "value": 0.04},
            {"lat": 9.9312,  "lng": 76.2673, "region": "Kerala Coastal Grid (Kochi)", "alert_level": "GREEN", "value": 0.05}
        ]
        actions = ["All grids operational. National infrastructure systems nominal."]
        
        aviation = [
            { "route_id": "IN-US-POLAR", "status": "NOMINAL", "action": "Proceed with planned flight path" },
            { "route_id": "IN-EU-NORTH", "status": "NOMINAL", "action": "Optimal signal strength. Normal operations." },
            { "route_id": "DEL-LON-TRANS", "status": "NOMINAL", "action": "HF Radio communication stable." },
            { "route_id": "MUM-NYC-POLAR", "status": "NOMINAL", "action": "No solar radiation risk detected." }
        ]
    else:
        if 5.0 <= kp < 7.0:
            s_class = "G1-G2 (Moderate Storm)"
            s_color = "#FFA500"
            action_text = "Monitor transformer temperatures closely across high-latitude nodes."
            
            # Moderate State Distribution
            grid_triggers = [
                {"lat": 28.7041, "lng": 77.1025, "region": "Northern Grid (Delhi NCR)", "alert_level": "YELLOW", "value": 0.5},
                {"lat": 26.1445, "lng": 91.7362, "region": "Northeastern Grid (Guwahati)", "alert_level": "YELLOW", "value": 0.5},
                {"lat": 22.5726, "lng": 88.3639, "region": "Eastern Grid (Kolkata)", "alert_level": "YELLOW", "value": 0.4},
                {"lat": 34.0837, "lng": 74.7973, "region": "Kashmir Sub-Grid (Srinagar)", "alert_level": "YELLOW", "value": 0.6},
                {"lat": 32.7266, "lng": 74.8570, "region": "Duggar Sector Grid (Jammu)", "alert_level": "YELLOW", "value": 0.6},
                {"lat": 26.1158, "lng": 91.7086, "region": "Assam Hub Grid (Dispur)", "alert_level": "YELLOW", "value": 0.5},
                {"lat": 23.0225, "lng": 72.5714, "region": "Gujarat Corridor (Ahmedabad)", "alert_level": "GREEN", "value": 0.2},
                {"lat": 19.0760, "lng": 72.8777, "region": "Western Grid (Mumbai)", "alert_level": "GREEN", "value": 0.18},
                {"lat": 17.3850, "lng": 78.4867, "region": "Central Grid (Hyderabad)", "alert_level": "GREEN", "value": 0.15},
                {"lat": 20.2961, "lng": 85.8245, "region": "Odisha Coastal Node (Bhubaneswar)", "alert_level": "GREEN", "value": 0.2},
                {"lat": 12.9716, "lng": 77.5946, "region": "Southern Grid (Bengaluru)", "alert_level": "GREEN", "value": 0.1},
                {"lat": 13.0827, "lng": 80.2707, "region": "Tamil Nadu Link (Chennai)", "alert_level": "GREEN", "value": 0.1},
                {"lat": 11.6234, "lng": 92.7265, "region": "Bay of Bengal Telemetry (Port Blair)", "alert_level": "GREEN", "value": 0.08},
                {"lat": 9.9312,  "lng": 76.2673, "region": "Kerala Coastal Grid (Kochi)", "alert_level": "GREEN", "value": 0.07}
            ]
        else:
            s_class = "G4-G5 (Catastrophic Storm)"
            s_color = "#8B0000"
            action_text = "CRITICAL RISK: Isolate Northern & High-Latitude lines immediately. Shed load by 35%."
            
            # Catastrophic State Distribution (Realistic physics mapping based on latitude)
            grid_triggers = [
                {"lat": 28.7041, "lng": 77.1025, "region": "Northern Grid (Delhi NCR)", "alert_level": "RED", "value": 1.0},
                {"lat": 26.1445, "lng": 91.7362, "region": "Northeastern Grid (Guwahati)", "alert_level": "RED", "value": 1.0},
                {"lat": 34.0837, "lng": 74.7973, "region": "Kashmir Sub-Grid (Srinagar)", "alert_level": "RED", "value": 1.0},
                {"lat": 32.7266, "lng": 74.8570, "region": "Duggar Sector Grid (Jammu)", "alert_level": "RED", "value": 1.0},
                {"lat": 26.1158, "lng": 91.7086, "region": "Assam Hub Grid (Dispur)", "alert_level": "RED", "value": 0.98},
                {"lat": 22.5726, "lng": 88.3639, "region": "Eastern Grid (Kolkata)", "alert_level": "YELLOW", "value": 0.65},
                {"lat": 23.0225, "lng": 72.5714, "region": "Gujarat Corridor (Ahmedabad)", "alert_level": "YELLOW", "value": 0.55},
                {"lat": 19.0760, "lng": 72.8777, "region": "Western Grid (Mumbai)", "alert_level": "YELLOW", "value": 0.5},
                {"lat": 20.2961, "lng": 85.8245, "region": "Odisha Coastal Node (Bhubaneswar)", "alert_level": "YELLOW", "value": 0.45},
                {"lat": 17.3850, "lng": 78.4867, "region": "Central Grid (Hyderabad)", "alert_level": "GREEN", "value": 0.25},
                {"lat": 12.9716, "lng": 77.5946, "region": "Southern Grid (Bengaluru)", "alert_level": "GREEN", "value": 0.18},
                {"lat": 13.0827, "lng": 80.2707, "region": "Tamil Nadu Link (Chennai)", "alert_level": "GREEN", "value": 0.15},
                {"lat": 11.6234, "lng": 92.7265, "region": "Bay of Bengal Telemetry (Port Blair)", "alert_level": "GREEN", "value": 0.1},
                {"lat": 9.9312,  "lng": 76.2673, "region": "Kerala Coastal Grid (Kochi)", "alert_level": "GREEN", "value": 0.1}
            ]

        actions = [
            f"[GRID ALERT] {action_text}",
            "[INDUCED CURRENT] Geomagnetically Induced Currents (GIC) spiking drastically on ground assets."
        ]
        
        if kp >= 7.0:
            aviation = [
                { "route_id": "IN-US-POLAR", "status": "RE-ROUTED", "action": "CRITICAL: High radiation risk over North Pole. Divert to Sub-Polar Route B." },
                { "route_id": "IN-EU-NORTH", "status": "WARNING", "action": "HF Radio Blackout expected. Monitor backup satellite comms." },
                { "route_id": "DEL-LON-TRANS", "status": "RE-ROUTED", "action": "ALERT: Cosmic ray influx spiking. Divert 5 degrees South." },
                { "route_id": "MUM-NYC-POLAR", "status": "NOMINAL", "action": "Safe route altitude maintained. Proceed with caution." }
            ]
        else:
            aviation = [
                { "route_id": "IN-US-POLAR", "status": "MONITOR", "action": "Expect minor HF propagation delay." },
                { "route_id": "IN-EU-NORTH", "status": "NOMINAL", "action": "Proceed with caution. Solar wind velocity elevated." },
                { "route_id": "DEL-LON-TRANS", "status": "MONITOR", "action": "Watch for intermittent signal fading." },
                { "route_id": "MUM-NYC-POLAR", "status": "NOMINAL", "action": "Route clear. Solar particle flux within bounds." }
            ]

    return {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline_status": cached_space_weather_state["pipeline_status"],
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
