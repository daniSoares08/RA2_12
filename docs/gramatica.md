# Gramática da Linguagem

**Responsável:** Daniel Campos Soares

## Regras de Produção (EBNF)

> TODO: documentar as regras de produção completas em formato EBNF.
> Use letras minúsculas para não-terminais e maiúsculas para terminais.

```
programa    -> (START) lista_cmd (END)
lista_cmd   -> TODO
cmd         -> TODO
expr        -> TODO
expr_rpn    -> TODO
operador    -> TODO
...
```

## Estruturas de Controle

> TODO: documentar a sintaxe definida pelo grupo para decisão e laços.
> As estruturas devem estar entre parênteses e seguir notação pós-fixada.

### Tomada de Decisão

Forma (pós-fixada, tudo entre parênteses):

```
( (condicao) (corpo) IF )
```

- `condicao` e `corpo` são subexpressões/subcomandos **já entre parênteses**.
- `IF` é keyword em maiúsculas.

### Laço de Repetição

Forma:

```
( (condicao) (corpo) WHILE )
```

- `WHILE` é keyword em maiúsculas.
