#!/usr/bin/env python3
# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12

import sys
import json
from pathlib import Path

from lexer import lerTokens
from gramatica import construirGramatica
from parser_ll1 import parsear
from arvore import gerarArvore, gerarAssembly, imprimirArvore, salvarArvoreJSON


def main():
    # --- 1. Valida argumento de linha de comando ---
    if len(sys.argv) < 2:
        print("Uso: python AnalisadorSintatico.py <arquivo_fonte>", file=sys.stderr)
        print("Exemplo: python AnalisadorSintatico.py testes/teste1.txt", file=sys.stderr)
        sys.exit(1)

    caminho_fonte = sys.argv[1]

    # --- 2. Análise léxica ---
    print(f"[LEX] Lendo tokens de: {caminho_fonte}")
    try:
        tokens = lerTokens(caminho_fonte)
    except FileNotFoundError as e:
        print(f"[ERRO] Arquivo não encontrado: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"[ERRO LÉXICO] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[LEX] {len(tokens)} token(s) reconhecido(s).")

    # --- 3. Constrói gramática, FIRST, FOLLOW e tabela LL(1) ---
    print("[GRAM] Construindo gramática e tabela LL(1)...")
    try:
        info_gramatica = construirGramatica()
    except ValueError as e:
        print(f"[ERRO GRAMÁTICA] Conflito LL(1): {e}", file=sys.stderr)
        sys.exit(1)

    tabela_ll1 = info_gramatica["tabela_ll1"]

    # --- 4. Análise sintática (parser LL(1) com pilha) ---
    print("[PARSE] Analisando sintaticamente...")
    resultado = parsear(tokens, tabela_ll1)

    if resultado["erros"]:
        print("[AVISOS SINTÁTICOS]")
        for erro in resultado["erros"]:
            print(f"  {erro}")

    if not resultado["ok"]:
        print("[ERRO] Análise sintática falhou. Corrija os erros acima e tente novamente.",
              file=sys.stderr)
        sys.exit(1)

    print(f"[PARSE] OK — {len(resultado['derivacao'])} passo(s) de derivação.")

    # --- 5. Constrói a árvore sintática ---
    print("[ARVORE] Construindo árvore sintática...")
    try:
        arvore = gerarArvore(resultado)
    except ValueError as e:
        print(f"[ERRO ÁRVORE] {e}", file=sys.stderr)
        sys.exit(1)

    # --- 6. Salva a árvore em JSON ---
    base = Path(caminho_fonte).stem          # e.g. "teste1"
    caminho_json = Path(f"{base}_arvore.json")
    salvarArvoreJSON(arvore, caminho_json)
    print(f"[ARVORE] Árvore salva em: {caminho_json}")

    # Exibe a árvore no terminal (útil para depuração)
    print("[ARVORE] Estrutura:")
    imprimirArvore(arvore)

    # --- 7. Gera código Assembly ARMv7 ---
    print("[ASM] Gerando Assembly ARMv7...")
    try:
        assembly = gerarAssembly(arvore)
    except Exception as e:
        print(f"[ERRO ASM] {e}", file=sys.stderr)
        sys.exit(1)

    caminho_asm = Path(f"{base}.s")
    caminho_asm.write_text(assembly, encoding="utf-8")
    print(f"[ASM] Código Assembly salvo em: {caminho_asm}")
    print()
    print("=" * 60)
    print(assembly)
    print("=" * 60)


if __name__ == "__main__":
    main()