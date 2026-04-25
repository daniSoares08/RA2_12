# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12

from __future__ import annotations

import json
from pathlib import Path

# Todos os não-terminais da gramática definida em gramatica.py
NAO_TERMINAIS = frozenset({
    "PROGRAMA",
    "LISTA_CMD",
    "LISTA_APOS_ABRE",
    "CMD",
    "EXPR_RPN",
    "EXPR_RPN_APOS_ID",
    "EXPR_RPN_APOS_NUM",
    "EXPR_RPN_APOS_GRUPO",
    "EXPR",
    "FINALIZADOR",
    "OPERADOR",
})

EPSILON = "ε"

# ---------------------------------------------------------------------------
# Construção da árvore sintática
# ---------------------------------------------------------------------------

def gerarArvore(resultado_parser: dict) -> dict:
    """Constrói a árvore sintática a partir do resultado de parsear().

    Parâmetros
    ----------
    resultado_parser : dict
        Dicionário com as chaves ``ok``, ``derivacao`` e ``tokens`` conforme
        retornado por ``parsear()`` em ``parser_ll1.py``.

    Retorna
    -------
    dict
        Nó raiz da árvore no formato ``{"tipo": str, "valor": str|None, "filhos": list}``.

    Raises
    ------
    ValueError
        Se o resultado do parser indicar erros sintáticos.
    """
    if not resultado_parser.get("ok", False):
        erros = resultado_parser.get("erros", [])
        raise ValueError(
            "Derivação contém erros sintáticos:\n" + "\n".join(erros)
        )

    derivacao: list[dict] = resultado_parser["derivacao"]
    tokens: list[dict] = resultado_parser["tokens"]

    # Índices mutáveis compartilhados pela recursão
    deriv_idx = [0]
    token_idx = [0]

    raiz = _construir_no(derivacao, deriv_idx, tokens, token_idx)
    return raiz


def _construir_no(
    derivacao: list[dict],
    deriv_idx: list[int],
    tokens: list[dict],
    token_idx: list[int],
) -> dict | None:
    """Reconstrói recursivamente a árvore a partir da sequência de derivações
    em pré-ordem emitida pelo parser LL(1).

    Cada entrada de ``derivacao`` tem o formato::

        {"nao_terminal": "NOME", "producao": ["s1", "s2", ...]}

    A lista é consumida da esquerda para a direita. Para cada símbolo da
    produção:
    - Se for não-terminal → consome o próximo passo da derivação recursivamente.
    - Se for terminal (incluindo ``ε``) → consome o próximo token do buffer.
    """
    if deriv_idx[0] >= len(derivacao):
        return None

    passo = derivacao[deriv_idx[0]]
    nao_terminal: str = passo["nao_terminal"]
    producao: list[str] = passo["producao"]
    deriv_idx[0] += 1

    filhos: list[dict] = []

    for simbolo in producao:
        if simbolo == EPSILON:
            # Produção vazia — não gera filho nem consome token
            continue

        if simbolo in NAO_TERMINAIS:
            filho = _construir_no(derivacao, deriv_idx, tokens, token_idx)
            if filho is not None:
                filhos.append(filho)
        else:
            # Terminal: consome o próximo token do buffer se ele casar
            while token_idx[0] < len(tokens):
                tok = tokens[token_idx[0]]
                term = _terminal_de_token(tok)
                if term == "$":
                    break
                token_idx[0] += 1
                if term == simbolo:
                    folha = _folha_de_token(tok)
                    if folha is not None:
                        filhos.append(folha)
                    break

    return {"tipo": nao_terminal, "valor": None, "filhos": filhos}


def _terminal_de_token(token: dict) -> str:
    """Mesma lógica de ``_terminal_de_token`` do ``parser_ll1.py``."""
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
    if tipo in ("OPERADOR_ARIT", "OPERADOR_REL"):
        return valor
    if tipo in ("RES", "START", "END", "IF", "WHILE"):
        return tipo
    return valor


def _folha_de_token(token: dict) -> dict | None:
    """Cria um nó-folha para um token terminal.

    Parênteses estruturais e palavras-chave de delimitação (START, END) não
    geram folhas visíveis na árvore para mantê-la limpa.
    """
    tipo = token.get("tipo")
    valor = token.get("valor", "")

    if tipo in ("ABRE_PAREN", "FECHA_PAREN"):
        return None  # parênteses são estrutura, não conteúdo

    tipo_folha_map = {
        "NUMERO":        "NUM",
        "IDENTIFICADOR": "ID",
        "OPERADOR_ARIT": "OP",
        "OPERADOR_REL":  "OP",
        "RES":           "RES",
        "START":         "START",
        "END":           "END",
        "IF":            "IF",
        "WHILE":         "WHILE",
    }
    tipo_folha = tipo_folha_map.get(tipo, tipo)
    return {"tipo": tipo_folha, "valor": valor, "filhos": []}


