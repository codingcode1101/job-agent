from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main import run_agent
from db import save_chat, get_recent_chats

app = FastAPI()


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


@app.get("/hello")
def hello():
    return {"message": "Hello from my job agent!"}


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()
    session_id = request.session_id.strip()

    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空。")

    if not session_id:
        raise HTTPException(status_code=400, detail="会话编号不能为空。")

    answer = run_agent(question, session_id)
    record_id = save_chat(question, answer, session_id)

    return {
        "id": record_id,
        "session_id": session_id,
        "answer": answer,
    }


@app.get("/history")
def history(session_id: str = "default"):
    session_id = session_id.strip()

    if not session_id:
        raise HTTPException(status_code=400, detail="会话编号不能为空。")

    records = get_recent_chats(session_id)
    return {
        "session_id": session_id,
        "records": records,
    }