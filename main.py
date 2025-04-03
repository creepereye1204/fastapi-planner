from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from pydantic import Field
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging
import uuid
import os


logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.DEBUG,
    datefmt="%m/%d/%Y %I:%M:%S %p",
)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",  # 파란색
        "INFO": "\033[92m",  # 초록색
        "WARNING": "\033[93m",  # 노란색
        "ERROR": "\033[91m",  # 빨간색
        "CRITICAL": "\033[41m",  # 빨간색 배경
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        return f"{log_color}{super().format(record)}{self.RESET}"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": ColoredFormatter,  # 컬러 포맷터 사용
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",  # 컬러 포맷터 사용
            "level": "DEBUG",  # 콘솔 핸들러의 로그 레벨을 DEBUG로 설정
        },
    },
    "loggers": {
        "prod": {
            "handlers": ["console"],
            "level": "DEBUG",  # 모든 로그 출력
            "propagate": True,
        }
    },
}
logging.config.dictConfig(LOGGING)  # 로깅 설정 구성
logger = logging.getLogger("prod")
# .env 파일 경로 지정
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

# 환경 변수 사용
MONGODB_URL = os.getenv("ENV")
DB_NAME = "mongo"


# MongoDB 모델 정의
class Item(Document):
    id: UUID = Field(default_factory=uuid4)
    description: Optional[str] = Field(default=None, description="아이템 설명")
    price: float = Field(gt=0, description="가격은 0보다 커야 합니다")
    tax: Optional[float] = Field(default=None, ge=0, description="세금")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "items"


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = None  # 클라이언트 초기화
    try:
        # 시작 시 실행
        client = AsyncIOMotorClient(MONGODB_URL)
        await init_beanie(database=client[DB_NAME], document_models=[Item])
        yield
    except Exception as e:
        print(f"MongoDB 연결 오류: {e}")  # 로깅 추가
        raise  # 애플리케이션 시작 실패를 알림
    finally:
        # 종료 시 실행
        if client:
            client.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI with Beanie and MongoDB"}


@app.post("/items/", response_model=Item)
async def create_item(item: Item) -> Item:
    try:
        await item.insert()
        return item

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/items/", response_model=List[Item])
async def get_items(skip: int = 0, limit: int = 10) -> List[Item]:
    try:
        items = await Item.find_all().skip(skip).limit(limit).to_list()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
