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

- **Configurar .gitignore**: creamos un `.gitignore` para que git ignore las dependencias del venv. Dentro de `.gitignore` escribimos `venv` y commiteamos.

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

### Resumen requisitos previos:

- Generar entorno virutal `venv` e ignorarlo en `.gitignore`.
- Instalar dependencias de ambos `requirements.txt`.
- Exportación y configuración de la API_KEY `export AI_AGENTIC_API_KEY="xxxxxxxxxxxxxx"`
- Traer la última versión del repo y hacer el checkout a nuestra rama `feature/langchain_workshop_exercise0 `.

## Datos sintéticos

- Dentro del workshop, el proyecto **Hotel Bookings Database** emplea una base PostgreSQL para el booking de hoteles para generar datos sintéticos.

- A nosotros por ahora sólo nos interesa el script `gen_synthetic_hotels.py` para completar una serie de archivos con información sintética de hoteles y bookings a partir unos tmeplates proporcionados por los .yaml del proyecto rollo nombre del hotel, número de habitaciones, ciudad,...

```bash
python3 ./bookings-db/src/gen_synthetic_hotels.py
``` 
- De esta forma se generan los datos sintéticos para los hoteles y los bookings en `bookings-db/output_files/`:
  - **`bookings`**
    - `all_bookings.xlsx`
  - **`hotels`**
    - `hotels.json`
    -  `hotels.xlsx`
    -  `hotels.csv`
    - `all_hotels.csv`
    - `hotel_details.md`
    - `hotel_rooms.md`
    - `hotel_room_queries.csv`

## Core Implementation

Aquí ya indagamos en el funcionaminto del agente `hotel_simple_agent.py` dentro de `ai_agents_hospitality`


