# Interface e recursos gráficos

A interface usa Tkinter e ttk com fundo escuro, acentos verdes e azuis e um tabuleiro de madeira escura. O jogo mostra sementes, quantidades e placares. Os identificadores internos das posições aparecem somente na documentação técnica e no código.

## Controles

- Clique numa casa iluminada para jogar.
- Tab percorre os controles; no tabuleiro, as setas mudam o foco e Enter ou Espaço confirmam.
- As teclas 1–6 escolhem as casas da esquerda para a direita na fileira atual.
- Esc volta ao menu. Menu e Sair permanecem disponíveis durante animações e cálculos.
- A animação pode ser normal, rápida ou desligada; o resultado da jogada não muda.
- A lista de partidas permite filtrar jogos em andamento ou concluídos e abrir com duplo clique ou Enter.

## Organização

`aparencia.py` define cores, fontes e estilos; `tabuleiro.py` desenha e recebe entradas; `interface.py` coordena as telas. O Canvas não aplica regras nem modifica diretamente o estado da partida.

O tabuleiro usa a mesma escala horizontal e vertical. As casas continuam circulares ao redimensionar a janela, a partir de 900 × 640. Os gráficos são PNGs originais em vários tamanhos, gerados com supersampling e redução Lanczos. O aplicativo escolhe o tamanho adequado e carrega as imagens com `tk.PhotoImage`, sem precisar de Pillow para jogar.

## Recriar os gráficos

Os arquivos em `mancala/recursos/` fazem parte do jogo e são versionados. Para modificar sua aparência, edite `scripts/gerar_graficos.py` e execute:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-graficos.txt
.\.venv\Scripts\python.exe scripts/gerar_graficos.py
```

A geração tem uma semente aleatória fixa. O empacotamento inclui os PNGs no executável; o diagnóstico de instalação verifica se todos os 180 recursos podem ser lidos pelo Tk. Ambientes virtuais, saves, logs, caches e executáveis continuam fora do Git.
