# Contribuição, documentação e comentários

O objetivo é permitir que outra pessoa entenda uma alteração e confira seu efeito com segurança. Documente o comportamento que existe no código; propostas de mudança devem ser apresentadas como propostas.

## Onde colocar cada explicação

| Lugar | O que documentar | Exemplo neste projeto |
|---|---|---|
| `README.md` | Como instalar, jogar, testar e distribuir | Comandos do ambiente virtual e caminho do EXE |
| `docs/arquitetura.md` | Como os módulos se conectam e quais contratos preservar | Resultado definitivo separado da animação |
| `docs/interface.md` | Comportamento visual e organização dos desenhos | Escala uniforme, cache e uso de Pillow |
| Docstring de módulo ou classe | Papel da unidade e limites de responsabilidade | `Partida` coordena o estado, mas não salva sozinha |
| Docstring de função | Contrato: entrada, retorno, efeitos e erros relevantes | `resolver_jogada` devolve outro estado e rejeita casa inválida |
| Comentário `#` perto do trecho | Motivo, restrição ou decisão que não é evidente | Por que uma resposta antiga da máquina deve ser descartada |
| Teste | Exemplo executável do comportamento esperado | Voltar ao menu preserva o resultado durante a animação |

Evite repetir a mesma explicação longa em vários lugares. O comentário explica a decisão local; o guia mostra como ela se encaixa no todo. Use links para conectar os documentos.

## Padrão dos comentários Python

Use português, como os nomes do projeto, e frases curtas. Prefira um comentário imediatamente acima do trecho a uma explicação comprida no fim da linha. A indentação acompanha o código que ele explica.

```python
# O evento pede a parada; a geração também rejeita resultados já na fila.
self.geracao += 1
```

Esse comentário explica por que incrementar o contador é necessário. `# Incrementa geracao` apenas repetiria a instrução. Se o nome já explica uma operação simples, não é necessário adicionar comentário.

Uma docstring usa três aspas duplas e é a primeira instrução do módulo, classe ou função. Em uma função decorada, fica dentro da função, depois de `def`, não entre o decorador e a definição. Comece pelo que a unidade faz; acrescente detalhes apenas quando ajudam a usá-la corretamente.

Exemplo do contrato de uma função existente:

```python
def proxima_posicao(posicao, jogador):
    """Avança uma posição e pula o depósito adversário, sem mover sementes.

    Recebe um índice de 0 a 13 e jogador 0 ou 1, já válidos. Este é o único
    lugar que decide o próximo destino durante a distribuição.
    """
    seguinte = PROXIMAS[posicao]
    if seguinte == DEPOSITOS[1 - jogador]:
        seguinte = PROXIMAS[seguinte]
    return seguinte
```

Uma boa docstring responde, quando relevante:

- O que a função devolve, incluindo o significado de `None` ou de uma tupla.
- Que dados espera e quem é responsável por validá-los.
- Se modifica um objeto, grava um arquivo ou precisa da thread do Tk.
- Que erro esperado pode ocorrer e quem o trata.
- Que unidade usa: segundos, índice de posição, jogador 0/1 ou profundidade em escolhas.

Não é preciso criar seções formais de parâmetros e retornos em toda função curta. Também não use docstrings para narrar cada linha do algoritmo. Tipos e nomes claros continuam sendo parte da documentação, mas renomear funções ou mudar assinaturas exige uma revisão separada de compatibilidade.

## Comentários que devem ser evitados

- Tradução literal da operação: `# Soma 1` antes de `contador += 1`.
- Promessas que o código não cumpre: “IA imbatível”, “salvamento infalível” ou “sempre mais rápido”.
- Código antigo comentado; o histórico do Git já preserva versões anteriores.
- Assinaturas pessoais, datas de cada edição ou grandes faixas decorativas.
- `TODO` genérico como “melhorar isso”. Quando houver trabalho pendente real, descreva o problema e, se existir, ligue à issue que o acompanha.
- Explicações desatualizadas após mudar o código. Comentário errado também é um defeito.

Comentários não corrigem uma implementação confusa por si só. Se a explicação necessária for muito extensa, registre o fluxo no guia e avalie uma refatoração em outra alteração, com comportamento e testes claramente definidos.

## Como alterar preservando o que já existe

