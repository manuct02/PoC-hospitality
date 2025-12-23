"""
SQL Agent para consultas analíticas de bookings
Ejercicio 2: Agente SQL que consulta PostgreSQL para obtener estadísticas de reservas
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from typing import Optional
from datetime import time, datetime, timedelta

from sqlalchemy import create_engine, text
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from config.agent_config import get_agent_config

from util.logger_config import logger

# Configuración de la base de datos
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "bookings_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}
agent_config= get_agent_config()
# Cache global para la conexión

_db_engine= None

def get_database_engine():
    """ Obtiene o crea el engine de SQLAlchemy """
    global _db_engine

    if _db_engine is None:
        connection_string= (f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        logger.info(f"Conectando a PostgreSQL en {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        _db_engine = create_engine(connection_string)
        logger.info("Conexión a PostgreSQL establecida")
    
    return _db_engine

def execute_sql_query(query: str) -> str:

    """
    Ejecuta una query SQL y devuelve los resultados formateados

      - input: query SQL a ejecutar
      - output: resultados formateados como texto
    """

    try:
        engine= get_database_engine()
        with engine.connect() as conn:
            result= conn.execute(text(query))
            rows= result.fetchall()

            if not rows:
                return "No se encontraron resultados"
            
            # Formatear resultados

            if len(rows)==1 and len(rows[0])==1:
                # Un slo valor
                return str(rows[0][0])
            
            else: 
                # Múltiples filas/columnas
                return "\n".join([str(dict(row._mapping)) for row in rows[:50]])
    
    except Exception as e:
        logger.error(f"Error ejecutando SQL: {str(e)}")
        return f"Error: {str(e)}"

@tool
def query_bookings_database(sql_query: str)-> str:
    """
    Ejecuta una consulta SQL en la base de datos de bookings
      - input: Query de SQL válida
      - output: resultados de la query
    """
    # Validación básica de seguridad

    sql_lower= sql_query.lower().strip()
    if not sql_lower.startswith("select"):
        return "Error: Sólo se permiten queries SELECT"
    
    if any(keyword in sql_lower for keyword in ["drop", "delete", "insert", "update", "alter"]): 
        return "Error: Sólo se permiten queries SELECT de lectura"
    
    return execute_sql_query(sql_query)

@tool
def get_bookings_schema() -> str:
    """
    Obtiene el esquema completo de la tabla bookings.
    
    Returns:
        str: Descripción del esquema
    """
    return """
Tabla: bookings

Columnas:
1. hotel_name (VARCHAR) - Nombre del hotel
2. room_id (VARCHAR) - ID único de la habitación  
3. room_type (VARCHAR) - Tipo: 'Single', 'Double', 'Triple'
4. room_category (VARCHAR) - Categoría: 'Standard', 'Premium'
5. check_in_date (DATE) - Fecha de entrada
6. check_out_date (DATE) - Fecha de salida
7. guest_name (VARCHAR) - Nombre del huésped
8. guest_email (VARCHAR) - Email del huésped
9. guest_phone (VARCHAR) - Teléfono
10. guest_address (VARCHAR) - Dirección
11. number_of_guests (INTEGER) - Número de huéspedes
12. special_requests (TEXT) - Peticiones especiales
13. meal_plan (VARCHAR) - Plan: 'Room Only', 'Bed & Breakfast', 'Half Board', 'Full Board'
14. total_price (DECIMAL) - Precio total en euros
15. city (VARCHAR) - Ciudad del hotel
16. total_nights (INTEGER) - Noches (check_out - check_in)

Ejemplos de queries:
- SELECT COUNT(*) FROM bookings
- SELECT hotel_name, COUNT(*) FROM bookings GROUP BY hotel_name
- SELECT city, SUM(total_price) FROM bookings GROUP BY city
"""

def create_sql_agent():
    """Crea el agente SQL con bind_tools"""
    
    llm= ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", 
        temperature=0, 
        google_api_key=agent_config.api_key
    )

    # Vincular las herramientas
    tools= [query_bookings_database, get_bookings_schema]
    llm_with_tools= llm.bind_tools(tools=tools)

    return llm_with_tools, tools

def invoke_sql_agent(query: str, conversation_history: Optional[list]= None)-> str:
    """
    Procesa las consultas sobre nookings usando el SQL agent.
      - inputs: 
        - query del usuario
        - historial de la coversación
      
      - outputs: respuesta en lenguaje natural
    """

    try:
        logger.info(f"Procesando consulta SQL: {query}")
        llm_with_tools, tools= create_sql_agent()

        # Construir mensajes
        system_prompt= """Eres un experto analista de datos de reservas hoteleras.

