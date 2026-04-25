# Conjuntos FIRST e FOLLOW

**Responsável:** Daniel Campos Soares

## Conjuntos FIRST

| Não-terminal | FIRST |
|---|---|
| `programa` | { `(` } |
| `lista_cmd` | { `(` } |
| `lista_apos_abre` | { `(`, `END`, `NUM`, `ID`, `MEM` } |
| `cmd` | { `(`, `NUM`, `ID`, `MEM` } |
| `expr_rpn` | { `(`, `NUM`, `ID`, `MEM` } |
| `expr_rpn_apos_id` | { `(`, `NUM`, `ID`, `MEM`, `ε` } |
| `expr_rpn_apos_num` | { `(`, `NUM`, `ID`, `MEM`, `RES` } |
| `expr_rpn_apos_grupo` | { `(`, `NUM`, `ID`, `MEM` } |
| `expr` | { `(`, `NUM`, `ID`, `MEM` } |
| `finalizador` | { `ID`, `MEM`, `IF`, `WHILE`, `+`, `-`, `*`, `&#124;`, `/`, `%`, `^`, `>`, `<`, `==`, `!=`, `>=`, `<=` } |
| `operador` | { `+`, `-`, `*`, `&#124;`, `/`, `%`, `^`, `>`, `<`, `==`, `!=`, `>=`, `<=` } |

## Conjuntos FOLLOW

| Não-terminal | FOLLOW |
|---|---|
| `programa` | { `$` } |
| `lista_cmd` | { `$` } |
| `lista_apos_abre` | { `$` } |
| `cmd` | { `)` } |
| `expr_rpn` | { `)` } |
| `expr_rpn_apos_id` | { `)` } |
| `expr_rpn_apos_num` | { `)` } |
| `expr_rpn_apos_grupo` | { `)` } |
| `expr` | { `ID`, `MEM`, `IF`, `WHILE`, `+`, `-`, `*`, `&#124;`, `/`, `%`, `^`, `>`, `<`, `==`, `!=`, `>=`, `<=` } |
| `finalizador` | { `)` } |
| `operador` | { `)` } |

## Observação

`$` representa o fim da entrada. `ε` representa a produção vazia usada principalmente para aceitar leitura simples de memória, como `(VAR)`, sem exigir um operador depois do identificador.
