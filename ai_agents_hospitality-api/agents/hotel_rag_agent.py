'''
Ejercicio 1 Workshop: Creación del RAG
'''
import json
import os
from pathlib import Path
from typing import List, Optional
'''Loaders para el texto plano'''
from langchain_community.document_loaders import JSONLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
'''Modelos de embeddings y vector store'''
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
'''Prompt y chains de langchain'''
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

from util.configuration import PROJECT_ROOT
from util.logger_config import logger
from config.agent_config import get_agent_config

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.prompts import PromptTemplate

'''Las rutas de los datos y el almacén de vectores'''
DATA_PATH = PROJECT_ROOT.parent / "bookings-db" / "output_files" / "hotels"
VECTOR_STORE_PATH = PROJECT_ROOT / "vector_store"

_rag_chain= None
_vectorstore= None
_hotels_data_cache = None  


'''========================= LOADER ============================='''



def load_hotel_documents()-> List:
    '''
    - input: json y md con los datos de 50 hoteles sintéticos
    - output: lista de objetos 'Document' de texto plano
    '''
    documents= []

    json_path= DATA_PATH / "hotels.json"

    if json_path.exists():
        logger.info(f"Loading JSON data from {json_path}")
        json_loader= JSONLoader(file_path=str(json_path), jq_schema= '.Hotels[]', text_content=False)
        json_docs= json_loader.load()
        logger.info(f"Loaded {len(json_docs)} documents from JSON")
        documents.extend(json_docs)
    else:
        logger.warning(f"JSON file not found: {json_path}")
    
    details_path = DATA_PATH / "hotel_details.md"
    if details_path.exists():
        logger.info(f"Loading hotel details from {details_path}")
        details_loader = TextLoader(str(details_path), encoding='utf-8')
        details_docs = details_loader.load()
        logger.info(f"Loaded {len(details_docs)} documents from hotel_details.md")
        documents.extend(details_docs)
    else:
        logger.warning(f"Hotel details file not found: {details_path}")
    
    rooms_path = DATA_PATH / "hotel_rooms.md"
    if rooms_path.exists():
        logger.info(f"Loading hotel rooms from {rooms_path}")
        rooms_loader = TextLoader(str(rooms_path), encoding='utf-8')
        rooms_docs = rooms_loader.load()
        logger.info(f"Loaded {len(rooms_docs)} documents from hotel_rooms.md")
        documents.extend(rooms_docs)
    else:
        logger.warning(f"Hotel rooms file not found: {rooms_path}")
    
    logger.info(f"Total documents loaded: {len(documents)}")
    return documents



''' ====================================== CHUNKING =========================================='''


def split_documents(documents: List)->List:
    '''
    Splitear los documents en chunks de menor tamaño

      - input: lista de documents
      - output: lista de documents chunkeados
    '''
    text_splitter= RecursiveCharacterTextSplitter(
        chunk_size= 1000,
        chunk_overlap= 200,
        length_function= len,
        separators=["\n\n", "\n", " ", ""] 
    )

    chunks= text_splitter.split_documents(documents= documents)
    logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
    
    return chunks




''' ======================= CHROMADB EMBEDDINGS/VECTORSTORE ================================='''




def get_or_create_vectorstore(force_rebuild: bool= False):
    '''
    Creamos un vectorstore donde almacena embeddings de los documentos
    Si ya existe en disco lo carga desde ahí
    '''

    global _vectorstore

    # Si ya está cargado enla memoria que lo devuelva
    if _vectorstore is not None and not force_rebuild:
        logger.info("Using cached vectorstore from memory")
        return _vectorstore
    
    # Configurar los embeddings (modelo de google)
    agent_config= get_agent_config()
    embeddings= GoogleGenerativeAIEmbeddings(model= "models/embedding-001", api_key= agent_config.api_key)

    # Si está en el disco los cargamos desde ahí para no estar rebuildeando el modelo

    if VECTOR_STORE_PATH.exists() and not force_rebuild:
        logger.info(f"Loading existing vectorstore from {VECTOR_STORE_PATH}")
        _vectorstore = Chroma(
            persist_directory=str(VECTOR_STORE_PATH),
            embedding_function=embeddings
        )
        logger.info("Vectorstore loaded successfully from disk")
        return _vectorstore
    
    # Si no existe lo creamos de 0

    logger.info("Creating new vector store...")

    # 1 Carga de documentos

    documents= load_hotel_documents()
    if not documents:
        raise ValueError("No documents loaded. cannot create embeddings")
    
    # 2 Chunkear los documents
    chunks= split_documents(documents)
    logger.info(f"Processing {len(chunks)} chunks for embedding...")

    # 3 Crear vectorstore con ChromaDB
    _vectorstore= Chroma.from_documents(documents= chunks,
        embedding= embeddings,
        persist_directory= str(VECTOR_STORE_PATH))
    
    logger.info(f"Vectorstore created and persisted to {VECTOR_STORE_PATH}")
    return _vectorstore



