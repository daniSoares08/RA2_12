# Tabela de Análise LL1

**Responsável:** Daniel Campos Soares

Cada célula mapeia `(não-terminal, terminal)` para a produção aplicada. Células vazias indicam erro sintático.

A tabela foi construída automaticamente em `gramatica.py` a partir da gramática, FIRST e FOLLOW. Se duas produções caíssem na mesma célula, `construirTabelaLL1()` lançaria erro de conflito LL(1).

| Não-terminal \ Terminal | `(` | `)` | `START` | `END` | `NUM` | `ID` | `MEM` | `RES` | `IF` | `WHILE` | `+` | `-` | `*` | `&#124;` | `/` | `%` | `^` | `>` | `<` | `==` | `!=` | `>=` | `<=` | `$` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `programa` | `programa → ( START ) LISTA_CMD` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `lista_cmd` | `lista_cmd → ( LISTA_APOS_ABRE` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `lista_apos_abre` | `lista_apos_abre → CMD ) LISTA_CMD` |  |  | `lista_apos_abre → END )` | `lista_apos_abre → CMD ) LISTA_CMD` | `lista_apos_abre → CMD ) LISTA_CMD` | `lista_apos_abre → CMD ) LISTA_CMD` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `cmd` | `cmd → EXPR_RPN` |  |  |  | `cmd → EXPR_RPN` | `cmd → EXPR_RPN` | `cmd → EXPR_RPN` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `expr_rpn` | `expr_rpn → ( EXPR_RPN ) EXPR_RPN_APOS_GRUPO` |  |  |  | `expr_rpn → NUM EXPR_RPN_APOS_NUM` | `expr_rpn → ID EXPR_RPN_APOS_ID` | `expr_rpn → MEM EXPR_RPN_APOS_ID` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `expr_rpn_apos_id` | `expr_rpn_apos_id → EXPR FINALIZADOR` | `expr_rpn_apos_id → ε` |  |  | `expr_rpn_apos_id → EXPR FINALIZADOR` | `expr_rpn_apos_id → EXPR FINALIZADOR` | `expr_rpn_apos_id → EXPR FINALIZADOR` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `expr_rpn_apos_num` | `expr_rpn_apos_num → EXPR FINALIZADOR` |  |  |  | `expr_rpn_apos_num → EXPR FINALIZADOR` | `expr_rpn_apos_num → EXPR FINALIZADOR` | `expr_rpn_apos_num → EXPR FINALIZADOR` | `expr_rpn_apos_num → RES` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `expr_rpn_apos_grupo` | `expr_rpn_apos_grupo → EXPR FINALIZADOR` |  |  |  | `expr_rpn_apos_grupo → EXPR FINALIZADOR` | `expr_rpn_apos_grupo → EXPR FINALIZADOR` | `expr_rpn_apos_grupo → EXPR FINALIZADOR` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `expr` | `expr → ( EXPR_RPN )` |  |  |  | `expr → NUM` | `expr → ID` | `expr → MEM` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `finalizador` |  |  |  |  |  | `finalizador → ID` | `finalizador → MEM` |  | `finalizador → IF` | `finalizador → WHILE` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` | `finalizador → OPERADOR` |  |
| `operador` |  |  |  |  |  |  |  |  |  |  | `operador → +` | `operador → -` | `operador → *` | `operador → &#124;` | `operador → /` | `operador → %` | `operador → ^` | `operador → >` | `operador → <` | `operador → ==` | `operador → !=` | `operador → >=` | `operador → <=` |  |

## Nota de compatibilidade

A célula de `finalizador` com terminal `ID` existe apenas para compatibilidade com o `lexer.py` atual, que ainda pode classificar a palavra `MEM` como identificador. A versão conceitual da linguagem usa `MEM` como keyword de armazenamento.
