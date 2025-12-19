# WORKSHOP RESOLUTION

# Exercise 1: Hotel Details with RAG

## 📋 Descripción

Implementación de un agente inteligente de consultas hoteleras usando **RAG (Retrieval-Augmented Generation)** con LangChain, ChromaDB y Google Generative AI.

El agente es capaz de:
- ✅ Responder preguntas en lenguaje natural sobre hoteles
- ✅ Buscar información relevante en una base de conocimiento vectorial (50 hoteles)
- ✅ Usar herramientas especializadas para consultas estructuradas (búsqueda, conteo, precios)
- ✅ Generar respuestas precisas y completas en formato Markdown

---

### Componentes principales:

1. **Vector Store (ChromaDB)**
   - 50 hoteles sintéticos de Francia (París, Nice, Cannes)
   - Embeddings generados con Google Generative AI
   - Búsqueda semántica por similitud

2. **Tools (Herramientas especializadas)**
   - `search_hotels_by_city`: Busca hoteles en una ciudad específica
   - `list_all_hotels`: Lista todos los hoteles disponibles
   - `count_rooms`: Cuenta habitaciones con filtros opcionales
   - `get_room_prices`: Obtiene precios de habitaciones

3. **Agente Orquestador**
   - Decide automáticamente cuándo usar tools vs RAG
   - Combina resultados de múltiples fuentes
   - Formatea respuestas en lenguaje natural

4. **RAG Chain**
   - Recupera contexto relevante del vector store (k=20 chunks)
   - Genera respuestas basadas en documentos reales
   - Responde preguntas descriptivas y cualitativas

---

## 🚀 Instalación y Setup

### Requisitos previos

- Python 3.10+
- Google API Key (para Gemini)
- Docker & Docker Compose (opcional, para producción)


- Instalamos las dependencias necesarias para el RAG de langchain y el vector store `chromadb`.

- Generamos los datos sintéticos de 50 hoteles que va a usar el RAG con `gen_synthetic_hotels.py`. Para cambiar a 50 hoteles hay que indagar en la configuración de del bookings hasta `generate_hotels_param.yaml` y hardcodear el 50.

```bash
python3 gen_synthetic_hitels.py
```

- Creamos el script del Rag (`hotel_rag_agent.py`) en `\home\manuelmaturana\hospitality_PoC\ai_agents_hospitality\agents`.

# RAG

## Loader

Para tratar documentos locales primero hay que pasar estos a texto plano usando `loaders`.

```python
def load_hotel_documents()-> List:
    
    documents= []

    json_path= DATA_PATH / "hotels.json"

    json_loader= JSONLoader(file_path=str(json_path), jq_schema= '.Hotels[]', text_content=False)
    json_docs= json_loader.load()
    documents.extend(json_docs)
    
    return documents
```

## Chunking

Tras pasar los datos sintéticos a texto plano legible de tipo `document` dividimos éstos en chunks en pos de un mejor retrieval posterior

```python
def split_documents(documents: List)->List:
        text_splitter= RecursiveCharacterTextSplitter(
        chunk_size= 1000,
        chunk_overlap= 200,
        length_function= len,
        separators=["\n\n", "\n", " ", ""] 
    )

    chunks= text_splitter.split_documents(documents= documents)
    logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
    
    return chunks
```

## VectorStore 
Creamos un vectorstore donde almacena embeddings de los documentos. Si ya existe en disco lo carga desde ahí.
```python
def get_or_create_vectorstore(force_rebuild: bool= False):
    # Si ya está cargado enla memoria que lo devuelva
    if _vectorstore is not None and not force_rebuild:
    # Configurar los embeddings (modelo de google)
    agent_config= get_agent_config()
    embeddings= GoogleGenerativeAIEmbeddings(model= "models/embedding-001", api_key= agent_config.api_key)

    # Si no existe lo creamos de 0

    documents= load_hotel_documents()
    if not documents:
        raise ValueError("No documents loaded. cannot create embeddings")
    
    # 2 Chunkear los documents
    chunks= split_documents(documents)

    # 3 Crear vectorstore con ChromaDB
    _vectorstore= Chroma.from_documents(documents= chunks,
        embedding= embeddings,
        persist_directory= str(VECTOR_STORE_PATH))
 
    return _vectorstore
```

Siguiendo el orden del workshop, a continuación creamos la cadena del RAG usando `langchain`. Luego veremos un paso intermedio entre el vectorstore y la cadena.

## RAG Chain

```python

def create_rag_chain():

    #Usaremos esta función también a la hora de tratar la query así que si ya existe la devolvemos

    if _rag_chain is not None:
        logger.info("Using cached RAG chain")
        return _rag_chain
        
    agent_config= get_agent_config()
    # Creamos el llm instance
    llm= ChatGoogleGenerativeAI(
        model= agent_config.model,
        temperature= agent_config.temperature,
        google_api_key= agent_config.api_key
    )

    # Obetener el vectorstore y crear retriever

    vectorstore= get_or_create_vectorstore()

    # Hacer el prompt

    system_prompt = "PROMPT ESPECÍFICO"

    # Crear la plantilla del prompt

    prompt_template= ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}")
    ])

    # guardar en el cache

    _rag_chain= {"llm": llm, "vectorstore": vectorstore, "prompt": prompt_template}
    logger.info("RAG chain created succesfully")
    return _rag_chain
```

También gestionamos después la función para gestionar la query.

