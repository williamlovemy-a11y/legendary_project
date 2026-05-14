from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../"), name = "static")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma3:4b"

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")
    history = data.get("history", [])
    
    message = history + [{"role": "user", "content": "user_message"}]

    async def generate():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                OLLAMA_URL,
                JSON={"model": MODEL_NAME, "message": messages, "stream": True},
                timeout = 60.0
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield line + "\n"

    return StreamingResponse(generate(), media_type = "test/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)