# Gramática da Linguagem

**Responsável:** Daniel Campos Soares

## Regras de Produção (EBNF)

A gramática abaixo usa nomes de **não-terminais em minúsculas** na documentação e **terminais em maiúsculas ou símbolos literais**. No código (`gramatica.py`), os mesmos não-terminais aparecem em maiúsculas para manter o padrão usado pelos módulos Python do projeto.

```ebnf
programa              -> "(" START ")" lista_cmd
lista_cmd             -> "(" lista_apos_abre
lista_apos_abre       -> END ")"
                       | cmd ")" lista_cmd

cmd                   -> expr_rpn

expr_rpn              -> ID expr_rpn_apos_id
                       | MEM expr_rpn_apos_id
                       | NUM expr_rpn_apos_num
                       | "(" expr_rpn ")" expr_rpn_apos_grupo

expr_rpn_apos_id      -> expr finalizador
                       | ε

expr_rpn_apos_num     -> RES
                       | expr finalizador

expr_rpn_apos_grupo   -> expr finalizador

expr                  -> NUM
                       | ID
                       | MEM
                       | "(" expr_rpn ")"

finalizador           -> operador
                       | MEM
                       | ID
                       | IF
                       | WHILE

operador              -> "+" | "-" | "*" | "|" | "/" | "%" | "^"
                       | ">" | "<" | "==" | "!=" | ">=" | "<="
```

## Leitura prática da gramática

- Todo programa começa com `(START)` e termina com `(END)`.
- `lista_cmd` foi fatorada de propósito. Isso evita o conflito LL(1) entre “mais um comando começando com `(`” e “fim do programa começando com `(END)`”.
- `expr_rpn` representa o conteúdo dentro dos parênteses de uma expressão/comando.
- `expr` representa um operando: número, memória/identificador ou expressão aninhada.
- `ε` representa produção vazia.

## Operações RPN aceitas

```txt
(A B +)
(A B -)
(A B *)
(A B |)
(A B /)
(A B %)
(A B ^)
(A B >)
(A B <)
(A B ==)
(A B !=)
(A B >=)
(A B <=)
```

`A` e `B` podem ser `NUM`, `ID`, `MEM` ou outra expressão entre parênteses.

## Comandos Especiais

### Resultado anterior

```txt
(N RES)
```

- `N` deve ser um número inteiro não negativo.
- Exemplo: `(2 RES)`.

### Armazenamento em memória

Forma adotada pelo grupo nos testes:

```txt
(V NOME_MEMORIA MEM)
```

Exemplo:

```txt
(42.0 VAR MEM)
```

Nesta forma, `V` é o valor/expressão a armazenar, `VAR` é o identificador da memória, e `MEM` funciona como keyword pós-fixada de armazenamento.

### Leitura de memória

```txt
(MEMORIA)
```

Exemplo:

```txt
(VAR)
```

## Estruturas de Controle

As estruturas seguem a ideia pós-fixada da linguagem: primeiro vêm os operandos, depois a keyword.

### Tomada de Decisão

Forma adotada:

```txt
( (condicao) (corpo) IF )
```

Exemplo:

```txt
((1 2 <) (3 4 +) IF)
```

### Laço de Repetição

Forma adotada:

```txt
( (condicao) (corpo) WHILE )
```

Exemplo:

```txt
((CONT 0 >) (CONT 1 -) WHILE)
```

## Observação de integração

O terminal `MEM` está previsto na gramática como keyword. Porém, no `lexer.py` atual, a palavra `MEM` ainda pode chegar ao parser como `ID`, porque o lexer trata palavras maiúsculas como identificadores. Por isso, a tabela também aceita `ID` no ponto do finalizador de armazenamento. Quando o lexer for ajustado para gerar token `MEM`, essa compatibilidade pode ser removida sem mudar a ideia da gramática.
