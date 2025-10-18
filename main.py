from fastapi import FastAPI
from src.auth.auth_router import router as auth_router
from src.admin.admin_router import router as admin_router

app = FastAPI(
    title="Arbitrage Platform API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(admin_router)

@app.get("/")
async def root():
    return {"message": "Arbitrage Platform API", "version": "1.0.0"}
