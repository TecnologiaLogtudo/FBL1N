# utils.py
# Módulo para funções auxiliares, como a configuração de logs.

import logging

def setup_logging():
    """
    Configura o sistema de logging, adicionando níveis customizados e
    registrando eventos em um arquivo e no console.
    """
    # Adiciona níveis de log customizados para melhor semântica
    # Nível para sucesso de operações importantes
    logging.SUCCESS = 25  # Entre INFO (20) e WARNING (30)
    logging.addLevelName(logging.SUCCESS, "SUCCESS")
    # Nível para indicar o início de uma fase/etapa principal
    logging.STAGE = 26
    logging.addLevelName(logging.STAGE, "STAGE")
    # Nível para indicar o início de uma sub-etapa
    logging.STAIR = 27
    logging.addLevelName(logging.STAIR, "STAIR")

    # Adiciona os métodos correspondentes à classe Logger
    logging.Logger.success = lambda self, msg, *args, **kwargs: self.log(logging.SUCCESS, msg, *args, **kwargs)
    logging.Logger.stage = lambda self, msg, *args, **kwargs: self.log(logging.STAGE, msg, *args, **kwargs)
    logging.Logger.stair = lambda self, msg, *args, **kwargs: self.log(logging.STAIR, msg, *args, **kwargs)

    """
    Configura o sistema de logging para registrar eventos em um arquivo e no console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("processamento.log")
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def format_currency(x): return f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
def format_percentage(x): return f"{x*100:.2f}%"