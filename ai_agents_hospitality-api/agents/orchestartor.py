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

