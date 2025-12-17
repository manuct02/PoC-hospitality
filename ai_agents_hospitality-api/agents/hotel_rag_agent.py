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

from util.configuration import PROJECT_ROOT
from util.logger_config import logger
from config.agent_config import get_agent_config

'''Las rutas de los datos y el almacén de vectores'''
DATA_PATH = PROJECT_ROOT.parent / "bookings-db" / "output_files" / "hotels"
VECTOR_STORE_PATH = PROJECT_ROOT / "vector_store"

_rag_chain= None
_vectorstore= None

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

def get_or_create_vectorstore(force_rebuild: bool= False):
    '''
    Docstring for get_or_create_vectorstore
    
    :param force_rebuild: Description
    :type force_rebuild: bool
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

'''============== AGENTE RIBUSTO ================='''

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
            name= hotel.get('Name', 'Unknown')
            address= hotel.get('Address', {})
            result += f"**{name}**\n"
            result += f"- Address: {address.get('Address', 'N/A')}\n"
            result += f"- Zip Code: {address.get('ZipCode', 'N/A')}\n\n"
        
        result += f"Total: {len(city_hotels)} hotels"
        return result
        
    except Exception as e:
        return f"Error searching hotels: {str(e)}"
















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

        


    