'''================================= HERRAMIENTAS ============================='''



def load_hotels_data():
    '''
    carga los datos de hoteles dentro del JSON
    Devuelve un diccionario con los datos de los hoteles {'Hotels': [...]}
    '''

    global _hotels_data_cache
    if '_hotels_data_cache' not in globals() or _hotels_data_cache is None:
        json_path = DATA_PATH / "hotels.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            _hotels_data_cache = json.load(f)
    
    return _hotels_data_cache

@tool
def search_hotels_by_city(city: str)->str:
    '''
    Busca hoteles de una ciudad específica, el agente debe usar esta herramienta
    cuando se le prgunte por hoteles en ciudades particulares
      - input: el nombre de una ciudad 'str'
      - output: información formateada sobre los hoteles en la ciudad
    '''

    try:
        data= load_hotels_data()
        hotels= data.get('Hotels', [])

        city_hotels= [
            h for h in hotels
            if h.get('Address', {}).get('City', '').lower() == city.lower()
        ]

        if not city_hotels:
            available_cities = set(h.get('Address', {}).get('City', '') for h in hotels)
            return f"No hotels found in {city}. Available cities: {', '.join(sorted(available_cities))}"
   
        # Formatear la respuesta
        result= f"## Hotels in {city}\n\n"
        for hotel in city_hotels:
            name= hotel.get('Name', '')
            address= hotel.get('Address', {})
            result += f"**{name}**\n"
            result += f"- Address: {address.get('Address', 'N/A')}\n"
            result += f"- Zip Code: {address.get('ZipCode', 'N/A')}\n\n"
        
        result += f"Total: {len(city_hotels)} hotels"
        return result
        
    except Exception as e:
        return f"Error searching hotels: {str(e)}"


@tool
def list_all_hotels() -> str:
    '''
    Lista TODOS los hoteles disponibles en el sistema, agrupados por ciudad.
    Usa esta herramienta cuando el usuario pregunte por "todos los hoteles", 
    "hoteles en Francia", o quiera ver el catálogo completo.
    
    - input: ninguno
    - output: información formateada de todos los hoteles organizados por ciudad
    '''
    
    try:
        data = load_hotels_data()
        hotels = data.get('Hotels', [])
        
        if not hotels:
            return "No hotels found in the system."
        
        # Agrupar hoteles por ciudad
        hotels_by_city = {}
        for hotel in hotels:
            city = hotel.get('Address', {}).get('City', 'Unknown')
            if city not in hotels_by_city:
                hotels_by_city[city] = []
            hotels_by_city[city].append(hotel)
        
        # Formatear resultado
        result = f"## All Hotels in France\n\n"
        result += f"**Total: {len(hotels)} hotels across {len(hotels_by_city)} cities**\n\n"
        
        for city in sorted(hotels_by_city.keys()):
            city_hotels = hotels_by_city[city]
            result += f"### {city} ({len(city_hotels)} hotels)\n\n"
            
            for hotel in city_hotels:
                name = hotel.get('Name', 'Unknown')
                address = hotel.get('Address', {})
                result += f"- **{name}**\n"
                result += f"  - Address: {address.get('Address', 'N/A')}\n"
                result += f"  - Zip Code: {address.get('ZipCode', 'N/A')}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error listing all hotels: {str(e)}"


