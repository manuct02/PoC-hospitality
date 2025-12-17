# AI Hospitality API - Workshop Starter

Este es un proyecto de inicio para un workshop de LangChain. Implementa un microservicio FastAPI con WebSocket que responde con datos hardcodeados sobre hoteles.

## 🎯 Objetivo del Workshop

Este proyecto es un punto de partida para aprender a implementar agentes de IA con LangChain. Actualmente, el sistema responde con respuestas predefinidas. Tu objetivo es:

1. Reemplazar las respuestas hardcodeadas con agentes de LangChain reales
2. Implementar herramientas y ejecutores personalizados
3. Conectar con bases de datos y APIs externas
4. Crear un sistema inteligente de hospitalidad

## 📋 Características Actuales

- **WebSocket Interface**: Comunicación en tiempo real con el cliente
- **Respuestas Predefinidas**: Responde a 8 consultas diferentes sobre hoteles
- **Interfaz Web**: Chat UI limpio y moderno
- **Sistema de Logging**: Seguimiento de operaciones

## 🛠️ Requisitos

- Python 3.12+
- FastAPI
- Uvicorn
- WebSockets
- Jinja2

## 📦 Instalación

1. **Crear y activar un entorno virtual:**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Uso

1. **Iniciar el servidor:**
   ```bash
   python main.py
   ```

   O con variables de entorno personalizadas:
   ```bash
   ENVIRONMENT=development python main.py
   ```

2. **Acceder a la interfaz web:**
   ```
   http://localhost:8001
   ```

3. **Conectar vía WebSocket:**
   ```
   ws://localhost:8001/ws/{uuid}
   ```

## 🗂️ Estructura del Proyecto

```
ai_hospitality-api/
├── util/                     # Módulos de utilidad
│   ├── __init__.py
│   ├── configuration.py      # Configuración de la aplicación
│   └── logger_config.py      # Configuración de logging
├── static/                   # Archivos estáticos
│   ├── acc_logo.png
│   ├── scripts.js           # JavaScript del cliente
│   └── styles.css           # Estilos CSS
├── templates/               # Plantillas HTML
│   └── index.html          # Interfaz principal
├── logs/                    # Directorio de logs
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias Python
├── pyproject.toml         # Configuración del proyecto
└── README.md              # Este archivo
```

## 🧪 Consultas de Prueba

El sistema actualmente responde a las siguientes consultas (hardcodeadas):

### Consultas sobre Configuración de Hoteles:

* list the hotels in France
* tell me the prices for triple premium rooms in Paris
* compare the triple room prices at off season for room and breakfast at the hotels in Nice
* tell me the the lowest price for a standard sigle room in Nice considering no meal plan
* tell me for hotels in Paris the meal charge for half board
* tell me the amount of rooms per type for hotels in Paris
* tell me price of a double room, standard category, in G. Victoria for peak and off season
* tell me the price for a premium triple room for Obsidian Tower next October 14th considering room and breakfast and 4 guests

## ⚙️ Configuración

El proyecto usa Pydantic Settings con variables de entorno. La aplicación carga la configuración desde archivos `.env.{ENVIRONMENT}` basados en la variable de entorno `ENVIRONMENT` (por defecto: `development`).

### Variables de Entorno Opcionales (con valores por defecto)

**Configuración de API:**
- `API_HOST`: Host del servidor (default: "0.0.0.0")
- `API_PORT`: Puerto del servidor (default: 8001)

**Configuración de CORS:**
- `CORS_ORIGINS`: Lista de orígenes CORS permitidos (default: ["*"])

**Contexto de Entorno:**
- `ENVIRONMENT`: Nombre del entorno que determina qué archivo `.env.{ENVIRONMENT}` cargar (default: "development")

## 🐳 Docker

### Construir la imagen

```bash
docker build --no-cache -t ai_hospitality-api .
```

### Ejecutar el contenedor

```bash
docker run -p 8001:8001 \
  -e ENVIRONMENT=development \
  ai_hospitality-api
```

## 📝 Próximos Pasos (Workshop)

1. **Instalar LangChain:**
   ```bash
   pip install langchain langchain-google-genai
   ```

2. **Crear Agentes:**
   - Implementar agentes especializados para diferentes tipos de consultas
   - Crear herramientas personalizadas
   - Configurar ejecutores

3. **Conectar con Datos Reales:**
   - Integrar con bases de datos
   - Implementar APIs de datos de hoteles
   - Agregar capacidades de búsqueda semántica

4. **Mejorar el Sistema:**
   - Agregar manejo de contexto
   - Implementar memoria de conversación
   - Agregar validación de datos

## 📚 Recursos

- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Protocol](https://websockets.readthedocs.io/)

## 🤝 Contribuir

Este es un proyecto de workshop. Siéntete libre de experimentar y mejorar la implementación.

## 📄 Licencia

Este proyecto es parte de un workshop educativo.



