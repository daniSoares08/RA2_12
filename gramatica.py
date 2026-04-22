# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12


def calcularFirst(gramatica):
    # TODO: calcular conjuntos FIRST para cada não-terminal da gramática
    # TODO: tratar produções com epsilon (vazio)
    # TODO: retornar dicionário {não-terminal: conjunto FIRST}
    pass


def calcularFollow(gramatica, first):
    # TODO: calcular conjuntos FOLLOW para cada não-terminal da gramática
    # TODO: usar conjuntos FIRST já calculados como auxiliar
    # TODO: retornar dicionário {não-terminal: conjunto FOLLOW}
    pass


def construirTabelaLL1(gramatica, first, follow):
    # TODO: construir tabela de análise LL1 mapeando (não-terminal, terminal) -> produção
    # TODO: verificar ausência de conflitos (garantir que a gramática é LL1)
    # TODO: lançar erro se conflito for encontrado
    # TODO: retornar dicionário {(não-terminal, terminal): produção}
    pass


def construirGramatica():
    # TODO: definir regras de produção para expressões RPN em notação pós-fixada
    # TODO: incluir regras para comandos especiais: (N RES), (V MEM), (MEM)
    # TODO: incluir regras para estruturas de controle (decisão e laços) definidas pelo grupo
    # TODO: incluir regras para programa completo: (START) ... (END)
    # TODO: incluir tratamento de aninhamento sem limite definido
    # TODO: chamar calcularFirst, calcularFollow e construirTabelaLL1
    # TODO: retornar dicionário com chaves: 'gramatica', 'first', 'follow', 'tabela_ll1'
    pass