# ---------------------------------------------------------------------------
# Geração de código Assembly ARMv7 (Cpulator-ARMv7 DEC1-SOC v16.1)
# ---------------------------------------------------------------------------

def gerarAssembly(arvore: dict) -> str:
    """Percorre a árvore sintática e emite código Assembly ARMv7.

    Convenções adotadas:
    - Valores inteiros trafegam na pilha (SP) via PUSH/POP.
    - Registradores temporários: R0–R3 (operandos), R4–R11 (salvo pelo callee).
    - R12 (IP) é usado como temporário interno.
    - Variáveis de memória ficam na seção .data.
    - Potenciação (^) é implementada com loop inline.
    - Divisão real (|) usa SDIV (inteira) por limitação do Cpulator.
    """
    if arvore is None:
        return ""

    secao_data: list[str] = []
    secao_text: list[str] = []
    variaveis: dict[str, str] = {}
    label_counter: list[int] = [0]

    def novo_label(prefixo: str = "L") -> str:
        lbl = f"{prefixo}{label_counter[0]}"
        label_counter[0] += 1
        return lbl

    def declarar_variavel(nome: str) -> str:
        """Declara variável na seção .data se ainda não existir."""
        if nome not in variaveis:
            label = f"var_{nome.lower()}"
            variaveis[nome] = label
            secao_data.append(f"{label}:    .word 0")
        return variaveis[nome]

    def emit(*linhas: str) -> None:
        for linha in linhas:
            secao_text.append(linha)

    def _visitar(no: dict) -> None:
        """Visita recursiva da árvore gerando código."""
        if no is None:
            return

        tipo: str = no["tipo"]
        valor = no.get("valor")
        filhos: list[dict] = no.get("filhos", [])

        # --- Nó raiz do programa ---
        if tipo == "PROGRAMA":
            for filho in filhos:
                _visitar(filho)
            return

        # --- Nós estruturais transparentes: apenas repassam aos filhos ---
        if tipo in ("LISTA_CMD", "LISTA_APOS_ABRE", "CMD"):
            for filho in filhos:
                _visitar(filho)
            return

        # --- Palavras-chave estruturais sem geração de código ---
        if tipo in ("START", "END"):
            return

        # --- Número literal ---
        if tipo == "NUM":
            if valor and "." in valor:
                intval = int(float(valor))
                emit(f"    @ float {valor} truncado para {intval}")
                emit(f"    MOV  R0, #{intval}")
            else:
                intval = int(valor) if valor else 0
                if -255 <= intval <= 255:
                    emit(f"    MOV  R0, #{intval}")
                else:
                    emit(f"    LDR  R0, ={intval}")
            emit("    PUSH {R0}")
            return

        # --- Identificador / leitura de memória ---
        if tipo == "ID":
            label = declarar_variavel(valor)
            emit(f"    @ leitura de {valor}")
            emit(f"    LDR  R0, ={label}")
            emit("    LDR  R0, [R0]")
            emit("    PUSH {R0}")
            return

        # --- Operador (aritmético ou relacional) ---
        if tipo == "OP":
            op = valor
            emit("    POP  {R1}")   # segundo operando (topo)
            emit("    POP  {R0}")   # primeiro operando
            _gerar_op(op, emit, novo_label)
            emit("    PUSH {R0}")
            return

        # --- RES ---
        if tipo == "RES":
            emit("    @ RES: resultado anterior nao suportado em runtime ARMv7")
            emit("    MOV  R0, #0")
            emit("    PUSH {R0}")
            return

        # ---------------------------------------------------------------
        # EXPR_RPN: núcleo da linguagem — detecta padrão semântico
        # ---------------------------------------------------------------
        if tipo == "EXPR_RPN":
            _visitar_expr_rpn(filhos, emit, declarar_variavel, novo_label, _visitar)
            return

        # ---------------------------------------------------------------
        # EXPR_RPN_APOS_NUM: depois de um NUM pode ser RES ou (EXPR FINALIZADOR)
        # ---------------------------------------------------------------
        if tipo == "EXPR_RPN_APOS_NUM":
            # Se o único filho é RES → já gerado pelo visitante de EXPR_RPN
            # Se são [EXPR, FINALIZADOR] → gera o segundo operando e o finalizador
            for filho in filhos:
                _visitar(filho)
            return

        # ---------------------------------------------------------------
        # EXPR_RPN_APOS_ID: depois de ID/MEM pode ser vazio ou (EXPR FINALIZADOR)
        # ---------------------------------------------------------------
        if tipo == "EXPR_RPN_APOS_ID":
            for filho in filhos:
                _visitar(filho)
            return

        # ---------------------------------------------------------------
        # EXPR_RPN_APOS_GRUPO: depois de (expr) vem sempre (EXPR FINALIZADOR)
        # ---------------------------------------------------------------
        if tipo == "EXPR_RPN_APOS_GRUPO":
            for filho in filhos:
                _visitar(filho)
            return

        # ---------------------------------------------------------------
        # EXPR: operando simples
        # ---------------------------------------------------------------
        if tipo == "EXPR":
            for filho in filhos:
                _visitar(filho)
            return

        # ---------------------------------------------------------------
        # FINALIZADOR: pode ser OPERADOR, MEM (armazenamento), ID (compat.
        # com lexer atual para MEM), IF ou WHILE
        # ---------------------------------------------------------------
        if tipo == "FINALIZADOR":
            _visitar_finalizador(filhos, emit, declarar_variavel, novo_label, _visitar)
            return

        # ---------------------------------------------------------------
        # OPERADOR: folha com o símbolo do operador — delega ao pai (OP)
        # ---------------------------------------------------------------
        if tipo == "OPERADOR":
            # O OPERADOR só tem um filho folha OP; visitamos para emitir código
            for filho in filhos:
                _visitar(filho)
            return

        # Fallback: visita filhos
        for filho in filhos:
            _visitar(filho)

    # -----------------------------------------------------------------------
    # Visitante especializado: EXPR_RPN
    # -----------------------------------------------------------------------

    def _visitar_expr_rpn(filhos, emit, declarar_variavel, novo_label, _visitar):
        """Interpreta o conteúdo de um nó EXPR_RPN.

        A estrutura real da árvore reflete os não-terminais intermediários da
        gramática LL(1) — EXPR_RPN_APOS_NUM, EXPR_RPN_APOS_ID, etc. — por isso
        não buscamos padrões por posição absoluta, mas percorremos a estrutura
        recursivamente deixando cada nó especializado fazer sua parte.

        O único caso que exige detecção explícita é o armazenamento em memória:
        (valor ID MEM) / (valor ID ID_como_MEM), que aparece como
        FINALIZADOR → ID[MEM] na árvore.
        """
        for filho in filhos:
            _visitar(filho)

    # -----------------------------------------------------------------------
    # Visitante especializado: FINALIZADOR
    # -----------------------------------------------------------------------

    def _visitar_finalizador(filhos, emit, declarar_variavel, novo_label, _visitar):
        """Interpreta o nó FINALIZADOR.

        Produções possíveis (ver gramatica.py):
          FINALIZADOR → OPERADOR          (operação aritmética/relacional)
          FINALIZADOR → MEM               (armazenamento: token MEM real)
          FINALIZADOR → ID                (compat. lexer: MEM chega como ID)
          FINALIZADOR → IF
          FINALIZADOR → WHILE

        Quando o filho é IF ou WHILE, os operandos já estão na pilha:
          - pilha[topo]   = corpo (EXPR_RPN aninhado, tipo EXPR dentro de EXPR_RPN_APOS_GRUPO)
          - pilha[topo-1] = condição
        Esses valores foram empilhados pelo visitante de EXPR_RPN_APOS_GRUPO/EXPR.

        Quando o filho é ID com valor "MEM" (ou é um nó MEM real):
          - pilha[topo]   = nome da variável como endereço (precisa pop para label)
          - pilha[topo-1] = valor a armazenar
        Mas na gramática atual o nome da variável chega como ID *antes* do MEM,
        ou seja: já foi empilhado via _visitar(ID). Por isso descartamos esse push
        e usamos o valor diretamente para montar o label.
        """
        if not filhos:
            return

        filho = filhos[0]
        tipo_f = filho["tipo"]
        valor_f = filho.get("valor", "")

        # --- Armazenamento: FINALIZADOR → ID onde valor == "MEM" ---
        # O lexer atual não tem token MEM, então "MEM" chega como IDENTIFICADOR.
        # Na árvore isso vira folha ID com valor "MEM".
        # O nó anterior (EXPR) já empilhou o nome da variável (e.g. "VAR").
        # Precisamos: (1) desfazer o push do nome, (2) pegar o label, (3) STR.
        if tipo_f == "ID" and valor_f == "MEM":
            # O nó EXPR que veio antes empilhou o ID da variável como leitura.
            # Desfazemos isso: o push do ID colocou lixo (a variável ainda não
            # foi inicializada). Descartamos com POP e usamos o valor simbólico.
            # Para saber o nome da variável precisamos olhar o contexto — ele
            # está no irmão EXPR que foi visitado logo antes. Passamos via
            # closure inspecionando as últimas emissões não é elegante; a
            # abordagem correta é o visitante de EXPR_RPN_APOS_NUM/_APOS_ID
            # reconhecer o padrão. Fazemos isso aqui de forma direta:
            # o penúltimo grupo de emissões foi: "leitura de VAR / LDR / LDR / PUSH"
            # — removemos essas 4 linhas e substituímos pelo STR.
            _desfazer_leitura_e_armazenar(emit, secao_text, declarar_variavel)
            return

        # --- IF ---
        if tipo_f == "IF":
            _gerar_if_da_pilha(emit, novo_label)
            return

        # --- WHILE ---
        if tipo_f == "WHILE":
            _gerar_while_da_pilha(emit, novo_label)
            return

        # --- Caso padrão: OPERADOR ou MEM token real ---
        for f in filhos:
            _visitar(f)

    # -----------------------------------------------------------------------
    # Armazenamento em memória: desfaz o push do ID e emite STR
    # -----------------------------------------------------------------------

    def _desfazer_leitura_e_armazenar(emit, secao_text, declarar_variavel):
        """Remove o código de leitura do ID (nome da variável) emitido pelo
        visitante de EXPR, extrai o nome da variável e emite o STR.

        Bloco emitido pelo visitante de ID (leitura):
            @ leitura de NOME
            LDR  R0, =var_nome
            LDR  R0, [R0]
            PUSH {R0}

        Substituímos por:
            @ armazenar em NOME
            POP  {R0}
            LDR  R1, =var_nome
            STR  R0, [R1]
        """
        # Busca as últimas 4 linhas que correspondem à leitura do ID-nome
        # e extrai o label de lá.
        nome_var = None
        label_var = None
        idx_inicio = None

        for i in range(len(secao_text) - 1, -1, -1):
            linha = secao_text[i].strip()
            if linha.startswith("@ leitura de "):
                nome_var = linha[len("@ leitura de "):]
                idx_inicio = i
                break

        if nome_var is not None and idx_inicio is not None:
            label_var = declarar_variavel(nome_var)
            # Remove as 4 linhas de leitura (@ comentário + LDR label + LDR [R0] + PUSH)
            del secao_text[idx_inicio: idx_inicio + 4]
            secao_text.append(f"    @ armazenar em {nome_var}")
            secao_text.append("    POP  {R0}")
            secao_text.append(f"    LDR  R1, ={label_var}")
            secao_text.append("    STR  R0, [R1]")
        else:
            # Fallback: não encontrou o bloco — emite STR genérico
            secao_text.append("    @ armazenar (variavel desconhecida)")
            secao_text.append("    POP  {R1}   @ nome ignorado")
            secao_text.append("    POP  {R0}   @ valor")

    # -----------------------------------------------------------------------
    # IF da pilha
    # -----------------------------------------------------------------------

    def _gerar_if_da_pilha(emit, novo_label):
        """Gera código para IF.

        Neste ponto da árvore, os dois blocos (condição e corpo) já foram
        visitados e seus resultados estão na pilha (ordem de empilhamento:
        condição primeiro, corpo depois).

        Estratégia: não usamos a pilha diretamente para controle de fluxo —
        o gerador de EXPR_RPN_APOS_GRUPO visitou primeiro a sub-EXPR_RPN da
        condição (que empilhou 1 ou 0) e depois a sub-EXPR da expressão corpo
        (que também empilhou um resultado).

        Como o código ARMv7 é linear, precisamos reorganizar: desfazemos o push
        do corpo, emitimos a lógica de desvio sobre a condição e depois o corpo.

        Aqui adotamos a estratégia mais simples que funciona com a estrutura de
        árvore atual: o visitante de EXPR_RPN_APOS_GRUPO visita EXPR (corpo) após
        a condição — logo o corpo já está emitido. Inserimos o teste e o desvio
        *antes* do código do corpo retroativamente.

        Para não fazer reordenação de código emitido (frágil), adotamos a
        estratégia de usar um label de saída e um teste no final da condição,
        que já foi emitida antes de entrarmos aqui.

        Estrutura real na pilha de código emitido neste ponto:
          ... [código da condição] ... [código do corpo] ...  ← já no secao_text

        Precisamos:
          1. Encontrar o ponto de separação condição / corpo no secao_text.
          2. Inserir CMP + BEQ entre eles.
          3. Adicionar label de fim após o corpo.

        Como isso é complexo sem marcadores, usamos marcadores sentinela emitidos
        pelos visitantes de EXPR_RPN (ver _visitar_com_marca).
        """
        label_fim = novo_label("if_fim_")
        # Remove __MARCA_COND__ residual (IF não precisa de label de retorno)
        for i in range(len(secao_text) - 1, -1, -1):
            if secao_text[i].strip() == "__MARCA_COND__":
                del secao_text[i]
                break
        _inserir_teste_condicional(secao_text, label_fim, "BEQ")
        emit(f"{label_fim}:")
        emit("    POP  {R0}   @ descarta resultado do corpo IF")

    # -----------------------------------------------------------------------
    # WHILE da pilha
    # -----------------------------------------------------------------------

    def _gerar_while_da_pilha(emit, novo_label):
        """Gera código para WHILE.

        Mesma estratégia do IF, mas com jump de volta ao início.
        """
        label_inicio = novo_label("while_ini_")
        label_fim = novo_label("while_fim_")

        # Insere o label de início e o teste retroativamente
        _inserir_label_inicio_e_teste(secao_text, label_inicio, label_fim)
        emit(f"    POP  {{R0}}   @ descarta resultado do corpo WHILE")
        emit(f"    B    {label_inicio}")
        emit(f"{label_fim}:")

    # -----------------------------------------------------------------------
    # Helpers de inserção retroativa de labels
    # -----------------------------------------------------------------------

    def _inserir_teste_condicional(secao_text, label_fim, branch_op):
        """Encontra a marca __MARCA_CORPO__ e insere o teste condicional antes."""
        for i in range(len(secao_text) - 1, -1, -1):
            if secao_text[i].strip() == "__MARCA_CORPO__":
                secao_text[i : i + 1] = [
                    "    POP  {R0}",
                    "    CMP  R0, #0",
                    f"    {branch_op}  {label_fim}",
                ]
                return
        # Fallback: sem marca, insere antes das últimas 4 linhas de código (heurística)
        pos = max(0, len(secao_text) - 4)
        secao_text[pos:pos] = [
            "    POP  {R0}",
            "    CMP  R0, #0",
            f"    {branch_op}  {label_fim}",
        ]

    def _inserir_label_inicio_e_teste(secao_text, label_inicio, label_fim):
        """Para WHILE: insere label de início antes da condição e teste antes do corpo."""
        # 1. Substitui __MARCA_CORPO__ pelo teste condicional
        for i in range(len(secao_text) - 1, -1, -1):
            if secao_text[i].strip() == "__MARCA_CORPO__":
                secao_text[i : i + 1] = [
                    "    POP  {R0}",
                    "    CMP  R0, #0",
                    f"    BEQ  {label_fim}",
                ]
                break

        # 2. Substitui __MARCA_COND__ pelo label de início do loop
        for i in range(len(secao_text) - 1, -1, -1):
            if secao_text[i].strip() == "__MARCA_COND__":
                secao_text[i : i + 1] = [f"{label_inicio}:"]
                return

        # Fallback sem marcas (não deve acontecer com a gramática atual)
        # Insere o label logo após "_start:" se existir, senão no início
        for i, linha in enumerate(secao_text):
            if linha.strip() == "_start:":
                secao_text.insert(i + 1, f"{label_inicio}:")
                return
        secao_text.insert(0, f"{label_inicio}:")

    # -----------------------------------------------------------------------
    # Visita de EXPR_RPN com marcadores para IF/WHILE
    # -----------------------------------------------------------------------
    # Os marcadores sentinela permitem que _gerar_if_da_pilha e
    # _gerar_while_da_pilha encontrem retroativamente a fronteira
    # condição / corpo no código já emitido.
    #
    # A gramática produz IF/WHILE via:
    #   EXPR_RPN → ( EXPR_RPN ) EXPR_RPN_APOS_GRUPO
    #   EXPR_RPN_APOS_GRUPO → EXPR FINALIZADOR
    #   FINALIZADOR → IF  (ou WHILE)
    #
    # Então a ordem de visita é:
    #   1. EXPR_RPN interno (condição)  ← emite código da condição
    #   2. EXPR (corpo)                 ← emite código do corpo
    #   3. FINALIZADOR → IF/WHILE       ← chama _gerar_if/while_da_pilha
    #
    # Precisamos inserir __MARCA_COND__ antes de (1) e __MARCA_CORPO__ entre
    # (1) e (2). Fazemos isso sobrecarregando o visitante de EXPR_RPN_APOS_GRUPO.

    _visitar_original = _visitar  # salva referência antes de monkey-patch

    def _visitar_com_marcas(no: dict) -> None:
        """Versão de _visitar que emite marcadores para IF/WHILE."""
        if no is None:
            return
        tipo = no["tipo"]
        filhos = no.get("filhos", [])

        if tipo == "EXPR_RPN_APOS_GRUPO":
            # filhos = [EXPR (corpo), FINALIZADOR]
            # O código da condição já foi emitido (era o EXPR_RPN interno de EXPR_RPN).
            # Emitimos a marca de corpo antes de visitar o EXPR.
            filho_expr = None
            filho_fin = None
            for f in filhos:
                if f["tipo"] == "EXPR":
                    filho_expr = f
                elif f["tipo"] == "FINALIZADOR":
                    filho_fin = f

            fin_tipo = None
            if filho_fin:
                for f2 in filho_fin.get("filhos", []):
                    if f2["tipo"] in ("IF", "WHILE"):
                        fin_tipo = f2["tipo"]
                        break

            if fin_tipo in ("IF", "WHILE"):
                # Emite marca de fim-de-condição / início-de-corpo
                secao_text.append("__MARCA_CORPO__")
                if filho_expr:
                    _visitar(filho_expr)
                if filho_fin:
                    _visitar(filho_fin)
            else:
                _visitar(no)
            return

        _visitar(no)

    # Substituímos o visitante de EXPR_RPN para usar marcas quando necessário
    _visitar_original_expr_rpn = _visitar_expr_rpn

    def _visitar_expr_rpn_com_marcas(filhos, emit, declarar_variavel, novo_label, _visitar):
        """Emite __MARCA_COND__ antes da condição quando detecta IF/WHILE no contexto."""
        # Detecta se este EXPR_RPN contém um EXPR_RPN_APOS_GRUPO com IF/WHILE.
        # Nesse caso emite __MARCA_COND__ antes de visitar o primeiro filho
        # (o EXPR_RPN interno que é a condição).
        tem_if_while = False
        for filho in filhos:
            if filho["tipo"] == "EXPR_RPN_APOS_GRUPO":
                for f2 in filho.get("filhos", []):
                    if f2["tipo"] == "FINALIZADOR":
                        for f3 in f2.get("filhos", []):
                            if f3["tipo"] in ("IF", "WHILE"):
                                tem_if_while = True
        if tem_if_while:
            secao_text.append("__MARCA_COND__")
        for filho in filhos:
            _visitar_com_marcas(filho)

    # Redefine _visitar_expr_rpn para usar marcas
    # (em Python closures são late-binding, então atribuímos à variável original)

    # Reinicia o visitante principal para usar _visitar_com_marcas em EXPR_RPN
    def _visitar(no: dict) -> None:  # noqa: F811  (redefine intencionalmente)
        if no is None:
            return
        tipo: str = no["tipo"]
        valor = no.get("valor")
        filhos: list[dict] = no.get("filhos", [])

        if tipo == "PROGRAMA":
            for filho in filhos:
                _visitar(filho)
            return

        if tipo in ("LISTA_CMD", "LISTA_APOS_ABRE", "CMD"):
            for filho in filhos:
                _visitar(filho)
            return

        if tipo in ("START", "END"):
            return

        if tipo == "NUM":
            if valor and "." in valor:
                intval = int(float(valor))
                emit(f"    @ float {valor} truncado para {intval}")
                emit(f"    MOV  R0, #{intval}")
            else:
                intval = int(valor) if valor else 0
                if -255 <= intval <= 255:
                    emit(f"    MOV  R0, #{intval}")
                else:
                    emit(f"    LDR  R0, ={intval}")
            emit("    PUSH {R0}")
            return

        if tipo == "ID":
            label = declarar_variavel(valor)
            emit(f"    @ leitura de {valor}")
            emit(f"    LDR  R0, ={label}")
            emit("    LDR  R0, [R0]")
            emit("    PUSH {R0}")
            return

        if tipo == "OP":
            emit("    POP  {R1}")
            emit("    POP  {R0}")
            _gerar_op(valor, emit, novo_label)
            emit("    PUSH {R0}")
            return

        if tipo == "RES":
            emit("    @ RES: resultado anterior nao suportado em runtime ARMv7")
            emit("    MOV  R0, #0")
            emit("    PUSH {R0}")
            return

        if tipo == "EXPR_RPN":
            _visitar_expr_rpn_com_marcas(filhos, emit, declarar_variavel, novo_label, _visitar)
            return

        if tipo in ("EXPR_RPN_APOS_NUM", "EXPR_RPN_APOS_ID"):
            for filho in filhos:
                _visitar(filho)
            return

        if tipo == "EXPR_RPN_APOS_GRUPO":
            _visitar_com_marcas(no)
            return

        if tipo == "EXPR":
            for filho in filhos:
                _visitar(filho)
            return

        if tipo == "FINALIZADOR":
            _visitar_finalizador(filhos, emit, declarar_variavel, novo_label, _visitar)
            return

        if tipo == "OPERADOR":
            for filho in filhos:
                _visitar(filho)
            return

        for filho in filhos:
            _visitar(filho)

    # -----------------------------------------------------------------------
    # Ponto de entrada da geração
    # -----------------------------------------------------------------------
    emit(".global _start")
    emit("_start:")
    _visitar(arvore)
    emit("")
    emit("    @ fim do programa")
    emit("    MOV  R7, #1")
    emit("    SWI  0")

    linhas: list[str] = []
    if secao_data:
        linhas.append(".data")
        linhas.extend(secao_data)
        linhas.append("")
    linhas.append(".text")
    linhas.extend(secao_text)

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Geração de operadores (extraído para reutilização)
# ---------------------------------------------------------------------------