@tool
def count_rooms(city: str = None, hotel_name: str = None, room_type: str = None) -> str:
    """
    Cuenta las habitaciones del hotel aplicando según qué filtros
    
    Args:
        city: filtrar por el nombre de la ciudad (optional)
        hotel_name: filtrar por el nombre del hotel (optional)
        room_type: filtrar por el tipo de habitación: individual, doble, triple... (optional)
        
    Returns:
        Total de habitaciones para los filtros
    """
    try:
        data = load_hotels_data()
        hotels = data.get('Hotels', [])
        
        total_rooms = 0
        filtered_hotels = []
        
        for hotel in hotels:
            if city and hotel.get('Address', {}).get('City', '').lower() != city.lower():
                continue
            
            if hotel_name and hotel_name.lower() not in hotel.get('Name', '').lower():
                continue
            
            filtered_hotels.append(hotel)
            rooms = hotel.get('Rooms', [])
            
            if room_type:
                rooms = [r for r in rooms if r.get('Type', '').lower() == room_type.lower()]
            
            total_rooms += len(rooms)
        
        filters_desc = []
        if city:
            filters_desc.append(f"in {city}")
        if hotel_name:
            filters_desc.append(f"hotel: {hotel_name}")
        if room_type:
            filters_desc.append(f"type: {room_type}")
        
        filters_text = " ".join(filters_desc) if filters_desc else "all hotels"
        
        result = f"## Room Count\n\n"
        result += f"**Total rooms {filters_text}:** {total_rooms}\n"
        result += f"**Hotels found:** {len(filtered_hotels)}\n"
        
        return result
        
    except Exception as e:
        return f"Error counting rooms: {str(e)}"
    
@tool
def get_room_prices(city: str = None, room_type: str = None, category: str = None) -> str:
    """
    Coger el precio de la habitación con filtros.

    Usar esta herramienta para cuestiones sobre precios y temporadas
    
    Args:
        city: filtrar por ciudad (optional)
        room_type: filtrar por tipo de habitación - "Single", "Double", or "Triple" (optional)
        category: filtrar por categoría - "Standard" or "Premium" (optional)
        
    Returns:
        Precio formateado para las habitaciones filtradas
    """
    try:
        data = load_hotels_data()
        hotels = data.get('Hotels', [])
        
        results = []
        
        for hotel in hotels:
            if city and hotel.get('Address', {}).get('City', '').lower() != city.lower():
                continue
            
            hotel_name = hotel.get('Name', '')
            rooms = hotel.get('Rooms', [])
            
            for room in rooms:
                if room_type and room.get('Type', '').lower() != room_type.lower():
                    continue
                if category and room.get('Category', '').lower() != category.lower():
                    continue
                
                results.append({
                    'hotel': hotel_name,
                    'city': hotel.get('Address', {}).get('City', 'Unknown'),
                    'type': room.get('Type', 'N/A'),
                    'category': room.get('Category', 'N/A'),
                    'guests': room.get('Guests', 'N/A'),
                    'price_off': room.get('PriceOffSeason', 0),
                    'price_peak': room.get('PricePeakSeason', 0)
                })
        
        if not results:
            return "No rooms found matching the criteria."
        
        result = f"## Room Prices\n\n"
        
        filters = []
        if city:
            filters.append(f"City: {city}")
        if room_type:
            filters.append(f"Type: {room_type}")
        if category:
            filters.append(f"Category: {category}")
        
        if filters:
            result += f"**Filters:** {', '.join(filters)}\n\n"
        
        # Agrupar por hotel
        hotels_data = {}
        for r in results:
            hotel_key = r['hotel']
            if hotel_key not in hotels_data:
                hotels_data[hotel_key] = []
            hotels_data[hotel_key].append(r)
        
        for hotel_name, rooms in hotels_data.items():
            result += f"### {hotel_name}\n\n"
            for room in rooms[:5]:
                result += f"- **{room['category']} {room['type']}** (Guests: {room['guests']})\n"
                result += f"  - Off Season: €{room['price_off']:.2f}/night\n"
                result += f"  - Peak Season: €{room['price_peak']:.2f}/night\n\n"
            
            if len(rooms) > 5:
                result += f"  _(... and {len(rooms) - 5} more rooms)_\n\n"
        
        result += f"**Total rooms found:** {len(results)}\n"
        
        return result
        
    except Exception as e:
        return f"Error getting prices: {str(e)}"
    


