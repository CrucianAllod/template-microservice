from pydantic import BaseModel, Field

class TestMessage(BaseModel):
    content: str = Field(
        ...,
        example="Hello from FastAPI template!",
        description="Содержимое тестового сообщения."
    )
    sender: str = Field(
        "Template API",
        example="Auth Service",
        description="Идентификатор отправителя сообщения."
    )