def _gerar_op(op: str, emit, novo_label) -> None:
    """Emite as instruções ARMv7 para um operador binário.

    Pré-condição: R0 = operando esquerdo, R1 = operando direito (já no POP).
    Pós-condição: resultado em R0.
    """
    if op == "+":
        emit("    ADD  R0, R0, R1")
    elif op == "-":
        emit("    SUB  R0, R0, R1")
    elif op == "*":
        emit("    MUL  R0, R0, R1")
    elif op in ("/", "|"):
        emit("    SDIV R0, R0, R1")
    elif op == "%":
        emit("    SDIV R2, R0, R1")
        emit("    MUL  R2, R2, R1")
        emit("    SUB  R0, R0, R2")
    elif op == "^":
        lp = novo_label("pow_loop_")
        le = novo_label("pow_end_")
        emit("    MOV  R2, #1")
        emit(f"{lp}:")
        emit("    CMP  R1, #0")
        emit(f"    BEQ  {le}")
        emit("    MUL  R2, R2, R0")
        emit("    SUB  R1, R1, #1")
        emit(f"    B    {lp}")
        emit(f"{le}:")
        emit("    MOV  R0, R2")
    elif op == ">":
        lv, lf = novo_label("cmp_t_"), novo_label("cmp_f_")
        emit("    CMP  R0, R1")
        emit(f"    BGT  {lv}")
        emit("    MOV  R0, #0")
        emit(f"    B    {lf}")
        emit(f"{lv}:")
        emit("    MOV  R0, #1")
        emit(f"{lf}:")
    elif op == "<":
        lv, lf = novo_label("cmp_t_"), novo_label("cmp_f_")
        emit("    CMP  R0, R1")
        emit(f"    BLT  {lv}")
        emit("    MOV  R0, #0")
        emit(f"    B    {lf}")
        emit(f"{lv}:")
        emit("    MOV  R0, #1")
        emit(f"{lf}:")
    elif op == "==":
        lv, lf = novo_label("cmp_t_"), novo_label("cmp_f_")
        emit("    CMP  R0, R1")
        emit(f"    BEQ  {lv}")
        emit("    MOV  R0, #0")
        emit(f"    B    {lf}")
        emit(f"{lv}:")
        emit("    MOV  R0, #1")
        emit(f"{lf}:")
    elif op == "!=":
        lv, lf = novo_label("cmp_t_"), novo_label("cmp_f_")
        emit("    CMP  R0, R1")
        emit(f"    BNE  {lv}")
        emit("    MOV  R0, #0")
        emit(f"    B    {lf}")
        emit(f"{lv}:")
        emit("    MOV  R0, #1")
        emit(f"{lf}:")
    elif op == ">=":
        lv, lf = novo_label("cmp_t_"), novo_label("cmp_f_")
        emit("    CMP  R0, R1")
        emit(f"    BGE  {lv}")
        emit("    MOV  R0, #0")
        emit(f"    B    {lf}")
        emit(f"{lv}:")
        emit("    MOV  R0, #1")
        emit(f"{lf}:")
    elif op == "<=":
        lv, lf = novo_label("cmp_t_"), novo_label("cmp_f_")
        emit("    CMP  R0, R1")
        emit(f"    BLE  {lv}")
        emit("    MOV  R0, #0")
        emit(f"    B    {lf}")
        emit(f"{lv}:")
        emit("    MOV  R0, #1")
        emit(f"{lf}:")


