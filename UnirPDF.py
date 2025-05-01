import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PyPDF2 import PdfMerger
import shutil
import re
import unicodedata

CAMINHO_BANCO = r"C:\Users\5132\OneDrive - Clube Paineiras do Morumby\Área de Trabalho\UnirPDF\BancoDeNomes.txt"

def normalizar(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode().lower()

def carregar_nomes():
    try:
        with open(CAMINHO_BANCO, 'r', encoding='utf-8') as f:
            return [linha.strip() for linha in f if linha.strip()]
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Banco de nomes não encontrado:\n{CAMINHO_BANCO}")
        return []

def extrair_nome(arquivo, nomes_banco):
    nome_arquivo_normalizado = normalizar(arquivo)
    for nome in nomes_banco:
        nome_normalizado = normalizar(nome)
        padrao = r'\b' + re.escape(nome_normalizado) + r'\b'
        if re.search(padrao, nome_arquivo_normalizado):
            return nome  # nome original do banco
    return None

def nome_valido(nome):
    return re.match(r'^\d+(?:\.\d+)+', nome) is not None

def extrair_prefixo_numero(nome):
    match = re.match(r'^(\d+(?:\.\d+)+)', nome)
    if match:
        return [int(x) for x in match.group(1).split('.')]
    return [float('inf')]

def limpar_nome_arquivo(nome):
    nome = re.sub(r'[\\/*?:"<>|]', '', nome)  # Remove caracteres inválidos
    return nome[:150]  # Limita tamanho do nome do arquivo

def processar_pasta(pasta, nomes_banco, nomes_selecionados):
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf") and nome_valido(f)]
    agrupados = {}

    for arq in arquivos:
        nome = extrair_nome(arq, nomes_banco)
        if nome and nome in nomes_selecionados:
            agrupados.setdefault(nome, []).append(arq)

    for pessoa, lista in agrupados.items():
        lista.sort(key=extrair_prefixo_numero)
        merger = PdfMerger()
        apontamentos = []

        for arq in lista:
            caminho_pdf = os.path.join(pasta, arq)
            merger.append(caminho_pdf)
            if "apontamento" in arq.lower():
                cod = re.search(r'\d+(?:\.\d+)*', arq)
                if cod:
                    apontamentos.append(cod.group())

        nome_arquivo = f"Certidões de buscas - {pessoa}"
        if apontamentos:
            nome_arquivo += " - APONTAMENTO " + " E ".join(apontamentos)
        nome_arquivo = limpar_nome_arquivo(nome_arquivo) + ".pdf"

        caminho_final = os.path.join(pasta, nome_arquivo)
        merger.write(caminho_final)
        merger.close()

        # Move originais para pasta Avulsas
        destino = os.path.join(pasta, "Avulsas")
        os.makedirs(destino, exist_ok=True)
        for arq in lista:
            shutil.move(os.path.join(pasta, arq), os.path.join(destino, arq))

def escolher_nomes_encontrados(nomes_encontrados):
    janela_sel = tk.Toplevel()
    janela_sel.title("Selecione os nomes que deseja processar")
    janela_sel.geometry("200x500")

    frame_container = tk.Frame(janela_sel)
    frame_container.pack(fill="both", expand=True)

    canvas = tk.Canvas(frame_container)
    scrollbar = tk.Scrollbar(frame_container, orient="vertical", command=canvas.yview)
    frame_checkboxes = tk.Frame(canvas)

    frame_checkboxes.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=frame_checkboxes, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    selecionados = []
    vars_check = []

    for nome in nomes_encontrados:
        var = tk.BooleanVar()
        chk = tk.Checkbutton(frame_checkboxes, text=nome, variable=var, anchor="w", justify="left", wraplength=450)
        chk.pack(fill="x", padx=5, pady=2)
        vars_check.append(var)

    def confirmar():
        for i, var in enumerate(vars_check):
            if var.get():
                selecionados.append(nomes_encontrados[i])
        janela_sel.destroy()

    btn = tk.Button(janela_sel, text="Confirmar", command=confirmar)
    btn.pack(pady=10)

    janela_sel.transient(janela)
    janela_sel.grab_set()
    janela.wait_window(janela_sel)
    return selecionados


def processar_tudo():
    nomes_banco = carregar_nomes()
    if not nomes_banco:
        return

    if not pastas_selecionadas:
        messagebox.showwarning("Atenção", "Nenhuma pasta selecionada.")
        return

    for pasta in pastas_selecionadas:
        arquivos = [f for f in os.listdir(pasta) if f.lower().endswith('.pdf')]
        nomes_encontrados = sorted(set(
            extrair_nome(f, nomes_banco)
            for f in arquivos if extrair_nome(f, nomes_banco)
        ))

        if not nomes_encontrados:
            messagebox.showinfo("Atenção", f"Nenhum nome reconhecido na pasta:\n{pasta}")
            continue

        nomes_escolhidos = escolher_nomes_encontrados(nomes_encontrados)
        if nomes_escolhidos:
            processar_pasta(pasta, nomes_banco, nomes_escolhidos)

    messagebox.showinfo("Sucesso", "Certidões juntadas com sucesso!")

def ao_selecionar(event):
    lista_arquivos.delete(0, tk.END)
    sel = lista_pastas.curselection()
    if not sel:
        return
    caminho = lista_pastas.get(sel[0])
    arquivos = [f for f in os.listdir(caminho) if f.lower().endswith('.pdf')]
    for arq in arquivos:
        lista_arquivos.insert(tk.END, arq)

def selecionar_pasta():
    root = tk.Tk()
    root.withdraw()
    pasta = filedialog.askdirectory(title="Selecione a pasta das certidões", mustexist=True)
    if not pasta:
        return

    pastas_selecionadas.clear()
    lista_pastas.delete(0, tk.END)
    lista_arquivos.delete(0, tk.END)

    pastas_selecionadas.append(pasta)
    lista_pastas.insert(tk.END, pasta)

# INTERFACE
janela = tk.Tk()
janela.title("Juntar Certidões por Pessoa")
janela.geometry("800x500")

pastas_selecionadas = []

topo = tk.Frame(janela)
topo.pack(pady=10)

btn_pasta = tk.Button(topo, text="Selecionar Pasta de Certidões", command=selecionar_pasta)
btn_pasta.pack()

corpo = tk.Frame(janela)
corpo.pack(pady=10, fill="both", expand=True)

lista_pastas = tk.Listbox(corpo, width=60, height=20)
lista_pastas.pack(side=tk.LEFT, padx=10, fill="both", expand=True)
lista_pastas.bind("<<ListboxSelect>>", ao_selecionar)

lista_arquivos = tk.Listbox(corpo, width=60, height=20)
lista_arquivos.pack(side=tk.RIGHT, padx=10, fill="both", expand=True)

btn_juntar = tk.Button(janela, text="Juntar Certidões", bg="green", fg="white",
                       font=("Arial", 12, "bold"), command=processar_tudo)
btn_juntar.pack(pady=15)

janela.mainloop()