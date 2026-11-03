# Interface e recursos gráficos

A interface usa Tkinter e ttk com fundo escuro, acentos verdes e azuis e um tabuleiro de madeira escura. O jogo mostra sementes, quantidades e placares. Os identificadores internos das posições aparecem somente na documentação técnica e no código.

## Controles

- Clique numa casa iluminada para jogar.
- Tab percorre os controles; no tabuleiro, as setas mudam o foco e Enter ou Espaço confirmam.
- As teclas 1–6 escolhem as casas da esquerda para a direita na fileira atual.
- Esc volta ao menu. Menu e Sair permanecem disponíveis durante animações e cálculos.
- A animação pode ser normal (aproximadamente 0,20 s por semente), rápida ou desligada; o resultado da jogada não muda. A máquina mostra “Pensando…” por pelo menos cinco segundos por escolha, sem bloquear Menu ou Sair.
- A lista de partidas permite filtrar jogos em andamento ou concluídos e abrir com duplo clique ou Enter.

## Organização

`aparencia.py` define cores, fontes e estilos; `tabuleiro.py` desenha e recebe entradas; `interface.py` coordena as telas. O Canvas não aplica regras nem modifica diretamente o estado da partida.

O tabuleiro usa a mesma escala horizontal e vertical. As casas continuam circulares ao redimensionar a janela, a partir de 900 × 640.

## Gráficos por código

`graficos.py` desenha madeira, cavidades, sementes e destaques com Pillow. O desenho mantém a textura determinística, as cores e a suavização da versão 0.2.0: renderização ampliada e redução Lanczos. A aparência depende do código; não há PNGs a preparar ou distribuir.

O original de alta resolução é gerado uma vez, sob demanda. O cache mantém no máximo dois tamanhos de tabuleiro, doze anéis e 52 pequenas sementes; não cresce indefinidamente durante o redimensionamento. O Canvas mantém apenas as referências Tk do tamanho atual e as libera ao trocar de tamanho ou destruir a tela. Não há cache em disco.

`requirements.txt` reúne Pillow e PyInstaller para desenvolvimento e empacotamento. `pyproject.toml` declara somente Pillow como dependência de execução. O executável leva as bibliotecas necessárias; quem joga não precisa instalar nada.

Os testes com hashes dos pixels preservam a aparência aprovada sem guardar imagens de referência no Git. O diagnóstico do executável gera os 32 tamanhos de tabuleiro, seus três destaques e as 52 sementes, verificando a integração Pillow/Tk.

## Simplificações adotadas

- Um módulo de desenho substitui 180 arquivos PNG e o script separado que os exportava.
- Geometria única para desenhar cavidades e calcular as áreas clicáveis.
- Um arquivo de requisitos para desenvolvimento e empacotamento, preservando a organização da branch principal.
- Nenhum banco de dados, serviço online, framework gráfico extra ou cache persistente: partidas continuam em JSON.

A separação entre regras, persistência, busca da máquina e interface continua necessária para testar e alterar cada parte sem misturar responsabilidades.
