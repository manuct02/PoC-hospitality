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

COLUMNAS EN BASE DE DATOS SQL (tabla bookings):
id, hotel_name, room_id, room_type, room_category, check_in_date, check_out_date,
guest_first_name, guest_last_name, guest_email, guest_phone, guest_country,
guest_city, guest_address, guest_zip_code, meal_plan, total_price, total_nights

REGLA CRÍTICA: Si la pregunta menciona CUALQUIERA de estas columnas o conceptos → usa 'sql':
- Personas/huéspedes/clientes/nombres (guest_first_name, guest_last_name)
- Email/correo (guest_email)
- Teléfono/phone (guest_phone)
- País/ciudad/dirección/código postal (guest_country, guest_city, guest_address, guest_zip_code)
- Reservas/bookings
- Fechas de check-in/check-out
- Planes de comida RESERVADOS (meal_plan en bookings)
- Precio total/ingresos (total_price)
- Noches (total_nights)
- Ocupación/estadísticas/analytics

A) INFORMACIÓN DE HOTELES (usa 'rag' SOLO si pregunta por):
- Características de hoteles (ubicación, políticas, descuentos)
- Tipos de habitaciones DISPONIBLES (no reservadas)
- Precios de CATÁLOGO (no de reservas concretas)
- Planes de comida OFRECIDOS (no los que se reservaron)
- Recomendaciones por zona

B) RESERVAS Y DATOS (usa 'sql' para TODO lo demás)

Si hay CUALQUIER duda → usa 'sql'

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

async def orchestrate_query(query: str, conversation_history: Optional[list]= None)-> str:
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
            response= await invoke_agent_with_tools(query=query, conversation_history=conversation_history)
        
        return response
     
    except Exception as e:
        logger.error(f"Error en orquestador: {str(e)}")
        return f"Lo siento, hubo un error al procesar tu consulta: {str(e)}"

if __name__=="__main__":
    
    # Test del orquestrador
    print("🎭 Probando Orchestrator...\n")

    test_queries = [
        # Deberían ir a RAG
        ("¿Cuánto cuesta una habitación doble premium en París?", "rag"),
        ("¿Qué hoteles hay en Madrid?", "rag"),
        ("¿Qué meal plans ofrece el hotel Obsidian Tower?", "rag"),
        
        # Deberían ir a SQL
        ("¿Cuántas reservas hay en enero de 2025?", "sql"),
        ("¿Cuál es la ocupación del Obsidian Tower en enero?", "sql"),
        ("¿Cuál es el RevPAR del Royal Sovereign?", "sql"),
    ]

    for query, expected in test_queries:
        print(f"📝 Query: {query}")
        classification= classify_query(query=query)
        status= "✅" if classification==expected else "❌"
        print(f"{status} Clasificado como: {classification} (esperado: {expected})")
    
        # Ejecutamos la query
        print("💬 Respuesta:")
        import asyncio
        response= asyncio.run(orchestrate_query(query=query))
        print(f"{response[:200]}...\n")
        print("="*60 + "\n")
    