# AzureHandsOnLab

¡Bienvenido al **Azure Hands-On Lab**! Este proyecto tiene como objetivo mostrar cómo integrar servicios de **Azure OpenAI** y **Azure AI Services** en una aplicación interactiva. Además, aprenderás a implementar este proyecto fácilmente utilizando **GitHub Codespaces** para que no tengas que instalar nada en tu máquina local.

## Estructura del Proyecto

```plaintext
AzureHandsOnLab/
├── images/                  # Imágenes utilizadas en la aplicación
├── templates/index.html     # Plantillas HTML (interfaz de usuario)
├── .env                     # Variables de entorno (tú crearás este archivo)
├── .env.example             # Usarás esta plantilla para crear tu propio .env
├── .gitignore               # Archivos ignorados por Git
├── main.py                  # Backend usando FastAPI y Azure servicios
├── output.wav               # Archivo de voz sintética generado por IA
├── README.md                # Documentación del proyecto (este archivo)
└── requirements.txt         # Cosas que requieres instalar para que todo funcione
```

---

## Pre-requisitos

Antes de ejecutar la aplicación, asegúrate de tener:

1. **Cuenta de Azure**: [Regístrate aquí](https://azure.microsoft.com/free/) si aún no tienes una.
2. **Acceso a GitHub** para clonar el proyecto e implementarlo en Codespaces.
3. **GitHub Codespaces** habilitado en tu cuenta.

---

## Creación de Recursos en Azure

### Paso 1: Crear un Grupo de Recursos
Un **Grupo de Recursos** en Azure es una colección lógica de recursos que se gestionan juntos.

1. Inicia sesión en [Azure Portal](https://portal.azure.com/).
2. En el menú de la izquierda, selecciona **Grupos de Recursos**.
3. Haz clic en **Crear**.
4. Provee un nombre al grupo, selecciona tu suscripción y una región.
5. Haz clic en **Revisar + Crear** y luego en **Crear**.

---

### Paso 2: Crear un Recurso de Azure OpenAI

1. En Azure Portal, busca **Azure OpenAI** en la barra de búsqueda.
2. Haz clic en **Crear**.
3. Selecciona el **Grupo de Recursos** que creaste en el paso anterior.
4. Asigna un nombre al recurso y selecciona la **Región** más cercana.
5. En la pestaña de **Autenticación**, habilita la autenticación basada en API.
6. Haz clic en **Revisar + Crear** y luego en **Crear**.
7. Una vez creado el recurso, ve a **Claves y Puntos de conexión** y copia:
   - **Punto de conexión** (endpoint)
   - **Clave API**

---

### Paso 3: Crear un Recurso de AI Services (Speech Service)

1. En Azure Portal, busca **Cognitive Services** en la barra de búsqueda.
2. Haz clic en **Crear**.
3. Selecciona **Speech** como el tipo de recurso.
4. Asigna un nombre al recurso y selecciona la **Región** que usaste para OpenAI.
5. Selecciona el mismo **Grupo de Recursos** que usaste antes.
6. Haz clic en **Revisar + Crear** y luego en **Crear**.
7. Ve a **Claves y Puntos de conexión** y copia:
   - **Clave API de Speech**
   - **Región de Servicio**

---

## Configuración del Proyecto

### Paso 1: Clonar el Repositorio

En GitHub, clona el siguiente repositorio a tu espacio de trabajo en Codespaces:

```bash
git clone https://github.com/DiegoLerma/AzureHandsOnLab.git
```

### Paso 2: Configurar las Variables de Entorno

1. Renombra el archivo `.env.example` a `.env`:

```bash
mv .env.example .env
```

2. Abre el archivo `.env` y agrega las claves y endpoints que obtuviste de los servicios de Azure:

```plaintext
AZURE_OPEN_AI_ENDPOINT=<tu-endpoint-openai>
AZURE_OPEN_AI_API_KEY=<tu-api-key-openai>
AZURE_OPEN_AI_DEPLOYMENT_MODEL=<nombre-del-modelo-desplegado>
AZURE_SPEECH_KEY=<tu-api-key-speech>
AZURE_SPEECH_REGION=<tu-region-speech>
```

### Paso 3: Instalar Dependencias

Abre el terminal en Codespaces y ejecuta:

```bash
pip install -r requirements.txt
```

---

## Ejecución de la Aplicación

1. Inicia la aplicación desde Codespaces:

```bash
python main.py
```

2. Abre la aplicación en tu navegador accediendo a:

```
http://127.0.0.1:8000/
```

---

## ¿Cómo Funciona la Aplicación?

- **Interfaz HTML**: Permite ingresar un tema para generar una historia de terror.
- **Backend con FastAPI**: Se conecta a Azure OpenAI para generar texto basado en el tema ingresado.
- **Azure Speech**: Convierte la historia generada en audio y lo envía al cliente para ser reproducido.

---

## Conclusión

Este laboratorio práctico fue creado por Diego Lerma y te permite experimentar con servicios avanzados de Azure como OpenAI y AI Services. Al integrar estos servicios en una aplicación interactiva, puedes explorar cómo la inteligencia artificial se aplica a escenarios creativos y prácticos. Con **GitHub Codespaces**, puedes compartir y colaborar fácilmente sin necesidad de configuraciones complejas en tu máquina local.

Si tienes alguna duda o problema, no dudes en crear un **Issue** en el repositorio o contactarme.

---

¡Diviértete creando historias de terror con Azure y GitHub Codespaces!

