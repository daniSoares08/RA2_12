# Integrantes do grupo (ordem alfabética):
# Daniel Campos Soares - daniSoares08
# Giovanni Bandeira Malucelli - Giomalu
# Victor Vanini Meyer - VictorMeyer1
#
# Nome do grupo no Canvas: RA2_12

NAO_TERMINAIS = {'PROGRAMA', 'LISTA_CMD', 'CMD', 'EXPR_RPN', 'EXPR'}

def gerarArvore(derivacao):
    if not derivacao.get("ok", False):
        raise ValueError("Derivação contém erros sintáticos")
    
    deriv_list = derivacao["derivacao"]
    tokens = derivacao["tokens"]
    
    deriv_index = [0]
    token_index = [0]
    
    raiz = _construir_no(deriv_list, deriv_index, tokens, token_index)
    return raiz

def _construir_no(deriv_list, deriv_index, tokens, token_index):
    if deriv_index[0] >= len(deriv_list):
        return None
    
    passo = deriv_list[deriv_index[0]]
    nao_terminal = passo["nao_terminal"]
    producao = passo["producao"]
    deriv_index[0] += 1
    
    filhos = []
    for simbolo in producao:
        if simbolo in NAO_TERMINAIS:
            filho = _construir_no(deriv_list, deriv_index, tokens, token_index)
            if filho:
                filhos.append(filho)
        else:
            if token_index[0] < len(tokens):
                token = tokens[token_index[0]]
                if _terminal_de_token(token) == simbolo:
                    tipo = _mapear_tipo_terminal(simbolo, token)
                    filhos.append({'tipo': tipo, 'valor': token['valor'], 'filhos': []})
                    token_index[0] += 1
    
    tipo = _mapear_tipo_nao_terminal(nao_terminal)
    valor = None
    
    if nao_terminal == 'EXPR_RPN' and len(filhos) >= 3:
        valor = filhos[-1]['valor']  
        filhos = filhos[:-1]  
    elif nao_terminal == 'EXPR' and len(filhos) == 1:
        return filhos[0]
    
    return {'tipo': tipo, 'valor': valor, 'filhos': filhos}

def _terminal_de_token(token):
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

def _mapear_tipo_terminal(simbolo, token):
    if simbolo == 'NUM':
        return 'NUM'
    elif simbolo == 'ID':
        return 'ID'
    else:
        return 'TOKEN'  

def _mapear_tipo_nao_terminal(nao_terminal):
    return nao_terminal


