# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12

from __future__ import annotations

# Conjunto padrão de sincronização 
SINCRONIZACAO_PADRAO = frozenset({")", "END", "$"})

def parsear(tokens, tabela_ll1):
    
    meta = _normalizar_meta(tabela_ll1)
    tabela = meta["tabela_ll1"]
    nao_terminais = frozenset(meta["nao_terminais"])
    simbolo_inicial = meta["simbolo_inicial"]
    sync_entrada = meta.get("sincronizar_entrada", SINCRONIZACAO_PADRAO)
    sync_pilha = meta.get("sincronizar_pilha", SINCRONIZACAO_PADRAO | nao_terminais)

    buffer = list(tokens)
    linha_eof = buffer[-1]["linha"] if buffer else 1
    buffer.append({"tipo": "EOF", "valor": "$", "linha": linha_eof})

    pilha: list[str] = ["$", simbolo_inicial]
    i = 0
    derivacao: list[dict] = []
    erros: list[str] = []

    while pilha:
        topo = pilha[-1]
        atual = buffer[i]
        a = _terminal_de_token(atual)

        if topo == "$":
            if a == "$":
                pilha.pop()
            else:
                msg = _reportarErro(atual, {"$"}, atual.get("linha", 0), emitir=False)
                erros.append(msg)
                i = _sincronizar_entrada(buffer, i, sync_entrada)
                if i < len(buffer) and _terminal_de_token(buffer[i]) == "$":
                    break
            continue

        if topo not in nao_terminais:
            if topo == a:
                pilha.pop()
                i += 1
            else:
                msg = _reportarErro(atual, {topo}, atual.get("linha", 0), emitir=False)
                erros.append(msg)
                pilha, i = _recuperacao_panico(pilha, buffer, i, sync_pilha, sync_entrada)
            continue

        producao = tabela.get((topo, a))
        if producao is None:
            msg = _reportarErro(
                atual,
                "um dos terminais esperados para expandir {0}".format(topo),
                atual.get("linha", 0),
                emitir=False,
            )
            erros.append(msg)
            pilha, i = _recuperacao_panico(pilha, buffer, i, sync_pilha, sync_entrada)
            continue

        pilha.pop()
        derivacao.append({"nao_terminal": topo, "producao": list(producao)})
        for simbolo in reversed(producao):
            if simbolo and simbolo != "ε":
                pilha.append(simbolo)

    ok = not erros and i == len(buffer) - 1 and not pilha
    return {
        "ok": ok,
        "derivacao": derivacao,
        "erros": erros,
        "tokens": buffer,
    }


def _normalizar_meta(tabela_ll1) -> dict:
    if not isinstance(tabela_ll1, dict):
        raise TypeError("tabela_ll1 deve ser dict (meta com tabela_ll1 e simbolo_inicial).")
    if "tabela_ll1" in tabela_ll1 and "nao_terminais" in tabela_ll1 and "simbolo_inicial" in tabela_ll1:
        return tabela_ll1
    raise ValueError(
        "Esperado dict com chaves 'tabela_ll1', 'nao_terminais', 'simbolo_inicial'."
    )


def _terminal_de_token(token: dict) -> str:
    tipo = token.get("tipo")
    valor = token.get("valor", "")
    if tipo == "EOF":
        return "$"
    if tipo == "ABRE_PAREN":
        return "("
    if tipo == "FECHA_PAREN":
        return ")"
    if tipo == "NUMERO":
        return "NUM"
    if tipo == "IDENTIFICADOR":
        return "ID"
    if tipo == "OPERADOR_ARIT":
        return valor
    if tipo == "OPERADOR_REL":
        return valor
    if tipo == "RES":
        return "RES"
    if tipo == "START":
        return "START"
    if tipo == "END":
        return "END"
    if tipo == "IF":
        return "IF"
    if tipo == "WHILE":
        return "WHILE"
    return valor


def _reportarErro(token, esperado, linha, emitir: bool = True) -> str:
    """Monta mensagem de erro sintático. Se ``emitir``, imprime em stdout."""
    if isinstance(esperado, (set, frozenset)):
        esp = ", ".join(sorted(esperado))
    else:
        esp = str(esperado)
    obtido_tipo = token.get("tipo", "?")
    obtido_valor = token.get("valor", "")
    lin = linha or token.get("linha", 0)
    msg = (
        "Erro sintatico na linha {0}: encontrado token tipo={1!r} valor={2!r}; "
        "esperado: {3}".format(lin, obtido_tipo, obtido_valor, esp)
    )
    if emitir:
        print(msg)
    return msg


