# Comparação local — gráficos por código

Medição de 27/10/2026, em Windows, com Python 3.14.3, PyInstaller 6.22.3 e Pillow 12.3.0. Medição local da candidata para avaliação no pull request.

| Medida | PNGs (referência 0.2.0) | Pillow (candidata 0.2.1) |
|---|---:|---:|
| EXE único, bytes | 17680765 | 16098807 |
| Abertura, mediana | 6.89 s | 9.21 s |
| Abertura, mínimo | 5.95 s | 6.97 s |
| Abertura, máximo | 16.22 s | 12.51 s |

O EXE ficou 8.9% menor. A mediana de abertura aumentou 33.7%. A variabilidade foi alta; estes números descrevem esta medição, sem garantir desempenho em outros computadores.

## Método

Sete processos novos de cada versão, após uma execução de aquecimento por versão, em ordem alternada. O cronômetro externo inclui a extração do EXE e termina após o menu e o tabuleiro serem desenhados em 1200 × 800. Partidas temporárias e janela fora da tela evitam alterar os dados do jogador.

A referência foi reconstruída do código de 0.2.0 com o mesmo ambiente e o mesmo modo de medição; não é o binário publicado daquela versão, que foi construído com Python 3.12. Não foram medidos boot frio nem diferentes máquinas.

## Verificações

- 29 testes aprovados, incluindo regras, interface, cache, espera da máquina e ritmo da animação.
- 180 comparações de pixels sem diferenças em relação aos PNGs anteriores.
- Pacotes em pasta e EXE único passaram pelo diagnóstico com Python fora do PATH.
- O pacote novo não inclui os PNGs do tabuleiro nem o leitor AVIF.
- SHA256 do EXE local: `58d4627a50ce57caadd6f899d3da9db104c2402059a1c5aa3021a02e6ce8c7a6`.

## Organização

`mancala/graficos.py` substitui os PNGs e o exportador anterior. `requirements.txt` reúne Pillow e PyInstaller; os metadados do projeto declaram somente Pillow como dependência de execução. O cache fica apenas na memória e tem limites.

`dist/`, `build/`, ambientes virtuais, saves e logs não entram no Git. O EXE de distribuição fica em `dist/arquivo-unico/MancalaSoJoga.exe`; no GitHub, binários pertencem às Releases.

A comparação automatizada é reproduzida por `scripts/comparar_abertura.py`. Os relatórios brutos e a referência antiga ficam na pasta de trabalho de comparação, fora do projeto.
