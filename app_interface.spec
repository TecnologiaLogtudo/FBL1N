# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# ==============================================================================
# INÍCIO DAS ALTERAÇÕES
# ==============================================================================

# 1. Adicione a importação do módulo 'os'
import os

# 2. Defina o caminho correto para a biblioteca customtkinter no seu VENV
#    Copie e cole o caminho que você obteu no passo anterior.
#    IMPORTANTE: Mantenha o 'r' no início para tratar como uma "raw string".
customtkinter_path = r"C:\Users\felip\OneDrive\Logtudo\Automações\Notas_Compensadas\.venv\Lib\site-packages\customtkinter"

# ==============================================================================
# FIM DAS ALTERAÇÕES
# ==============================================================================

a = Analysis(
    ['app_interface.py'],
    pathex=[],
    # 3. Use a variável 'customtkinter_path' aqui.
    binaries=[(customtkinter_path, 'customtkinter')], # <--- LINHA ALTERADA
    datas=[('config.py', '.'), ('utils.py', '.'), ('main.py', '.'), ('data_processor.py', '.'), ('report_processor.py', '.'), ('analysis_processor.py', '.'), ('final_report_generator.py', '.')],
    hiddenimports=[
        'customtkinter', 
        'tkinter.font', 
        'tkinter.ttk',
        'reportlab',
        'reportlab.platypus',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
    ], # Mantenha esta linha
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Resumo CTe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)