def gerarAssembly(arvore):
    if not arvore:
        return ""
    
    codigo = []  
    pilha_regs = []  
    variaveis = {}   
    label_counter = 0  
    
    def proximo_reg():
        if pilha_regs:
            return pilha_regs.pop()
        return "R0"  
    
    def push_reg(reg):
        pilha_regs.append(reg)
    
    def gerar_codigo_no(no):
        nonlocal label_counter  
        if not no:
            return  
        
        tipo = no['tipo']  
        valor = no.get('valor')  
        filhos = no.get('filhos', [])  
        
        if tipo == 'PROGRAMA':
            codigo.append(".global _start")  
            codigo.append("_start:")  
            for filho in filhos:  
                gerar_codigo_no(filho)  
            codigo.append("MOV R7, #1")  
            codigo.append("SWI 0")  # Chama sistema
        
        elif tipo == 'CMD':
            if filhos:
                primeiro_filho = filhos[0]
                if primeiro_filho['tipo'] == 'EXPR_RPN':
                    # Se é expressão, executa ela
                    gerar_codigo_no(primeiro_filho)
                elif len(filhos) == 3 and filhos[1]['tipo'] == 'ID' and filhos[2]['tipo'] == 'TOKEN' and filhos[2]['valor'] == 'MEM':
                    gerar_codigo_no(filhos[0])  # Calcula valor
                    var_name = filhos[1]['valor']  
                    reg = proximo_reg()  
                    codigo.append(f"POP {{{reg}}}")  
                    if var_name not in variaveis:  # Se nova, cria
                        variaveis[var_name] = f"VAR_{var_name}"
                        codigo.insert(0, f".data\n{variaveis[var_name]}: .word 0")  
                    codigo.append(f"STR {reg}, [{variaveis[var_name]}]")  # Salva
                    push_reg(reg)  
                elif len(filhos) == 2 and filhos[1]['tipo'] == 'TOKEN' and filhos[1]['valor'] == 'RES':
                    num = int(filhos[0]['valor'])  # Quantas vars
                    for i in range(num):  
                        var_name = f"VAR_{len(variaveis)}"  
                        variaveis[f"temp_{i}"] = var_name  
                        codigo.insert(0, f"{var_name}: .word 0")  
                elif len(filhos) == 4 and filhos[3]['tipo'] == 'TOKEN' and filhos[3]['valor'] == 'IF':
                    label_else = f"L{label_counter}"  
                    label_counter += 1
                    gerar_codigo_no(filhos[0])  
                    reg = proximo_reg()
                    codigo.append(f"POP {{{reg}}}")  
                    codigo.append(f"CMP {reg}, #0")  
                    codigo.append(f"BEQ {label_else}")  
                    gerar_codigo_no(filhos[1])  # Executa se verdadeiro
                    codigo.append(f"{label_else}:")  
                    push_reg(reg)
                elif len(filhos) == 4 and filhos[3]['tipo'] == 'TOKEN' and filhos[3]['valor'] == 'WHILE':
                    # WHILE: loop
                    label_start = f"L{label_counter}"  
                    label_counter += 1
                    label_end = f"L{label_counter}"  
                    label_counter += 1
                    codigo.append(f"{label_start}:")  
                    gerar_codigo_no(filhos[0])  
                    reg = proximo_reg()
                    codigo.append(f"POP {{{reg}}}")  
                    codigo.append(f"CMP {reg}, #0")  # Compara
                    codigo.append(f"BEQ {label_end}")  # Sai se falso
                    gerar_codigo_no(filhos[1])  
                    codigo.append(f"B {label_start}")  
                    codigo.append(f"{label_end}:")  
                    push_reg(reg)
                else:
                    for filho in filhos:
                        gerar_codigo_no(filho)
        
        elif tipo == 'EXPR_RPN':
            for filho in filhos:  
                gerar_codigo_no(filho)
            if valor:  
                reg1 = proximo_reg()  
                reg2 = proximo_reg()  
                codigo.append(f"POP {{{reg2}}}")  
                codigo.append(f"POP {{{reg1}}}")  
                if valor == '+':
                    codigo.append(f"ADD {reg1}, {reg1}, {reg2}")  # Soma
                elif valor == '-':
                    codigo.append(f"SUB {reg1}, {reg1}, {reg2}")  # Subtrai
                elif valor == '*':
                    codigo.append(f"MUL {reg1}, {reg1}, {reg2}")  # Multiplica
                elif valor == '/':
                    codigo.append(f"SDIV {reg1}, {reg1}, {reg2}")  # Divide
                elif valor == '%':
                    codigo.append(f"SDIV R12, {reg1}, {reg2}")  # Divide
                    codigo.append(f"MUL R12, R12, {reg2}")  # Multiplica de volta
                    codigo.append(f"SUB {reg1}, {reg1}, R12")  # Subtrai para resto
                elif valor == '^':
                    codigo.append(f"MOV R12, #1")  # Começa com 1
                    codigo.append(f"power_loop_{label_counter}:") 
                    codigo.append(f"CMP {reg2}, #0")  
                    codigo.append(f"BEQ power_end_{label_counter}")  # Se 0, fim
                    codigo.append(f"MUL R12, R12, {reg1}")  
                    codigo.append(f"SUB {reg2}, {reg2}, #1")  
                    codigo.append(f"B power_loop_{label_counter}")  
                    codigo.append(f"power_end_{label_counter}:")  
                    codigo.append(f"MOV {reg1}, R12")  
                    label_counter += 1
                elif valor == '|':
                    codigo.append(f"CMP {reg1}, {reg2}")
                    codigo.append(f"MOVGT {reg1}, {reg2}")  
                # Coloca resultado na pilha
                codigo.append(f"PUSH {{{reg1}}}")
                push_reg(reg2)  
                push_reg(reg1)
        
        elif tipo == 'NUM':
            if '.' in valor:
                codigo.append(f"VMOV.F64 D0, #{valor}")  # Carrega
                codigo.append("VPUSH {D0}")  # Empilha
            else:
                codigo.append(f"PUSH {{#{valor}}}")  # Empilha
        
        elif tipo == 'ID':
            if valor in variaveis:  
                reg = proximo_reg()  
                codigo.append(f"LDR {reg}, [{variaveis[valor]}]")  # Carrega da memória
                codigo.append(f"PUSH {{{reg}}}")  # Empilha
                push_reg(reg)  # Devolve
        
        else:
            for filho in filhos:
                gerar_codigo_no(filho)
    
    gerar_codigo_no(arvore)  
    return "\n".join(codigo)  


