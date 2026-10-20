# Mancala Só Joga

Novo projeto em Python, com nomes em português e regras separadas da interface. Usa apenas a biblioteca padrão, sem Pygame ou serviços online.

## Jogar sem instalar Python

Abra [Releases](https://github.com/rbinfantini/kalah/releases/latest), baixe **MancalaSoJoga.exe** e abra com dois cliques. O arquivo inclui Python, Tcl/Tk e as bibliotecas necessárias. Não é preciso instalar Python, Git ou executar comandos. O jogo funciona offline e abre sem terminal.

Também está disponível **MancalaSoJoga-Windows-x64.zip**, com o mesmo executável e instruções. Extraia o ZIP antes de jogar. `SHA256.txt` contém os hashes dos dois downloads.

O pacote é para Windows de 64 bits. Linux e macOS precisam de distribuições próprias; o executável Windows não é universal. Cada versão só é publicada depois que o processo automático testa as regras e executa uma verificação de menus, animação, salvamento e tutorial dentro do próprio pacote.

## Executar o código para desenvolver

No Windows, use Python 3.10 ou superior com Tcl/Tk e dê dois cliques em **`iniciar.pyw`**. Quando a extensão `.pyw` está associada ao Python no Windows, o jogo abre sem janela de terminal. Se o arquivo abrir num editor, escolha o Python (pythonw.exe) em **Abrir com** ou execute `pyw -3 iniciar.pyw` pelo terminal.

O arquivo `depurar.bat` abre o jogo **com terminal** para diagnóstico. Também é possível executar `python main.py`. As instalações oficiais do Python para Windows normalmente incluem Tkinter; em outros sistemas pode ser necessário instalá-lo separadamente. Não há dependências externas para instalar.

Se a inicialização sem console falhar, um aviso é exibido e o diagnóstico é salvo em `logs/inicializacao.log`, quando a pasta permite escrita.

`pyproject.toml` declara a versão do projeto, Python mínimo e dependências de execução: a lista é vazia. **Tkinter não é instalado com `pip install tkinter`**: ele faz parte de uma instalação Python com suporte Tcl/Tk. Para verificar sua instalação, execute `python -m tkinter`; deve abrir uma janela de demonstração. `requirements-build.txt` fixa a versão da ferramenta usada para gerar o executável.

Para desenvolver, crie seu próprio ambiente virtual na raiz do projeto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe main.py
```

Use `.\.venv\Scripts\pythonw.exe iniciar.pyw` para abrir sem console. A instalação editável também cria o comando `mancala-so-joga` dentro de `.venv\Scripts`. O ambiente `.venv` fica apenas no seu computador; cada desenvolvedor o recria. O jogo não precisa de `.env`, pois não usa credenciais ou configurações de serviços externos.

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

As partidas são salvas automaticamente ao iniciar e após cada escolha. Na execução a partir deste repositório, ficam na pasta `partidas_salvas/` do projeto. No executável Windows, ficam em `%LOCALAPPDATA%\MancalaSoJoga\partidas_salvas`, fora das bibliotecas e dos arquivos de instalação. Os logs do executável ficam em `%LOCALAPPDATA%\MancalaSoJoga\logs`. Assim, atualizar o executável não apaga as partidas.

A lista mostra todas as partidas válidas, da mais recente à mais antiga, inclusive concluídas. Tutorial não é salvo. Arquivos inválidos são preservados e informados na tela de carregamento. Para migrar da versão em Python, copie seus JSONs para a pasta de partidas do executável com o jogo fechado, preservando arquivos de mesmo nome.

Sair durante uma animação preserva o resultado completo da jogada. Carregar mostra esse resultado, sem repetir a distribuição. A gravação usa substituição atômica; falhas aparecem no rodapé.

## Computador

- Fácil: escolha aleatória válida.
- Normal: minimax com poda alfa-beta, até cinco escolhas e aproximadamente 0,35 segundo.
- Difícil: aprofundamento progressivo, até 28 escolhas e aproximadamente quatro segundos, ordenação de capturas/turnos extras e cache de posições com limites alfa-beta.

A profundidade conta escolhas, incluindo turnos extras. O computador usa as mesmas regras, sem vantagens artificiais, e mantém o resultado da última profundidade concluída quando o tempo acaba. Não há livro de aberturas nem garantia de jogo perfeito. A força competitiva ainda requer avaliação extensa; este é o nível mais profundo oferecido, não uma certificação de dificuldade extrema.

## Arquitetura

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Entrada para execução com console |
| `iniciar.pyw` | Entrada para execução sem console no Windows |
| `mancala/inicializacao.py` | Inicialização compartilhada, argumentos e registro de falhas |
| `depurar.bat` | Inicia com terminal para diagnóstico |
| `mancala/caminhos.py` | Local de gravação dos dados no código e no executável |
| `mancala/diagnostico.py` | Verifica a interface e persistência no pacote construído |
| `mancala/regras.py` | Estado, percurso, captura, turno e encerramento |
| `mancala/partidas.py` | Coordenação da jogada e persistência JSON |
| `mancala/estrategia.py` | Busca do computador |
| `mancala/animacao.py` | Reprodução dos eventos |
| `mancala/tutorial.py` | Cinco exercícios usando o motor real |
| `mancala/interface.py` | Menus, desenho e coordenação da janela |
| `testes/test_regras.py` | Regras, busca e armazenamento |
| `testes/test_caminhos.py` | Separação dos dados entre código e executável |
| `pyproject.toml` | Metadados, versão, Python mínimo e instalação do projeto |
| `requirements-build.txt` | Ferramenta de empacotamento |
| `scripts/empacotar_windows.ps1` | Construção e verificação dos pacotes |
| `.github/workflows/windows.yml` | Automação dos testes, construção e publicação |

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

Execute `.\.venv\Scripts\python.exe -m unittest discover -s testes -v`.

Verificações: percurso dos dois jogadores, 48 sementes, depósitos que nunca diminuem, turno extra, captura, encerramento, tutorial, 100 partidas aleatórias, salvar/retomar, arquivos inválidos e equivalência da busca otimizada com minimax sem poda em posições selecionadas.

Os testes automatizados não substituem a verificação visual da interface. Quem desenvolve precisa de Python com Tkinter; quem usa o pacote Windows recebe esse ambiente incluído.

## Gerar o pacote Windows

A automação em `.github/workflows/windows.yml` usa Windows e Python 3.12 de 64 bits. Primeiro testa as regras e constrói um pacote em pasta; depois constrói o executável único. Ambos passam pelo diagnóstico da interface, tutorial, computador e persistência, com Python removido do `PATH`. Os relatórios ficam nos artefatos da execução.

Uma versão ainda não publicada em `main` gera uma Release com EXE, ZIP e SHA256. A versão vem de `pyproject.toml`. Para publicar uma atualização, aumente esse número, por exemplo de `0.1.0` para `0.1.1`. Versões já publicadas são preservadas; novas construções com o mesmo número ficam somente nos artefatos do GitHub Actions. Pull requests executam a construção e os testes, sem publicar Releases.

Para gerar localmente no Windows, após criar o ambiente virtual:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
powershell -File scripts/empacotar_windows.ps1 -Python .\.venv\Scripts\python.exe
```

Os resultados são `dist/arquivo-unico/MancalaSoJoga.exe`, `dist/MancalaSoJoga-Windows-x64.zip` e `dist/SHA256.txt`. Compartilhe o EXE ou o ZIP. `build/` e `dist/` são gerados e ignorados pelo Git. O processo é documentado pelo [PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).

## Git

O repositório contém código, testes, documentação, metadados e configurações de construção e versionamento. `.gitignore` exclui partidas salvas, logs, caches, ambientes virtuais, `.env`, EXEs, ZIPs e pastas do sistema. Os binários ficam em Releases. Não copie bibliotecas instaladas ou a pasta `.venv` para o Git.

Para começar em outro computador:

```powershell
git clone https://github.com/rbinfantini/kalah.git
cd kalah
```

Para uma alteração:

```powershell
git switch -c melhoria/nome-da-alteracao
.\.venv\Scripts\python.exe -m unittest discover -s testes -v
git status --short
git add caminho/do/arquivo.py
git diff --cached
git commit -m "Descreve a melhoria"
git push -u origin melhoria/nome-da-alteracao
```

Revise os arquivos antes do commit. Não use `git add -f` para arquivos ignorados. Ao atualizar uma instalação anterior, copie `partidas_salvas/` para a nova pasta se quiser continuar suas partidas; essa pasta permanece local.