```python
sync def handle_hotel_query_rag(query: str)-> str:
    try:
        # 1 Obtener la cadena de RAG
        rag_chain= create_rag_chain()
        llm= rag_chain.get("llm")
        vectorstore = rag_chain.get("vectorstore")
        prompt_template= rag_chain.get("prompt")

        # 2 Recuperar los documentos más relevantes para el contexto
        logger.info(f"Processing query: {query}")
        relevant_docs= vectorstore.similarity_search(query, k=5)
        logger.info(f"Found {len(relevant_docs)} relevant documents")

        # 3 Construir el contexto

        context= "\n\n".join([doc.page_content for doc in relevant_docs])

        # 4 Crear prompt con contexto

        messages= prompt_template.format_messages(
            context= context, 
            question= query
            )
        
        # 5 Respuesta
        
        response= llm.invoke(messages)

        logger.info("Response generated successfully")
        return response.content
```


## 🛠️ Herramientas (Tools) del Agente RAG - Exercise 1

### 📋 Resumen Ejecutivo

Durante la implementación del Exercise 1, creamos **4 herramientas especializadas** para complementar el sistema RAG. Estas tools permiten al agente realizar consultas estructuradas sobre datos exactos que requieren filtrado, conteo o agregación, tareas donde el RAG puro (búsqueda semántica) no es óptimo.

---



El **RAG puro** tiene limitaciones:

1. **No es determinístico para datos exactos**
   - Pregunta: "¿Cuántas habitaciones hay en París?"
   - RAG: Recupera chunks aleatorios → Puede contar mal o perder información

2. **Limitación de chunks (k=20)**
   - Con 50 hoteles, 20 chunks no cubren todos los datos
   - Respuestas incompletas: "Aquí hay 15 hoteles..." (cuando hay 20 en París)

3. **Mal para operaciones de agregación**
   - Contar, sumar, filtrar → requiere procesar TODOS los datos
   - RAG solo ve una "muestra" de documentos

4. **Ineficiente para consultas estructuradas**
   - "Lista todos los hoteles en Nice"
   - RAG: Busca semánticamente → lento, puede fallar
   - Tool: Filtra JSON directamente → rápido, 100% preciso

## 🔧 Las 4 Herramientas Implementadas

### 1. `search_hotels_by_city(city: str)`

**Propósito:** Buscar hoteles en una ciudad específica.

**Cuándo se usa:** 
- "Hoteles en París"
- "Lista hoteles en Nice"
- "Qué hoteles hay en Cannes"

**Por qué es necesaria:**
- Filtrado exacto por ciudad (no confusión semántica)
- Acceso directo al JSON → 100% precisión
- Más rápido que búsqueda semántica

**Ejemplo:**
```python
# Input: "Hoteles en París"
search_hotels_by_city(city="Paris")

# Output: 
## Hotels in Paris

**Grand Victoria**
- Address: 123 Rue de Paris
- Zip Code: 75001

**Obsidian Tower**
- Address: 456 Avenue des Champs
- Zip Code: 75002

Total: 17 hotels
``` 

### 2. `list_all_hotels()`

**Propósito**: Listar todos los hoteles del sistema.

**Por qué es necesaria**:
 - RAG con chunks limitados--> no puede recuperar todos los hoteles
 - Esta tool garantiza el conocimiento de los 50 hoteles
 - Agrupa por ciudad para mejor legibilidad

 **Ejemplo**:
 ```python
 # Input: "Lista todos los hoteles en Francia"
list_all_hotels()

# Output:
## All Hotels in France

**Total: 50 hotels across 3 cities**

### Paris (17 hotels)
- **Grand Victoria**
- **Obsidian Tower**
- ...

### Nice (16 hotels)
- **Savoy London**
- ...

### Cannes (17 hotels)
- **Ritz Paris**
- ...
``` 

### 3. `count_rooms(city, hotel_name, room_type)`

**Propósito**:  Contar habitaciones con filtros opcionales.

**Cuándo se usa**:
- "¿Cuántas habitaciones hay en París?"
- "Número de habitaciones dobles"
- "Cuántas habitaciones tiene el Grand Victoria"

**Por qué es necesaria**:
 - Operación de agregación → RAG no es confiable
 - Necesita procesar TODOS los datos, no solo k chunks
 - Filtros combinables (ciudad + tipo + hotel)

 **Ejemplo**:
 ```python
 # Input: "¿Cuántas habitaciones dobles hay en París?"
count_rooms(city="Paris", room_type="Double")

# Output:
## Room Count

**Total rooms in Paris type: Double:** 234
**Hotels found:** 17
``` 

### 4. `get_room_prices(city, room_type, category)`

**Propósito**:  Obtener precios de habitaciones con filtros.

**Cuándo se usa**:
- "Precios de habitaciones en París"
- "¿Cuánto cuestan las habitaciones dobles?"
- "Precios de habitaciones Premium en Cannes"

**Por qué es necesaria**:
 - Consultas de precios requieren datos estructurados exactos
 - Distinguir: temporada alta vs baja, Standard vs Premium
 - RAG podría mezclar precios de diferentes hoteles

 **Ejemplo**:
 ```python
# Input: "Precios de habitaciones dobles en Cannes"
get_room_prices(city="Cannes", room_type="Double")

# Output:
## Room Prices

**Filters:** City: Cannes, Type: Double

### Ritz Paris
- **Standard Double** (Guests: 2)
  - Off Season: €120.00/night
  - Peak Season: €180.00/night

- **Premium Double** (Guests: 2)
  - Off Season: €200.00/night
  - Peak Season: €350.00/night

**Total rooms found:** 45
``` 
