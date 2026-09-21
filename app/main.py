import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.model_manager import ModelManager
from app.backend import ResponseProcessor
from app.chat_history import ChatHistoryManager

app = FastAPI(title="QwQ-32B CoT Offline AI Suite")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

model_manager = ModelManager()
history_manager = ChatHistoryManager()


class ScanRequest(BaseModel):
    directory_path: str

class LoadModelRequest(BaseModel):
    model_path: str
    n_ctx: int = 4096
    n_gpu_layers: int = 0
    n_batch: int = 512
    n_ubatch: int = 512
    use_mock: bool = False

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    messages: List[Dict[str, str]]
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.95
    reasoning_mode: bool = True
    system_prompt: Optional[str] = "Anda adalah asisten AI serbaguna yang akurat dan responsif."

class MathMLRequest(BaseModel):
    latex: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/scan")
async def scan_models(req: ScanRequest):
    files = model_manager.scan_directory(req.directory_path)
    return {"status": "ok", "models": files}

@app.post("/api/load_model")
async def load_model(req: LoadModelRequest):
    try:
        model_manager.load_model(
            model_path=req.model_path,
            n_ctx=req.n_ctx,
            n_gpu_layers=req.n_gpu_layers,
            n_batch=req.n_batch,
            n_ubatch=req.n_ubatch,
            use_mock=req.use_mock
        )
        return {
            "status": "ok",
            "message": "Model berhasil dimuat.",
            "current_model": req.model_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/unload_model")
async def unload_model():
    model_manager.unload_model()
    return {"status": "ok", "message": "Model berhasil dilepas dari memori."}

@app.get("/api/model_status")
async def model_status():
    return {
        "loaded": model_manager.current_model is not None,
        "current_model_path": model_manager.current_model_path,
        "use_mock": model_manager.use_mock
    }

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    if model_manager.current_model is None:
        raise HTTPException(status_code=400, detail="Belum ada model yang dimuat.")

    # Get or create chat session
    session_id = req.session_id
    if not session_id:
        session = history_manager.create_session()
        session_id = session["id"]

    # Save last user message
    last_user_msg = req.messages[-1]["content"] if req.messages else ""
    history_manager.add_message(session_id, "user", last_user_msg)

    async def event_generator():
        full_text = ""
        stream_gen = model_manager.generate_stream(
            messages=req.messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
            reasoning_mode=req.reasoning_mode,
            system_prompt=req.system_prompt
        )

        for chunk in stream_gen:
            full_text += chunk
            data_json = json.dumps({"chunk": chunk, "session_id": session_id})
            yield f"data: {data_json}\n\n"
            await asyncio.sleep(0.01)

        # Parse final result
        reasoning, answer = ResponseProcessor.parse_cot_reasoning(full_text)
        history_manager.add_message(session_id, "assistant", answer, reasoning=reasoning)

        done_json = json.dumps({
            "done": True,
            "session_id": session_id,
            "full_text": full_text,
            "reasoning": reasoning,
            "answer": answer
        })
        yield f"data: {done_json}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/sessions")
async def get_sessions():
    return {"sessions": history_manager.list_sessions()}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = history_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")
    return session

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    success = history_manager.delete_session(session_id)
    return {"status": "ok", "deleted": success}

@app.post("/api/sessions/clear")
async def clear_sessions():
    history_manager.clear_all()
    return {"status": "ok"}

@app.post("/api/convert_mathml")
async def convert_mathml(req: MathMLRequest):
    mathml = ResponseProcessor.latex_to_mathml(req.latex)
    return {"latex": req.latex, "mathml": mathml}