''' ================================= AGENTE ========================================='''

def create_hotel_agent():
    '''
    Crear el agente de hoteles capaz de llamar a las tools cuando toque
    '''

    # 1 Configuración del LLM

    agent_config= get_agent_config()
    llm= ChatGoogleGenerativeAI(model= agent_config.model, temperature= 0, google_api_key= agent_config.api_key)

    # 2 Definir las tools

    tools= [ search_hotels_by_city, list_all_hotels, count_rooms, get_room_prices]

    # 3 El binding de las tools

    llm_with_tools= llm.bind_tools(tools= tools)

    logger.info("Hotel agent with tools created successfully")
    return llm_with_tools

async def invoke_agent_with_tools(query: str)-> str:
    '''
    El invoke al agente con tools para responder
      
      - input: query del usuario
      - output: respuesta del agente
    '''

    try:
        # obtener el llm con tools
        llm_with_tools= create_hotel_agent()
        # sistema de mansajes
        messages = [
            ("system", """You are a helpful hotel assistant with access to specialized tools and a detailed knowledge base.

Available Tools:
- search_hotels_by_city(city: str): Returns hotels in ONE specific city
- list_all_hotels(): Returns ALL 50 hotels in the system (across all cities in France)
- count_rooms(city, hotel_name, room_type): Counts rooms matching filters  
- get_room_prices(city, room_type, category): Returns room pricing information

CRITICAL RULES - FOLLOW THESE EXACTLY:
1. When user asks about "all hotels", "hotels in France", "list hotels", "show hotels" → ALWAYS call list_all_hotels()
2. When user asks about hotels in a SPECIFIC city (Paris, Nice, Cannes, whatever city you know) → call search_hotels_by_city(city)
3. When user asks "how many rooms" and whatever following that → call count_rooms()
4. When user asks about prices → call get_room_prices()
5. Only skip tools for specific hotel details (amenities, policies, descriptions)

ALL hotels in the system are in France 

Examples - MUST USE TOOLS:
✅ "Hotels in Paris" → search_hotels_by_city(city="Paris")
✅ "List all hotels" → list_all_hotels()
✅ "Hotels in France" → list_all_hotels()
✅ "Show me the hotels" → list_all_hotels()
✅ "How many rooms in Nice?" → count_rooms(city="Nice")
✅ "Room prices in Cannes" → get_room_prices(city="Cannes")

Examples - NO TOOLS:
❌ "Tell me about Grand Victoria" → use knowledge base
❌ "What are meal charges?" → use knowledge base
            """),
            ("user", query)
        ]

        # invocar al llm

        response= llm_with_tools.invoke(messages)

        # si el LLM necesita la tool para responder

        if response.tool_calls:
            # Ejecutar las tools y recopilar resultados
            tool_results= []
            for tool_call in response.tool_calls:
                tool_name= tool_call["name"]
                tool_args= tool_call["args"]
            
                if tool_name == "search_hotels_by_city":
                    result = search_hotels_by_city.invoke(tool_args)
                elif tool_name == "list_all_hotels":
                    result = list_all_hotels.invoke(tool_args)
                elif tool_name == "count_rooms":
                    result = count_rooms.invoke(tool_args)
                elif tool_name == "get_room_prices":
                    result = get_room_prices.invoke(tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"
                
                tool_results.append(f"Tool: {tool_name}\nResult:\n{result}")
            
            # Ahora el LLM toma los resultados de las tools y genera una respuesta natural
            agent_config = get_agent_config()
            llm = ChatGoogleGenerativeAI(model=agent_config.model, temperature=0, google_api_key=agent_config.api_key)
            
            formatting_messages = [
                ("system", """You are a helpful hotel assistant. You have used specialized tools to get information.

Now, take the tool results below and present them to the user in a natural, conversational, and well-formatted way.

IMPORTANT:
- Use natural language, as if speaking to a person
- Format numbers and prices in a human-friendly way (e.g., "€450 per night" not just "450")
- Use Markdown for clarity (headers, lists, tables) but write naturally
- Be complete - include ALL information from the tool results
- If there are multiple hotels/rooms, present ALL of them clearly
- Use the tools whenever you thinl they may help but as a support in order to answer not as output
Tool Results:
{results}""".format(results="\n\n".join(tool_results))),
                ("user", query)
            ]
            
            final_response = llm.invoke(formatting_messages)
            return final_response.content
        else:
            # Si no usa tools, usar RAG para obtener contexto relevante
            logger.info(f"No tool called, using RAG for query: {query}")
            
            # Obtener documentos relevantes del vector store
            vectorstore = get_or_create_vectorstore()
            retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
            relevant_docs = retriever.invoke(query)
            
            # Construir contexto con los documentos recuperados
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Llamar al LLM con el contexto del RAG
            agent_config = get_agent_config()
            llm = ChatGoogleGenerativeAI(model=agent_config.model, temperature=0, google_api_key=agent_config.api_key)
            rag_messages = [
                ("system", """You are a professional hotel assistant with access to detailed hotel information.

INSTRUCTIONS:
1. Use the context below to answer the user's question COMPLETELY and in DETAIL
2. Include ALL relevant information found in the context (addresses, prices, policies, amenities, etc.)
3. Format your response in clear Markdown with headers, lists, and tables when appropriate
4. If the question asks about multiple items, include ALL of them, not just a sample
5. For numerical data (prices, counts), include exact numbers
6. If specific information is NOT in the context, clearly state what's missing
7. You must be able to calculate simple operations

IMPORTANT: Provide COMPLETE answers, not summaries. Don't say "here are some examples" - give ALL the information.

Context from knowledge base:
{context}""".format(context=context)),
                ("user", query)
            ]
            
            rag_response = llm.invoke(rag_messages)
            return rag_response.content
    
    except Exception as e:
        logger.error(f"Error in agent: {e}")
        import traceback
        traceback.print_exc()
        return f"Sorry, error: {str(e)}"




''' =================================== CADENA DEL RAG ==============================='''




def create_rag_chain():

    global _rag_chain

    #si ya existe la devolvemos

    if _rag_chain is not None:
        logger.info("Using cached RAG chain")
        return _rag_chain
    
    agent_config= get_agent_config()

    # Crear el LLm instance

    llm= ChatGoogleGenerativeAI(
        model= agent_config.model,
        temperature= agent_config.temperature,
        google_api_key= agent_config.api_key
    )

    # Obetener el vectorstore y crear retriever

    vectorstore= get_or_create_vectorstore()

    # Hacer el prompt

    system_prompt = """You are a helpful and knowledgeable hotel assistant.
Your job is to answer questions about hotels, rooms, prices, and availability.

Use the following context to answer the user's question accurately and concisely.
If you cannot find the information in the context, politely say so.

Context:
{context}

Important guidelines:
- Be specific with prices, room types, and hotel names
- If comparing hotels, present the information in a clear format
- Always mention the currency (€) for prices
- If asked about availability or bookings, remind that you can only provide information, not make reservations
- ONLY answer based on the context provided. If location is not mentioned, say you don't have that information
"""
    # Crear la plantilla del prompt

    prompt_template= ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{question}")
    ])

    # guardar en el cache

    _rag_chain= {"llm": llm, "vectorstore": vectorstore, "prompt": prompt_template}
    logger.info("RAG chain created succesfully")
    return _rag_chain

async def handle_hotel_query_rag(query: str)-> str:
    '''
    Procesa la consulta usando el RAG

      - input: query del usuario
      - output: respuesta basada en el contexto recuperado
    '''

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

        # 3 Cnstruir el contexto

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
    
    except Exception as e:
        logger.error(f"Error processing RAG query: {e}")
        import traceback
        traceback.print_exc()
        return f"Sorry, I encountered an error: {str(e)}"

        


    