# ---------------------------------------------------------------------------
# Utilitários de saída
# ---------------------------------------------------------------------------

def imprimirArvore(no: dict | None, nivel: int = 0) -> None:
    """Imprime a árvore sintática de forma indentada no stdout."""
    if no is None:
        return
    indent = "  " * nivel
    tipo = no["tipo"]
    valor = no.get("valor")
    linha = f"{indent}{tipo}" + (f"  [{valor}]" if valor is not None else "")
    print(linha)
    for filho in no.get("filhos", []):
        imprimirArvore(filho, nivel + 1)


def salvarArvoreJSON(arvore: dict, caminho: str | Path) -> None:
    """Serializa a árvore em JSON com indentação."""
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(arvore, f, indent=2, ensure_ascii=False)


# Mantém nomes legados (usados pelos testes do próprio módulo)
_imprimirArvore = imprimirArvore
_salvarArvoreJSON = salvarArvoreJSON


# ---------------------------------------------------------------------------
# Testes internos (executados com: python arvore.py)
# ---------------------------------------------------------------------------

def _testarGeracaoArvore():
    from parser_ll1 import parsear
    from gramatica import construirGramatica

    info = construirGramatica()
    tabela = info["tabela_ll1"]

    # Teste 1: (START) (3 4 +) (END)
    tokens1 = [
        {"tipo": "ABRE_PAREN",   "valor": "(",     "linha": 1},
        {"tipo": "START",        "valor": "START",  "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",      "linha": 1},
        {"tipo": "ABRE_PAREN",   "valor": "(",      "linha": 1},
        {"tipo": "NUMERO",       "valor": "3",      "linha": 1},
        {"tipo": "NUMERO",       "valor": "4",      "linha": 1},
        {"tipo": "OPERADOR_ARIT","valor": "+",      "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",      "linha": 1},
        {"tipo": "ABRE_PAREN",   "valor": "(",      "linha": 1},
        {"tipo": "END",          "valor": "END",    "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",      "linha": 1},
    ]
    r1 = parsear(tokens1, tabela)
    print("=== Teste 1: (3 4 +) ===")
    if r1["ok"]:
        a1 = gerarArvore(r1)
        imprimirArvore(a1)
        salvarArvoreJSON(a1, "/tmp/arvore_teste1.json")
        print("JSON salvo em /tmp/arvore_teste1.json")
    else:
        print("Erros:", r1["erros"])

    print()

    # Teste 2: (START) (5 10 <) (END)
    tokens2 = [
        {"tipo": "ABRE_PAREN",   "valor": "(",     "linha": 1},
        {"tipo": "START",        "valor": "START",  "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",      "linha": 1},
        {"tipo": "ABRE_PAREN",   "valor": "(",      "linha": 1},
        {"tipo": "NUMERO",       "valor": "5",      "linha": 1},
        {"tipo": "NUMERO",       "valor": "10",     "linha": 1},
        {"tipo": "OPERADOR_REL", "valor": "<",      "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",      "linha": 1},
        {"tipo": "ABRE_PAREN",   "valor": "(",      "linha": 1},
        {"tipo": "END",          "valor": "END",    "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",      "linha": 1},
    ]
    r2 = parsear(tokens2, tabela)
    print("=== Teste 2: (5 10 <) ===")
    if r2["ok"]:
        a2 = gerarArvore(r2)
        imprimirArvore(a2)
    else:
        print("Erros:", r2["erros"])

    print()

    # Teste 3: armazenamento (42 VAR MEM)
    tokens3 = [
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "START",         "valor": "START","linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "NUMERO",        "valor": "42",   "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "VAR",  "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "MEM",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "END",           "valor": "END",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
    ]
    r3 = parsear(tokens3, tabela)
    print("=== Teste 3: (42 VAR MEM) — armazenamento ===")
    if r3["ok"]:
        a3 = gerarArvore(r3)
        imprimirArvore(a3)
    else:
        print("Erros:", r3["erros"])

    print()

    # Teste 4: IF ((1 2 <) (3 4 +) IF)
    tokens4 = [
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "START",         "valor": "START","linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "1",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "2",   "linha": 1},
        {"tipo": "OPERADOR_REL",  "valor": "<",   "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "3",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "4",   "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+",   "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "IF",            "valor": "IF",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "END",           "valor": "END", "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
    ]
    r4 = parsear(tokens4, tabela)
    print("=== Teste 4: ((1 2 <)(3 4 +) IF) ===")
    if r4["ok"]:
        a4 = gerarArvore(r4)
        imprimirArvore(a4)
    else:
        print("Erros:", r4["erros"])


def _testarGeracaoAssembly():
    from parser_ll1 import parsear
    from gramatica import construirGramatica

    info = construirGramatica()
    tabela = info["tabela_ll1"]

    def testar(nome, tokens):
        r = parsear(tokens, tabela)
        if not r["ok"]:
            print(f"{nome}: ERRO PARSER", r["erros"])
            return
        arvore = gerarArvore(r)
        asm = gerarAssembly(arvore)
        print(f"=== {nome} ===")
        print(asm)
        print()

    # (10 3 +)
    testar("10 3 +", [
        {"tipo": "ABRE_PAREN",   "valor": "(",    "linha": 1},
        {"tipo": "START",        "valor": "START","linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",   "valor": "(",    "linha": 1},
        {"tipo": "NUMERO",       "valor": "10",   "linha": 1},
        {"tipo": "NUMERO",       "valor": "3",    "linha": 1},
        {"tipo": "OPERADOR_ARIT","valor": "+",    "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",   "valor": "(",    "linha": 1},
        {"tipo": "END",          "valor": "END",  "linha": 1},
        {"tipo": "FECHA_PAREN",  "valor": ")",    "linha": 1},
    ])

    # (42 VAR MEM) — armazenamento
    testar("42 VAR MEM", [
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "START",         "valor": "START","linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "NUMERO",        "valor": "42",   "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "VAR",  "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "MEM",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "END",           "valor": "END",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
    ])

    # ((1 2 <)(3 4 +) IF)
    testar("IF (1 2 <)(3 4 +)", [
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "START",         "valor": "START","linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "1",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "2",   "linha": 1},
        {"tipo": "OPERADOR_REL",  "valor": "<",   "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "3",   "linha": 1},
        {"tipo": "NUMERO",        "valor": "4",   "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+",   "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "IF",            "valor": "IF",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",   "linha": 1},
        {"tipo": "END",           "valor": "END", "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",   "linha": 1},
    ])

    # ((CONT 0 >) (CONT 1 -) WHILE)
    testar("WHILE CONT > 0", [
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "START",         "valor": "START","linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        # inicializa CONT = 3
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "NUMERO",        "valor": "3",    "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "CONT", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "MEM",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        # while (CONT 0 >) (CONT 1 -)
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "CONT", "linha": 1},
        {"tipo": "NUMERO",        "valor": "0",    "linha": 1},
        {"tipo": "OPERADOR_REL",  "valor": ">",    "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "CONT", "linha": 1},
        {"tipo": "NUMERO",        "valor": "1",    "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "-",    "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        {"tipo": "WHILE",         "valor": "WHILE","linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
        {"tipo": "ABRE_PAREN",    "valor": "(",    "linha": 1},
        {"tipo": "END",           "valor": "END",  "linha": 1},
        {"tipo": "FECHA_PAREN",   "valor": ")",    "linha": 1},
    ])


if __name__ == "__main__":
    _testarGeracaoArvore()
    print()
    _testarGeracaoAssembly()