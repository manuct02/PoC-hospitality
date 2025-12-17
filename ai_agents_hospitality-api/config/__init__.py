"""
Configuration module for AI agents.

This module provides centralized configuration management that loads settings
from both configuration files and environment variables, with environment
variables taking precedence.
"""

from .agent_config import AgentConfig, get_agent_config

__all__ = ["AgentConfig", "get_agent_config"]

