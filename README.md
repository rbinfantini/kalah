# Mancala

Novo projeto em Python, com nomes em português e regras separadas da interface. Usa apenas a biblioteca padrão, sem Pygame ou serviços online.

## Abrir

No Windows, use Python 3.10 ou superior com Tcl/Tk e dê dois cliques em **`iniciar.pyw`**. Quando a extensão `.pyw` está associada ao Python no Windows, o jogo abre sem janela de terminal. Se o arquivo abrir num editor, escolha o Python (pythonw.exe) em **Abrir com** ou execute `pyw -3 iniciar.pyw` pelo terminal.

O arquivo `depurar.bat` abre o jogo **com terminal** para diagnóstico. Também é possível executar `python main.py`. As instalações oficiais do Python para Windows normalmente incluem Tkinter; em outros sistemas pode ser necessário instalá-lo separadamente. Não há dependências externas para instalar.

Se a inicialização sem console falhar, um aviso é exibido e o diagnóstico é salvo em `logs/inicializacao.log`, quando a pasta permite escrita.

## Tabuleiro e regras

São **48 sementes**: 12 casas começam com quatro cada. P7 (A) e P13 (B) começam vazios.

```text
               B: da direita para a esquerda
           P12  P11  P10  P9  P8  P6
      P13                              P7
            P0   P1   P2  P3  P4  P5
               A: da esquerda para a direita
```

Percurso: `P0 → P1 → P2 → P3 → P4 → P5 → P7 → P6 → P8 → P9 → P10 → P11 → P12 → P13 → P0`.

O percurso troca a ordem numérica de P6/P7 para preservar seis casas por jogador com depósitos P7 e P13: o número identifica uma posição, não sua vizinhança aritmética.

- Escolha uma casa própria com sementes. O motor retira todas e distribui uma por posição usando `proxima_posicao(posicao, jogador)`.
- O depósito adversário é pulado. Sementes depositadas nunca saem durante a partida; depósitos não são selecionáveis como jogada.
- Terminar no depósito próprio concede outra escolha, salvo se a partida acabou.
- Terminar em casa própria que estava vazia captura a última semente e as sementes da oposta, se a oposta estiver ocupada.
- Se um lado fica vazio, as sobras vão para os depósitos dos respectivos donos. Vence o maior depósito.
- Cada posição guarda um inteiro de 0 a 48. Todas as sementes cabem em qualquer posição; entretanto, todas em uma casa e o outro lado vazio exige encerramento e recolha, não é uma posição regular entre escolhas.

## Menus e partidas

Menu: Jogar, Carregar jogo, Tutorial e Sair. Jogar permite dupla ou máquina; máquina oferece Fácil, Normal e Difícil. Menu e Sair permanecem disponíveis durante cálculos e animações. Clique nas casas ou use os botões Pn; Tab e Enter permitem acessar os controles.

As partidas são salvas automaticamente ao iniciar e após cada escolha, na pasta `partidas_salvas/` junto ao programa. A lista mostra todas as partidas válidas, da mais recente à mais antiga, inclusive concluídas. Tutorial não é salvo. Arquivos inválidos são preservados e informados na tela de carregamento. A pasta do programa precisa permitir escrita.

Sair durante uma animação preserva o resultado completo da jogada. Carregar mostra esse resultado, sem repetir a distribuição. A gravação usa substituição atômica; falhas aparecem no rodapé.

## Computador

- Fácil: escolha aleatória válida.
- Normal: minimax com poda alfa-beta, até cinco escolhas e aproximadamente 0,35 segundo.
- Difícil: aprofundamento progressivo, até 28 escolhas e aproximadamente quatro segundos, ordenação de capturas/turnos extras e cache de posições com limites alfa-beta.

A profundidade conta escolhas, incluindo turnos extras. O computador usa as mesmas regras, sem vantagens artificiais, e mantém o resultado da última profundidade concluída quando o tempo acaba. Não há livro de aberturas nem garantia de jogo perfeito. A força competitiva ainda requer avaliação extensa; este é o nível mais profundo oferecido, não uma certificação de dificuldade extrema.

## Arquitetura

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Inicializa a janela |
| `iniciar.pyw` | Inicia sem console no Windows e registra falhas de inicialização |
| `depurar.bat` | Inicia com terminal para diagnóstico |
| `mancala/regras.py` | Estado, percurso, captura, turno e encerramento |
| `mancala/partidas.py` | Coordenação da jogada e persistência JSON |
| `mancala/estrategia.py` | Busca do computador |
| `mancala/animacao.py` | Reprodução dos eventos |
| `mancala/tutorial.py` | Cinco exercícios usando o motor real |
| `mancala/interface.py` | Menus, desenho e coordenação da janela |
| `testes/test_regras.py` | Regras, busca e armazenamento |

```text
Clique na casa
  → Partida.jogar(casa)
  → resolver_jogada(estado, casa)
      → retirar sementes
      → repetir proxima_posicao() e depositar uma semente
      → capturar se aplicável
      → encerrar ou definir próximo jogador
  → salvar novo estado
  → AnimadorJogada reproduz os eventos
  → aguardar pessoa ou solicitar busca do computador
```

O estado definitivo e o tabuleiro exibido são distintos durante a animação. A máquina chama o mesmo motor com `registrar_eventos=False`, poupando alocações. A busca roda numa thread cancelável sem chamar Tkinter fora da thread principal. Resultados antigos são descartados após mudanças de tela.

## Testes

Execute `python -m unittest discover -s testes -v`.

Verificações: percurso dos dois jogadores, 48 sementes, depósitos que nunca diminuem, turno extra, captura, encerramento, tutorial, 100 partidas aleatórias, salvar/retomar, arquivos inválidos e equivalência da busca otimizada com minimax sem poda em posições selecionadas.

Os testes automatizados não substituem a verificação visual da interface. É necessário Python com uma instalação funcional do Tkinter; não há executável independente do Python.

## Git

O repositório contém código, testes, documentação e configurações de versionamento. `.gitignore` exclui partidas salvas, logs, caches, ambientes virtuais, arquivos ZIP e pastas do sistema. Esses arquivos locais não devem ser enviados.

Para começar em outro computador:

```powershell
git clone https://github.com/rbinfantini/kalah.git
cd kalah
```

Para uma alteração:

```powershell
git switch -c melhoria/nome-da-alteracao
python -m unittest discover -s testes -v
git status --short
git add caminho/do/arquivo.py
git diff --cached
git commit -m "Descreve a melhoria"
git push -u origin melhoria/nome-da-alteracao
```

Revise os arquivos antes do commit. Não use `git add -f` para arquivos ignorados. Ao atualizar uma instalação anterior, copie `partidas_salvas/` para a nova pasta se quiser continuar suas partidas; essa pasta permanece local.
