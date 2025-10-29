"""
Created on Tue Mar  4 20:42:40 2025

@author: pjuli
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import csv
import json
from typing import Dict, List, Optional, Iterable, Tuple

# Variáveis globais com type hints
checkbox_vars: Dict[int, tk.BooleanVar] = {}   # chave: índice da sequência
sequencias: List[List[str]] = []                # lista de sequências (cada sequência é uma lista de strings)
indices_exibidos: List[int] = []                # índices atualmente exibidos (ex: após uma busca)
current_theme: str = "claro"                    # (não utilizado nesta versão)

def detectar_material(seq: str) -> str:
    """
    Determina o tipo do material genético do corpo da sequência.
    Ignora os símbolos '-' e analisa somente os caracteres.
    Retorna "DNA" se os caracteres forem apenas A, C, G, T;
    "RNA" se forem apenas A, C, G, U; caso contrário, retorna "ERRO".
    """
    cleaned: str = seq.replace("-", "").upper()
    if not cleaned:
        return "ERRO"
    allowed_dna: set[str] = set("ACGT")
    allowed_rna: set[str] = set("ACGU")
    if set(cleaned) <= allowed_dna:
        return "DNA"
    if set(cleaned) <= allowed_rna:
        return "RNA"
    return "ERRO"

def abrir_arquivo(entry_caminho: tk.Entry, canvas: tk.Canvas, scrollable_frame: tk.Frame) -> None:
    """
    Abre múltiplos arquivos e carrega as sequências de cada um deles.
    Permite selecionar arquivos FASTA (*.fasta, *.fa) e TXT.
    Exibe os caminhos dos arquivos selecionados no entry e atualiza a exibição.
    """
    caminhos: Tuple[str, ...] = filedialog.askopenfilenames(
        filetypes=[
            ("FASTA files", "*.fasta *.fa"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
    )
    if caminhos:
        entry_caminho.delete(0, tk.END)
        entry_caminho.insert(0, "; ".join(caminhos))
        sequencias.clear()
        for caminho in caminhos:
            sequencias.extend(ler_sequencias(caminho))
        exibir_sequencias(scrollable_frame, sequencias)

def ler_sequencias(caminho_arquivo: str) -> List[List[str]]:
    """Lê sequências de um arquivo (formato FASTA ou similar)."""
    lista_sequencias: List[List[str]] = []
    with open(caminho_arquivo, "r") as arquivo:
        lista_atual: List[str] = []
        for linha in arquivo:
            linha = linha.strip()
            if linha.startswith(">"):
                if lista_atual:
                    lista_sequencias.append(lista_atual)
                lista_atual = [linha]
            else:
                lista_atual.append(linha)
        if lista_atual:
            lista_sequencias.append(lista_atual)
    return lista_sequencias

def ver_mais(seq_str: str) -> None:
    """
    Abre uma janela (Toplevel) mostrando a sequência completa em um ScrolledText.
    """
    top: tk.Toplevel = tk.Toplevel()
    top.title("Sequência Completa")
    text_area: scrolledtext.ScrolledText = scrolledtext.ScrolledText(top, wrap=tk.WORD, width=80, height=20)
    text_area.pack(fill="both", expand=True)
    text_area.insert("1.0", seq_str)
    text_area.configure(state="disabled")

def exibir_sequencias(scrollable_frame: tk.Frame, sequencias: List[List[str]], indices: Optional[Iterable[int]] = None) -> None:
    """
    Exibe as sequências no frame de forma organizada, mostrando apenas parte delas,
    incluindo botão "Ver mais" e o tipo do material genético (DNA, RNA ou ERRO).
    Atualiza a variável global 'indices_exibidos' com os índices atualmente exibidos.
    """
    global indices_exibidos
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    if indices is None:
        indices = range(len(sequencias))
    indices_exibidos = list(indices)

    for idx in indices_exibidos:
        seq: List[str] = sequencias[idx]
        header: str = seq[0]
        seq_str: str = "".join(seq[1:])
        
        seq_frame: tk.Frame = tk.Frame(scrollable_frame, bd=1, relief="solid", padx=5, pady=5)
        seq_frame.pack(fill="x", padx=5, pady=5)
        
        if idx not in checkbox_vars:
            checkbox_vars[idx] = tk.BooleanVar()
        var: tk.BooleanVar = checkbox_vars[idx]
        
        chk: tk.Checkbutton = tk.Checkbutton(seq_frame, variable=var)
        chk.grid(row=0, column=0, rowspan=2, sticky="n", padx=5)
        
        lbl_header: tk.Label = tk.Label(seq_frame, text=header, fg="blue", font=("Helvetica", 10, "bold"))
        lbl_header.grid(row=0, column=1, sticky="w", padx=5)
        
        max_chars: int = 100
        if len(seq_str) > max_chars:
            truncated_seq: str = seq_str[:max_chars] + "..."
        else:
            truncated_seq = seq_str
        
        lbl_seq: tk.Label = tk.Label(seq_frame, text=truncated_seq, wraplength=600, justify="left")
        lbl_seq.grid(row=1, column=1, sticky="w", padx=5)
        
        if len(seq_str) > max_chars:
            btn_ver_mais: tk.Button = tk.Button(seq_frame, text="Ver mais", command=lambda s=seq_str: ver_mais(s))
            btn_ver_mais.grid(row=1, column=2, sticky="w", padx=5)
        
        tipo: str = detectar_material(seq_str)
        lbl_tipo: tk.Label = tk.Label(seq_frame, text=f"Tipo: {tipo}", fg="green", font=("Helvetica", 9))
        lbl_tipo.grid(row=2, column=1, sticky="w", padx=5)

def buscar_sequencia(entry_busca: tk.Entry, scrollable_frame: tk.Frame) -> None:
    """
    Busca por uma sequência, parte do header ou pelo tipo do material genético,
    permitindo múltiplos termos (a busca funciona com um AND: todos os tokens devem ser encontrados em header, sequência ou tipo).
    Se nenhum resultado for encontrado, exibe uma mensagem e retorna para a exibição de todas as sequências.
    """
    termo: str = entry_busca.get().strip().lower()
    if not termo:
        exibir_sequencias(scrollable_frame, sequencias)
        return

    tokens: List[str] = termo.split()
    indices_filtrados: List[int] = []
    for idx, seq in enumerate(sequencias):
        header_text: str = seq[0].lower()
        sequence_text: str = "".join(seq[1:]).lower()
        type_text: str = detectar_material("".join(seq[1:])).lower()
        if all(token in header_text or token in sequence_text or token in type_text for token in tokens):
            indices_filtrados.append(idx)

    if not indices_filtrados:
        messagebox.showinfo("Busca", "Nenhuma sequência ou header encontrado com os termos informados. Exibindo todas as sequências.")
        exibir_sequencias(scrollable_frame, sequencias)
    else:
        exibir_sequencias(scrollable_frame, sequencias, indices=indices_filtrados)

def salvar_selecoes(entry_caminho: tk.Entry, formato: str) -> None:
    """
    Salva as sequências selecionadas em arquivo, considerando apenas os itens atualmente exibidos.
    Suporta exportar para os formatos: FASTA, TXT, CSV e JSON.
    """
    caminho_arquivo: str = entry_caminho.get()
    if not caminho_arquivo:
        messagebox.showerror("Erro", "Nenhum arquivo selecionado.")
        return

    sequencias_selecionadas: List[List[str]] = []
    for idx in indices_exibidos:
        if idx in checkbox_vars and checkbox_vars[idx].get():
            sequencias_selecionadas.append(sequencias[idx])

    if not sequencias_selecionadas:
        messagebox.showinfo("Informação", "Nenhuma sequência selecionada.")
        return

    opcao: bool = messagebox.askyesno("Opção",
        "Deseja salvar as sequências selecionadas em um único arquivo? (Sim) ou em múltiplos arquivos? (Não)")
    pasta_saida: str = filedialog.askdirectory(title="Escolha a pasta para salvar os arquivos")
    if not pasta_saida:
        messagebox.showerror("Erro", "Nenhuma pasta selecionada.")
        return

    if formato.upper() in ("FASTA", "TXT"):
        ext: str = ".fasta" if formato.upper() == "FASTA" else ".txt"
        def escrever(seq: List[str]) -> str:
            header: str = seq[0]
            corpo: str = "\n".join(seq[1:])
            return f"{header}\n{corpo}\n"
    elif formato.upper() == "CSV":
        ext = ".csv"
        def escrever(seq: List[str]) -> Tuple[str, str, str]:
            header = seq[0]
            corpo = "".join(seq[1:])
            tipo = detectar_material(corpo)
            return (header, corpo, tipo)
    elif formato.upper() == "JSON":
        ext = ".json"
    else:
        messagebox.showerror("Erro", "Formato de saída não suportado.")
        return

    if opcao:
        caminho_saida: str = os.path.join(pasta_saida, f"sequencias_selecionadas{ext}")
        if formato.upper() in ("FASTA", "TXT"):
            with open(caminho_saida, "w") as saida:
                for seq in sequencias_selecionadas:
                    saida.write(escrever(seq))
        elif formato.upper() == "CSV":
            with open(caminho_saida, "w", newline="") as saida:
                writer = csv.writer(saida)
                writer.writerow(["Header", "Sequence", "Type"])
                for seq in sequencias_selecionadas:
                    writer.writerow(escrever(seq))
        elif formato.upper() == "JSON":
            lista_json = []
            for seq in sequencias_selecionadas:
                header = seq[0]
                corpo = "".join(seq[1:])
                tipo = detectar_material(corpo)
                lista_json.append({"header": header, "sequence": corpo, "type": tipo})
            with open(caminho_saida, "w") as saida:
                json.dump(lista_json, saida, indent=4)
        messagebox.showinfo("Informação", f"Sequências salvas em '{caminho_saida}'.")
    else:
        for i, seq in enumerate(sequencias_selecionadas, start=1):
            nome_arquivo: str = os.path.join(pasta_saida, f"sequencia_{i}{ext}")
            if formato.upper() in ("FASTA", "TXT"):
                with open(nome_arquivo, "w") as saida:
                    saida.write(escrever(seq))
            elif formato.upper() == "CSV":
                with open(nome_arquivo, "w", newline="") as saida:
                    writer = csv.writer(saida)
                    writer.writerow(["Header", "Sequence", "Type"])
                    writer.writerow(escrever(seq))
            elif formato.upper() == "JSON":
                header = seq[0]
                corpo = "".join(seq[1:])
                tipo = detectar_material(corpo)
                with open(nome_arquivo, "w") as saida:
                    json.dump({"header": header, "sequence": corpo, "type": tipo}, saida, indent=4)
        messagebox.showinfo("Informação", f"Sequências salvas na pasta '{pasta_saida}'.")

def processar_gaps(lista_sequencias: List[List[str]], metodo: str) -> List[List[str]]:
    """
    Processa os gaps das sequências de acordo com o método escolhido.
    método "manter": mantém os gaps como '-'
    método "substituir": substitui '-' por 'N'
    método "remover": remove todos os '-' da sequência.
    """
    resultado: List[List[str]] = []
    for seq in lista_sequencias:
        header: str = seq[0]
        corpo: str = "".join(seq[1:])
        if metodo == "manter":
            novo_corpo = corpo
        elif metodo == "substituir":
            novo_corpo = corpo.replace("-", "N")
        elif metodo == "remover":
            novo_corpo = corpo.replace("-", "")
        else:
            novo_corpo = corpo
        resultado.append([header, novo_corpo])
    return resultado

def aplicar_opcoes(metodo: str, janela_opcoes: tk.Toplevel, scrollable_frame: tk.Frame) -> None:
    """Aplica a opção selecionada para tratamento de gaps."""
    global sequencias
    sequencias = processar_gaps(sequencias, metodo)
    messagebox.showinfo("Informação", f"Gaps processados com o método: {metodo}.")
    janela_opcoes.destroy()
    exibir_sequencias(scrollable_frame, sequencias)

def abrir_janela_opcoes(scrollable_frame: tk.Frame) -> None:
    
    janela_opcoes: tk.Toplevel = tk.Toplevel()
    janela_opcoes.title("Configurações de Gaps")
    janela_opcoes.geometry("300x250")

    label_info: tk.Label = tk.Label(
        janela_opcoes,
        text="Como os gaps estão sendo tratados atualmente:\n'-'\nSelecione uma opção para tratar gaps:"
    )
    label_info.pack(pady=10)

    gap_method_var: tk.StringVar = tk.StringVar(value="manter")
    rb_manter: tk.Radiobutton = tk.Radiobutton(
        janela_opcoes, text="Manter '-' (Padrão)", variable=gap_method_var, value="manter"
    )
    rb_manter.pack(anchor="w", padx=20, pady=5)
    rb_substituir: tk.Radiobutton = tk.Radiobutton(
        janela_opcoes, text="Substituir por 'N'", variable=gap_method_var, value="substituir"
    )
    rb_substituir.pack(anchor="w", padx=20, pady=5)
    rb_remover: tk.Radiobutton = tk.Radiobutton(
        janela_opcoes, text="Remover gaps", variable=gap_method_var, value="remover"
    )
    rb_remover.pack(anchor="w", padx=20, pady=5)

    btn_aplicar: tk.Button = tk.Button(
        janela_opcoes, text="Aplicar",
        command=lambda: aplicar_opcoes(gap_method_var.get(), janela_opcoes, scrollable_frame)
    )
    btn_aplicar.pack(pady=10)

def abrir_visao_geral() -> None:
    """
    Abre uma janela de visão geral, exibindo a quantidade total de sequências,
    o tamanho de cada uma e o tipo de material genético.
    """
    janela_visao: tk.Toplevel = tk.Toplevel()
    janela_visao.title("Visão Geral")
    janela_visao.geometry("400x300")
    
    total: int = len(sequencias)
    summary: str = f"Número total de sequências: {total}\n\n"
    for i, seq in enumerate(sequencias, start=1):
        header: str = seq[0]
        corpo: str = "".join(seq[1:])
        tamanho: int = len(corpo)
        tipo: str = detectar_material(corpo)
        summary += f"Seq {i}: {header}\n   Tamanho: {tamanho} | Tipo: {tipo}\n\n"
    
    text_area: scrolledtext.ScrolledText = scrolledtext.ScrolledText(janela_visao, wrap=tk.WORD, width=50, height=15)
    text_area.pack(fill="both", expand=True, padx=10, pady=10)
    text_area.insert("1.0", summary)
    text_area.configure(state="disabled")

def main() -> None:
    global sequencias, root
    root = tk.Tk()
    root.title("Sequence Handler")

    menubar: tk.Menu = tk.Menu(root)
    root.config(menu=menubar)

    # Menu Arquivo
    file_menu: tk.Menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Arquivo", menu=file_menu)
    file_menu.add_command(label="Abrir", command=lambda: abrir_arquivo(entry_caminho, canvas, scrollable_frame))
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=root.quit)

    # Menu Opções (somente Configurações e Visão Geral)
    options_menu: tk.Menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Opções", menu=options_menu)
    options_menu.add_command(label="Configurações", command=lambda: abrir_janela_opcoes(scrollable_frame))
    options_menu.add_separator()
    options_menu.add_command(label="Visão Geral", command=abrir_visao_geral)

    # Menu Ajuda
    help_menu: tk.Menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre", command=lambda: messagebox.showinfo("Sobre", "Sequence Handler v1.0"))

    # Frame para seleção de arquivo e checkbox "Selecionar Tudo"
    frame_entrada: tk.Frame = tk.Frame(root)
    frame_entrada.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    label_caminho: tk.Label = tk.Label(frame_entrada, text="Caminho do arquivo:")
    label_caminho.grid(row=0, column=0, padx=5, pady=5)

    entry_caminho: tk.Entry = tk.Entry(frame_entrada, width=50)
    entry_caminho.grid(row=0, column=1, padx=5, pady=5)

    botao_abrir: tk.Button = tk.Button(
        frame_entrada, text="Abrir Arquivo",
        command=lambda: abrir_arquivo(entry_caminho, canvas, scrollable_frame)
    )
    botao_abrir.grid(row=0, column=2, padx=5, pady=5)

    master_select_var: tk.BooleanVar = tk.BooleanVar(value=False)
    def toggle_select_all() -> None:
        for idx in indices_exibidos:
            if idx in checkbox_vars:
                checkbox_vars[idx].set(master_select_var.get())
    cb_selecionar_tudo: tk.Checkbutton = tk.Checkbutton(
        frame_entrada, text="Selecionar Tudo",
        variable=master_select_var, command=toggle_select_all
    )
    cb_selecionar_tudo.grid(row=0, column=3, padx=5, pady=5)

    # Canvas e Scrollable Frame
    canvas_frame: tk.Frame = tk.Frame(root)
    canvas_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    canvas: tk.Canvas = tk.Canvas(canvas_frame, bg="white")
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar: tk.Scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame: tk.Frame = tk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    scrollable_frame.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

    # Frame de busca
    frame_busca: tk.Frame = tk.Frame(root)
    frame_busca.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    label_busca: tk.Label = tk.Label(frame_busca, text="Buscar sequência:")
    label_busca.grid(row=0, column=0, padx=5, pady=5)

    entry_busca: tk.Entry = tk.Entry(frame_busca, width=50)
    entry_busca.grid(row=0, column=1, padx=5, pady=5)

    botao_buscar: tk.Button = tk.Button(
        frame_busca, text="Buscar", command=lambda: buscar_sequencia(entry_busca, scrollable_frame)
    )
    botao_buscar.grid(row=0, column=2, padx=5, pady=5)

    # Frame de opções de saída
    frame_opcoes: tk.Frame = tk.Frame(root)
    frame_opcoes.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

    label_formato: tk.Label = tk.Label(frame_opcoes, text="Formato de Saída:")
    label_formato.grid(row=0, column=0, padx=5, pady=5)

    opcoes_formato: List[str] = ["FASTA", "TXT", "CSV", "JSON"]
    formato_var: tk.StringVar = tk.StringVar(value="FASTA")
    formato_menu: tk.OptionMenu = tk.OptionMenu(frame_opcoes, formato_var, *opcoes_formato)
    formato_menu.grid(row=0, column=1, padx=5, pady=5)

    botao_salvar: tk.Button = tk.Button(
        frame_opcoes, text="Salvar Seleções",
        command=lambda: salvar_selecoes(entry_caminho, formato_var.get())
    )
    botao_salvar.grid(row=0, column=2, padx=5, pady=5)

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()

if __name__ == "__main__":
    main()
