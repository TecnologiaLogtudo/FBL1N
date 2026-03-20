import pandas as pd
from .canonical_mapper import MidasCanonicalMapper

class MidasSpreadsheetProcessor:
    """
    Classe responsável por ler relatórios exportados (CSV/Excel), aplicar
    as regras de negócio (filtros, limpezas) e encaminhar os dados para mapeamento.
    """
    @staticmethod
    def process_and_map(file_path: str) -> str:
        print("Iniciando o tratamento da planilha baixada...")
        
        # Carrega o arquivo usando Pandas, verificando a extensão
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        else:
            df = pd.read_excel(file_path)
        
        # Padroniza todos os valores de texto da planilha para minúsculo
        df = df.apply(lambda col: col.str.lower() if col.dtype == 'object' else col)
        
        # Filtra a coluna "Tipo" buscando apenas os registros "cte" (agora em minúsculo)
        if "Tipo" in df.columns:
            df = df[df["Tipo"] == "cte"]
            
        # Regras de negócio para duplicatas na coluna "Número"
        if "Número" in df.columns and "Status" in df.columns:
            # Ordenamos pela coluna "Status" ('finalizado' vem antes de 'rejeitado' em ordem alfabética)
            df = df.sort_values(by="Status")
            # Removemos as duplicatas baseadas no "Número", mantendo a primeira ocorrência
            df = df.drop_duplicates(subset=["Número"], keep="first")
            
        # Mantém apenas as colunas desejadas (caso existam na planilha)
        colunas_desejadas = ["Número", "Tipo", "Data de Criação", "Status"]
        df = df[[col for col in colunas_desejadas if col in df.columns]]
        
        raw_data = df.to_dict(orient="records")
        return MidasCanonicalMapper.to_canonical(raw_data)