def _imprimirArvore(no, nivel=0):
    if not no:
        return
    
    indent = "  " * nivel
    
    tipo = no['tipo']
    valor = no.get('valor')
    if valor is not None:
        print(f"{indent}{tipo} {valor}")
    else:
        print(f"{indent}{tipo}")
    
    filhos = no.get('filhos', [])
    for filho in filhos:
        _imprimirArvore(filho, nivel + 1)


def _salvarArvoreJSON(arvore, caminho_saida):
    import json
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(arvore, f, indent=2, ensure_ascii=False)


def _testarGeracaoArvore():
    print("=== Teste 1: Expressão simples (3 4 +) ===")
    tokens_mock = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "3", "linha": 1},
        {"tipo": "NUMERO", "valor": "4", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "EOF", "valor": "$", "linha": 1}
    ]
    derivacao_mock = [
        {"nao_terminal": "PROGRAMA", "producao": ["(", "START", ")", "LISTA_CMD", "(", "END", ")"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "+"]}
    ]
    mock_data = {"ok": True, "derivacao": derivacao_mock, "tokens": tokens_mock}
    arvore = gerarArvore(mock_data)
    _imprimirArvore(arvore)
    _salvarArvoreJSON(arvore, "teste_arvore_simples.json")
    
    print("\n=== Teste 2: Expressão aninhada (3 (4 5 +) *) ===")
    tokens_mock2 = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "3", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "4", "linha": 1},
        {"tipo": "NUMERO", "valor": "5", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "*", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "EOF", "valor": "$", "linha": 1}
    ]
    derivacao_mock2 = [
        {"nao_terminal": "PROGRAMA", "producao": ["(", "START", ")", "LISTA_CMD", "(", "END", ")"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "EXPR_RPN", "*"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "+"]}
    ]
    mock_data2 = {"ok": True, "derivacao": derivacao_mock2, "tokens": tokens_mock2}
    arvore2 = gerarArvore(mock_data2)
    _imprimirArvore(arvore2)
    _salvarArvoreJSON(arvore2, "teste_arvore_aninhada.json")
    
    print("\n=== Teste 3: Estrutura de controle IF ===")
    tokens_mock3 = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "1", "linha": 1},
        {"tipo": "NUMERO", "valor": "2", "linha": 1},
        {"tipo": "OPERADOR_REL", "valor": "<", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "3", "linha": 1},
        {"tipo": "NUMERO", "valor": "4", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "IF", "valor": "IF", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "EOF", "valor": "$", "linha": 1}
    ]
    derivacao_mock3 = [
        {"nao_terminal": "PROGRAMA", "producao": ["(", "START", ")", "LISTA_CMD", "(", "END", ")"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD"]},
        {"nao_terminal": "CMD", "producao": ["(", "EXPR_RPN", ")", "(", "CMD", ")", "IF"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "<"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "+"]}
    ]
    mock_data3 = {"ok": True, "derivacao": derivacao_mock3, "tokens": tokens_mock3}
    arvore3 = gerarArvore(mock_data3)
    _imprimirArvore(arvore3)
    _salvarArvoreJSON(arvore3, "teste_arvore_if.json")
    
    print("\nTestes concluídos! Árvores salvas em arquivos JSON.")


def _testarGeracaoAssembly():
    print("=== Teste Assembly 1: Operações aritméticas básicas (+, -, *, /, %) ===")
    tokens_mock = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "START", "valor": "START", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "10", "linha": 1},
        {"tipo": "NUMERO", "valor": "3", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "15", "linha": 1},
        {"tipo": "NUMERO", "valor": "4", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "-", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "6", "linha": 1},
        {"tipo": "NUMERO", "valor": "2", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "*", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "20", "linha": 1},
        {"tipo": "NUMERO", "valor": "5", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "/", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "17", "linha": 1},
        {"tipo": "NUMERO", "valor": "3", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "%", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "END", "valor": "END", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "EOF", "valor": "$", "linha": 1}
    ]
    derivacao_mock = [
        {"nao_terminal": "PROGRAMA", "producao": ["(", "START", ")", "LISTA_CMD", "(", "END", ")"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD", "LISTA_CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "+"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD", "LISTA_CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "-"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD", "LISTA_CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "*"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD", "LISTA_CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "/"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "%"]}
    ]
    mock_data = {"ok": True, "derivacao": derivacao_mock, "tokens": tokens_mock}
    arvore = gerarArvore(mock_data)
    assembly = gerarAssembly(arvore)
    print(assembly)
    with open("teste_assembly_aritmetico.s", "w") as f:
        f.write(assembly)
    
    print("\n=== Teste Assembly 2: Expressão aninhada e potência (^) ===")
    tokens_mock2 = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "START", "valor": "START", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "2", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "3", "linha": 1},
        {"tipo": "NUMERO", "valor": "2", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "^", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "*", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "END", "valor": "END", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "EOF", "valor": "$", "linha": 1}
    ]
    derivacao_mock2 = [
        {"nao_terminal": "PROGRAMA", "producao": ["(", "START", ")", "LISTA_CMD", "(", "END", ")"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "EXPR_RPN", "*"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "^"]}
    ]
    mock_data2 = {"ok": True, "derivacao": derivacao_mock2, "tokens": tokens_mock2}
    arvore2 = gerarArvore(mock_data2)
    assembly2 = gerarAssembly(arvore2)
    print(assembly2)
    with open("teste_assembly_aninhado.s", "w") as f:
        f.write(assembly2)
    
    print("\n=== Teste Assembly 3: Estruturas de controle (IF e WHILE) ===")
    tokens_mock3 = [
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "START", "valor": "START", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "5", "linha": 1},
        {"tipo": "NUMERO", "valor": "10", "linha": 1},
        {"tipo": "OPERADOR_REL", "valor": "<", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "NUMERO", "valor": "1", "linha": 1},
        {"tipo": "NUMERO", "valor": "2", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "+", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "IF", "valor": "IF", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "CONT", "linha": 1},
        {"tipo": "NUMERO", "valor": "0", "linha": 1},
        {"tipo": "OPERADOR_REL", "valor": ">", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "IDENTIFICADOR", "valor": "CONT", "linha": 1},
        {"tipo": "NUMERO", "valor": "1", "linha": 1},
        {"tipo": "OPERADOR_ARIT", "valor": "-", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "WHILE", "valor": "WHILE", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "ABRE_PAREN", "valor": "(", "linha": 1},
        {"tipo": "END", "valor": "END", "linha": 1},
        {"tipo": "FECHA_PAREN", "valor": ")", "linha": 1},
        {"tipo": "EOF", "valor": "$", "linha": 1}
    ]
    derivacao_mock3 = [
        {"nao_terminal": "PROGRAMA", "producao": ["(", "START", ")", "LISTA_CMD", "(", "END", ")"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD", "LISTA_CMD"]},
        {"nao_terminal": "CMD", "producao": ["(", "EXPR_RPN", ")", "(", "CMD", ")", "IF"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "<"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["NUM", "NUM", "+"]},
        {"nao_terminal": "LISTA_CMD", "producao": ["CMD"]},
        {"nao_terminal": "CMD", "producao": ["(", "EXPR_RPN", ")", "(", "CMD", ")", "WHILE"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["ID", "NUM", ">"]},
        {"nao_terminal": "CMD", "producao": ["EXPR_RPN"]},
        {"nao_terminal": "EXPR_RPN", "producao": ["ID", "NUM", "-"]}
    ]
    mock_data3 = {"ok": True, "derivacao": derivacao_mock3, "tokens": tokens_mock3}
    arvore3 = gerarArvore(mock_data3)
    assembly3 = gerarAssembly(arvore3)
    print(assembly3)
    with open("teste_assembly_controle.s", "w") as f:
        f.write(assembly3)
    
    print("\nTestes concluídos! Arquivos .s salvos para teste no Cpulator-ARMv7.")
