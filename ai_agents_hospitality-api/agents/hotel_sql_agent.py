"""
SQL Agent para consultas analíticas de bookings
Ejercicio 2: Agente SQL que consulta PostgreSQL para obtener estadísticas de reservas
"""

import os
from typing import Optional
from datetime import time, datetime, timedelta

from sqlalchemy import create_engine, text

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

from util.logger_config import logger