def _sincronizar_entrada(buffer, i: int, sync: frozenset) -> int:
    while i < len(buffer) and _terminal_de_token(buffer[i]) not in sync:
        i += 1
    return i


def _recuperacao_panico(pilha, buffer, i, sync_pilha, sync_entrada):
    while pilha and pilha[-1] not in sync_pilha:
        pilha.pop()
    if pilha and pilha[-1] in sync_pilha and pilha[-1] != "$":
        pilha.pop()
    i = _sincronizar_entrada(buffer, i, sync_entrada)
    return pilha, i


# --- Fixtures LL(1) mínimas até construirGramatica() ficar pronto ---


def _meta_fixture_expr_plana():
    
    nts = frozenset({"S", "A", "B"})
    tab = {
        ("S", "("): ["(", "A", ")"],
        ("A", "NUM"): ["NUM", "B"],
        ("B", "NUM"): ["NUM", "+"],
    }
    return {
        "tabela_ll1": tab,
        "nao_terminais": nts,
        "simbolo_inicial": "S",
    }


def _meta_fixture_if_simples():
    """Aceita ``( ID ID > ID IF )``."""
    nts = frozenset({"S", "L1", "L2", "L3", "L4", "L5"})
    tab = {
        ("S", "("): ["(", "L1"],
        ("L1", "ID"): ["ID", "L2"],
        ("L2", "ID"): ["ID", "L3"],
        ("L3", ">"): [">", "L4"],
        ("L4", "ID"): ["ID", "L5"],
        ("L5", "IF"): ["IF", ")"],
    }
    return {
        "tabela_ll1": tab,
        "nao_terminais": nts,
        "simbolo_inicial": "S",
    }


def _meta_fixture_while_simples():
    """Aceita ``( ID ID < ID WHILE )``."""
    nts = frozenset({"S", "L1", "L2", "L3", "L4", "L5"})
    tab = {
        ("S", "("): ["(", "L1"],
        ("L1", "ID"): ["ID", "L2"],
        ("L2", "ID"): ["ID", "L3"],
        ("L3", "<"): ["<", "L4"],
        ("L4", "ID"): ["ID", "L5"],
        ("L5", "WHILE"): ["WHILE", ")"],
    }
    return {
        "tabela_ll1": tab,
        "nao_terminais": nts,
        "simbolo_inicial": "S",
    }


def _tokens_expr_plana():
    return [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "3.14", "linha": 1},
        {"tipo": "NUMERO", "valor": "2.0", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
    ]


def _tokens_expr_invalida():
    return [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 2},
        {"tipo": "IDENTIFICADOR", "valor": "A", "linha": 2},
        {"tipo": "IDENTIFICADOR", "valor": "B", "linha": 2},
        {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 2},
        {"tipo": "IDENTIFICADOR", "valor": "C", "linha": 2},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 2},
    ]


def _testarExpressaoValida():
    meta = _meta_fixture_expr_plana()
    r = parsear(_tokens_expr_plana(), meta)
    assert r["ok"], r["erros"]
    assert len(r["derivacao"]) >= 3

    meta_if = _meta_fixture_if_simples()
    tok_if = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "A", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "B", "linha": 1},
        {"tipo": "OPERADOR_REL", "valor": ">", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "C", "linha": 1},
        {"tipo": "IF", "valor": "IF", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
    ]
    r_if = parsear(tok_if, meta_if)
    assert r_if["ok"], r_if["erros"]

    meta_w = _meta_fixture_while_simples()
    tok_w = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "I", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "J", "linha": 1},
        {"tipo": "OPERADOR_REL", "valor": "<", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "K", "linha": 1},
        {"tipo": "WHILE", "valor": "WHILE", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
    ]
    r_w = parsear(tok_w, meta_w)
    assert r_w["ok"], r_w["erros"]

    print("OK: _testarExpressaoValida")


def _testarExpressaoInvalida():
    meta = _meta_fixture_expr_plana()
    r = parsear(_tokens_expr_invalida(), meta)
    assert not r["ok"]
    assert r["erros"]
    for e in r["erros"]:
        assert "linha" in e.lower() or "Linha" in e

    r2 = parsear(
        [
            {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 3},
        ],
        meta,
    )
    assert not r2["ok"]

    print("OK: _testarExpressaoInvalida")


def _testarEstruturaControle():
    _testarExpressaoValida()
    print("OK: _testarEstruturaControle (fixtures IF e WHILE)")


if __name__ == "__main__":
    _testarExpressaoValida()
    _testarExpressaoInvalida()
    _testarEstruturaControle()
