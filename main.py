import uvicorn
from fastapi import FastAPI
from database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from routers import auth

app = FastAPI(title="Analiza backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             
    allow_credentials=True,            
    allow_methods=["*"],               
    allow_headers=["*"],               
)

app.include_router(auth.router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
