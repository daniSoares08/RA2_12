# RA2_12 - Analisador Sintático

**Instituição:** PUCPR
**Ano:** 2026  
**Disciplina:** Linguagens Formais e Compiladores  
**Professor:** Frank Coelho De Alcantara

## Integrantes (ordem alfabética)

| Nome | GitHub |
|---|---|
| Daniel Campos Soares | [@daniSoares08](https://github.com/daniSoares08) |
| Giovanni Bandeira Malucelli | [@Giomalu](https://github.com/Giomalu) |
| Victor Vanini Meyer | [@VictorMeyer1](https://github.com/VictorMeyer1) |

## Sobre o Projeto

Analisador sintático descendente recursivo LL1 para uma linguagem de programação simplificada em notação polonesa reversa (RPN). Geração de código Assembly ARMv7 para o ambiente Cpulator-ARMv7 DEC1-SOC(v16.1).

## Compilação e Execução

**Requisitos:** Python 3.8+

O programa recebe como entrada um arquivo de texto contendo o **código-fonte** da linguagem (uma expressão/comando por linha, no formato mostrado em `testes/`).

```bash
python AnalisadorSintatico.py testes/teste1.txt
```

Em sistemas Unix, após `chmod +x AnalisadorSintatico.py`:

```bash
./AnalisadorSintatico testes/teste1.txt
```

## Sintaxe da Linguagem

Todo programa deve começar com `(START)` e terminar com `(END)`.

### Operações Aritméticas (notação RPN)

| Operação | Sintaxe | Exemplo |
|---|---|---|
| Adição | `(A B +)` | `(3 2 +)` |
| Subtração | `(A B -)` | `(5 1 -)` |
| Multiplicação | `(A B *)` | `(4 3 *)` |
| Divisão Real | `(A B \|)` | `(7.0 2.0 \|)` |
| Divisão Inteira | `(A B /)` | `(7 2 /)` |
| Resto | `(A B %)` | `(7 2 %)` |
| Potenciação | `(A B ^)` | `(2 8 ^)` |

### Comandos Especiais

| Comando | Descrição |
|---|---|
| `(N RES)` | Retorna resultado de N linhas anteriores |
| `(V MEM)` | Armazena valor V na memória MEM |
| `(MEM)` | Retorna valor armazenado em MEM |

### Estruturas de Controle

- **IF:** `( ( condição ) ( corpo ) IF )` — condição e corpo são subexpressões entre parênteses; `IF` em maiúsculas.
- **WHILE:** `( ( condição ) ( corpo ) WHILE )` — idem com `WHILE`.
- **Relacionais:** `>`, `<`, `==`, `!=`, `>=`, `<=` dentro das expressões RPN (ex.: `( 1 2 < )`).

Detalhes em [docs/gramatica.md](docs/gramatica.md).

## Documentação

- [Gramática completa (EBNF)](docs/gramatica.md)
- [Conjuntos FIRST e FOLLOW](docs/first_follow.md)
- [Tabela de Análise LL1](docs/tabela_ll1.md)
- [Árvore Sintática (última execução)](docs/arvore_sintatica.md)

## Estrutura do Repositório

```
RA2_12/
├── AnalisadorSintatico.py   # main() e integração
├── gramatica.py             # construirGramatica, FIRST, FOLLOW, tabela LL1
├── parser_ll1.py            # parsear (parser LL1 com pilha)
├── lexer.py                 # lerTokens
├── arvore.py                # gerarArvore, gerarAssembly
├── testes/
│   ├── teste1.txt           # casos válidos
│   ├── teste2.txt           # casos válidos com estruturas de controle
│   └── teste3_erros.txt     # casos com erros léxicos e sintáticos
├── docs/
│   ├── gramatica.md
│   ├── first_follow.md
│   ├── tabela_ll1.md
│   └── arvore_sintatica.md
├── divisao_daniel.md
├── divisao_giovanni.md
└── divisao_victor.md
```
