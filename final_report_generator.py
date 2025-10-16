# final_report_generator.py
import pandas as pd
import numpy as np
from utils import logger, format_currency

class FinalReportGenerator:
    """
    Classe responsável por gerar o arquivo Excel final com as análises
    e tabelas dinâmicas a partir dos dados já processados.
    """
    def __init__(self, analyzed_df):
        """
        Inicializa o gerador com o DataFrame final analisado.
        
        Args:
            analyzed_df (pd.DataFrame): O DataFrame vindo do AnalysisProcessor.
        """
        self.analyzed_df = analyzed_df.copy() if analyzed_df is not None else pd.DataFrame()
        logger.info("Gerador de Relatório Final inicializado.")

    def _format_currency_column(self, series):
        """Formata uma série de valores numéricos como moeda brasileira."""
        return series.apply(lambda x: format_currency(x) if pd.notna(x) and x != 0 else np.nan)

    def _generate_comprehensive_summary(self):
        """
        Gera uma tabela única consolidada com todas as transportadoras e serviços.
        Formato solicitado:
        - Cada transportadora como seção separada
        - Serviços como linhas
        - Colunas: Não compensado, Não lançado, Total geral
        """
        logger.info("Gerando tabela consolidada de resumo...")
        
        if self.analyzed_df.empty:
            logger.warning("DataFrame de análise está vazio. Nenhuma tabela será gerada.")
            return pd.DataFrame()

        # Garante que as colunas de valor sejam numéricas para a soma
        self.analyzed_df['Valor recebido'] = pd.to_numeric(self.analyzed_df['Valor recebido'], errors='coerce').fillna(0)
        
        # Lista completa de serviços esperados
        expected_services = [
            'Complemento', 'Descarga', 'Diária no cliente', 'Diária parado', 
            'Frete', 'Pedágio', 'Reentrega'
        ]
        
        # Lista de transportadoras
        transportadoras = ['Logtudo Bahia', 'Logtudo Ceará', 'Logtudo Pernambuco']
        
        # Dicionário para armazenar todos os resultados
        all_results = {}
        
        for transportadora in transportadoras:
            logger.info(f"Processando transportadora: {transportadora}")
            
            # Filtra dados para a transportadora atual
            df_transportadora = self.analyzed_df[
                (self.analyzed_df['Transportadora'] == transportadora) &
                (self.analyzed_df['Serviço'].isin(expected_services))
            ].copy()
            
            # Pivot table para status pgto
            pivot = pd.pivot_table(
                df_transportadora,
                values='Valor recebido',
                index='Serviço',
                columns='Status pgto',
                aggfunc='sum',
                fill_value=0,
                margins=True,
                margins_name='Total Geral'
            ).rename_axis(None, axis=1).reset_index()
            
            # Garante que todas as colunas existam
            for status in ['Não compensado', 'Não lançado']:
                if status not in pivot.columns:
                    pivot[status] = 0
            
            # Garante que todos os serviços existam
            for service in expected_services:
                if service not in pivot['Serviço'].values:
                    new_row = pd.DataFrame({
                        'Serviço': [service],
                        'Não compensado': [0],
                        'Não lançado': [0]
                    })
                    if 'Total Geral' in pivot.columns:
                        new_row['Total Geral'] = 0
                    
                    pivot = pd.concat([pivot, new_row], ignore_index=True)
            
            # Ordena os serviços
            pivot = pivot.set_index('Serviço').reindex(expected_services + ['Total Geral']).reset_index()
            
            # Calcula Total Geral para cada linha (exceto a linha total final)
            for i in range(len(pivot) - 1):  # Exclui a última linha (Total Geral)
                pivot.loc[i, 'Total Geral'] = pivot.loc[i, 'Não compensado'] + pivot.loc[i, 'Não lançado']
            
            # Calcula os totais finais
            pivot.loc[pivot['Serviço'] == 'Total Geral', 'Total Geral'] = \
                pivot.loc[pivot['Serviço'] == 'Total Geral', 'Não compensado'] + \
                pivot.loc[pivot['Serviço'] == 'Total Geral', 'Não lançado']
            
            # Formata valores como moeda
            for col in ['Não compensado', 'Não lançado', 'Total Geral']:
                pivot[col] = self._format_currency_column(pivot[col])
            
            # Armazena resultados para esta transportadora
            transportadora_results = {}
            for _, row in pivot.iterrows():
                service_name = row['Serviço']
                transportadora_results[service_name] = {
                    'Não compensado': row['Não compensado'],
                    'Não lançado': row['Não lançado'],
                    'Total Geral': row['Total Geral']
                }
            
            all_results[transportadora] = {
                'Transporte/Serviço': transportadora_results
            }
        
        logger.info("Tabela consolidada gerada com sucesso.")
        return all_results

    def _create_dataframe_from_nested_dict(self, nested_dict):
        """Converte o dicionário aninhado em um DataFrame para exportação."""
        data_rows = []
        
        for transportadora, services_data in nested_dict.items():
            for service_name, metrics in services_data['Transporte/Serviço'].items():
                if service_name == 'Total Geral':
                    continue  # Pula o total geral aqui, pois será calculado no nível superior
                
                row = {
                    'Transportadora': transportadora,
                    'Serviço': service_name,
                    'Não compensado': metrics['Não compensado'],
                    'Não lançado': metrics['Não lançado'],
                    'Total Geral': metrics['Total Geral']
                }
                data_rows.append(row)
        
        return pd.DataFrame(data_rows)

    def generate_report(self):
        """
        Gera o relatório final consolidado.
        
        Returns:
            dict: Dicionário com a aba final.
        """
        logger.info("--- INICIANDO GERAÇÃO DO RELATÓRIO FINAL CONSOLIDADO ---")
        
        # Gera os dados consolidados
        consolidated_data = self._generate_comprehensive_summary()
        
        # Cria um DataFrame para exportação
        export_df = self._create_dataframe_from_nested_dict(consolidated_data)
        
        # Calcula totais por transportadora (corrigido o FutureWarning)
        totals_by_transportadora = []
        for transportadora in ['Logtudo Bahia', 'Logtudo Ceará', 'Logtudo Pernambuco']:
            transport_data = export_df[export_df['Transportadora'] == transportadora]
            
            total_nao_compensado = 0
            total_nao_lancado = 0
            
            # Itera sobre os valores para converter de string para numérico
            for value in transport_data['Não compensado']:
                if pd.notna(value) and value != 'nan':
                    try:
                        # Remove formatação de moeda e converte para float
                        clean_value = float(str(value).replace('R$', '').replace('.', '').replace(',', '.'))
                        total_nao_compensado += clean_value
                    except (ValueError, TypeError):
                        pass
            
            for value in transport_data['Não lançado']:
                if pd.notna(value) and value != 'nan':
                    try:
                        # Remove formatação de moeda e converte para float
                        clean_value = float(str(value).replace('R$', '').replace('.', '').replace(',', '.'))
                        total_nao_lancado += clean_value
                    except (ValueError, TypeError):
                        pass
            
            total_geral = total_nao_compensado + total_nao_lancado
            
            totals_by_transportadora.append({
                'Transportadora': transportadora,
                'Serviço': 'Total Geral',
                'Não compensado': format_currency(total_nao_compensado),
                'Não lançado': format_currency(total_nao_lancado),
                'Total Geral': format_currency(total_geral)
            })
        
        # Adiciona os totais ao DataFrame
        totals_df = pd.DataFrame(totals_by_transportadora)
        final_export_df = pd.concat([export_df, totals_df], ignore_index=True)
        
        final_report_sheets = {
            'Resumo Consolidado': final_export_df
        }
        
        logger.info("--- GERAÇÃO DO RELATÓRIO FINAL CONCLUÍDA. ---")
        return final_report_sheets