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
        


    

