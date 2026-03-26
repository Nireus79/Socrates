#!/usr/bin/env python
"""Minimal FastAPI app to test routing"""
from fastapi import APIRouter, FastAPI
import uvicorn

# Create app
app = FastAPI(title="MinimalApp")

# Create router
test_router = APIRouter(prefix="/test")

@test_router.get("/endpoint")
async def test_endpoint():
    return {"message": "works"}

# Include router at module level
print(f"[APP] Before router: {len(app.routes)} routes")
app.include_router(test_router)
print(f"[APP] After router: {len(app.routes)} routes")

# Direct endpoint
@app.get("/direct")
async def direct_endpoint():
    return {"message": "direct"}

print(f"[APP] After direct: {len(app.routes)} routes")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
