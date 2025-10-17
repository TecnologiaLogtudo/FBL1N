# app_interface.py
# Interface Gráfica para o Processador de Planilhas
import tkinter as tk
from tkinter import filedialog, messagebox, ttk # ttk importado aqui
import customtkinter as ctk
import pandas as pd
import threading
import os
import sys

# Adiciona o diretório atual ao sys.path para garantir que os imports funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Seus imports existentes
    from main import main as run_main_process
    from utils import logger # Garanta que utils.py esteja na mesma pasta
    from config import OUTPUT_FILE_PATH # Garanta que config.py esteja na mesma pasta
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que main.py, utils.py e config.py estão no mesmo diretório.")
    sys.exit()

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
            color = "cyan"
        else: # info, warning
            color = "white"

        self.log_text.insert(tk.END, f"{message}\n", msg_type)
        self.log_text.tag_config(msg_type, foreground=color)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        # Também loga para o arquivo de log do projeto
        if msg_type == "error":
            logger.error(message)
        else:
            logger.info(message)

    def update_status(self, message, color="white"):
        """Atualiza o rótulo de status."""
        if not hasattr(self, 'status_label') or not self.status_label.winfo_exists():
            return # Ainda não existe o rótulo de status
        
        self.status_label.configure(text=f"Status: {message}", text_color=color)

    def select_file(self, path_variable):
        """Abre o explorador de arquivos e atualiza a variável de caminho."""
        filename = filedialog.askopenfilename(
            title="Selecionar Arquivo",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            path_variable.set(filename)
            self.log(f"Arquivo selecionado: {filename}", "info")

    # ===================================================================
    # MÉTODO PRINCIPAL DE CONSTRUÇÃO DA UI (setup_ui)
    # ===================================================================
    def setup_ui(self):
        """Cria e posiciona todos os widgets da interface."""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # --- Seção 1: Configuração de Arquivos ---
        config_frame = ctk.CTkFrame(self.main_frame)
        config_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(config_frame, text="Configuração de Arquivos", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Input File
        ctk.CTkLabel(config_frame, text="Base de Dados (.xlsx):").grid(row=1, column=0, padx=10, pady=(10, 5), sticky="w")
        self.input_file_path = tk.StringVar(value="base_de_dados.xlsx")
        input_entry = ctk.CTkEntry(config_frame, textvariable=self.input_file_path, width=400)
        input_entry.grid(row=1, column=1, padx=10, pady=(10, 5), sticky="ew")
        ctk.CTkButton(config_frame, text="Selecionar", command=lambda: self.select_file(self.input_file_path)).grid(row=1, column=2, padx=10, pady=(10, 5))
        
        # Report File
        ctk.CTkLabel(config_frame, text="Relatório Externo (.xls):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.report_file_path = tk.StringVar(value="relatorio.xls")
        report_entry = ctk.CTkEntry(config_frame, textvariable=self.report_file_path, width=400)
        report_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(config_frame, text="Selecionar", command=lambda: self.select_file(self.report_file_path)).grid(row=2, column=2, padx=10, pady=5)

        # --- Seção 2: Controles e Status ---
        controls_frame = ctk.CTkFrame(self.main_frame)
        controls_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
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
        self.notebook.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

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
        self.export_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.export_frame.grid_remove() 
        
        ctk.CTkLabel(self.export_frame, text="Exportar Arquivo:", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkButton(self.export_frame, text="Exportar para .xlsx", command=lambda: self.export_file("xlsx")).grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkButton(self.export_frame, text="Exportar para .pdf", command=lambda: self.export_file("pdf")).grid(row=0, column=2, padx=10, pady=10)

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
        self.log("Painel de Controle iniciado. Pronto para operação.", "success")
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
            self.log("==================================================", "success")
            self.log("Iniciando novo ciclo de processamento via interface.", "success")
            self.update_status("Executando...", "orange")
            
            input_file = self.input_file_path.get()
            report_file = self.report_file_path.get()
            output_file = OUTPUT_FILE_PATH 

            run_main_process(input_file, report_file, output_file)
            
            self.log("Processamento concluído com sucesso!", "success")
            self.update_status("Concluído com Sucesso", "green")
            self.load_data_for_view()
            self.export_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
            messagebox.showinfo("Sucesso", "O processamento foi concluído e os resultados estão disponíveis para visualização e exportação.")

        except Exception as e:
            self.log(f"ERRO CRÍTICO DURANTE O PROCESSAMENTO: {str(e)}", "error")
            self.log("Verifique os logs detalhados para mais informações.", "error")
            self.update_status("Erro", "red")
            messagebox.showerror("Erro de Processamento", f"Ocorreu um erro durante a execução:\n\n{str(e)}")
        finally:
            self.progress_bar.grid_forget() 
            self.execute_button.configure(state=tk.NORMAL)
            self.log("==================================================\n", "success")

    def validate_inputs(self):
        """Valida se os arquivos de entrada existem."""
        input_file = self.input_file_path.get()
        report_file = self.report_file_path.get()

        if not os.path.exists(input_file):
            self.log(f"ERRO: Arquivo de entrada não encontrado: {input_file}", "error")
            messagebox.showerror("Erro de Arquivo", f"O arquivo de entrada não foi encontrado:\n{input_file}")
            return False
        if not os.path.exists(report_file):
            self.log(f"ERRO: Arquivo de relatório não encontrado: {report_file}", "error")
            messagebox.showerror("Erro de Arquivo", f"O arquivo de relatório não foi encontrado:\n{report_file}")
            return False
        return True

    def load_data_for_view(self):
        """Carrega os dados do arquivo de saída para as abas de visualização."""
        try:
            df_summary = pd.read_excel(OUTPUT_FILE_PATH, sheet_name='Resumo Consolidado', skiprows=2)
            if not df_summary.empty:
                self.display_dataframe(self.summary_tree, df_summary)
                self.log("Tabela 'Resumo Consolidado' carregada para visualização.", "info")

            df_details = pd.read_excel(OUTPUT_FILE_PATH, sheet_name='Resumo Consolidado', skiprows=2, header=None, skipcols=6)
            if not df_details.empty:
                detail_headers = ['Emissão', 'Mês', 'Transportadora', 'CTRC', 'Cliente', 'Serviço', 'Senha Ravex', 'DT Frete', 'Destino', 'Nota fiscal', 'Status Pgto', 'Valor CTe', 'Valor pago', 'Valor recebido']
                df_details.columns = detail_headers[:len(df_details.columns)]
                self.display_dataframe(self.details_tree, df_details)
                self.log("Tabela 'Detalhes de Pendências' carregada para visualização.", "info")
        except Exception as e:
            self.log(f"Não foi possível carregar os dados para visualização: {e}", "error")

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

        # Lista das colunas que esperamos valores monetários
        monetary_cols = ['Não compensado', 'Não lançado', 'Total Geral']
        
        for col in monetary_cols:
            if col in df_display.columns:
                try:
                    # Tenta converter a coluna para numérico.
                    # Erros e células vazias (NaN) se tornam 0.0
                    df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0.0)
                    
                    # Agora que é um número, aplica a formatação para string
                    df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                except Exception as e:
                    # Se algo der errado deixo a coluna como está (texto original)
                    # e aviso no log
                    self.log(f"Aviso: Não foi possível formatar a coluna '{col}'. Erro: {e}", "error")
                    # Tenta pelo menos limpar valores nulos para não quebrar a exibição
                    df_display[col] = df_display[col].fillna('')
        
        # Insere os dados no Treeview linha por linha
        for _, row in df_display.iterrows():
            tree.insert("", "end", values=list(row))

    def export_file(self, file_type):
        """Exporta o arquivo de saída para .xlsx ou .pdf."""
        if not os.path.exists(OUTPUT_FILE_PATH):
            messagebox.showwarning("Arquivo Não Encontrado", "O arquivo de saída ainda não foi gerado. Execute o processamento primeiro.")
            return

        if file_type == "xlsx":
            try:
                dest_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
                    initialfile="relatorio_final.xlsx"
                )
                if dest_path:
                    import shutil
                    shutil.copy(OUTPUT_FILE_PATH, dest_path)
                    self.log(f"Arquivo .xlsx exportado com sucesso para: {dest_path}", "success")
                    messagebox.showinfo("Exportação Bem-sucedida", f"O arquivo Excel foi salvo em:\n{dest_path}")
            except Exception as e:
                self.log(f"Erro ao exportar arquivo .xlsx: {e}", "error")
                messagebox.showerror("Erro de Exportação", f"Não foi possível exportar o arquivo .xlsx.\n\nErro: {e}")

        elif file_type == "pdf":
            try:
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                import pandas as pd

                dest_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
                    initialfile="relatorio_final.pdf"
                )
                
                if not dest_path:
                    return

                df_summary = pd.read_excel(OUTPUT_FILE_PATH, sheet_name='Resumo Consolidado', skiprows=2)
                
                if df_summary.empty:
                    messagebox.showwarning("Dados Vazios", "Não há dados na aba 'Resumo Consolidado' para gerar o PDF.")
                    return

                doc = SimpleDocTemplate(dest_path, pagesize=letter)
                elements = []
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=30,
                    alignment=1, # 1 = center
                    textColor=colors.darkblue
                )

                elements.append(Paragraph("RESUMO CONSOLIDADO DE TRANSPORTES", title_style))
                elements.append(Spacer(1, 12))

                df_display = df_summary.copy()
                monetary_cols = ['Não compensado', 'Não lançado', 'Total Geral']
                for col in monetary_cols:
                    if col in df_display.columns:
                        df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                table_data = [df_display.columns.tolist()] + df_display.values.tolist()
                
                table = Table(table_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
                ])
                table.setStyle(style)
                
                elements.append(table)
                elements.append(Spacer(1, 20))

                from datetime import datetime
                footer_text = f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                elements.append(Paragraph(footer_text, styles['Normal']))
                
                doc.build(elements)
                self.log(f"Arquivo .pdf exportado com sucesso para: {dest_path}", "success")
                messagebox.showinfo("Exportação Bem-sucedida", f"O arquivo PDF foi salvo em:\n{dest_path}")

            except Exception as e:
                self.log(f"Erro ao exportar arquivo .pdf: {e}", "error")
                messagebox.showerror("Erro de Exportação", f"Não foi possível exportar o arquivo .PDF.\n\nErro: {e}")

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = App()
    app.mainloop()