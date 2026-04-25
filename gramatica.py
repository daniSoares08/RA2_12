# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12

from __future__ import annotations

from collections import OrderedDict

EPSILON = "ε"
SIMBOLO_INICIAL = "PROGRAMA"


def _first_da_sequencia(sequencia, first, gramatica):
    """Calcula FIRST de uma sequência de símbolos.

    A sequência pode conter terminais, não-terminais ou EPSILON. Essa função é
    usada tanto no cálculo de FOLLOW quanto na construção da tabela LL(1).
    """
    if not sequencia or sequencia == [EPSILON]:
        return {EPSILON}

    resultado = set()
    todos_aceitam_vazio = True

    for simbolo in sequencia:
        if simbolo == EPSILON:
            resultado.add(EPSILON)
            break

        if simbolo not in gramatica:  # terminal
            resultado.add(simbolo)
            todos_aceitam_vazio = False
            break

        resultado.update(first[simbolo] - {EPSILON})
        if EPSILON not in first[simbolo]:
            todos_aceitam_vazio = False
            break

    if todos_aceitam_vazio:
        resultado.add(EPSILON)

    return resultado


def calcularFirst(gramatica):
    """Calcula os conjuntos FIRST para todos os não-terminais.

    Retorna um dicionário no formato:
        {"NAO_TERMINAL": {"terminal1", "terminal2", ...}}
    """
    first = {nao_terminal: set() for nao_terminal in gramatica}

    mudou = True
    while mudou:
        mudou = False

        for nao_terminal, producoes in gramatica.items():
            for producao in producoes:
                antes = len(first[nao_terminal])

                if not producao or producao == [EPSILON]:
                    first[nao_terminal].add(EPSILON)
                else:
                    first[nao_terminal].update(
                        _first_da_sequencia(producao, first, gramatica)
                    )

                if len(first[nao_terminal]) != antes:
                    mudou = True

    return first


def calcularFollow(gramatica, first):
    """Calcula os conjuntos FOLLOW para todos os não-terminais.

    O símbolo inicial recebe '$', que representa fim da entrada.
    """
    follow = {nao_terminal: set() for nao_terminal in gramatica}
    follow[SIMBOLO_INICIAL].add("$")

    mudou = True
    while mudou:
        mudou = False

        for origem, producoes in gramatica.items():
            for producao in producoes:
                for indice, simbolo in enumerate(producao):
                    if simbolo not in gramatica:
                        continue

                    beta = producao[indice + 1 :]
                    first_beta = _first_da_sequencia(beta, first, gramatica)

                    antes = len(follow[simbolo])
                    follow[simbolo].update(first_beta - {EPSILON})

                    if not beta or EPSILON in first_beta:
                        follow[simbolo].update(follow[origem])

                    if len(follow[simbolo]) != antes:
                        mudou = True

    return follow


def construirTabelaLL1(gramatica, first, follow):
    """Constrói a tabela LL(1) e acusa conflito quando existir.

    A tabela retornada usa chaves no formato (nao_terminal, terminal) e valores
    contendo a produção aplicada.
    """
    tabela = {}

    for nao_terminal, producoes in gramatica.items():
        for producao in producoes:
            first_producao = _first_da_sequencia(producao, first, gramatica)

            for terminal in sorted(first_producao - {EPSILON}):
                chave = (nao_terminal, terminal)
                if chave in tabela and tabela[chave] != producao:
                    raise ValueError(
                        "Conflito LL(1) em {0}: {1} e {2}".format(
                            chave, tabela[chave], producao
                        )
                    )
                tabela[chave] = list(producao)

            if EPSILON in first_producao:
                for terminal in sorted(follow[nao_terminal]):
                    chave = (nao_terminal, terminal)
                    if chave in tabela and tabela[chave] != producao:
                        raise ValueError(
                            "Conflito LL(1) em {0}: {1} e {2}".format(
                                chave, tabela[chave], producao
                            )
                        )
                    tabela[chave] = list(producao)

    return tabela


def construirGramatica():
    """Define a gramática fixa da linguagem e monta FIRST, FOLLOW e tabela LL(1).
    """
    gramatica = OrderedDict(
        {
            # Programa completo: (START) comandos... (END)
            "PROGRAMA": [["(", "START", ")", "LISTA_CMD"]],

            # Lista de comandos fatorada para remover o conflito entre comando e (END).
            "LISTA_CMD": [["(", "LISTA_APOS_ABRE"]],
            "LISTA_APOS_ABRE": [
                ["END", ")"],
                ["CMD", ")", "LISTA_CMD"],
            ],

            # Um comando é o conteúdo que fica dentro dos parênteses externos.
            "CMD": [["EXPR_RPN"]],

            # Expressões/comandos em RPN. As alternativas foram fatoradas para
            # permitir LL(1) mesmo quando NUM, ID e '(' podem iniciar expressões.
            "EXPR_RPN": [
                ["ID", "EXPR_RPN_APOS_ID"],
                ["MEM", "EXPR_RPN_APOS_ID"],
                ["NUM", "EXPR_RPN_APOS_NUM"],
                ["(", "EXPR_RPN", ")", "EXPR_RPN_APOS_GRUPO"],
            ],
            "EXPR_RPN_APOS_ID": [
                ["EXPR", "FINALIZADOR"],
                [EPSILON],
            ],
            "EXPR_RPN_APOS_NUM": [
                ["RES"],
                ["EXPR", "FINALIZADOR"],
            ],
            "EXPR_RPN_APOS_GRUPO": [["EXPR", "FINALIZADOR"]],

            # Operando válido: número, identificador/memória ou expressão aninhada.
            "EXPR": [
                ["NUM"],
                ["ID"],
                ["MEM"],
                ["(", "EXPR_RPN", ")"],
            ],

            # Finalizadores pós-fixados: operadores aritméticos/relacionais,
            # comandos especiais e estruturas de controle.
            "FINALIZADOR": [
                ["OPERADOR"],
                ["MEM"],
                ["ID"],  # compatibilidade temporária com o lexer atual para a keyword MEM
                ["IF"],
                ["WHILE"],
            ],
            "OPERADOR": [
                ["+"],
                ["-"],
                ["*"],
                ["|"],
                ["/"],
                ["%"],
                ["^"],
                [">"],
                ["<"],
                ["=="],
                ["!="],
                [">="],
                ["<="],
            ],
        }
    )

    first = calcularFirst(gramatica)
    follow = calcularFollow(gramatica, first)
    tabela_bruta = construirTabelaLL1(gramatica, first, follow)

    # O parser_ll1.py atual espera que a tabela venha junto com metadados.
    # Mantemos também as chaves (nao_terminal, terminal) no próprio dicionário
    # para preservar a interface de tabela mapeada descrita na divisão da tarefa.
    tabela_ll1 = dict(tabela_bruta)
    tabela_ll1.update(
        {
            "tabela_ll1": tabela_bruta,
            "nao_terminais": set(gramatica.keys()),
            "simbolo_inicial": SIMBOLO_INICIAL,
            "sincronizar_entrada": {")", "END", "$"},
            "sincronizar_pilha": set(gramatica.keys()) | {")", "END", "$"},
        }
    )

    return {
        "gramatica": gramatica,
        "first": first,
        "follow": follow,
        "tabela_ll1": tabela_ll1,
        "tabela_ll1_bruta": tabela_bruta,
        "simbolo_inicial": SIMBOLO_INICIAL,
        "epsilon": EPSILON,
    }