1. Confira a branch, alterações locais e a versão atual da `main`. Não sobrescreva trabalho de outra pessoa para começar uma edição.
2. Leia o trecho e seus testes. Identifique o que depende dele: regras, JSON, animação, busca ou desenho.
3. Faça uma alteração com objetivo único. Numa revisão de documentação, preserve nomes, assinaturas, condições, constantes, textos da interface e formato dos saves.
4. Revise o diff, inclusive exclusões e arquivos novos. Não traga de volta arquivos que a `main` removeu.
5. Execute as verificações adequadas e descreva o que foi comprovado e o que não foi medido.
6. Prepare um commit pequeno e um PR explicando o problema, o resultado e a validação. Faça merge apenas depois da revisão combinada com a equipe.

Para uma alteração só de comentários/docstrings, é possível comparar a árvore sintática Python antes e depois desconsiderando docstrings. Isso ajuda a detectar alterações acidentais nas instruções. Docstrings continuam sendo metadados acessíveis por `__doc__`; essa comparação verifica a estrutura executável, não afirma que os arquivos são idênticos.

## O que verificar

Use o ambiente descrito no [README](../README.md#executar-o-código-para-desenvolver). Os comandos abaixo são para PowerShell, na raiz do projeto; não é necessário ativar o ambiente virtual.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s testes -v
```

| Alteração | Conferência principal |
|---|---|
| Regras ou percurso | Conservação de 48 sementes, depósitos, captura, turno extra e encerramento em `test_regras.py` |
| Estratégia | Jogadas válidas e comparação com minimax de referência em `test_regras.py` |
| Salvamento ou caminhos | Salvar/carregar, arquivos inválidos e separação entre código e EXE |
| Interface, cancelamento ou ritmo | Testes com Tk real em `test_interface.py`, mais verificação visual quando a tela mudar |
| Gráficos | Hashes de pixels, cache, áreas clicáveis e proporções; conferir visualmente qualquer mudança intencional |
| Empacotamento ou dependências | Construir e executar o diagnóstico dos dois formatos pelo script de empacotamento |
| Documentação e comentários | Links, exemplos, coerência com o código e ausência de alterações acidentais na lógica |

Os testes de Tk podem ser ignorados quando não existe ambiente gráfico. Uma execução com esses testes ignorados não comprova que a interface passou. Os testes usam dados temporários, sem alterar partidas pessoais.

O teste de regressão gráfica compara uma seleção de imagens com hashes da aparência aprovada. O diagnóstico gera as 180 variações e verifica a transferência para Tk; isso não equivale a comparar os pixels de todas elas. A comparação completa dos 180 desenhos foi realizada durante a migração e está registrada em [comparacao-local.md](comparacao-local.md).

Não atualize hashes só para fazer um teste passar. Primeiro identifique a causa e revise visualmente a mudança. Atualizar Pillow também pode afetar os pixels e requer essa conferência.

O [README](../README.md#gerar-o-pacote-windows) contém o comando de construção do EXE. Uma edição de comentários não exige, por si só, redistribuir o jogo ou alterar sua versão. Os resultados históricos de desempenho em `comparacao-local.md` devem continuar identificados como uma medição daquela ocasião.

## O que entra no Git

Código, testes, guias, metadados e configurações necessários para reproduzir o projeto. As dependências ficam declaradas em `pyproject.toml` e `requirements.txt`; sua instalação fica no ambiente local. A organização atual mantém um único `requirements.txt` para desenvolvimento e empacotamento.

Ambientes virtuais, saves, logs, caches, relatórios locais, `build/`, `dist/`, EXEs e ZIPs não fazem parte dos arquivos versionados. Os executáveis são publicados em Releases. Não adicione PNGs gerados para documentar o funcionamento do renderizador; explique o código e use as verificações existentes.

Antes de publicar uma alteração em uma cópia com Git configurado:

```powershell
git status --short
git diff
git diff --cached
```

Confira também o conteúdo dos arquivos novos, que não aparecem em `git diff` antes de serem adicionados. Selecione explicitamente os arquivos desejados para o commit. Não use `git add -f` para incluir arquivos ignorados.

## Incorporar documentação de outra pessoa

Parta da `main` atual e leia as docstrings já integradas. Preserve explicações
corretas junto das funções; acrescente nos guias o fluxo entre módulos e os
procedimentos de desenvolvimento. Não substitua arquivos Python inteiros por
cópias locais antigas apenas para reaplicar comentários. Resolva sobreposições
trecho a trecho e mantenha correções de comportamento em alterações separadas.
