"""
Agente Orquestrador---> Decide entre RAG Agent de hoteles y SQL Agent de bookings 
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from config.agent_config import get_agent_config
from util.logger_config import logger

# Importamos los agentes
from agents.hotel_rag_agent import invoke_agent_with_tools
from agents.hotel_sql_agent import invoke_sql_agent

def classify_query(query: str)-> str:
    """
    Clasifica la consulta para determinar qué agente usar.

      - input: query del usuario
      - output: str 'rag' para hoteles/habitaciones o 'sql' para bookings
    """

    agent_config= get_agent_config()

    # Usamos el LLM
    llm= ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", 
        temperature=0, 
        google_api_key=agent_config.api_key
    )

    system_prompt= """Eres un clasificador de consultas para un sistema hotelero.

Tu trabajo es determinar si la pregunta es sobre:

A) INFORMACIÓN DE HOTELES Y HABITACIONES (usa 'rag'):
- Información sobre hoteles (ubicación, dirección, políticas, descuentos)
- Tipos de habitaciones (Single, Double, Triple)
- Categorías (Standard, Premium)
- Precios de habitaciones (por temporada, por tipo)
- Planes de comidas ofrecidos
- Comparación de precios entre hoteles
- Cualquier pregunta sobre características de hoteles
- Cualquier consulta sobre recomendaciones por zona, precio, plan de ruta, qué hacer por la zona del hotel

B) RESERVAS Y ANALYTICS (usa 'sql'):
- Número de reservas (bookings)
- Ocupación de hoteles
- Ingresos (revenue)
- RevPAR
- Estadísticas de huéspedes
- Tendencias de reservas por fecha
- Comparación de meal plans en reservas
- Análisis de datos de bookings

Responde ÚNICAMENTE con 'rag' o 'sql' sin explicaciones."""
    messages= [ SystemMessage(content=system_prompt), HumanMessage(content=f"Pregunta: {query}")]
    response= llm.invoke(messages)
    classification= response.content.strip().lower()

    # Valia la respuesta
    if classification not in ["rag", "sql"]:
        logger.warning(f"Clasificación inválida '{classification}', usando 'rag' por defecto")
        return "rag"
    
    logger.info(f"Query clasificada como: {classification}")
    return classification

def orchestrate_query(query: str, conversation_history: Optional[list]= None)-> str:
    """
    Orquestra la consulta dirigiéndola al agente apropiado.

      - inputs:
        - query del usuaio
        - histrial de conversación
      - outputs:
        - respuesta del agente que toque
    
    """

    try: 
        logger.info(f"Orquestrando query: {query}")

        # Clasificar la consulta
        agent_type= classify_query(query=query)

        # Ejecutar el agente correspondiente
        if agent_type== 'sql':
            logger.info("Usando SQL Agent (bookings)")
            response= invoke_sql_agent(query=query, conversation_history=conversation_history)
        else:
            logger.info("Usando RAG Agent (hotels)")
            response= invoke_agent_with_tools(query=query, conversation_history=conversation_history)
        
        return response
     
    except Exception as e:
        logger.error(f"Error en orquestador: {str(e)}")
        return f"Lo siento, hubo un error al procesar tu consulta: {str(e)}"
    