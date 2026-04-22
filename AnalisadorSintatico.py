#!/usr/bin/env python3
# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12

import sys
from lexer import lerTokens
from gramatica import construirGramatica
from parser_ll1 import parsear
from arvore import gerarArvore, gerarAssembly


def main():
    # TODO: validar que um argumento foi passado (nome do arquivo)
    # TODO: chamar lerTokens(sys.argv[1]) para obter o vetor de tokens
    # TODO: chamar construirGramatica() para obter gramática, FIRST, FOLLOW e tabela LL1
    # TODO: chamar parsear(tokens, tabela_ll1) para obter a estrutura de derivação
    # TODO: chamar gerarArvore(derivacao) para construir a árvore sintática
    # TODO: chamar gerarAssembly(arvore) para gerar o código Assembly ARMv7
    # TODO: salvar árvore em arquivo (JSON ou formato customizado)
    # TODO: exibir resultado ou erros de forma clara ao usuário
    pass


if __name__ == "__main__":
    main()
