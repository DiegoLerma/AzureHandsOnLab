import os
import base64
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import openai
import uvicorn
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar la aplicación FastAPI
app = FastAPI()

# Autenticación y configuración de Azure OpenAI
endpoint = os.environ["AZURE_OPEN_AI_ENDPOINT"]  # Endpoint de Azure OpenAI
api_key = os.environ["AZURE_OPEN_AI_API_KEY"]    # Clave de API de Azure OpenAI

# Crear cliente asíncrono para Azure OpenAI
client = openai.AsyncAzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2023-09-01-preview"
)

# Configuración del modelo de Azure OpenAI
deployment = os.environ["AZURE_OPEN_AI_DEPLOYMENT_MODEL"]  # Nombre del despliegue del modelo
temperature = 0.8  # Controla la aleatoriedad en la generación de texto

# Configuración de Azure Speech
speech_key = os.environ["AZURE_SPEECH_KEY"]       # Clave de Azure Speech
service_region = os.environ["AZURE_SPEECH_REGION"]  # Región del servicio de Azure Speech
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "es-ES-AlvaroNeural"  # Voz para la síntesis de habla

# Crear sintetizador de voz sin especificar audio_config para obtener audio en bytes
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

async def synthesize_and_send_audio(text, websocket: WebSocket):
    """
    Sintetiza texto en audio y lo envía al cliente a través del WebSocket.

    Args:
        text (str): El texto a sintetizar.
        websocket (WebSocket): Conexión WebSocket con el cliente.
    """
    loop = asyncio.get_event_loop()
    # Ejecutar la síntesis de voz de forma asíncrona
    result = await loop.run_in_executor(None, lambda: speech_synthesizer.speak_text_async(text).get())

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data  # Datos de audio en bytes
        # Codificar audio en base64 para enviar como texto
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        # Enviar el audio al cliente con un prefijo identificador
        await websocket.send_text(f"__AUDIO__:{audio_base64}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        # Manejar errores en la síntesis de voz
        cancellation_details = result.cancellation_details
        error_message = f"Speech synthesis canceled: {cancellation_details.reason}"
        if cancellation_details.reason == speechsdk.CancellationReason.Error and cancellation_details.error_details:
            error_message += f" Error details: {cancellation_details.error_details}"
        await websocket.send_text(f"__ERROR__:{error_message}")

async def stream_processor(response, websocket: WebSocket):
    """
    Procesa la respuesta de Azure OpenAI en streaming y coordina la síntesis y envío de audio.

    Args:
        response: Respuesta en streaming de Azure OpenAI.
        websocket (WebSocket): Conexión WebSocket con el cliente.
    """
    accumulated_text = ""  # Texto acumulado para síntesis
    chunk_size_threshold = 300  # Umbral de caracteres antes de sintetizar
    end_of_sentence_punctuation = ('.', '!', '?')  # Puntuación que indica fin de oración

    async for chunk in response:
        if len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta.content:
                text_chunk = delta.content  # Fragmento de texto recibido
                accumulated_text += text_chunk
                await websocket.send_text(text_chunk)  # Enviar texto al cliente

                # Verificar si se debe sintetizar el texto acumulado
                if len(accumulated_text) >= chunk_size_threshold or any(accumulated_text.endswith(p) for p in end_of_sentence_punctuation):
                    # Sintetizar y enviar el audio del texto acumulado
                    await synthesize_and_send_audio(accumulated_text.strip(), websocket)
                    accumulated_text = ""  # Reiniciar texto acumulado

    # Sintetizar cualquier texto restante al finalizar
    if accumulated_text.strip():
        await synthesize_and_send_audio(accumulated_text.strip(), websocket)

# Ruta para servir el archivo HTML de la interfaz de usuario
@app.get("/", response_class=HTMLResponse)
async def get():
    """
    Sirve el archivo HTML de la interfaz de usuario.

    Returns:
        HTMLResponse: Contenido del archivo index.html.
    """
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Endpoint WebSocket para comunicación en tiempo real con el cliente
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Maneja la comunicación en tiempo real con el cliente a través de WebSockets.

    Args:
        websocket (WebSocket): Conexión WebSocket con el cliente.
    """
    await websocket.accept()
    try:
        while True:
            # Esperar a recibir un mensaje del cliente (tema de la historia)
            data = await websocket.receive_text()
            # Mensajes para el modelo de Azure OpenAI
            messages = [
                {"role": "system", "content": "Eres un contador de historias de terror experto."},
                {"role": "user", "content": data}
            ]
            # Solicitar una respuesta en streaming al modelo
            azure_open_ai_response = await client.chat.completions.create(
                model=deployment,
                temperature=temperature,
                messages=messages,
                stream=True
            )
            # Procesar y enviar la respuesta al cliente
            await stream_processor(azure_open_ai_response, websocket)
    except WebSocketDisconnect:
        print("Cliente desconectado")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

if __name__ == "__main__":
    # Iniciar el servidor Uvicorn para ejecutar la aplicación
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
