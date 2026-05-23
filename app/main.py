from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import quotes, simulation, analysis, agent

app = FastAPI(
    title="Investimentos AI",
    description=(
        "Real-time B3 stock quotes via HG Brasil API "
        "and investment simulation engine with multiple strategies."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotes.router)
app.include_router(simulation.router)
app.include_router(analysis.router)
app.include_router(agent.router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}
