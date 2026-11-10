"""Cores, tipografia e controles compartilhados pelas telas."""
import tkinter as tk
from tkinter import ttk

FUNDO = '#0c111b'
PAPEL = '#151e2b'
TEXTO = '#edf1f7'
SUAVE = '#9aa9bc'
LINHA = '#293548'
VERDE = '#7bd1bc'
VERDE_CLARO = '#203c3b'
AMBAR = '#e3b979'
AZUL = '#93b4ed'
ESCURO = '#101925'


def configurar_tema(janela):
    """
    Configura o tema visual compartilhado da interface Tk.

    Parameters
    ----------
    janela : tk.Tk
        Janela principal que receberá o estilo global.

    Returns
    -------
    ttk.Style
        Estilo configurado para os widgets da aplicação.
    """
    estilo = ttk.Style(janela)
    estilo.theme_use('clam')
    estilo.configure('.', font=('Segoe UI', 11))
    estilo.configure('TButton', background=PAPEL, foreground=TEXTO,
                     bordercolor=LINHA, lightcolor=PAPEL, darkcolor=PAPEL,
                     padding=(16, 10), relief='flat', focuscolor=VERDE)
    estilo.map('TButton', background=[('disabled', FUNDO), ('pressed', VERDE_CLARO),
                                     ('active', VERDE_CLARO)],
               foreground=[('disabled', '#929b90')],
               bordercolor=[('focus', VERDE), ('active', VERDE)])
    estilo.configure('Principal.TButton', background=VERDE, foreground=FUNDO,
                     bordercolor=VERDE, lightcolor=VERDE, darkcolor=VERDE,
                     font=('Segoe UI', 11, 'bold'), focuscolor=FUNDO)
    estilo.map('Principal.TButton', background=[('disabled', LINHA), ('active', '#a4e7d5')],
               foreground=[('disabled', SUAVE), ('!disabled', FUNDO)])
    estilo.configure('Discreto.TButton', background=FUNDO, bordercolor=FUNDO,
                     lightcolor=FUNDO, darkcolor=FUNDO, padding=(12, 8))
    estilo.configure('Casa.TButton', font=('Segoe UI', 10, 'bold'), padding=(8, 8))
    estilo.configure('Treeview', background=PAPEL, fieldbackground=PAPEL,
                     foreground=TEXTO, borderwidth=0, rowheight=42, font=('Segoe UI', 11))
    estilo.map('Treeview', background=[('selected', VERDE_CLARO)], foreground=[('selected', TEXTO)])
    estilo.configure('Treeview.Heading', background=VERDE_CLARO, foreground=TEXTO,
                     font=('Segoe UI', 10, 'bold'), padding=(12, 12), relief='flat')
    estilo.configure('TCombobox', padding=6, fieldbackground=PAPEL, foreground=TEXTO,
                     background=PAPEL, arrowcolor=SUAVE, bordercolor=LINHA,
                     lightcolor=PAPEL, darkcolor=PAPEL)
    estilo.map('TCombobox', fieldbackground=[('readonly', PAPEL)],
               foreground=[('readonly', TEXTO)], selectbackground=[('readonly', PAPEL)],
               selectforeground=[('readonly', TEXTO)])
    estilo.configure('Horizontal.TProgressbar', background=VERDE, troughcolor=LINHA,
                     borderwidth=0, thickness=4)
    janela.option_add('*TCombobox*Listbox.background', PAPEL)
    janela.option_add('*TCombobox*Listbox.foreground', TEXTO)
    janela.option_add('*TCombobox*Listbox.selectBackground', VERDE_CLARO)
    janela.option_add('*TCombobox*Listbox.selectForeground', TEXTO)
    estilo.configure('Vertical.TScrollbar', background=LINHA, troughcolor=PAPEL,
                     bordercolor=PAPEL, arrowcolor=SUAVE)
    return estilo


def rotulo(pai, texto='', tamanho=11, cor=TEXTO, negrito=False, editorial=False, **opcoes):
    """
    Cria um rótulo com a tipografia visual padrão do projeto.

    Parameters
    ----------
    pai : tk.Misc
        Container pai do widget.
    texto : str, optional
        Texto exibido no rótulo.
    tamanho : int, optional
        Tamanho da fonte em pontos.
    cor : str, optional
        Cor do texto.
    negrito : bool, optional
        Ativa a variação negrito.
    editorial : bool, optional
        Ativa a estilo editorial, semelhante ao destaque do título.
    **opcoes
        Opções adicionais para o widget Tk.

    Returns
    -------
    tk.Label
        Rótulo montado com o estilo do projeto.
    """
    fonte = ('Segoe UI', tamanho, 'bold' if negrito or editorial else 'normal')
    return tk.Label(pai, text=texto, bg=pai.cget('bg'), fg=cor, font=fonte,
                    anchor='w', justify='left', **opcoes)


def botao(pai, texto, acao, principal=False, estilo=None):
    """
    Cria um botão com os estilos visuais do jogo.

    Parameters
    ----------
    pai : tk.Misc
        Container do botão.
    texto : str
        Texto exibido no controle.
    acao : callable
        Função executada ao clicar.
    principal : bool, optional
        Usa o esquema de destaque principal.
    estilo : str, optional
        Nome de estilo ttk explícito.

    Returns
    -------
    ttk.Button
        Botão pronto para ser anexado ao layout.
    """
    controle = ttk.Button(pai, text=texto, command=acao, takefocus=True,
                          style=estilo or ('Principal.TButton' if principal else 'TButton'))
    controle.bind('<Return>', lambda _: controle.invoke())
    return controle


def painel(pai, **opcoes):
    """
    Cria um painel com borda sutil e fundo do tema do jogo.

    Parameters
    ----------
    pai : tk.Misc
        Container dono do painel.
    **opcoes
        Atributos extras para o widget tk.Frame.

    Returns
    -------
    tk.Frame
        Painel estilizado para menus e blocos de conteúdo.
    """
    return tk.Frame(pai, bg=PAPEL, highlightbackground=LINHA, highlightthickness=1, **opcoes)
