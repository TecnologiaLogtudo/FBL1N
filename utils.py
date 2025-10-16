# utils.py
# Módulo para funções auxiliares, como a configuração de logs.

import logging
import sys

def setup_logging():
    """
    Configura o sistema de logging para registrar eventos em um arquivo e no console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("processamento.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def format_currency(x): return f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
def format_percentage(x): return f"{x*100:.2f}%"