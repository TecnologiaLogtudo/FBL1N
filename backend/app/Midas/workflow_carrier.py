from __future__ import annotations

import asyncio
from pathlib import Path

from .playwright_runtime import AsyncPlaywrightRuntimeClient, PlaywrightRuntimeConfig

class MidasCarrierWorkflow:
    def __init__(
        self,
        username: str = "SEU_USUARIO",
        password: str = "SUA_SENHA",
        starting_date: str = "05/03/2026",
        ending_date: str = "20/03/2026",
        headless: bool = True,
        *,
        runtime_mode: str = "auto",
        timeout_ms: int | None = None,
        viewport_width: int | None = None,
        viewport_height: int | None = None,
        locale: str | None = None,
        user_agent: str | None = None,
        browser_args: str | None = None,
        download_dir: str | None = None,
        target_url: str | None = None,
    ):
        self.username = username
        self.password = password
        self.starting_date = starting_date
        self.ending_date = ending_date
        self.headless = headless
        self.runtime_config = PlaywrightRuntimeConfig.from_env(
            headless=headless,
            runtime_mode=runtime_mode,
            timeout_ms=timeout_ms,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            locale=locale,
            user_agent=user_agent,
            browser_args=browser_args,
        )
        self.download_dir = Path(download_dir) if download_dir else Path(__file__).resolve().parent / "temp"
        # URL base com os parâmetros solicitados
        self.target_url = target_url or (
            "https://nixweb.midassolutions.com.br/028/web/Account/Login"
            "?ReturnUrl=%2f028%2fweb%2fCarrierManagementPanel%2f%3fdateType%3dE%26startingDate%3d24%252F01%252F2023"
            "%26endingDate%3d08%252F02%252F2023%26status%3dF%252CA%252CR%26chk_status_1%3dF%26chk_status_2%3dA%26chk_status_3%3dR"
            "&dateType=E&startingDate=24%2F01%2F2023&endingDate=08%2F02%2F2023&status=F%2CA%2CR&chk_status_1=F&chk_status_2=A&chk_status_3=R"
        )

    async def run(self) -> str:
        """
        Inicia o fluxo acessando a URL via Playwright, realiza o preenchimento 
        do login e prepara a chamada para o mapeador.
        """
        print(
            f"Iniciando Playwright Async (modo={self.runtime_config.resolved_mode()}, "
            f"headless={self.runtime_config.headless})..."
        )

        async with AsyncPlaywrightRuntimeClient(self.runtime_config) as client:
            page = client.page
            if page is None:
                raise RuntimeError("Falha ao inicializar página do Playwright.")

            try:
                await page.goto(self.target_url, wait_until="domcontentloaded")
                print("Aguardando a página de login renderizar...")
                await page.wait_for_selector("input#UserName", state="visible")

                print("Página de login carregada. Preenchendo credenciais...")
                await page.fill("input#UserName", self.username)
                await page.fill("input#Password", self.password)
                await page.press("input#Password", "Enter")
                print("Login submetido! Aguardando o redirecionamento...")

                try:
                    await page.wait_for_selector("select#dateType", state="visible", timeout=8000)
                except Exception:
                    print("Fallback: submit por Enter falhou. Tentando clique no botão Entrar...")
                    await page.locator("button[type='submit'], input[type='submit'], input[value='Entrar']").first.click()
                    await page.wait_for_selector("select#dateType", state="visible")

                await page.wait_for_load_state("networkidle")
                print("Preenchendo os filtros de pesquisa...")
                await page.select_option("select#dateType", value="C")
                await page.fill("input#startingDate", self.starting_date)
                await page.fill("input#endingDate", self.ending_date)
                await page.wait_for_timeout(2000)
                await page.click("input#searchForm_submit")
                await page.wait_for_load_state("networkidle")

                print("Iniciando a exportação do relatório...")
                async with page.expect_download() as download_info:
                    await page.click("input[value='Exportar']")
                download = await download_info.value

                self.download_dir.mkdir(parents=True, exist_ok=True)
                file_path = self.download_dir / download.suggested_filename
                await download.save_as(str(file_path))
                print(f"Relatório exportado e salvo com sucesso em: {file_path}")
                return str(file_path)
            except Exception as exc:
                raise RuntimeError(f"Falha no workflow Midas durante login/exportação: {exc}") from exc

if __name__ == "__main__":
    # Aqui passamos headless=False para depuração visual.
    workflow = MidasCarrierWorkflow(
        username="SEU_USUARIO",
        password="SUA_SENHA",
        starting_date="05/03/2026",
        ending_date="20/03/2026",
        headless=False,
    )
    arquivo = asyncio.run(workflow.run())
    print("\nArquivo bruto gerado:")
    print(arquivo)
