import os
import re
import unicodedata
import streamlit as st
from PyPDF2 import PdfMerger
from tempfile import TemporaryDirectory

# Caminho para o banco (deve estar no mesmo repositório que este script)
CAMINHO_BANCO = "BancoDeNomes.txt"

def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode().lower()

def carregar_nomes():
    try:
        with open(CAMINHO_BANCO, 'r', encoding='utf-8') as f:
            return [linha.strip() for linha in f if linha.strip()]
    except FileNotFoundError:
        st.error("Arquivo 'BancoDeNomes.txt' não encontrado.")
        return []

def extrair_nome(arquivo, nomes_banco):
    nome_arquivo_normalizado = normalizar(arquivo)
    for nome in nomes_banco:
        nome_normalizado = normalizar(nome)
        padrao = r'\b' + re.escape(nome_normalizado) + r'\b'
        if re.search(padrao, nome_arquivo_normalizado):
            return nome
    return None

def nome_valido(nome):
    return re.match(r'^\d+(?:\.\d+)+', nome) is not None

def extrair_prefixo_numero(nome):
    match = re.match(r'^(\d+(?:\.\d+)+)', nome)
    if match:
        return [int(x) for x in match.group(1).split('.')]
    return [float('inf')]

def limpar_nome_arquivo(nome):
    nome = re.sub(r'[\\/*?:"<>|]', '', nome)
    return nome[:150]

def processar_arquivos(uploaded_files, nomes_banco, nomes_selecionados):
    agrupados = {}
    with TemporaryDirectory() as tempdir:
        for file in uploaded_files:
            if file.name.lower().endswith(".pdf") and nome_valido(file.name):
                nome = extrair_nome(file.name, nomes_banco)
                if nome and nome in nomes_selecionados:
                    agrupados.setdefault(nome, []).append(file)

        for pessoa, arquivos in agrupados.items():
            arquivos.sort(key=lambda f: extrair_prefixo_numero(f.name))
            merger = PdfMerger()
            apontamentos = []

            for arq in arquivos:
                temp_path = os.path.join(tempdir, arq.name)
                with open(temp_path, "wb") as f:
                    f.write(arq.read())
                merger.append(temp_path)
                if "apontamento" in arq.name.lower():
                    cod = re.search(r'\d+(?:\.\d+)*', arq.name)
                    if cod:
                        apontamentos.append(cod.group())

            nome_arquivo = f"Certidões de buscas - {pessoa}"
            if apontamentos:
                nome_arquivo += " - APONTAMENTO " + " E ".join(apontamentos)
            nome_arquivo = limpar_nome_arquivo(nome_arquivo) + ".pdf"

            out_path = os.path.join(tempdir, nome_arquivo)
            merger.write(out_path)
            merger.close()

            with open(out_path, "rb") as f:
                st.download_button(
                    label=f"📥 Baixar: {nome_arquivo}",
                    data=f,
                    file_name=nome_arquivo,
                    mime="application/pdf"
                )

# === INTERFACE STREAMLIT ===
st.title("📎 Juntar Certidões por Pessoa")
st.markdown("Faça o upload dos PDFs e o script irá agrupá-los com base nos nomes do arquivo 'BancoDeNomes.txt'.")

uploaded_files = st.file_uploader("Envie os arquivos PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    nomes_banco = carregar_nomes()
    nomes_encontrados = sorted(set(
        extrair_nome(f.name, nomes_banco)
        for f in uploaded_files if extrair_nome(f.name, nomes_banco)
    ))

    if nomes_encontrados:
        nomes_selecionados = st.multiselect("Selecione os nomes para juntar os PDFs:", nomes_encontrados)
        if st.button("🔄 Juntar PDFs") and nomes_selecionados:
            processar_arquivos(uploaded_files, nomes_banco, nomes_selecionados)
    else:
        st.warning("Nenhum nome reconhecido entre os arquivos enviados.")
