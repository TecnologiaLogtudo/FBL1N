# app_interface.py
# Interface Gráfica para o Processador de Planilhas

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys
import logging
import pandas as pd
import customtkinter as ctk

# --- Importação de dependência opcional (ReportLab) ---
try:
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, NextPageTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    # Se a biblioteca não estiver instalada, o programa continuará funcionando,
    # mas a funcionalidade de exportar para PDF será desativada.
    REPORTLAB_AVAILABLE = False


def resource_path(relative_path):
    """
    Obtenha o caminho absoluto para o recurso, funciona para o desenvolvimento e para o PyInstaller.
    """
    # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
    try:
        # Estamos executando como executável PyInstaller
        # pylint: disable=protected-access, no-member
        base_path = sys._MEIPASS
    except (AttributeError, Exception): # pylint: disable=broad-exception-caught
        # Capturando Exception genéricamente porque queremos garantir que 
        # o código nunca quebre, mesmo que algo inesperado aconteça
        # Estamos executando em ambiente de desenvolvimento
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Seus imports existentes
# Importamos aqui, após definir resource_path
try:
    from main import main as run_main_process
    from utils import logger # Garanta que utils.py esteja na mesma pasta
    from config import OUTPUT_FILE_PATH # Garanta que config.py esteja na mesma pasta
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que main.py, utils.py e config.py estão no mesmo diretório.")
    sys.exit()


