from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, SessionLocal, Base
from seed import seed_data
from routers import auth, contracts, hives, inspections, anomalies, settlements, orchards, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="蜂场授粉服务管理平台",
    description="蜜蜂授粉服务管理平台后端API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(hives.router, prefix="/api")
app.include_router(inspections.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(settlements.router, prefix="/api")
app.include_router(orchards.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "蜂场授粉服务管理平台 API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
