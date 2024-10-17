import os
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import openai
import uvicorn
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import asyncio

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

# Configuración de Azure Speech
speech_key = os.environ["AZURE_SPEECH_KEY"]
service_region = os.environ["AZURE_SPEECH_REGION"]
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "es-ES-AlvaroNeural"  # Puedes cambiar la voz según tus necesidades

# Configurar el formato de salida de audio si lo deseas
# speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)

# Crear un sintetizador de habla (sin especificar audio_config para obtener audio en bytes)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

# Procesador de respuestas en streaming
async def stream_processor(response, websocket: WebSocket):
    accumulated_text = ""
    chunk_size_threshold = 300  # Número mínimo de caracteres antes de sintetizar
    end_of_sentence_punctuation = ('.', '!', '?')

    async for chunk in response:
        if len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta.content:
                text_chunk = delta.content
                accumulated_text += text_chunk
                await websocket.send_text(text_chunk)  # Enviar texto al cliente (opcional)

                # Verificar si se ha acumulado suficiente texto o si se ha llegado al final de una oración
                if len(accumulated_text) >= chunk_size_threshold or any(accumulated_text.endswith(p) for p in end_of_sentence_punctuation):
                    await synthesize_and_send_audio(accumulated_text.strip(), websocket)
                    accumulated_text = ""

    # Sintetizar cualquier texto restante
    if accumulated_text.strip():
        await synthesize_and_send_audio(accumulated_text.strip(), websocket)

async def synthesize_and_send_audio(text, websocket: WebSocket):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: speech_synthesizer.speak_text_async(text).get())

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data  # Esto es bytes
        # Codificar en base64 para enviar como texto
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        # Enviar el audio como un mensaje con un prefijo identificador
        await websocket.send_text(f"__AUDIO__:{audio_base64}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        error_message = f"Speech synthesis canceled: {cancellation_details.reason}"
        if cancellation_details.reason == speechsdk.CancellationReason.Error and cancellation_details.error_details:
            error_message += f" Error details: {cancellation_details.error_details}"
        await websocket.send_text(f"__ERROR__:{error_message}")

# Servir el archivo HTML en la raíz
@app.get("/", response_class=HTMLResponse)
async def get():
    with open("templates/index.html", "r", encoding="utf-8") as f:
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
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
