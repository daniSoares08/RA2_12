# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12


def gerarArvore(derivacao):
    # TODO: transformar a estrutura de derivação do parser em árvore sintática
    # TODO: cada nó deve conter: tipo, valor, filhos (lista de nós)
    # TODO: salvar árvore em arquivo JSON (ou formato customizado definido pelo grupo)
    # TODO: imprimir árvore em formato legível para documentação (texto indentado)
    # TODO: retornar nó raiz da árvore sintática
    pass


def gerarAssembly(arvore):
    # TODO: percorrer a árvore sintática em pós-ordem para gerar código Assembly ARMv7
    # TODO: gerar instruções para operações aritméticas (+, -, *, |, /, %, ^) usando pilha
    # TODO: gerar instruções para comandos especiais (RES, MEM)
    # TODO: gerar instruções para estruturas de controle (decisão e laços) com labels
    # TODO: tratar literais inteiros, reais (double IEEE 754) e variáveis de memória
    # TODO: garantir execução correta no Cpulator-ARMv7 DEC1-SOC(v16.1)
    # TODO: retornar string com o código Assembly gerado
    pass


def _imprimirArvore(no, nivel=0):
    # TODO: imprimir o nó e seus filhos com indentação proporcional ao nível
    pass


def _salvarArvoreJSON(arvore, caminho_saida):
    # TODO: serializar a árvore sintática para JSON e salvar no arquivo indicado
    pass


def _testarGeracaoArvore():
    # TODO: testar geração de árvore para expressões simples e aninhadas
    # TODO: testar geração de árvore para estruturas de controle
    pass


def _testarGeracaoAssembly():
    # TODO: testar código Assembly gerado para cada operação aritmética
    # TODO: testar Assembly para expressões aninhadas e estruturas de controle
    # TODO: verificar resultado correto no Cpulator-ARMv7
    pass
