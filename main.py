import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import openai
import uvicorn
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# Configurar la aplicación FastAPI
app = FastAPI()

# Autenticación de Azure OpenAI
endpoint = os.environ["AZURE_OPEN_AI_ENDPOINT"]
api_key = os.environ["AZURE_OPEN_AI_API_KEY"]

client = openai.AsyncAzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2023-09-01-preview"
)

# Configuración del modelo de Azure OpenAI
deployment = os.environ["AZURE_OPEN_AI_DEPLOYMENT_MODEL"]
temperature = 0.7

# Modelo de entrada
class Prompt(BaseModel):
    input: str

# Procesador de respuestas en streaming
async def stream_processor(response, websocket: WebSocket):
    async for chunk in response:
        if len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta.content:
                await websocket.send_text(delta.content)

# Servir el archivo HTML en la raíz
@app.get("/", response_class=HTMLResponse)
async def get():
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Endpoint de la API para la transmisión usando WebSockets
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            azure_open_ai_response = await client.chat.completions.create(
                model=deployment,
                temperature=temperature,
                messages=[{"role": "user", "content": data}],
                stream=True
            )
            await stream_processor(azure_open_ai_response, websocket)
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
