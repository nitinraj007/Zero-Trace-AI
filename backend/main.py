import asyncio
import random
import time
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. FIREBASE ADMIN INITIALIZATION
# ==========================================
# Make sure 'zerotraceai.json' is in the same directory as this script.
try:
    cred = credentials.Certificate("zerotraceai.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("[SYSTEM] Successfully connected to Firebase Project: zerotraceai-777f1")
except Exception as e:
    print(f"[CRITICAL ERROR] Failed to initialize Firebase Admin SDK. Ensure 'zerotraceai.json' exists. Error: {e}")
    # Fallback/Mock DB for development if JSON is missing, but script will likely fail gracefully later.
    db = None

# ==========================================
# 2. FASTAPI APP INITIALIZATION
# ==========================================
app = FastAPI(
    title="Zero-Day Command Center API",
    description="Real-Time AI-Powered Threat Detection & Prevention System Backend",
    version="1.0.0"
)

# Allow CORS for dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 3. PYDANTIC MODELS (DATA VALIDATION)
# ==========================================
# Represents the payload sent by the lightweight eBPF agents running on customer servers
class SyscallTelemetry(BaseModel):
    server_id: str = Field(..., description="Hostname of the monitored server")
    pid: int = Field(..., description="Process ID generating the syscalls")
    process_name: str
    syscall_count: int
    memory_allocated_mb: float
    network_connections: int
    timestamp: float

# ==========================================
# 4. ML / AI THREAT PIPELINE (SIMULATED)
# ==========================================
def run_ml_analysis(telemetry: SyscallTelemetry):
    """
    Simulates the AI Pattern Recognition (PDR Phase 3).
    Evaluates incoming telemetry using simulated ML Models (Isolation Forest, Autoencoders).
    """
    # 1. Calculate Anomaly Score (0.0 to 1.0)
    # In a real scenario, this would be a PyTorch/Scikit-learn model inference.
    anomaly_score = random.random()
    
    # 2. Check against Baseline (Threshold = 0.85)
    if anomaly_score > 0.85:
        # Threat Detected! Generate Alert Payload
        threat_patterns = [
            ("JNDI Injection (Log4Shell)", True, "Process Killed", "text-red-400 border-red-500/30"),
            ("Unusual Heap Allocation", False, "Isolated", "text-orange-400 border-orange-500/30"),
            ("Unexpected eBPF Syscall", False, "Alerting", "text-gray-300 border-gray-600"),
            ("Lateral Movement Attempt", True, "Connection Dropped", "text-red-400 border-red-500/30"),
            ("Suspicious ROP Chain", True, "Process Killed", "text-red-400 border-red-500/30"),
        ]
        
        pattern_name, is_critical, action, action_color = random.choice(threat_patterns)
        confidence = (anomaly_score * 100)
        
        alert_payload = {
            "pattern": pattern_name,
            "server": telemetry.server_id,
            "pid": str(telemetry.pid),
            "conf": f"{confidence:.1f}%",
            "confColor": "text-red-400" if confidence > 90 else "text-orange-400",
            "action": action,
            "actionColor": action_color,
            "isCritical": is_critical,
            "timestamp": firestore.SERVER_TIMESTAMP  # Real-time Firestore Sync
        }
        
        # 3. Push to Firestore (PDR Phase 4 & 5)
        if db:
            # Matches the strict public data path the frontend is listening to
            collection_ref = db.collection('artifacts').document('zeroday-platform').collection('public').document('data').collection('zeroday_alerts')
            collection_ref.add(alert_payload)
            print(f"[THREAT DETECTED] {pattern_name} on {telemetry.server_id} (Conf: {confidence:.1f}%) -> Pushed to Firestore.")

# ==========================================
# 5. API ENDPOINTS
# ==========================================
@app.post("/api/v1/telemetry", tags=["Agent API"])
async def ingest_telemetry(telemetry: SyscallTelemetry, background_tasks: BackgroundTasks):
    """
    Endpoint for server agents to push real-time syscall data.
    Uses BackgroundTasks so the agent isn't blocked by ML processing (High Throughput).
    """
    background_tasks.add_task(run_ml_analysis, telemetry)
    return {"status": "received", "processing": True}

@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """System health check for orchestrators (Kubernetes/Load Balancers)."""
    return {"status": "healthy", "time": datetime.utcnow().isoformat(), "db_connected": db is not None}

# ==========================================
# 6. AUTO-SIMULATOR BACKGROUND TASK
# ==========================================
async def background_threat_simulator():
    """
    Simulates thousands of active agents sending telemetry.
    Generates background noise, occasionally creating a zero-day anomaly.
    """
    print("[SYSTEM] Starting ML Telemetry Simulator...")
    servers = ["prod-web-01", "db-cluster-04", "cache-redis-02", "internal-api-01", "auth-service-01"]
    
    while True:
        # Simulate an incoming eBPF agent payload
        simulated_telemetry = SyscallTelemetry(
            server_id=random.choice(servers),
            pid=random.randint(100, 9000),
            process_name="java" if random.random() > 0.5 else "nginx",
            syscall_count=random.randint(50, 5000),
            memory_allocated_mb=random.uniform(10.0, 4000.0),
            network_connections=random.randint(0, 50),
            timestamp=time.time()
        )
        
        # Process it through the ML pipeline
        run_ml_analysis(simulated_telemetry)
        
        # Wait 3 to 8 seconds before next telemetry batch
        await asyncio.sleep(random.uniform(3.0, 8.0))

@app.on_event("startup")
async def startup_event():
    # Start the background simulator so the dashboard receives data immediately
    asyncio.create_task(background_threat_simulator())

# ==========================================
# 7. SERVER EXECUTION
# ==========================================
if __name__ == "__main__":
    print("""
    =================================================
    ZERO-DAY PATTERN RECOGNITION BACKEND (FastAPI)
    =================================================
    Initializing AI Models...
    Connecting to Firebase (zerotraceai-777f1)...
    Ready to ingest Agent eBPF telemetry.
    """)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)