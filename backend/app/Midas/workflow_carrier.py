import os
from playwright.sync_api import sync_playwright
from .spreadsheet_processor import MidasSpreadsheetProcessor

class MidasCarrierWorkflow:
    def __init__(self, username: str = "SEU_USUARIO", password: str = "SUA_SENHA", starting_date: str = "05/03/2026", ending_date: str = "20/03/2026", headless: bool = True):
        self.username = username
        self.password = password
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.headless = headless
        # URL base com os parâmetros solicitados
        self.target_url = "https://nixweb.midassolutions.com.br/028/web/Account/Login?ReturnUrl=%2f028%2fweb%2fCarrierManagementPanel%2f%3fdateType%3dE%26startingDate%3d24%252F01%252F2023%26endingDate%3d08%252F02%252F2023%26status%3dF%252CA%252CR%26chk_status_1%3dF%26chk_status_2%3dA%26chk_status_3%3dR&dateType=E&startingDate=24%2F01%2F2023&endingDate=08%2F02%2F2023&status=F%2CA%2CR&chk_status_1=F&chk_status_2=A&chk_status_3=R"

    def run(self) -> str:
        """
        Inicia o fluxo acessando a URL via Playwright, realiza o preenchimento 
        do login e prepara a chamada para o mapeador.
        """
        print(f"Iniciando navegador com Playwright e acessando a URL configurada...")
        
        with sync_playwright() as p:
            # Controlado pelo parâmetro 'headless' no __init__
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            page.goto(self.target_url)
            
            print("Aguardando a página de login renderizar...")
            page.wait_for_selector("input#UserName", state="visible")
            
            print("Página de login carregada. Preenchendo credenciais...")
            
            # Preenche os campos usando os seletores de ID fornecidos
            page.fill("input#UserName", self.username)
            page.fill("input#Password", self.password)
            
            # Pressiona "Enter" estando no campo de senha para fazer o login
            page.press("input#Password", "Enter")
            
            print("Login submetido! Aguardando o redirecionamento...")
            
            try:
                print("Aguardando a tela do painel renderizar...")
                # Tenta aguardar a tela do painel com um timeout menor (ex: 8000ms = 8 segundos)
                page.wait_for_selector("select#dateType", state="visible", timeout=8000)
            except Exception:
                print("Fallback: O login via 'Enter' falhou. Tentando clicar no botão de Entrar...")
                # Busca por seletores comuns para botões de submissão/login e clica no primeiro encontrado
                page.locator("button[type='submit'], input[type='submit'], input[value='Entrar']").first.click()
                # Aguarda novamente pelo elemento da próxima tela com o tempo padrão do Playwright (30s)
                page.wait_for_selector("select#dateType", state="visible")
                
            # Garante que a rede esteja ociosa antes de prosseguir com os preenchimentos
            page.wait_for_load_state("networkidle")
            
            print("Preenchendo os filtros de pesquisa...")
            # Seleciona 'Envio' (valor 'C') no dropdown Período por
            page.select_option("select#dateType", value="C")
            
            # Preenche a Data Inicial
            page.fill("input#startingDate", self.starting_date)
            
            # Preenche a Data Final
            page.fill("input#endingDate", self.ending_date)

            print("Aguardando 2 segundos antes de pesquisar...")
            page.wait_for_timeout(2000)

            print("Clicando no botão Pesquisar...")
            # Clica no botão de pesquisar
            page.click("input#searchForm_submit")
            
            # Aguarda a atualização da tabela/grid após a pesquisa
            page.wait_for_load_state("networkidle")

            print("Iniciando a exportação do relatório...")
            # Prepara o Playwright para interceptar o download disparado pelo clique
            with page.expect_download() as download_info:
                page.click("input[value='Exportar']")
            
            download = download_info.value
            
            # Prepara a pasta 'temp' dentro do diretório atual (app/Midas/temp)
            temp_dir = os.path.join(os.path.dirname(__file__), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Salva o arquivo usando o nome sugerido pelo próprio navegador/servidor
            file_path = os.path.join(temp_dir, download.suggested_filename)
            download.save_as(file_path)
            print(f"Relatório exportado e salvo com sucesso em: {file_path}")

            # Mantém o navegador aberto até que o usuário pressione ENTER no terminal
            print("\nFluxo de automação concluído. O navegador permanecerá aberto.")
            input("Pressione [ENTER] neste terminal para fechar o navegador e encerrar o script... ")
        
            # Delega o tratamento da planilha e mapeamento para a classe separada
            canonical_json = MidasSpreadsheetProcessor.process_and_map(file_path)
            
            browser.close()
            return canonical_json

if __name__ == "__main__":
    # Aqui passamos headless=False para que você consiga ver o navegador preenchendo os dados no teste!
    workflow = MidasCarrierWorkflow(username="JOYCE.RAIANE", password="Joyce123@", starting_date="05/03/2026", ending_date="20/03/2026", headless=False)
    resultado = workflow.run()
    print("\nResultado do JSON Canônico gerado:")
    print(resultado)