IMPORTANTE - Columnas disponibles en la tabla 'bookings':
- hotel_name (NO hotel_id - usa DISTINCT hotel_name para contar hoteles)
- room_id
- room_type ('Single', 'Double', 'Triple')
- room_category ('Standard', 'Premium')
- check_in_date, check_out_date (tipo DATE)
- guest_first_name, guest_last_name, guest_email, guest_phone
- guest_country, guest_city, guest_address, guest_zip_code
- meal_plan ('Room Only', 'Bed & Breakfast', 'Half Board', 'Full Board')
- total_price (DECIMAL)
- total_nights (INTEGER)

Tienes acceso a estas herramientas:
1. get_bookings_schema() - Para ver el esquema completo
2. query_bookings_database(sql_query) - Para ejecutar consultas SQL

PROCESO:
1. Analiza la pregunta
2. Genera el SQL correcto usando SOLO las columnas listadas arriba
3. Ejecuta la query con query_bookings_database()
4. Interpreta los resultados y responde en español de forma clara

REGLAS CRÍTICAS:
- NUNCA uses 'hotel_id' (no existe) - usa 'hotel_name'
- Para contar hoteles: SELECT COUNT(DISTINCT hotel_name) FROM bookings
- Solo queries SELECT
- Usa valores exactos de las columnas categóricas
- Responde SIEMPRE en español de forma natural y amigable
- Incluye números concretos en tus respuestas"""
      
        messages= [SystemMessage(content= system_prompt)]
        
        # Agregar historial
        if conversation_history:
            for role, msg in conversation_history[-4:]:
                if role== "user":
                    messages.append(HumanMessage(content=msg))
                else:
                    messages.append(AIMessage(content=msg))
        
        # Agregar pregunta actual
        messages.append(HumanMessage(content=query))

        # Invocar LLM
        response= llm_with_tools.invoke(messages)

        # Si hay tool_calls, ejecutarlos:
        if response.tool_calls:
            logger.info(f"Ejecutando {len(response.tool_calls)} herramientas")

            tool_results= []
            for tool_call in response.tool_calls:
                tool_name= tool_call["name"]
                tool_args= tool_call["args"]

                # Ejecutar la herramienta
                tool_func= next(t for t in tools if t.name==tool_name)
                result= tool_func.invoke(tool_args)
                tool_results.append(f"Resultado de {tool_name}: {result}")
            
            # Reformular con LLM
            reformulation_prompt= f"""
Pregunta original: {query}

Resultados de las herramientas:
{chr(10).join(tool_results)}

Genera una respuesta en lenguaje natural clara y concisa en español."""
            
            agent_config = get_agent_config()
            llm_basic= ChatGoogleGenerativeAI(model= "gemini-2.0-flash-exp", temperature= 0, google_api_key= agent_config.api_key )

            final_response= llm_basic.invoke([HumanMessage(content=reformulation_prompt)])
            return final_response.content
        
        else:
            return response.content
    
    except Exception as e:
        logger.error(f"Error en SQL agent: {str(e)}")
        return f"Lo siento, hubo un error: {str(e)}"
    
def test_connection():
    """ Prueba la conexión a PostgreSQL """

    try:
        engine = get_database_engine()
        with engine.connect() as conn:
            result= conn.execute(text("SELECT COUNT(*) FROM bookings"))
            count= result.fetchone()[0]
            logger.info(f"Conexión OK. Total bookings: {count}")
            return True
    
    except Exception as e:
        logger.error(f"Error de conexión: {str(e)}")
        return False

if __name__== "__main__":
    print("🔍 Probando SQL Agent...")

    if test_connection():
        print("✅ Conexión a PostgreSQL OK\n")

        test_queries = ["¿Cuántas reservas hay?",
                        "¿Cuál es el hotel con más reservas?",
                        "¿Cuántas reservas hay en enero de 2025?",
                        "¿Cuál es el revenue total por hotel?"]
        
        for q in test_queries:
            print(f"📊 {q}")
            resp= invoke_sql_agent(q)
            print(f"💬 {resp}\n")
    else:
        print("❌ Error de conexión")
