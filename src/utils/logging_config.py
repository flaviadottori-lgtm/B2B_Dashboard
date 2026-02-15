"""
Logging estruturado para o projeto.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
) -> None:
    """
    Configura logging estruturado para o projeto.
    
    Args:
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho opcional para arquivo de log
    """
    # Mapper string -> logging level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Handler para console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formato: [HH:MM:SS] | LEVEL | module | message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler para arquivo (opcional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        print(f"📝 Logs salvos em: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Obtém logger para um módulo específico.
    
    Args:
        name: Nome do logger (geralmente __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
