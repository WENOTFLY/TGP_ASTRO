from fastapi import APIRouter, FastAPI
from pydantic import BaseModel


class Update(BaseModel):
    message: dict[str, object] | None = None


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/tg/webhook")
async def tg_webhook(update: Update) -> dict[str, str]:
    return {"status": "ok"}


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


app = create_app()
