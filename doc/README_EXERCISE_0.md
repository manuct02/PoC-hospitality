# Exercise 0 – Simple Agentic Assistant

## Cinfiguraciones previas

- **Ruta del entorno virtual.**
```bash
/home/manuelmaturana/PRJ/hospitality_PoC
```

- **Creación del entorno virtual.**
```bash
python3 -m venv venv
```

- **Instalación de las dependencias**: existen dos `requirements.txt`en diferentes rutas pertinentes antes de afrontar el ejercicio 0. Partimos de `/home/manuelmaturana/PRJ/hospitality_PoC` para instalar lo referente a `langchain`, `langchain-google-genai`...
```bash
pip install -r ./bookings-db/requirements.txt
pip install -r ./ai_agents_hospitality/requirements.txt
```

- Configuramos la API_KEY como variable de entorno dentro del `bashrc.` del WSL para no tener que hardcodearla **(PELIGROSO)**.  En nuestro caso, al ser de GoogleStudio hay que exportar la clave como dicta la configuración del agente (`config_agent.py`). Aquí se identifica la key como `"AI_AGENTIC_API_KEY"`, exportamos esta variable con nuestra key y le reasignamos `"GEMINI_API_KEY"` (si no no la encuentra).

```bash
export AI_AGENTIC_API_KEY="xxxxxxxxxxxxxx"
export GEMINI_API_KEY="$AI_AGENTIC_API_KEY"
```

## Branch

Antes de ponernos  a toquetear nada dentro de visual studio, traemos la versión actualizada del repo y nos situamos en la rama main.

```bash
git fetch -all
```

- **Checkout a la rama del workshop**
```bash
git checkout -b feature/langchain_workshop_exercise0 \
  origin/feature/langchain_workshop_exercise0
```

donde `feature/langchain_workshop_exercise0` es la rama que creo yo y dónde se desarrollarán todos los commits del ejercicio 0 (este `.md` y poco más) y `origin/feature/langchain_workshop_exercise0` es la del repo de David con `origin` delante para decirle al git que me la traiga del repo original.