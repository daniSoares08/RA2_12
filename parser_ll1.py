# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12


def parsear(tokens, tabela_ll1):
    # TODO: inicializar pilha de análise com símbolo inicial da gramática e marcador de fim ($)
    # TODO: inicializar buffer de entrada com os tokens recebidos
    # TODO: implementar laço principal do algoritmo LL1 com pilha:
    #         enquanto pilha não vazia:
    #           se topo == terminal: comparar com token atual e avançar
    #           se topo == não-terminal: consultar tabela_ll1 e empilhar produção
    #           se erro: chamar _reportarErro()
    # TODO: construir e retornar estrutura de derivação para uso em gerarArvore()
    pass


def _reportarErro(token, esperado, linha):
    # TODO: formatar e exibir mensagem de erro sintático indicando linha, token encontrado e esperado
    # TODO: implementar recuperação básica de erros (modo pânico ou sincronização)
    pass


def _testarExpressaoValida():
    # TODO: testar expressões válidas simples: (3.14 2.0 +)
    # TODO: testar expressões aninhadas: ((A B +) (C D *) /)
    # TODO: testar comandos especiais: (0 RES), (3.14 X MEM), (X)
    pass


def _testarExpressaoInvalida():
    # TODO: testar erros sintáticos: (A B + C), (, (A B, etc.
    # TODO: verificar mensagens de erro claras com número de linha
    pass


def _testarEstruturaControle():
    # TODO: testar estruturas de decisão e laços definidos pelo grupo
    pass