class TkinterLogHandler(logging.Handler):
    """Handler de logging customizado que redireciona logs para um widget de texto do Tkinter."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # Determina o tipo de mensagem com base no nível do log
        msg_type = "info"
        if record.levelno == logging.SUCCESS:
            msg_type = "success"
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            msg_type = "error"
        elif record.levelno == logging.WARNING:
            msg_type = "warning"
        elif record.levelno == logging.STAGE:
            msg_type = "stage"
        elif record.levelno == logging.STAIR:
            msg_type = "stair"
        
        # A UI deve ser atualizada na thread principal
        self.text_widget.after(0, self.text_widget.log, msg, msg_type)

class App(ctk.CTk):
    """
    Aplicativo CustomTkinter para a interface do processador de planilhas.
    """

    # ===================================================================
    # MÉTODOS AUXILIARES (Devem vir ANTES de __init__)
    # ===================================================================
    def log(self, message, msg_type="info"):
        """Adiciona uma mensagem à caixa de log com formatação de cor."""
        if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
            return # Ainda não existe a caixa de log

        self.log_text.config(state=tk.NORMAL) 

        if msg_type == "success":
            color = "green"
        elif msg_type == "error":
            color = "red"
        elif msg_type == "stage":
            color = "blue"
        elif msg_type == "stair":
            color = "cyan"
        else: # info, warning
            color = "white"

        self.log_text.insert(tk.END, f"{message}\n", msg_type)
        self.log_text.tag_config(msg_type, foreground=color)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_status(self, message, color="white"):
        """Atualiza o rótulo de status."""
        if not hasattr(self, 'status_label') or not self.status_label.winfo_exists():
            return # Ainda não existe o rótulo de status
        
        self.status_label.configure(text=f"Status: {message}", text_color=color)

    def update_progress(self, value):
        """Atualiza a barra de progresso."""
        if not hasattr(self, 'progress_bar') or not self.progress_bar.winfo_exists():
            return
        self.progress_bar.set(value)

    def select_file(self, path_variable):
        """Abre o explorador de arquivos e atualiza a variável de caminho."""
        filename = filedialog.askopenfilename(
            title="Selecionar Arquivo",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            path_variable.set(filename)
            logger.info("Arquivo selecionado: %s", filename)

    # ===================================================================
    # MÉTODO PRINCIPAL DE CONSTRUÇÃO DA UI (setup_ui)
    # ===================================================================
    def setup_ui(self):
        """Cria e posiciona todos os widgets da interface."""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # --- Seção 0: Escolha de Fluxo (Destaque) ---
        self.mode_frame = ctk.CTkFrame(self.main_frame, fg_color="#1a4371", border_color="#5fa1eb", border_width=2, corner_radius=10)
        self.mode_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 15), sticky="ew")
        self.mode_frame.grid_columnconfigure(0, weight=1)
        self.mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.mode_frame, text="📌 ESCOLHA O FLUXO DE PROCESSAMENTO", font=ctk.CTkFont(size=18, weight="bold"), text_color="#e0e0e0").grid(row=0, column=0, columnspan=2, pady=(15, 10))

        self.process_mode_var = tk.StringVar(value="standard")
        
        self.radio_standard = ctk.CTkRadioButton(self.mode_frame, text="Processo Padrão (FBL1N x BSoft)", variable=self.process_mode_var, value="standard", command=self.update_ui_for_mode, font=ctk.CTkFont(size=14, weight="bold"))
        self.radio_standard.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="e")

        self.radio_inverse = ctk.CTkRadioButton(self.mode_frame, text="Processo Inverso (Verificar Títulos em Aberto)", variable=self.process_mode_var, value="open_titles", command=self.update_ui_for_mode, font=ctk.CTkFont(size=14, weight="bold"))
        self.radio_inverse.grid(row=1, column=1, padx=20, pady=(0, 15), sticky="w")

        # --- Seção 1: Configuração de Arquivos ---
        config_frame = ctk.CTkFrame(self.main_frame)
        config_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(config_frame, text="Configuração de Arquivos", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Input File
        ctk.CTkLabel(config_frame, text="Base de Dados (.xlsx):").grid(row=1, column=0, padx=10, pady=(10, 5), sticky="w")
        self.input_file_path = tk.StringVar(value="arquivo FBL1N")
        input_entry = ctk.CTkEntry(config_frame, textvariable=self.input_file_path, width=400)
        input_entry.grid(row=1, column=1, padx=10, pady=(10, 5), sticky="ew")
        ctk.CTkButton(config_frame, text="Selecionar", command=lambda: self.select_file(self.input_file_path)).grid(row=1, column=2, padx=10, pady=(10, 5))
        
        # Report File
        self.report_label = ctk.CTkLabel(config_frame, text="Relatório Externo (.xls):")
        self.report_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.report_file_path = tk.StringVar(value="relatorio BSoft")
        self.report_entry = ctk.CTkEntry(config_frame, textvariable=self.report_file_path, width=400)
        self.report_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.report_btn = ctk.CTkButton(config_frame, text="Selecionar", command=lambda: self.select_file(self.report_file_path))
        self.report_btn.grid(row=2, column=2, padx=10, pady=5)
        
        # Open Titles File (Oculto por padrão)
        self.open_titles_label = ctk.CTkLabel(config_frame, text="Títulos em Aberto (.xls/.xlsx):")
        self.open_titles_path = tk.StringVar(value="planilha títulos em aberto")
        self.open_titles_entry = ctk.CTkEntry(config_frame, textvariable=self.open_titles_path, width=400)
        self.open_titles_btn = ctk.CTkButton(config_frame, text="Selecionar", command=lambda: self.select_file(self.open_titles_path))

        # Ano de Análise
        ctk.CTkLabel(config_frame, text="Ano de Análise:").grid(row=3, column=0, padx=10, pady=(5, 10), sticky="w")
        self.analysis_year = tk.StringVar(value="2025")
        year_entry = ctk.CTkEntry(config_frame, textvariable=self.analysis_year, width=100)
        year_entry.grid(row=3, column=1, padx=10, pady=(5, 10), sticky="w")

        # --- Seção 2: Controles e Status ---
        controls_frame = ctk.CTkFrame(self.main_frame)
        controls_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Status Bar
        self.status_label = ctk.CTkLabel(controls_frame, text="Status: Pronto", font=ctk.CTkFont(size=14), text_color="green")
        self.status_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Execute Button
        self.execute_button = ctk.CTkButton(controls_frame, text="Executar Processamento", command=self.start_process, fg_color="green", hover_color="darkgreen", font=ctk.CTkFont(size=16, weight="bold"))
        self.execute_button.grid(row=0, column=1, padx=20, pady=10, sticky="e")

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(controls_frame)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        # --- Seção 3: Abas (Logs e Resultados) ---
        self.notebook = ctk.CTkTabview(self.main_frame)
        self.notebook.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Aba de Logs
        self.log_tab = self.notebook.add("Logs")
        self.log_text = tk.Text(self.log_tab, wrap=tk.WORD, bg="#1e1e1e", fg="white", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
        # Aba de Resultados
        self.results_tab = self.notebook.add("Visualizar Resultados")
        self.results_notebook = ctk.CTkTabview(self.results_tab)
        self.results_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Sub-aba: Resumo Consolidado (USANDO ttk.Treeview)
        self.summary_frame = self.results_notebook.add("Resumo Consolidado")
        self.summary_tree = ttk.Treeview(self.summary_frame)
        self.summary_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Sub-aba: Detalhes de Pendências (USANDO ttk.Treeview)
        self.details_frame = self.results_notebook.add("Detalhes de Pendências")
        self.details_tree = ttk.Treeview(self.details_frame)
        self.details_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- Seção 4: Exportação (aparece após sucesso) ---
        self.export_frame = ctk.CTkFrame(self.main_frame)
        self.export_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.export_frame.grid_remove() 
        
        ctk.CTkLabel(self.export_frame, text="Exportar Arquivo:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkButton(self.export_frame, text="Exportar para .xlsx", command=lambda: self.export_file("xlsx")).grid(row=0, column=1, padx=10, pady=10)
        
        self.pdf_button = ctk.CTkButton(self.export_frame, text="Exportar para .pdf", command=lambda: self.export_file("pdf"))
        self.pdf_button.grid(row=0, column=2, padx=10, pady=10)
        if not REPORTLAB_AVAILABLE:
            self.pdf_button.configure(state=tk.DISABLED, text="Exportar para .pdf (indisponível)")

    def update_ui_for_mode(self):
        """Atualiza os campos de arquivo visíveis dependendo do modo selecionado."""
        if self.process_mode_var.get() == "standard":
            self.open_titles_label.grid_remove()
            self.open_titles_entry.grid_remove()
            self.open_titles_btn.grid_remove()
            
            self.report_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            self.report_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
            self.report_btn.grid(row=2, column=2, padx=10, pady=5)
        else:
            self.report_label.grid_remove()
            self.report_entry.grid_remove()
            self.report_btn.grid_remove()
            
            self.open_titles_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
            self.open_titles_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
            self.open_titles_btn.grid(row=2, column=2, padx=10, pady=5)


    # ===================================================================
    # MÉTODO DE INICIALIZAÇÃO (__init__)
    # ===================================================================
    def __init__(self):
        super().__init__()

        self.title("Análise de Transportes - Painel de Controle")
        self.geometry("1100x750")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Configuração de tema
        ctk.set_appearance_mode("System") 
        ctk.set_default_color_theme("blue") 

        # Agora os métodos já existem, então a chamagem é segura
        self.setup_ui()

        # Configura o handler de logging para a UI
        # Adiciona um novo nível de log para "success"
        logging.SUCCESS = 25  # Entre INFO (20) e WARNING (30)
        logging.addLevelName(logging.SUCCESS, "SUCCESS")

        # Adiciona um novo nível de log para "stage"
        logging.STAGE = 26 # Depois de SUCCESS
        logging.addLevelName(logging.STAGE, "STAGE")

        # Adiciona um novo nível de log para o início de cada ETAPA
        logging.STAIR = 27 # Depois de STAGE
        logging.addLevelName(logging.STAIR, "STAIR")

        # Cria o handler e o adiciona ao logger raiz
        tkinter_handler = TkinterLogHandler(self)
        logging.getLogger().addHandler(tkinter_handler)
        
        # Define um método de atalho para o novo nível
        logging.Logger.success = lambda self, msg, *args, **kwargs: self.log(logging.SUCCESS, msg, *args, **kwargs)
        logging.Logger.stage = lambda self, msg, *args, **kwargs: self.log(logging.STAGE, msg, *args, **kwargs)
        logging.Logger.stair = lambda self, msg, *args, **kwargs: self.log(logging.STAIR, msg, *args, **kwargs)

        logger.success("Painel de Controle iniciado. Pronto para operação.")
        self.update_status("Pronto", "green")

    # ===================================================================
    # MÉTODOS DE LÓGICA DO APLICATIVO
    # ===================================================================
    def start_process(self):
        """Inicia o processamento em uma thread separada para não travar a UI."""
        if not self.validate_inputs():
            return
            
        self.execute_button.configure(state=tk.DISABLED)
        self.progress_bar.grid() 
        
        self.notebook.set("Logs")
        self.export_frame.grid_remove()
        
        for tree in [self.summary_tree, self.details_tree]:
            for item in tree.get_children():
                tree.delete(item)

        process_thread = threading.Thread(target=self.run_process_wrapper)
        process_thread.start()

    def run_process_wrapper(self):
        """Envolve a chamada da função principal para capturar erros."""
        try:
            logger.success("===================================================")
            logger.success("Iniciando novo ciclo de processamento via interface.")
            self.update_status("Executando...", "orange")
            
            input_file = self.input_file_path.get()
            analysis_year = int(self.analysis_year.get())
            output_file = resource_path(OUTPUT_FILE_PATH) 
            mode = self.process_mode_var.get()
            
            report_file = self.report_file_path.get() if mode == "standard" else None
            open_titles_file = self.open_titles_path.get() if mode == "open_titles" else None

            run_main_process(input_file=input_file, report_file=report_file, output_file=output_file, 
                             analysis_year=analysis_year, process_mode=mode, open_titles_file=open_titles_file, 
                             progress_callback=self.update_progress)
            
            logger.success("Processamento concluído com sucesso!")
            self.update_status("Concluído com Sucesso", "green")
            self.load_data_for_view()
            self.export_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            messagebox.showinfo("Sucesso", "O processamento foi concluído e os resultados estão disponíveis para visualização e exportação.")

        except (ValueError, TypeError, KeyError) as e:
            # Erros de dados e valores
            logger.error("Erro de validação de dados: %s", e)
            messagebox.showerror("Erro de Dados", f"Dados inválidos ou formatos incorretos:\n\n{str(e)}")
        except (RuntimeError, ConnectionError, OSError) as e:
            # Erros de sistema e execução
            logger.error("ERRO CRÍTICO DURANTE O PROCESSAMENTO: %s", e)
            logger.error("Verifique os logs detalhados para mais informações.")
            self.update_status("Erro", "red")
            messagebox.showerror("Erro de Processamento", f"Ocorreu um erro durante a execução:\n\n{str(e)}")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Último recurso: captura o restante
            logger.exception("ERRO INESPERADO: %s", e)
            logger.error("Verifique os logs detalhados para mais informações.")
            self.update_status("Erro", "red")
            messagebox.showerror("Erro Inesperado", "Ocorreu um erro não esperado. Verifique os logs detalhados.")
        finally:
            self.progress_bar.set(0)
            self.execute_button.configure(state=tk.NORMAL)
            logger.success("==================================================\n")

    def validate_inputs(self):
        """Valida se os arquivos de entrada existem."""
        input_file = self.input_file_path.get()
        year_str = self.analysis_year.get()
        mode = self.process_mode_var.get()

        try:
            int(year_str)
        except (ValueError, TypeError):
            logger.error("ERRO: O ano de análise '%s' não é um número válido.", year_str)
            messagebox.showerror("Erro de Validação", f"O ano de análise deve ser um número válido (ex: 2025).\nValor inserido: {year_str}")
            return False

        if not os.path.exists(input_file):
            logger.error("ERRO: Arquivo de entrada não encontrado: %s", input_file)
            messagebox.showerror("Erro de Arquivo", f"O arquivo de entrada não foi encontrado:\n{input_file}")
            return False
            
        if mode == "standard":
            report_file = self.report_file_path.get()
            if not os.path.exists(report_file):
                logger.error("ERRO: Arquivo de relatório não encontrado: %s", report_file)
                messagebox.showerror("Erro de Arquivo", f"O arquivo de relatório não foi encontrado:\n{report_file}")
                return False
        else:
            open_titles_file = self.open_titles_path.get()
            if not os.path.exists(open_titles_file):
                logger.error("ERRO: Arquivo de títulos em aberto não encontrado: %s", open_titles_file)
                messagebox.showerror("Erro de Arquivo", f"A planilha de títulos em aberto não foi encontrada:\n{open_titles_file}")
                return False
        return True

    def load_data_for_view(self):
        """Carrega os dados do arquivo de saída para as abas de visualização."""
        try:
            output_file_path = resource_path(OUTPUT_FILE_PATH)
            mode = self.process_mode_var.get()
            
            if mode == "standard":
                df_summary = pd.read_excel(output_file_path, sheet_name='Resumo Consolidado', skiprows=2, usecols="A:E", nrows=25)
                if not df_summary.empty:
                    self.display_dataframe(self.summary_tree, df_summary)
                    logger.info("Tabela 'Resumo Consolidado' carregada para visualização.")

                df_details_full = pd.read_excel(output_file_path, sheet_name='Resumo Consolidado', skiprows=2, header=None)
                df_details_raw = df_details_full.iloc[:, 6:]

                if not df_details_raw.empty:
                    all_detail_headers = ['Emissão', 'Mês', 'Transportadora', 'CTRC', 'Cliente', 'Serviço', 'Senha Ravex', 'DT Frete', 'Destino', 'Nota fiscal', 'Status Pgto', 'Valor CTe', 'Valor pago', 'Recebido/A receber']
                    df_details_raw.columns = all_detail_headers[:len(df_details_raw.columns)]
                    df_details_raw = df_details_raw.iloc[1:].reset_index(drop=True)

                    cols_to_display = ['Emissão', 'Mês', 'Transportadora', 'CTRC', 'Serviço', 'Valor CTe', 'Status Pgto', 'Valor pago', 'Recebido/A receber']
                    existing_cols = [col for col in cols_to_display if col in df_details_raw.columns]
                    df_details = df_details_raw[existing_cols]

                    self.display_dataframe(self.details_tree, df_details)
                    logger.info("Tabela 'Detalhes de Pendências' carregada para visualização.")
            else:
                df_summary = pd.read_excel(output_file_path, sheet_name='Resumo Aberto', skiprows=2, usecols="A:F")
                if not df_summary.empty:
                    self.display_dataframe(self.summary_tree, df_summary)
                
                df_details = pd.read_excel(output_file_path, sheet_name='Aberto vs Pago', skiprows=2)
                if not df_details.empty:
                    self.display_dataframe(self.details_tree, df_details)

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Não foi possível carregar os dados para visualização: %s", e, exc_info=True)

    def display_dataframe(self, tree, df):
        """Exibe um DataFrame em um ttk.Treeview."""
        # Limpa itens existentes
        for item in tree.get_children():
            tree.delete(item)

        # Cria as colunas
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"

        # Define os cabeçalhos
        for col in tree["columns"]:
            tree.heading(col, text=col)
            # Ajusta a largura da coluna para caber melhor os valores
            if 'Valor' in col or 'Total' in col:
                tree.column(col, width=120, anchor='e') # 'e' para alinhar à direita para valores
            else:
                tree.column(col, width=120, anchor='center')

        # Cria uma cópia para manipulação, não alterando o original
        df_display = df.copy()

        # Lista expandida de colunas que podem conter valores monetários
        monetary_cols = ['Não compensado', 'Não lançado', 'Total Geral', 'Valor CTe', 'Valor pago', 'Recebido/A receber']
        
        for col in monetary_cols:
            if col in df_display.columns:
                try:
                    # Garante que a coluna seja tratada como string para limpeza
                    s = df_display[col].astype(str)
                    
                    # Limpa a string de formatação monetária (R$, .,)
                    s = s.str.replace("R$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
                    
                    # Converte para numérico, tratando erros e preenchendo com 0
                    numeric_values = pd.to_numeric(s, errors='coerce').fillna(0.0)
                    
                    # Aplica a formatação monetária para exibição
                    df_display[col] = numeric_values.apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                except Exception as e: # pylint: disable=broad-exception-caught
                    logger.warning("Não foi possível formatar a coluna monetária '%s'. Erro: %s", col, e)
                    df_display[col] = df_display[col].fillna('')
        
        # Insere os dados no Treeview linha por linha
        for _, row in df_display.iterrows():
            tree.insert("", "end", values=list(row))

    def export_file(self, file_type):
        """Exporta o arquivo de saída para .xlsx ou .pdf."""
        output_file_path = resource_path(OUTPUT_FILE_PATH)

        if not os.path.exists(output_file_path):
            messagebox.showwarning("Arquivo Não Encontrado", "O arquivo de saída ainda não foi gerado. Execute o processamento primeiro.")
            return
            
        default_filename = f"Job_Processo_{self.analysis_year.get()}"

        if file_type == "xlsx":
            try:
                dest_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
                    initialfile=f"{default_filename}.xlsx"
                )
                if dest_path:
                    import shutil
                    try:
                        shutil.copy(output_file_path, dest_path)
                        logger.success("Arquivo .xlsx exportado com sucesso para: %s", dest_path)
                        messagebox.showinfo("Exportação Bem-sucedida", f"O arquivo Excel foi salvo em:\n{dest_path}")
                    except PermissionError:
                        logger.error("Erro de permissão ao salvar o arquivo em: %s. Verifique se o arquivo já está aberto.", dest_path)
                        messagebox.showerror("Erro de Permissão", f"Não foi possível salvar o arquivo em:\n{dest_path}\n\nVerifique se o arquivo já está aberto em outro programa e tente novamente.")
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.error("Erro ao exportar arquivo .xlsx: %s", e, exc_info=True)
                messagebox.showerror("Erro de Exportação", f"Não foi possível exportar o arquivo .xlsx.\n\nErro: {e}")

        elif file_type == "pdf":
            if not REPORTLAB_AVAILABLE:
                messagebox.showerror("Dependência Faltando", "A biblioteca 'reportlab' é necessária para exportar para PDF.\n\nInstale-a com: pip install reportlab")
                return
            try:

                dest_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
                    initialfile=f"{default_filename}.pdf"
                )
                
                if not dest_path:
                    return

                mode = self.process_mode_var.get()
                if mode == "open_titles":
                    messagebox.showinfo("Exportação de PDF", "O design customizado em PDF está disponível nativamente apenas na versão Web para o Processo Inverso.\n\nPor favor, utilize o arquivo Excel Exportado que já possui toda formatação.")
                    return

                # --- Carregamento e Preparação dos Dados ---
                # Tabela 1: Resumo Consolidado
                df_summary = pd.read_excel(output_file_path, sheet_name='Resumo Consolidado', skiprows=2, usecols="A:E")
                df_summary.dropna(how='all', inplace=True) # Remove linhas totalmente vazias

                # Tabela 2: Detalhes de Pendências
                df_details_full = pd.read_excel(output_file_path, sheet_name='Resumo Consolidado', skiprows=2, header=None)
                df_details_raw = df_details_full.iloc[:, 6:]
                
                df_details = pd.DataFrame()
                if not df_details_raw.empty:
                    # Define todos os cabeçalhos possíveis para a seção de detalhes
                    detail_headers = ['Emissão', 'Mês', 'Transportadora', 'CTRC', 'Cliente', 'Serviço', 'Senha Ravex', 'DT Frete', 'Destino', 'Nota fiscal', 'Valor CTe', 'Status Pgto', 'Valor pago', 'Recebido/A receber']
                    df_details_raw.columns = detail_headers[:len(df_details_raw.columns)]
                    
                    # Seleciona apenas as colunas desejadas para o PDF
                    cols_to_keep = ['Emissão', 'Mês', 'Transportadora', 'CTRC', 'Serviço', 'Valor CTe', 'Status Pgto', 'Valor pago', 'Recebido/A receber']
                    
                    # Garante que apenas colunas existentes sejam selecionadas para evitar erros
                    existing_cols = [col for col in cols_to_keep if col in df_details_raw.columns]
                    df_details = df_details_raw[existing_cols]
                    
                def _format_currency_pdf(val):
                    if pd.isna(val) or str(val).strip() in ['', '-', 'Não lançado', 'Não compensado']:
                        return val
                    try:
                        clean_val = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
                        return f"R$ {float(clean_val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    except (ValueError, TypeError):
                        return val

                for col in ['Não compensado', 'Não lançado', 'Total Geral']:
                    if col in df_summary.columns:
                        df_summary[col] = df_summary[col].apply(_format_currency_pdf)
                for col in ['Valor CTe', 'Valor pago', 'Recebido/A receber']:
                    if col in df_details.columns:
                        df_details[col] = df_details[col].apply(_format_currency_pdf)

                if df_summary.empty and df_details.empty:
                    messagebox.showwarning("Dados Vazios", "Não há dados na aba 'Resumo Consolidado' para gerar o PDF.")
                    return

                # --- Definição do Template do Documento com Múltiplas Orientações ---
                class MyDocTemplate(BaseDocTemplate):
                    def __init__(self, filename, **kw):
                        super().__init__(filename, **kw)
                        
                        frame_portrait = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='frame_portrait')  # pylint: disable=no-member
                        frame_landscape = Frame(self.leftMargin, self.bottomMargin, self.height, self.width, id='frame_landscape') # pylint: disable=no-member

                        self.addPageTemplates([
                            PageTemplate(id='portrait', frames=[frame_portrait], onPage=self._add_footer, pagesize=letter),
                            PageTemplate(id='landscape', frames=[frame_landscape], onPage=self._add_footer, pagesize=landscape(letter)),
                        ])

                    def _add_footer(self, canvas, doc):
                        canvas.saveState()
                        from datetime import datetime
                        footer_text = f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                        canvas.setFont('Helvetica', 9)
                        page_num = canvas.getPageNumber()
                        canvas.drawString(inch, 0.5 * inch, footer_text)
                        canvas.drawRightString(doc.pagesize[0] - inch, 0.5 * inch, f"Página {page_num}")
                        canvas.restoreState()

                doc = MyDocTemplate(dest_path)
                elements = []
                styles = getSampleStyleSheet()
                
                # --- Título Principal ---
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=20, alignment=1, textColor=colors.darkblue)
                elements.append(Paragraph("RESUMO CONSOLIDADO DE TRANSPORTES", title_style))

                # --- Tabela de Resumo (Portrait) ---
                if not df_summary.empty:
                    df_summary = df_summary.fillna('').astype(str)
                    table_data_summary = [df_summary.columns.tolist()] + df_summary.values.tolist()
                    
                    col_widths_summary = [1.6*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch]
                    
                    table_summary = Table(table_data_summary, colWidths=col_widths_summary, repeatRows=1)
                    style_summary = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BACKGROUND', (0, -3), (-1, -1), colors.cyan),
                    ])

                    # Adiciona formatação para números negativos em vermelho
                    for i, row_values in enumerate(df_summary.values):
                        table_row_index = i + 1
                        for j, cell_value in enumerate(row_values):
                            try:
                                val_str = str(cell_value).replace('R$', '').replace('.', '').replace(',', '.').strip()
                                if val_str and float(val_str) < 0:
                                    style_summary.add('TEXTCOLOR', (j, table_row_index), (j, table_row_index), colors.red)
                            except (ValueError, TypeError):
                                continue # Ignora se não for um número
                    ])
                    table_summary.setStyle(style_summary)
                    elements.append(table_summary)

                # --- Tabela de Detalhes (Landscape) ---
                if not df_details.empty:
                    elements.append(NextPageTemplate('landscape'))
                    elements.append(PageBreak())

                    elements.append(Paragraph("DETALHES DE PENDÊNCIAS", styles['Heading2']))
                    elements.append(Spacer(1, 12))

                    # Garante que todos os dados sejam strings antes da verificação
                    df_details = df_details.fillna('').astype(str)

                    # Lógica de formatação condicional
                    conditional_styles = []
                    try:
                        status_col_name = 'Status Pgto'
                        recebido_col_name = 'Recebido/A receber'
                        
                        if status_col_name in df_details.columns and recebido_col_name in df_details.columns:
                            status_col_idx = df_details.columns.get_loc(status_col_name)
                            recebido_col_idx = df_details.columns.get_loc(recebido_col_name)

                            for i, row_values in enumerate(df_details.iloc[1:].values):
                                table_row_index = i + 1
                                status_value = row_values[status_col_idx]
                                
                                if status_value.strip() == 'Não lançado':
                                    conditional_styles.append(
                                        ('BACKGROUND', (recebido_col_idx, table_row_index), (recebido_col_idx, table_row_index), colors.HexColor('#FFCCCC'))
                                    )

                            # Novo: Formatação para números negativos em vermelho
                            for i, row_values in enumerate(df_details.iloc[1:].values):
                                table_row_index = i + 1
                                for j, cell_value in enumerate(row_values):
                                    try:
                                        # Tenta converter para float, mesmo que seja string
                                        if pd.notna(cell_value) and float(cell_value) < 0:
                                            conditional_styles.append(('TEXTCOLOR', (j, table_row_index), (j, table_row_index), colors.red))
                                    except (ValueError, TypeError):
                                        continue # Ignora se não for um número
                    except Exception as e:
                        logger.warning("Não foi possível aplicar o estilo condicional ao PDF: %s", e)

                    # A primeira linha de dados é uma duplicata do cabeçalho, então a removemos.
                    table_data_details = [df_details.columns.tolist()] + df_details.values.tolist()[1:]
                    
                    col_widths_details = [1*inch, 0.7*inch, 1.5*inch, 0.8*inch, 1.2*inch, 1*inch, 1.2*inch, 0.9*inch, 1.2*inch]
                    
                    table_details = Table(table_data_details, colWidths=col_widths_details[:len(df_details.columns)], repeatRows=1)
                    style_details = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.darkgrey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ])

                    for style in conditional_styles:
                        style_details.add(*style)

                    table_details.setStyle(style_details)
                    elements.append(table_details)
                
                try:
                    doc.build(elements)
                    logger.success("Arquivo .pdf exportado com sucesso para: %s", dest_path)
                    messagebox.showinfo("Exportação Bem-sucedida", f"O arquivo PDF foi salvo em:\n{dest_path}")
                except PermissionError:
                    logger.error("Erro de permissão ao salvar o arquivo: %s. Verifique se o arquivo já está aberto.", dest_path)
                    messagebox.showerror("Erro de Permissão", f"Não foi possível salvar o arquivo em:\n{dest_path}\n\nVerifique se o arquivo já está aberto em outro programa e tente novamente.")

            except Exception as e:
                logger.error("Erro ao exportar arquivo .pdf: %s", e, exc_info=True)
                messagebox.showerror("Erro de Exportação", f"Não foi possível exportar o arquivo .PDF.\n\nErro: {e}")

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = App()
    app.mainloop()