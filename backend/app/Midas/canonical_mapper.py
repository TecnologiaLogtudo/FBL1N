import json
from typing import Dict, Any, List
from datetime import datetime

class MidasCanonicalMapper:
    """
    Classe base responsável por converter os dados brutos da Midas 
    para o formato de JSON Canônico.
    """
    
    @staticmethod
    def to_canonical(raw_data: List[Dict[str, Any]]) -> str:
        canonical_list = []
        
        for record in raw_data:
            # Mapeamento inicial básico. Os campos reais serão definidos posteriormente.
            canonical_record = {
                "sistema_origem": "MidasSolutions",
                "data_extracao": datetime.utcnow().isoformat(),
                "dados_brutos": record
            }
            canonical_list.append(canonical_record)
            
        return json.dumps(canonical_list, sort_keys=True, ensure_ascii=False)