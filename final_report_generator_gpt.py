# final_report_generator.py

import pandas as pd
from utils import format_currency, format_percentage


class FinalReportGenerator:
    """
    Gera o relatório final consolidado a partir do dataframe analisado.
    Recebe o resultado de AnalysisProcessor.run_analysis() e produz
    tabelas de resumo por mês, transportadora e totais gerais.
    """

    def __init__(self, analyzed_report_df: pd.DataFrame):
        self.df = analyzed_report_df.copy()

    def generate_summary(self):
        """
        Cria os resumos mensais e consolidados com totais e indicadores.
        Retorna um dicionário com:
          - 'Resumo Mensal'
          - 'Resumo Consolidado'
        """
        # --- Tratamento básico ---
        self.df['Mês'] = pd.to_datetime(self.df['Data']).dt.to_period('M').astype(str)
        self.df['Diferença'] = self.df['Valor Pago'] - self.df['Valor CTe']
        self.df['% Pago'] = (self.df['Valor Pago'] / self.df['Valor CTe']).fillna(0)

        # --- Resumo Mensal por Transportadora ---
        resumo_mensal = (
            self.df.groupby(['Mês', 'Transportadora'], as_index=False)
            .agg({
                'Nota Fiscal': 'count',
                'Valor CTe': 'sum',
                'Valor Pago': 'sum',
                'Diferença': 'sum'
            })
        )

        resumo_mensal.rename(columns={
            'Nota Fiscal': 'Qtde Notas',
        }, inplace=True)

        resumo_mensal['% Pago'] = (resumo_mensal['Valor Pago'] / resumo_mensal['Valor CTe']).fillna(0)

        # --- Resumo Consolidado ---
        resumo_consolidado = (
            self.df.groupby('Transportadora', as_index=False)
            .agg({
                'Nota Fiscal': 'count',
                'Valor CTe': 'sum',
                'Valor Pago': 'sum',
                'Diferença': 'sum'
            })
        )

        resumo_consolidado.rename(columns={'Nota Fiscal': 'Qtde Notas'}, inplace=True)
        resumo_consolidado['% Pago'] = (resumo_consolidado['Valor Pago'] / resumo_consolidado['Valor CTe']).fillna(0)

        # --- Totais gerais (última linha) ---
        total_geral = pd.DataFrame({
            'Transportadora': ['TOTAL GERAL'],
            'Qtde Notas': [self.df['Nota Fiscal'].count()],
            'Valor CTe': [self.df['Valor CTe'].sum()],
            'Valor Pago': [self.df['Valor Pago'].sum()],
            'Diferença': [self.df['Diferença'].sum()],
            '% Pago': [(self.df['Valor Pago'].sum() / self.df['Valor CTe'].sum()) if self.df['Valor CTe'].sum() else 0]
        })

        resumo_consolidado = pd.concat([resumo_consolidado, total_geral], ignore_index=True)

        return {
            "Resumo Mensal": resumo_mensal,
            "Resumo Consolidado": resumo_consolidado
        }

    def export_to_excel(self, summaries: dict, output_path: str):
        """
        Exporta os resumos gerados para um arquivo Excel com formatação básica.
        """
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            for sheet_name, df in summaries.items():
                df_to_export = df.copy()

                # Formatar valores
                if 'Valor CTe' in df_to_export.columns:
                    df_to_export['Valor CTe'] = df_to_export['Valor CTe'].apply(format_currency)
                if 'Valor Pago' in df_to_export.columns:
                    df_to_export['Valor Pago'] = df_to_export['Valor Pago'].apply(format_currency)
                if 'Diferença' in df_to_export.columns:
                    df_to_export['Diferença'] = df_to_export['Diferença'].apply(format_currency)
                if '% Pago' in df_to_export.columns:
                    df_to_export['% Pago'] = df_to_export['% Pago'].apply(format_percentage)

                df_to_export.to_excel(writer, sheet_name=sheet_name, index=False)

            writer._save()
