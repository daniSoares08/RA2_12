# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12

from __future__ import annotations

import json
import re
from pathlib import Path


TIPOS_VALIDOS = frozenset(
    {
        "ABRE_PAREN",
        "FECHA_PAREN",
        "NUMERO",
        "OPERADOR_ARIT",
        "OPERADOR_REL",
        "IDENTIFICADOR",
        "RES",
        "START",
        "END",
        "IF",
        "WHILE",
    }
)

_LEXEMA_NUMERO = re.compile(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$")
_LEXEMAS_EM_LINHA = re.compile(r"\(|\)|[^()\s]+")


def lerTokens(arquivo):
    
    caminho = Path(arquivo)
    if not caminho.is_file():
        raise FileNotFoundError("Arquivo nao encontrado: {0}".format(arquivo))

    tokens: list[dict] = []
    linha_atual = 1
    saldo = 0
    with caminho.open(encoding="utf-8") as f:
        for num_linha_arquivo, linha in enumerate(f, start=1):
            s = linha.strip()
            if not s:
                continue
            tokens_linha, linha_atual, saldo = _parse_linha_tokens(
                s, num_linha_arquivo, linha_atual, saldo
            )
            for token in tokens_linha:
                if not _validarToken(token):
                    raise ValueError(
                        "Token invalido na linha {0} do arquivo ({1}): {2}".format(
                            num_linha_arquivo,
                            caminho,
                            token,
                        )
                    )
                tokens.append(token)

            if "\t" not in s and "|" not in s and not s.startswith("{"):
                if not _linha_parece_codigo_fonte(s):
                    if s == "(":
                        saldo += 1
                    elif s == ")":
                        saldo -= 1
                        if saldo < 0:
                            raise ValueError(
                                "Parenteses desbalanceados no arquivo de tokens, linha {0}".format(
                                    num_linha_arquivo
                                )
                            )
                        if saldo == 0:
                            linha_atual += 1
    if saldo != 0:
        raise ValueError("Parenteses desbalanceados no arquivo de tokens (EOF).")
    return tokens


def _parse_linha_tokens(
    linha: str, num_linha_arquivo: int, linha_atual: int, saldo: int
) -> tuple[list[dict], int, int]:
    if linha.startswith("{"):
        try:
            d = json.loads(linha)
        except json.JSONDecodeError as e:
            raise ValueError(
                "JSON invalido na linha {0} do arquivo: {1}".format(num_linha_arquivo, e)
            ) from e
        return (
            [
                {
                    "tipo": str(d.get("tipo", "")),
                    "valor": str(d.get("valor", "")),
                    "linha": int(d.get("linha", 0)),
                }
            ],
            linha_atual,
            saldo,
        )

    if "\t" in linha:
        partes = linha.split("\t", 2)
        if len(partes) != 3:
            raise ValueError(
                "Linha {0}: esperado tipo, valor e linha (tab/pipe), obteve: {1!r}".format(
                    num_linha_arquivo,
                    linha,
                )
            )
        tipo, valor, linha_txt = partes[0].strip(), partes[1], partes[2].strip()
        try:
            nlinha = int(linha_txt)
        except ValueError as e:
            raise ValueError(
                "Linha {0}: numero de linha invalido: {1!r}".format(num_linha_arquivo, linha_txt)
            ) from e
        return ([{"tipo": tipo, "valor": valor, "linha": nlinha}], linha_atual, saldo)

    if linha.count("|") == 2 and not _linha_parece_codigo_fonte(linha):
        partes = linha.split("|", 2)
        if len(partes) != 3:
            raise ValueError(
                "Linha {0}: esperado tipo, valor e linha (tab/pipe), obteve: {1!r}".format(
                    num_linha_arquivo,
                    linha,
                )
            )
        tipo, valor, linha_txt = partes[0].strip(), partes[1], partes[2].strip()
        try:
            nlinha = int(linha_txt)
        except ValueError as e:
            raise ValueError(
                "Linha {0}: numero de linha invalido: {1!r}".format(num_linha_arquivo, linha_txt)
            ) from e
        return ([{"tipo": tipo, "valor": valor, "linha": nlinha}], linha_atual, saldo)

    if _linha_parece_codigo_fonte(linha):
        # Tokeniza a linha em lexemas e anota a linha do arquivo-fonte
        lexemas = _LEXEMAS_EM_LINHA.findall(linha)
        out: list[dict] = []
        saldo_linha = 0
        for lex in lexemas:
            tok = _token_de_lexema(lex, num_linha_arquivo, num_linha_arquivo)
            out.append(tok)
            if tok["tipo"] == "ABRE_PAREN":
                saldo_linha += 1
            elif tok["tipo"] == "FECHA_PAREN":
                saldo_linha -= 1
                if saldo_linha < 0:
                    raise ValueError(
                        "Parenteses desbalanceados na linha {0} do arquivo-fonte.".format(
                            num_linha_arquivo
                        )
                    )
        if saldo_linha != 0:
            raise ValueError(
                "Parenteses desbalanceados na linha {0} do arquivo-fonte.".format(num_linha_arquivo)
            )
        return out, linha_atual, 0

    return ([_token_de_lexema(linha, linha_atual, num_linha_arquivo)], linha_atual, saldo)


def _linha_parece_codigo_fonte(linha: str) -> bool:
    s = linha.strip()
    if not s:
        return False
    if s.startswith("{") or "\t" in s:
        return False
    return (" " in s) or (s.startswith("(") and s.endswith(")") and len(s) > 1)


def _token_de_lexema(lexema: str, linha: int, num_linha_arquivo: int) -> dict:
    if lexema == "(":
        return {"tipo": "ABRE_PAREN", "valor": "(", "linha": linha}
    if lexema == ")":
        return {"tipo": "FECHA_PAREN", "valor": ")", "linha": linha}
    if _LEXEMA_NUMERO.match(lexema):
        return {"tipo": "NUMERO", "valor": lexema, "linha": linha}
    if lexema in {">", "<", "==", "!=", ">=", "<="}:
        return {"tipo": "OPERADOR_REL", "valor": lexema, "linha": linha}
    if lexema in {"+", "-", "*", "|", "/", "%", "^", "//"}:
        return {"tipo": "OPERADOR_ARIT", "valor": lexema, "linha": linha}
    if lexema == "RES":
        return {"tipo": "RES", "valor": "RES", "linha": linha}
    if lexema == "START":
        return {"tipo": "START", "valor": "START", "linha": linha}
    if lexema == "END":
        return {"tipo": "END", "valor": "END", "linha": linha}
    if lexema == "IF":
        return {"tipo": "IF", "valor": "IF", "linha": linha}
    if lexema == "WHILE":
        return {"tipo": "WHILE", "valor": "WHILE", "linha": linha}
    if lexema.isupper() and lexema.isalpha():
        return {"tipo": "IDENTIFICADOR", "valor": lexema, "linha": linha}
    raise ValueError(
        "Lexema invalido na linha {0} do arquivo: {1!r}".format(num_linha_arquivo, lexema)
    )


def _validarToken(token) -> bool:
    if not isinstance(token, dict):
        return False
    if set(token.keys()) < {"tipo", "valor", "linha"}:
        return False
    tipo = token.get("tipo")
    valor = token.get("valor")
    linha = token.get("linha")
    if tipo not in TIPOS_VALIDOS:
        return False
    if not isinstance(valor, str):
        return False
    if not isinstance(linha, int) or linha < 1:
        return False

    if tipo == "ABRE_PAREN" and valor != "(":
        return False
    if tipo == "FECHA_PAREN" and valor != ")":
        return False
    if tipo == "NUMERO" and not _LEXEMA_NUMERO.match(valor):
        return False
    if tipo == "OPERADOR_ARIT" and valor not in {"+", "-", "*", "|", "/", "%", "^", "//"}:
        return False
    if tipo == "OPERADOR_REL" and valor not in {">", "<", "==", "!=", ">=", "<="}:
        return False
    if tipo == "IDENTIFICADOR":
        if not valor or not valor.isupper() or not valor.isalpha():
            return False
    if tipo == "RES" and valor != "RES":
        return False
    if tipo == "START" and valor != "START":
        return False
    if tipo == "END" and valor != "END":
        return False
    if tipo == "IF" and valor != "IF":
        return False
    if tipo == "WHILE" and valor != "WHILE":
        return False
    return True
