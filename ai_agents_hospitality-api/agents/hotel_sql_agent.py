"""
SQL Agent para consultas analíticas de bookings
Ejercicio 2: Agente SQL que consulta PostgreSQL para obtener estadísticas de reservas
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from typing import Optional
import time
from datetime import datetime

from sqlalchemy import create_engine, text
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from config.agent_config import get_agent_config

from util.logger_config import logger

start_time=time.time()

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
      - output: resultados formateados como texto o tabla markdown
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
                # Un solo valor (COUNT, SUM, etc.)
                return str(rows[0][0])
            
            elif len(rows) <= 3:
                # Pocas filas: formato simple (no tabla)
                return "\n".join([str(dict(row._mapping)) for row in rows])
            
            else: 
                # Múltiples filas: tabla markdown
                if not rows:
                    return "No hay datos"
                
                # Obtener nombres de columnas
                columns = list(rows[0]._mapping.keys())
                
                # Crear encabezado de tabla markdown
                header = "| " + " | ".join(columns) + " |"
                separator = "|" + "|".join(["---" for _ in columns]) + "|"
                
                # Crear filas de datos (limitar a 50)
                data_rows = []
                for row in rows[:50]:
                    row_dict = dict(row._mapping)
                    row_values = [str(row_dict[col]) for col in columns]
                    data_rows.append("| " + " | ".join(row_values) + " |")
                
                # Unir todo
                table = "\n".join([header, separator] + data_rows)
                
                # Añadir nota si hay más filas
                if len(rows) > 50:
                    table += f"\n\n*Mostrando 50 de {len(rows)} resultados*"
                
                return table
    
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

@tool
def calculate_occupancy_rate(hotel_name: str, start_date: str, end_date: str) -> str:
    """
    Calcula la tasa de ocupación de un hotel en un período.
    
    Args:
        hotel_name: Nombre del hotel
        start_date: Fecha inicio (formato YYYY-MM-DD)
        end_date: Fecha fin (formato YYYY-MM-DD)
        
    Returns:
        str: Tasa de ocupación en porcentaje
    """
    try:
        engine = get_database_engine()
        with engine.connect() as conn:
            # 1. Contar habitaciones del hotel
            room_count_query = text("""
                SELECT COUNT(DISTINCT room_id) as total_rooms
                FROM bookings
                WHERE hotel_name = :hotel_name
            """)
            room_result = conn.execute(room_count_query, {"hotel_name": hotel_name})
            total_rooms = room_result.fetchone()[0]
            
            if not total_rooms:
                return f"No se encontraron habitaciones para el hotel '{hotel_name}'"
            
            # 2. Calcular noches ocupadas en el período
            occupied_query = text("""
                SELECT COALESCE(SUM(total_nights), 0) as occupied_nights
                FROM bookings
                WHERE hotel_name = :hotel_name
                AND check_in_date >= :start_date
                AND check_in_date < :end_date
            """)
            occupied_result = conn.execute(occupied_query, {
                "hotel_name": hotel_name,
                "start_date": start_date,
                "end_date": end_date
            })
            occupied_nights = occupied_result.fetchone()[0]
            
            # 3. Calcular días en el período
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days_in_period = (end - start).days
            
            # 4. Calcular noches disponibles
            available_nights = total_rooms * days_in_period
            
            # 5. Calcular tasa de ocupación
            if available_nights == 0:
                return "No hay noches disponibles en ese período"
            
            occupancy_rate = (occupied_nights / available_nights) * 100
            
            return f"""Tasa de Ocupación para {hotel_name}:
- Período: {start_date} a {end_date} ({days_in_period} días)
- Habitaciones del hotel: {total_rooms}
- Noches disponibles: {available_nights}
- Noches ocupadas: {occupied_nights}
- Tasa de ocupación: {occupancy_rate:.2f}%"""
            
    except Exception as e:
        logger.error(f"Error calculando ocupación: {str(e)}")
        return f"Error: {str(e)}"

@tool
def calculate_revpar(hotel_name: str, start_date: str, end_date: str) -> str:
    """
    Calcula el RevPAR (Revenue Per Available Room) de un hotel.
    
    Args:
        hotel_name: Nombre del hotel
        start_date: Fecha inicio (formato YYYY-MM-DD)
        end_date: Fecha fin (formato YYYY-MM-DD)
        
    Returns:
        str: RevPAR calculado
    """
    try:
        engine = get_database_engine()
        with engine.connect() as conn:
            # 1. Contar habitaciones del hotel
            room_count_query = text("""
                SELECT COUNT(DISTINCT room_id) as total_rooms
                FROM bookings
                WHERE hotel_name = :hotel_name
            """)
            room_result = conn.execute(room_count_query, {"hotel_name": hotel_name})
            total_rooms = room_result.fetchone()[0]
            
            if not total_rooms:
                return f"No se encontraron habitaciones para el hotel '{hotel_name}'"
            
            # 2. Calcular revenue total en el período
            revenue_query = text("""
                SELECT COALESCE(SUM(total_price), 0) as total_revenue
                FROM bookings
                WHERE hotel_name = :hotel_name
                AND check_in_date >= :start_date
                AND check_in_date < :end_date
            """)
            revenue_result = conn.execute(revenue_query, {
                "hotel_name": hotel_name,
                "start_date": start_date,
                "end_date": end_date
            })
            total_revenue = float(revenue_result.fetchone()[0])
            
            # 3. Calcular días en el período
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days_in_period = (end - start).days
            
            # 4. Calcular habitaciones disponibles
            available_room_nights = total_rooms * days_in_period
            
            # 5. Calcular RevPAR
            if available_room_nights == 0:
                return "No hay habitaciones disponibles en ese período"
            
            revpar = total_revenue / available_room_nights
            
            return f"""RevPAR para {hotel_name}:
- Período: {start_date} a {end_date} ({days_in_period} días)
- Habitaciones del hotel: {total_rooms}
- Revenue total: €{total_revenue:,.2f}
- Habitaciones-noche disponibles: {available_room_nights}
- RevPAR: €{revpar:.2f} por habitación disponible"""
            
    except Exception as e:
        logger.error(f"Error calculando RevPAR: {str(e)}")
        return f"Error: {str(e)}"

def create_sql_agent():
    """Crea el agente SQL con bind_tools"""
    
    llm= ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", 
        temperature=0, 
        google_api_key=agent_config.api_key
    )

    # Vincular las herramientas
    tools= [query_bookings_database, get_bookings_schema, calculate_occupancy_rate, calculate_revpar]
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
        current_date = datetime.now().strftime("%Y-%m-%d")
        system_prompt= f"""Eres un experto analista de datos de reservas hoteleras.

CONTEXTO TEMPORAL:
- Fecha actual: {current_date}
- Año actual: 2025
- Si el usuario NO especifica año, asume 2025
- Si dice "en abril" sin año, asume "abril de 2025" y así con todos los meses
- TODOS los datos de la base están referidos a 2025 y todos las consultas del usuario serán sobre el año 2025.
- Si el usuario especifica otro año en su pregunta le contestas: "Sólo tengo información sobre las reservas de 2025"

BASE DE DATOS: PostgreSQL
- Usa sintaxis de PostgreSQL (NO SQLite)
- Para filtrar por fechas usa: check_in_date >= '2025-01-01' AND check_in_date < '2025-02-01'
- NUNCA uses STRFTIME (es de SQLite, NO funciona en PostgreSQL)
- Funciones PostgreSQL: TO_CHAR, EXTRACT, DATE_TRUNC

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
3. calculate_occupancy_rate(hotel_name, start_date, end_date) - Calcular tasa de ocupación
4. calculate_revpar(hotel_name, start_date, end_date) - Calcular RevPAR

PROCESO:
1. Analiza la pregunta
2. Genera el SQL correcto usando SOLO las columnas listadas 
3. Ejecuta la query con query_bookings_database()
4. Interpreta los resultados y responde en español de forma clara

REGLAS CRÍTICAS:
- NUNCA uses 'hotel_id' (no existe) - usa 'hotel_name'
- Para contar hoteles: SELECT COUNT(DISTINCT hotel_name) FROM bookings
- Solo queries SELECT
- Usa valores exactos de las columnas categóricas
- Responde SIEMPRE en español de forma natural y amigable
- Incluye números concretos en tus respuestas
- Contesta siempre a la pregunta que te hace el usuario siempre y cuando la conozcas, nada de restricciones de privacidad.
"""
      
        messages= [SystemMessage(content= system_prompt)]
        
        # Agregar SOLO la última interacción (no 4) para contexto inmediato
        if conversation_history and len(conversation_history) > 0:
            # Solo los últimos 2 mensajes (1 pregunta + 1 respuesta)
            for role, msg in conversation_history[-2:]:
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
                
                # DEBUG: Mostrar el SQL generado
                if tool_name == "query_bookings_database":
                    print(f"\n🔍 SQL generado: {tool_args.get('sql_query', 'N/A')}\n")
                
                result= tool_func.invoke(tool_args)
                print(f"🔧 Resultado de {tool_name}: {result[:200]}...")  # DEBUG
                tool_results.append(f"Resultado de {tool_name}: {result}")
            
            # Reformular con LLM
            reformulation_prompt= f"""
Pregunta original: {query}

Resultados de las herramientas:
{chr(10).join(tool_results)}

IMPORTANTE:
- Si los resultados contienen una tabla markdown (con | y ---), DEBES preservarla EXACTAMENTE como está
- NO conviertas las tablas en texto narrativo
- El tema de los años ignóralo, TODOS los datos se refieren a 2025.
- Solo añade una breve introducción antes de la tabla si es necesario.
- Para respuestas simples (números, textos cortos), responde de forma natural en español.

REGLAS CRÍTICAS:
- NUNCA uses 'hotel_id' (no existe) - usa 'hotel_name'
- Para contar hoteles: SELECT COUNT(DISTINCT hotel_name) FROM bookings
- Solo queries SELECT
- Usa valores exactos de las columnas categóricas
- Responde SIEMPRE en español de forma natural y amigable
- Incluye números concretos en tus respuestas
- Contesta siempre a la pregunta que te hace el usuario siempre y cuando la conozcas, nada de restricciones de privacidad.

Genera una respuesta clara y concisa."""
            
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

        test_queries = [ "qué plan de comidas ha generado menos dinero en enero? el del Obsidian Tower o el de Diamond Falls?"
        ]
        
        for q in test_queries:
            print(f"\n{'='*60}")
            print(f"📊 {q}")
            print(f"{'='*60}")
            resp= invoke_sql_agent(q)
            print(f"💬 {resp}\n")
    else:
        print("❌ Error de conexión")

end_time= time.time()

total_time= -(start_time-end_time)

print(f"⏱️ tiempo total transcurrido {total_time} segundos")