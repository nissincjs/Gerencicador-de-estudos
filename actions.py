from datetime import datetime
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, DB_FILE
)
from utils import (
    clear_screen, print_header, print_divider, mostrar_guia_dificuldade,
    obter_input_float, obter_input_str, parse_tempo_input, formatar_horas_minutos,
    obter_largura_ui
)
from database import salvar_dados

def exibir_ciclo(dados, pausar=True):
    """Exibe o ciclo de estudos calculado com progresso em formato de tabela estilizada."""
    clear_screen()
    
    materias = dados.get("materias", [])
    
    # Determina a largura da coluna "Matéria" com base no nome mais longo das matérias cadastradas
    if materias:
        w_materia = max(15, max(len(m["nome"]) for m in materias))
    else:
        w_materia = 15
        
    w_quest = 6
    w_peso = 7
    w_dif = 3
    w_meta = 12
    w_estudado = 12
    w_restante = 12
    
    # Calcula a largura total da tabela para alinhar perfeitamente cabeçalho, divisores e bordas
    # (7 colunas + 7 separadores de 2 espaços + 8 barras verticais = w_materia + w_quest + w_peso + w_dif + w_meta + w_estudado + w_restante + 22)
    largura_tabela = w_materia + w_quest + w_peso + w_dif + w_meta + w_estudado + w_restante + 22
    
    # Exibe o cabeçalho ajustado para a largura dinâmica da tabela
    print(C_CYAN + "╔" + "═" * (largura_tabela - 2) + "╗")
    print(f"║{C_CYAN}{'SEU CICLO DE ESTUDOS ESTRATÉGICO'.center(largura_tabela - 2)}{C_RESET}║")
    print("╚" + "═" * (largura_tabela - 2) + "╝")
    
    horas_totais = dados.get("horas_semanais", 0.0)
    data_inicio = dados.get("data_inicio_ciclo", "N/A")
    progresso = dados.get("progresso_atual", {})
    
    if not materias:
        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada ainda!{C_RESET}")
        print("Adicione matérias no menu principal para gerar o ciclo.")
        if pausar:
            print(C_CYAN + "─" * largura_tabela + C_RESET)
            input(f"Pressione {C_GREEN}Enter{C_RESET} para voltar ao menu...")
        return

    print(f"  {C_BOLD}Ciclo iniciado em:{C_RESET} {C_GREEN}{data_inicio}{C_RESET}")
    horas_totais_formatado = formatar_horas_minutos(horas_totais)
    print(f"  {C_BOLD}Total de Horas do Ciclo:{C_RESET} {C_GREEN}{horas_totais_formatado}{C_RESET}")
    
    # Divisor da largura exata da tabela
    print(C_CYAN + "─" * largura_tabela + C_RESET)

    # Calcular o fator de cada matéria com base na fórmula estratégica
    fator_total = 0.0
    materias_calculadas = []
    
    for m in materias:
        questoes_prova = m.get("questoes_prova", 10.0)
        peso_questao = m.get("peso_questao", 1.0)
        dificuldade = m.get("dificuldade", 1.0)
        
        fator = (questoes_prova * peso_questao) * dificuldade
        fator_total += fator
        
        materias_calculadas.append({
            "nome": m["nome"],
            "questoes_prova": questoes_prova,
            "peso_questao": peso_questao,
            "dificuldade": dificuldade,
            "fator": fator
        })

    # Ordena as matérias por fator decrescente (mais horas primeiro)
    materias_calculadas.sort(key=lambda x: x["fator"], reverse=True)

    # Desenho da Tabela de Progresso
    border_top = C_CYAN + "┌" + "─"*(w_materia+2) + "┬" + "─"*(w_quest+2) + "┬" + "─"*(w_peso+2) + "┬" + "─"*(w_dif+2) + "┬" + "─"*(w_meta+2) + "┬" + "─"*(w_estudado+2) + "┬" + "─"*(w_restante+2) + "┐" + C_RESET
    border_mid = C_CYAN + "├" + "─"*(w_materia+2) + "┼" + "─"*(w_quest+2) + "┼" + "─"*(w_peso+2) + "┼" + "─"*(w_dif+2) + "┼" + "─"*(w_meta+2) + "┼" + "─"*(w_estudado+2) + "┼" + "─"*(w_restante+2) + "┤" + C_RESET
    border_bot = C_CYAN + "└" + "─"*(w_materia+2) + "┴" + "─"*(w_quest+2) + "┴" + "─"*(w_peso+2) + "┴" + "─"*(w_dif+2) + "┴" + "─"*(w_meta+2) + "┴" + "─"*(w_estudado+2) + "┴" + "─"*(w_restante+2) + "┘" + C_RESET

    header = (
        C_CYAN + "│" + C_RESET + f" {'Matéria':<{w_materia}} " +
        C_CYAN + "│" + C_RESET + f" {'Quest.':>{w_quest}} " +
        C_CYAN + "│" + C_RESET + f" {'Peso Q.':>{w_peso}} " +
        C_CYAN + "│" + C_RESET + f" {'Dif':>{w_dif}} " +
        C_CYAN + "│" + C_RESET + f" {'Meta':>{w_meta}} " +
        C_CYAN + "│" + C_RESET + f" {'Estudado':>{w_estudado}} " +
        C_CYAN + "│" + C_RESET + f" {'Restante':>{w_restante}} " +
        C_CYAN + "│"
    )

    print(border_top)
    print(header)
    print(border_mid)
    
    for mc in materias_calculadas:
        pct = (mc["fator"] / fator_total) if fator_total > 0 else 0
        meta_horas = pct * horas_totais
        
        estudado_horas = progresso.get(mc["nome"], 0.0)
        restante_horas = max(0.0, meta_horas - estudado_horas)
        
        meta_formatada = formatar_horas_minutos(meta_horas)
        estudado_formatada = formatar_horas_minutos(estudado_horas)
        
        # Formata o restante com indicativo visual de concluído
        if restante_horas <= 0.00027:  # Limiar de 1 segundo de margem
            restante_formatada = "Concluído"
        else:
            restante_formatada = formatar_horas_minutos(restante_horas)
        
        restante_exibicao = f"{C_GREEN}{restante_formatada:>{w_restante}}{C_RESET}" if restante_formatada == "Concluído" else f"{restante_formatada:>{w_restante}}"
        
        print(
            C_CYAN + "│" + C_RESET + f" {mc['nome']:<{w_materia}} " +
            C_CYAN + "│" + C_RESET + f" {mc['questoes_prova']:>{w_quest}.1f} " +
            C_CYAN + "│" + C_RESET + f" {mc['peso_questao']:>{w_peso}.1f} " +
            C_CYAN + "│" + C_RESET + f" {mc['dificuldade']:>{w_dif}.1f} " +
            C_CYAN + "│" + C_RESET + f" {meta_formatada:>{w_meta}} " +
            C_CYAN + "│" + C_RESET + f" {estudado_formatada:>{w_estudado}} " +
            C_CYAN + "│" + C_RESET + f" {restante_exibicao} " +
            C_CYAN + "│"
        )

    print(border_bot)
    
    # Progresso Geral do Ciclo
    total_estudado = sum(progresso.values())
    pct_concluido = (total_estudado / horas_totais * 100) if horas_totais > 0 else 0
    total_estudado_f = formatar_horas_minutos(total_estudado)
    horas_totais_f = formatar_horas_minutos(horas_totais)
    print(f"\n{C_BOLD}Progresso Geral do Ciclo:{C_RESET} {C_GREEN}{total_estudado_f} / {horas_totais_f} ({pct_concluido:.1f}% concluído){C_RESET}")
    print(f"{C_BOLD}Fator de Relevância Total:{C_RESET} {fator_total:.1f}")
    
    if pausar:
        print(C_CYAN + "─" * largura_tabela + C_RESET)
        input(f"Pressione {C_GREEN}Enter{C_RESET} para voltar ao menu...")

def adicionar_materia(dados):
    """Permite adicionar uma nova matéria ao ciclo."""
    clear_screen()
    print_header("ADICIONAR NOVA MATÉRIA")
    
    nome = obter_input_str("Nome da matéria: ")
    
    # Valida duplicidade
    for m in dados["materias"]:
        if m["nome"].lower() == nome.lower():
            print(f"\n{C_RED}Erro: Já existe uma matéria chamada '{m['nome']}'.{C_RESET}")
            input("\nPressione Enter para retornar...")
            return

    questoes_prova = obter_input_float("Quantidade de questões na prova (ex: 10): ", min_val=1.0)
    peso_questao = obter_input_float("Peso de cada questão (ex: 1, 1.5, 2): ", min_val=0.1)
    
    print()
    mostrar_guia_dificuldade()
    dificuldade = obter_input_float("Dificuldade da matéria (1 a 5): ", min_val=1.0, max_val=5.0)
    
    dados["materias"].append({
        "nome": nome,
        "questoes_prova": questoes_prova,
        "peso_questao": peso_questao,
        "dificuldade": dificuldade
    })
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Matéria '{nome}' adicionada com sucesso!{C_RESET}")
    input("\nPressione Enter para continuar...")

def editar_materia(dados):
    """Permite alterar parâmetros de uma matéria cadastrada."""
    clear_screen()
    print_header("EDITAR MATÉRIA EXISTENTE")
    
    materias = dados.get("materias", [])
    if not materias:
        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada para editar.{C_RESET}")
        input("\nPressione Enter para voltar ao menu...")
        return
        
    for i, m in enumerate(materias, start=1):
        qp = m.get("questoes_prova", 10.0)
        pq = m.get("peso_questao", 1.0)
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']} (Questões: {qp}, Peso Q.: {pq}, Dif: {m['dificuldade']})")
        
    print_divider()
    opcao = obter_input_float("Escolha o número da matéria para editar (ou 0 para cancelar): ", min_val=0, max_val=len(materias))
    if opcao == 0:
        return
        
    idx = int(opcao) - 1
    materia = materias[idx]
    
    clear_screen()
    print_header(f"EDITANDO: {materia['nome']}")
    print(f"{C_YELLOW}(Deixe em branco/Pressione Enter para manter o valor atual){C_RESET}\n")
    
    novo_nome = obter_input_str(f"Nome da matéria [{materia['nome']}]: ", obrigatorio=False, default=materia['nome'])
    
    # Valida duplicidade se o nome for alterado
    if novo_nome.lower() != materia['nome'].lower():
        for m in materias:
            if m['nome'].lower() == novo_nome.lower():
                print(f"\n{C_RED}Erro: Já existe outra matéria cadastrada como '{m['nome']}'.{C_RESET}")
                input("\nPressione Enter para voltar...")
                return
    
    qp_atual = materia.get("questoes_prova", 10.0)
    questoes_prova = obter_input_float(f"Quantidade de questões na prova [{qp_atual}]: ", min_val=1.0, default=qp_atual)
    
    pq_atual = materia.get("peso_questao", 1.0)
    peso_questao = obter_input_float(f"Peso de cada questão [{pq_atual}]: ", min_val=0.1, default=pq_atual)
    
    print()
    mostrar_guia_dificuldade()
    dificuldade = obter_input_float(f"Dificuldade (1 a 5) [{materia['dificuldade']}]: ", min_val=1.0, max_val=5.0, default=materia['dificuldade'])
    
    # Se mudar o nome da matéria, também precisamos ajustar o progresso_atual e o histórico de sessões
    velho_nome = materia['nome']
    if novo_nome != velho_nome:
        if velho_nome in dados.get("progresso_atual", {}):
            dados["progresso_atual"][novo_nome] = dados["progresso_atual"].pop(velho_nome)
        for s in dados.get("historico_sessoes", []):
            if s.get("materia") == velho_nome:
                s["materia"] = novo_nome

    materia['nome'] = novo_nome
    materia['questoes_prova'] = questoes_prova
    materia['peso_questao'] = peso_questao
    materia['dificuldade'] = dificuldade
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Matéria '{novo_nome}' atualizada com sucesso!{C_RESET}")
    input("\nPressione Enter para continuar...")

def remover_materia(dados):
    """Permite deletar uma matéria cadastrada."""
    clear_screen()
    print_header("REMOVER MATÉRIA")
    
    materias = dados.get("materias", [])
    if not materias:
        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada para remover.{C_RESET}")
        input("\nPressione Enter para voltar ao menu...")
        return
        
    for i, m in enumerate(materias, start=1):
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']}")
        
    print_divider()
    opcao = obter_input_float("Escolha o número da matéria para remover (ou 0 para cancelar): ", min_val=0, max_val=len(materias))
    if opcao == 0:
        return
        
    idx = int(opcao) - 1
    materia_nome = materias[idx]['nome']
    
    confirmar = obter_input_str(f"Deseja realmente remover '{materia_nome}'? (S/N): ").upper()
    if confirmar == 'S':
        materias.pop(idx)
        # Limpa o progresso associado a essa matéria
        if materia_nome in dados.get("progresso_atual", {}):
            del dados["progresso_atual"][materia_nome]
        salvar_dados(dados)
        print(f"\n{C_GREEN}✔ Matéria '{materia_nome}' removida com sucesso!{C_RESET}")
    else:
        print(f"\n{C_YELLOW}Remoção cancelada.{C_RESET}")
        
    input("\nPressione Enter para continuar...")

def alterar_horas(dados):
    """Altera as horas totais disponíveis semanalmente."""
    clear_screen()
    print_header("ALTERAR HORAS SEMANAIS")
    
    horas_atuais = dados.get("horas_semanais", 0.0)
    print(f"Horas semanais atuais: {C_GREEN}{horas_atuais}h{C_RESET}\n")
    
    novas_horas = obter_input_float("Nova quantidade de horas semanais disponíveis: ", min_val=0.1)
    
    dados["horas_semanais"] = novas_horas
    salvar_dados(dados)
    
    print(f"\n{C_GREEN}✔ Horas semanais atualizadas para {novas_horas}h!{C_RESET}")
    input("\nPressione Enter para continuar...")

def verificar_conclusao_ciclo(dados):
    """Verifica se todas as metas do ciclo foram batidas e, se sim, reinicia o ciclo salvando no histórico."""
    materias = dados.get("materias", [])
    horas_totais = dados.get("horas_semanais", 0.0)
    progresso = dados.get("progresso_atual", {})
    
    if not materias or horas_totais <= 0:
        return False
        
    fator_total = 0.0
    materias_fator = {}
    for m in materias:
        fator = (m["questoes_prova"] * m["peso_questao"]) * m["dificuldade"]
        fator_total += fator
        materias_fator[m["nome"]] = fator
        
    concluiu_tudo = True
    for m in materias:
        fator = materias_fator[m["nome"]]
        pct = (fator / fator_total) if fator_total > 0 else 0
        meta = pct * horas_totais
        estudado = progresso.get(m["nome"], 0.0)
        # Se restarem mais de 1 segundo (0.00027 horas)
        if meta - estudado > 0.00027:
            concluiu_tudo = False
            break
            
    if concluiu_tudo:
        # Registra no histórico e reinicia
        data_fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        registro_materias = []
        for m in materias:
            f = materias_fator[m["nome"]]
            pct = f / fator_total
            registro_materias.append({
                "nome": m["nome"],
                "meta": pct * horas_totais,
                "estudado": progresso.get(m["nome"], 0.0)
            })
            
        novo_ciclo_historico = {
            "id": len(dados.get("historico_ciclos", [])) + 1,
            "data_inicio": dados.get("data_inicio_ciclo", data_fim),
            "data_fim": data_fim,
            "horas_planejadas": horas_totais,
            "materias_estudadas": registro_materias
        }
        dados.setdefault("historico_ciclos", []).append(novo_ciclo_historico)
        
        # Reinicia o progresso
        dados["progresso_atual"] = {}
        dados["data_inicio_ciclo"] = data_fim
        salvar_dados(dados)
        
        clear_screen()
        width = obter_largura_ui()
        print(C_GREEN + "╔" + "═" * (width - 2) + "╗")
        print("║" + "🎉 PARABÉNS! VOCÊ CONCLUIU SEU CICLO DE ESTUDOS! 🎉".center(width - 2) + "║")
        print("╚" + "═" * (width - 2) + "╝" + C_RESET)
        print(f"\n  • Início do Ciclo: {novo_ciclo_historico['data_inicio']}")
        print(f"  • Fim do Ciclo:    {novo_ciclo_historico['data_fim']}")
        print(f"  • Carga Horária:   {horas_totais}h total de foco")
        print(f"\n{C_YELLOW}Este ciclo foi arquivado no histórico de progresso.{C_RESET}")
        print(f"{C_GREEN}Um novo ciclo de estudos foi reiniciado automaticamente!{C_RESET}")
        return True
        
    return False

def registrar_progresso(dados):
    """Permite registrar horas estudadas em uma matéria e valida conclusão de ciclo."""
    clear_screen()
    print_header("REGISTRAR PROGRESSO DE ESTUDOS")
    
    materias = dados.get("materias", [])
    if not materias:
        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada para registrar progresso.{C_RESET}")
        input("\nPressione Enter para voltar...")
        return
        
    # Listagem de matérias
    for i, m in enumerate(materias, start=1):
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']}")
        
    print_divider()
    opcao = obter_input_float("Escolha o número da matéria estudada (ou 0 para cancelar): ", min_val=0, max_val=len(materias))
    if opcao == 0:
        return
        
    idx = int(opcao) - 1
    materia_nome = materias[idx]['nome']
    
    print(f"\nRegistrando progresso para: {C_BOLD}{materia_nome}{C_RESET}")
    print(f"Formatos aceitos: {C_YELLOW}1.5{C_RESET} (1h30m), {C_YELLOW}1:30{C_RESET} (1h30m), {C_YELLOW}1:30:12{C_RESET} (1h30m12s), {C_YELLOW}1h27m{C_RESET}, {C_YELLOW}30m12s{C_RESET}, {C_YELLOW}50s{C_RESET}")
    
    while True:
        entrada_tempo = obter_input_str("Quanto tempo você estudou? ")
        try:
            horas_estudadas = parse_tempo_input(entrada_tempo)
            if horas_estudadas <= 0:
                print(f"{C_RED}Erro: O tempo de estudo deve ser maior que zero.{C_RESET}")
                continue
            break
        except ValueError as e:
            print(f"{C_RED}Erro de formato: {e}. Tente novamente.{C_RESET}")
            
    # Atualiza o progresso
    progresso = dados.setdefault("progresso_atual", {})
    progresso[materia_nome] = progresso.get(materia_nome, 0.0) + horas_estudadas
    
    print(f"\n{C_YELLOW}(Opcional) Digite uma observação/anotação sobre o que estudou:{C_RESET}")
    obs = obter_input_str("Observação: ", obrigatorio=False)
    
    # Salva no histórico de sessões
    sessoes = dados.setdefault("historico_sessoes", [])
    sessoes.append({
        "materia": materia_nome,
        "horas": horas_estudadas,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": "registro",
        "obs": obs
    })
    
    salvar_dados(dados)
    
    tempo_formatado = formatar_horas_minutos(horas_estudadas)
    print(f"\n{C_GREEN}✔ Registrado {tempo_formatado} de estudos em '{materia_nome}'!{C_RESET}")
    
    # --- Verificação de Conclusão do Ciclo ---
    verificar_conclusao_ciclo(dados)
    input("\nPressione Enter para continuar...")

def ajustar_progresso(dados):
    """Permite ajustar/alterar o progresso acumulado de estudos de uma matéria."""
    clear_screen()
    print_header("AJUSTAR PROGRESSO DE ESTUDOS")
    
    materias = dados.get("materias", [])
    if not materias:
        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada para ajustar progresso.{C_RESET}")
        input("\nPressione Enter para voltar ao menu...")
        return
        
    progresso = dados.setdefault("progresso_atual", {})
    
    # Listagem de matérias com progresso atual
    for i, m in enumerate(materias, start=1):
        estudado_horas = progresso.get(m["nome"], 0.0)
        tempo_formatado = formatar_horas_minutos(estudado_horas)
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']} (Estudado: {C_GREEN}{tempo_formatado}{C_RESET})")
        
    print_divider()
    opcao = obter_input_float("Escolha o número da matéria para ajustar (ou 0 para cancelar): ", min_val=0, max_val=len(materias))
    if opcao == 0:
        return
        
    idx = int(opcao) - 1
    materia_nome = materias[idx]['nome']
    estudado_horas_atual = progresso.get(materia_nome, 0.0)
    tempo_atual_formatado = formatar_horas_minutos(estudado_horas_atual)
    
    print(f"\nAjustando progresso acumulado para: {C_BOLD}{materia_nome}{C_RESET}")
    print(f"Progresso atual: {C_GREEN}{tempo_atual_formatado}{C_RESET}")
    print(f"Formatos aceitos: {C_YELLOW}1.5{C_RESET} (1h30m), {C_YELLOW}1:30{C_RESET} (1h30m), {C_YELLOW}1:30:12{C_RESET} (1h30m12s), {C_YELLOW}1h27m{C_RESET}, {C_YELLOW}30m12s{C_RESET}, {C_YELLOW}50s{C_RESET}")
    print(f"{C_YELLOW}(Deixe em branco/Pressione Enter para manter o valor atual){C_RESET}\n")
    
    while True:
        entrada_tempo = input(f"Novo progresso acumulado [{tempo_atual_formatado}]: ").strip()
        if not entrada_tempo:
            print(f"\n{C_YELLOW}Progresso mantido em {tempo_atual_formatado}.{C_RESET}")
            input("\nPressione Enter para continuar...")
            return
            
        try:
            novas_horas = parse_tempo_input(entrada_tempo)
            if novas_horas < 0:
                print(f"{C_RED}Erro: O tempo de estudo não pode ser negativo.{C_RESET}")
                continue
            break
        except ValueError as e:
            print(f"{C_RED}Erro de formato: {e}. Tente novamente.{C_RESET}")
            
    progresso[materia_nome] = novas_horas
    
    # Salva no histórico de sessões
    sessoes = dados.setdefault("historico_sessoes", [])
    sessoes.append({
        "materia": materia_nome,
        "horas": novas_horas,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": "ajuste",
        "obs": f"Ajuste de progresso acumulado (anterior: {tempo_atual_formatado})"
    })
    
    salvar_dados(dados)
    
    tempo_novo_formatado = formatar_horas_minutos(novas_horas)
    print(f"\n{C_GREEN}✔ Progresso de '{materia_nome}' ajustado com sucesso para {tempo_novo_formatado}!{C_RESET}")
    
    # --- Verificação de Conclusão do Ciclo ---
    verificar_conclusao_ciclo(dados)
    input("\nPressione Enter para continuar...")

def exibir_historico_ciclos(dados):
    """Exibe a listagem de ciclos de estudos passados completados."""
    clear_screen()
    print_header("HISTÓRICO DE CICLOS CONCLUÍDOS")
    
    historico = dados.get("historico_ciclos", [])
    if not historico:
        print(f"\n{C_YELLOW}⚠ Nenhum ciclo concluído no histórico ainda.{C_RESET}")
        print("Complete as metas do seu ciclo atual para registrar sua primeira conquista!")
        input("\nPressione Enter para voltar ao menu...")
        return
        
    for c in reversed(historico):
        print(f"\n{C_BOLD}CICLO #{c['id']}{C_RESET} ─ {C_GREEN}CONCLUÍDO{C_RESET}")
        print(f"  Período: {c['data_inicio']} até {c['data_fim']}")
        print(f"  Carga Horária: {c['horas_planejadas']}h planejadas")
        print("  Estudo por matéria:")
        for mat in c.get("materias_estudadas", []):
            meta_f = formatar_horas_minutos(mat.get("meta", 0))
            est_f = formatar_horas_minutos(mat.get("estudado", 0))
            print(f"    • {mat['nome']}: {est_f} estudados (Meta: {meta_f})")
        print_divider()
        
    input("\nPressione Enter para voltar...")

def adicionar_sessao_estudo_manual(dados):
    """Permite adicionar uma nova sessão de estudos manual com data personalizada."""
    clear_screen()
    print_header("ADICIONAR REGISTRO DE ESTUDO MANUAL")
    
    materias = dados.get("materias", [])
    if not materias:
        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada. Cadastre uma matéria primeiro.{C_RESET}")
        input("\nPressione Enter para continuar...")
        return
        
    # 1. Matéria
    print("Selecione a Matéria:")
    for i, m in enumerate(materias, start=1):
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']}")
    print_divider()
    op_mat = obter_input_float("Escolha o número da matéria: ", min_val=1, max_val=len(materias))
    materia_nome = materias[int(op_mat) - 1]["nome"]
    
    # 2. Horas
    print(f"\nFormatos aceitos: {C_YELLOW}1.5{C_RESET} (1h30m), {C_YELLOW}1:30{C_RESET} (1h30m), {C_YELLOW}1:30:12{C_RESET} (1h30m12s), {C_YELLOW}1h27m{C_RESET}, {C_YELLOW}30m12s{C_RESET}, {C_YELLOW}50s{C_RESET}")
    while True:
        entrada_tempo = obter_input_str("Quanto tempo você estudou? ")
        try:
            horas_estudadas = parse_tempo_input(entrada_tempo)
            if horas_estudadas <= 0:
                print(f"{C_RED}Erro: O tempo de estudo deve ser maior que zero.{C_RESET}")
                continue
            break
        except ValueError as e:
            print(f"{C_RED}Erro de formato: {e}. Tente novamente.{C_RESET}")
            
    # 3. Data e Hora
    default_data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    while True:
        entrada_data = obter_input_str(f"Data/Hora do estudo [{default_data}]: ", obrigatorio=False, default=default_data)
        try:
            datetime.strptime(entrada_data, "%d/%m/%Y %H:%M:%S")
            break
        except ValueError:
            print(f"{C_RED}Erro: Data inválida! Use o formato DD/MM/AAAA HH:MM:SS.{C_RESET}")
            
    # 4. Observação
    obs = obter_input_str("Observação (opcional): ", obrigatorio=False)
    
    # Adiciona ao histórico de sessões
    sessoes = dados.setdefault("historico_sessoes", [])
    sessoes.append({
        "materia": materia_nome,
        "horas": horas_estudadas,
        "data": entrada_data,
        "tipo": "registro",
        "obs": obs
    })
    
    # Recalcula e salva
    from database import recalcular_progresso_atual
    recalcular_progresso_atual(dados)
    salvar_dados(dados)
    
    tempo_formatado = formatar_horas_minutos(horas_estudadas)
    print(f"\n{C_GREEN}✔ Registro de {tempo_formatado} em '{materia_nome}' adicionado com sucesso!{C_RESET}")
    input("\nPressione Enter para continuar...")

def editar_sessao_estudo(dados, sessoes_filtradas_com_index):
    """Edita um registro específico de sessão de estudo."""
    clear_screen()
    print_header("EDITAR REGISTRO DE ESTUDO")
    
    if not sessoes_filtradas_com_index:
        print(f"\n{C_YELLOW}Nenhum registro para editar.{C_RESET}")
        input("\nPressione Enter para continuar...")
        return
        
    num = obter_input_float("Digite o número do registro que deseja EDITAR: ", min_val=1, max_val=len(sessoes_filtradas_com_index))
    idx_filtro = len(sessoes_filtradas_com_index) - int(num)
    original_idx, s = sessoes_filtradas_com_index[idx_filtro]
    
    clear_screen()
    print_header(f"EDITANDO REGISTRO EM {s.get('data')}")
    print(f"{C_YELLOW}(Deixe em branco/Pressione Enter para manter o valor atual){C_RESET}\n")
    
    # 1. Matéria
    materias = dados.get("materias", [])
    print("Selecione a Matéria:")
    for i, m in enumerate(materias, start=1):
        marcador = " (Atual)" if m["nome"].lower() == s.get("materia", "").lower() else ""
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']}{marcador}")
    print_divider()
    op_mat = obter_input_float(f"Escolha o número da matéria (ou Enter para manter '{s.get('materia')}'): ", min_val=0, max_val=len(materias), default=-1)
    if op_mat == -1:
        nova_materia = s.get("materia")
    else:
        nova_materia = materias[int(op_mat) - 1]["nome"]
        
    # 2. Horas
    tempo_atual = formatar_horas_minutos(s.get("horas", 0.0))
    while True:
        entrada_tempo = input(f"Tempo de estudo [{tempo_atual}]: ").strip()
        if not entrada_tempo:
            novas_horas = s.get("horas", 0.0)
            break
        try:
            novas_horas = parse_tempo_input(entrada_tempo)
            if novas_horas <= 0:
                print(f"{C_RED}Erro: O tempo de estudo deve ser maior que zero.{C_RESET}")
                continue
            break
        except ValueError as e:
            print(f"{C_RED}Erro de formato: {e}. Tente novamente.{C_RESET}")
            
    # 3. Data e Hora
    while True:
        nova_data = input(f"Data/Hora do estudo [{s.get('data')}]: ").strip()
        if not nova_data:
            nova_data = s.get("data")
            break
        try:
            datetime.strptime(nova_data, "%d/%m/%Y %H:%M:%S")
            break
        except ValueError:
            print(f"{C_RED}Erro: Data inválida! Use o formato DD/MM/AAAA HH:MM:SS.{C_RESET}")
            
    # 4. Observação
    nova_obs = obter_input_str(f"Observação [{s.get('obs', '')}]: ", obrigatorio=False, default=s.get("obs", ""))
    
    # Atualiza o registro
    s["materia"] = nova_materia
    s["horas"] = novas_horas
    s["data"] = nova_data
    s["obs"] = nova_obs
    s["editado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Atualiza a lista no dados
    dados["historico_sessoes"][original_idx] = s
    
    # Recalcula o progresso e salva
    from database import recalcular_progresso_atual
    recalcular_progresso_atual(dados)
    salvar_dados(dados)
    
    print(f"\n{C_GREEN}✔ Registro de estudo editado com sucesso!{C_RESET}")
    input("\nPressione Enter para continuar...")

def excluir_sessao_estudo(dados, sessoes_filtradas_com_index):
    """Exclui um registro de sessão de estudo e recalcula o progresso."""
    clear_screen()
    print_header("EXCLUIR REGISTRO DE ESTUDO")
    
    if not sessoes_filtradas_com_index:
        print(f"\n{C_YELLOW}Nenhum registro para excluir.{C_RESET}")
        input("\nPressione Enter para continuar...")
        return
        
    num = obter_input_float("Digite o número do registro que deseja EXCLUIR: ", min_val=1, max_val=len(sessoes_filtradas_com_index))
    idx_filtro = len(sessoes_filtradas_com_index) - int(num)
    original_idx, s = sessoes_filtradas_com_index[idx_filtro]
    
    tempo_f = formatar_horas_minutos(s.get("horas", 0.0))
    print(f"\nVocê escolheu o registro:")
    print(f"  📅 Data:    {s.get('data')}")
    print(f"  📚 Matéria: {s.get('materia')}")
    print(f"  ⏱️ Tempo:   {tempo_f}")
    print_divider()
    
    confirmar = obter_input_str("Deseja realmente EXCLUIR este registro? (S/N): ").upper()
    if confirmar == 'S':
        dados["historico_sessoes"].pop(original_idx)
        
        # Recalcula o progresso e salva
        from database import recalcular_progresso_atual
        recalcular_progresso_atual(dados)
        salvar_dados(dados)
        
        print(f"\n{C_GREEN}✔ Registro excluído com sucesso!{C_RESET}")
    else:
        print(f"\n{C_YELLOW}Exclusão cancelada.{C_RESET}")
        
    input("\nPressione Enter para continuar...")

def exibir_historico_sessoes(dados):
    """Exibe o histórico detalhado de sessões de estudo (logs de progressos) com CRUD."""
    materia_filtro = None
    
    while True:
        try:
            clear_screen()
            sessoes = dados.get("historico_sessoes", [])
            
            titulo = "HISTÓRICO DETALHADO DE SESSÕES (LOGS)"
            if materia_filtro:
                titulo += f" - {materia_filtro.upper()}"
            print_header(titulo)
            
            # Filtra sessões guardando os índices originais
            sessoes_filtradas_com_index = []
            for idx, s in enumerate(sessoes):
                if not materia_filtro or s.get("materia", "").lower() == materia_filtro.lower():
                    sessoes_filtradas_com_index.append((idx, s))
                
            if not sessoes_filtradas_com_index:
                print(f"\n{C_YELLOW}⚠ Nenhuma sessão de estudo registrada.{C_RESET}")
                if materia_filtro:
                    print(f"Nenhum registro encontrado para a matéria '{materia_filtro}'.")
            else:
                # Mostra as mais antigas primeiro (ordem cronológica), numerando de K a 1 de cima para baixo
                # para que o mais recente (embaixo) tenha o número 1
                K = len(sessoes_filtradas_com_index)
                for idx_filtro, (original_idx, s) in enumerate(sessoes_filtradas_com_index):
                    i = K - idx_filtro
                    data_hora = s.get("data", "N/A")
                    materia = s.get("materia", "N/A")
                    horas = s.get("horas", 0.0)
                    tipo = s.get("tipo", "registro")
                    obs = s.get("obs", "")
                    editado_em = s.get("editado_em", None)
                    
                    tempo_f = formatar_horas_minutos(horas)
                    
                    if tipo == "ajuste":
                        msg = f"Ajustou o progresso acumulado para {C_GREEN}{tempo_f}{C_RESET}."
                    else:
                        msg = f"Estudou por {C_GREEN}{tempo_f}{C_RESET}."
                    
                    print(f"  [{C_CYAN}{i}{C_RESET}] 📅 Realizado em: {C_BOLD}{data_hora}{C_RESET}")
                    if editado_em:
                        print(f"      ✏️ Editado em:   {C_YELLOW}{editado_em}{C_RESET}")
                    print(f"      📚 Matéria:      {C_CYAN}{materia}{C_RESET}")
                    print(f"      💬 Ação:         {msg}")
                    if obs:
                        print(f"      📝 Obs:          {C_YELLOW}{obs}{C_RESET}")
                    print_divider()
                    
            print(f"  [{C_CYAN}1{C_RESET}] ➕ Adicionar Novo Registro de Estudo")
            if sessoes_filtradas_com_index:
                print(f"  [{C_CYAN}2{C_RESET}] ✏️  Editar Registro de Estudo")
                print(f"  [{C_CYAN}3{C_RESET}] ❌ Excluir Registro de Estudo")
            print(f"  [{C_CYAN}F{C_RESET}] Filtrar por Matéria")
            if materia_filtro:
                print(f"  [{C_CYAN}T{C_RESET}] Remover Filtro (Mostrar Todas)")
            print(f"  [{C_CYAN}L{C_RESET}] Limpar Histórico de Sessões")
            print(f"  [{C_CYAN}0{C_RESET}] Voltar ao Menu de Históricos")
            print_divider()
            
            opcao = input("Escolha uma opção: ").strip().upper()
            
            try:
                if not opcao or opcao == "0":
                    break
                elif opcao == "1":
                    adicionar_sessao_estudo_manual(dados)
                elif opcao == "2" and sessoes_filtradas_com_index:
                    editar_sessao_estudo(dados, sessoes_filtradas_com_index)
                elif opcao == "3" and sessoes_filtradas_com_index:
                    excluir_sessao_estudo(dados, sessoes_filtradas_com_index)
                elif opcao == "F":
                    materias = dados.get("materias", [])
                    if not materias:
                        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada para filtrar.{C_RESET}")
                        input("\nPressione Enter para continuar...")
                        continue
                        
                    clear_screen()
                    print_header("FILTRAR POR MATÉRIA")
                    for i, m in enumerate(materias, start=1):
                        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']}")
                    print_divider()
                    opcao_m = obter_input_float("Escolha o número da matéria (ou 0 para cancelar): ", min_val=0, max_val=len(materias))
                    if opcao_m > 0:
                        materia_filtro = materias[int(opcao_m) - 1]["nome"]
                elif opcao == "T":
                    materia_filtro = None
                elif opcao == "L":
                    confirmar = obter_input_str("Deseja realmente apagar TODO o histórico de sessões? (S/N): ").upper()
                    if confirmar == "S":
                        confirmar2 = obter_input_str("Digite 'CONFIRMAR' para prosseguir com a exclusão definitiva: ").upper()
                        if confirmar2 == "CONFIRMAR":
                            dados["historico_sessoes"] = []
                            from database import recalcular_progresso_atual
                            recalcular_progresso_atual(dados)
                            salvar_dados(dados)
                            print(f"\n{C_GREEN}✔ Histórico de sessões apagado com sucesso!{C_RESET}")
                            input("\nPressione Enter para continuar...")
                        else:
                            print(f"\n{C_YELLOW}Ação cancelada (confirmação inválida).{C_RESET}")
                            input("\nPressione Enter para continuar...")
                    else:
                        print(f"\n{C_YELLOW}Ação cancelada.{C_RESET}")
                        input("\nPressione Enter para continuar...")
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            break

def exibir_historico(dados):
    """Submenu para exibir históricos do ciclo e sessões de estudo."""
    while True:
        try:
            clear_screen()
            print_header("HISTÓRICOS DE ESTUDOS")
            
            print(f"  [{C_CYAN}1{C_RESET}] 📅 Ver Histórico de Ciclos Completados")
            print(f"  [{C_CYAN}2{C_RESET}] 📝 Ver Histórico Detalhado de Sessões (Logs)")
            print(f"  [{C_CYAN}0{C_RESET}] ↩️  Voltar ao Menu Principal")
            print_divider()
            
            opcao = input("Escolha uma opção: ").strip()
            try:
                if opcao == "1":
                    exibir_historico_ciclos(dados)
                elif opcao == "2":
                    exibir_historico_sessoes(dados)
                elif opcao == "0":
                    break
                else:
                    print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 2.{C_RESET}")
                    input("\nPressione Enter para tentar novamente...")
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            break

def configuracao_inicial(dados):
    """Guia o usuário na primeira configuração estratégica de estudos."""
    clear_screen()
    print_header("CONFIGURAÇÃO INICIAL ESTRATÉGICA")
    print("Olá! Vamos configurar seu Ciclo de Estudos inicial rapidamente.\n")
    
    dados["horas_semanais"] = obter_input_float("Quantas horas semanais você tem disponíveis para estudar? ", min_val=0.1)
    
    print("\nAdicione sua primeira matéria:")
    nome = obter_input_str("Nome da matéria: ")
    questoes_prova = obter_input_float("Quantidade de questões na prova (ex: 10): ", min_val=1.0)
    peso_questao = obter_input_float("Peso de cada questão (ex: 1, 1.5, 2): ", min_val=0.1)
    
    print()
    mostrar_guia_dificuldade()
    dificuldade = obter_input_float("Dificuldade da matéria (1 a 5): ", min_val=1.0, max_val=5.0)
    
    dados["materias"].append({
        "nome": nome,
        "questoes_prova": questoes_prova,
        "peso_questao": peso_questao,
        "dificuldade": dificuldade
    })
    
    dados["data_inicio_ciclo"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Configuração inicial concluída com sucesso!{C_RESET}")
    input("\nPressione Enter para acessar o Menu Principal...")

def calcular_metricas_acompanhamento(dados):
    from datetime import datetime, timedelta
    
    # 1. Carga horária total do ciclo
    horas_totais = dados.get("horas_semanais", 0.0)
    
    # 2. Total estudado no ciclo atual
    progresso = dados.get("progresso_atual", {})
    total_estudado = sum(progresso.values())
    
    # 3. Tempo restante no ciclo
    horas_restantes = max(0.0, horas_totais - total_estudado)
    
    # 4. Percentual concluído
    pct_concluido = (total_estudado / horas_totais * 100) if horas_totais > 0 else 0.0
    
    # 5. Dias/tempo decorrido no ciclo atual
    data_inicio_str = dados.get("data_inicio_ciclo")
    dt_inicio = None
    dias_no_ciclo = 0.0
    if data_inicio_str:
        try:
            dt_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y %H:%M:%S")
            dias_no_ciclo = (datetime.now() - dt_inicio).total_seconds() / 86400.0
        except Exception:
            pass
            
    if dias_no_ciclo < 0.0:
        dias_no_ciclo = 0.0
        
    # 6. Médias semanais baseadas no histórico geral de sessões de estudo
    sessoes = dados.get("historico_sessoes", [])
    sessoes_registro = [s for s in sessoes if s.get("tipo") == "registro"]
    total_horas_historico = sum(s.get("horas", 0.0) for s in sessoes_registro)
    
    datas = []
    for s in sessoes_registro:
        try:
            dt = datetime.strptime(s["data"], "%d/%m/%Y %H:%M:%S")
            datas.append(dt)
        except Exception:
            pass
            
    if datas:
        dt_primeira = min(datas)
        dias_desde_inicio = (datetime.now() - dt_primeira).total_seconds() / 86400.0
        semanas_desde_inicio = max(1.0 / 7.0, dias_desde_inicio / 7.0)
        media_semanal_historica = total_horas_historico / semanas_desde_inicio
    else:
        media_semanal_historica = 0.0
        dias_desde_inicio = 0.0
        
    # 7. Horas nos últimos 7 e 30 dias
    agora = datetime.now()
    horas_ultimos_7_dias = 0.0
    horas_ultimos_30_dias = 0.0
    for s in sessoes_registro:
        try:
            dt = datetime.strptime(s["data"], "%d/%m/%Y %H:%M:%S")
            dias_atras = (agora - dt).total_seconds() / 86400.0
            if dias_atras <= 7.0:
                horas_ultimos_7_dias += s.get("horas", 0.0)
            if dias_atras <= 30.0:
                horas_ultimos_30_dias += s.get("horas", 0.0)
        except Exception:
            pass
            
    if datas:
        dias_para_divisor_30 = min(30.0, max(1.0, dias_desde_inicio))
        media_semanal_30_dias = (horas_ultimos_30_dias / dias_para_divisor_30) * 7.0
    else:
        media_semanal_30_dias = 0.0
        
    # 8. Estimativa de ritmo diário (horas/dia)
    ritmo_diario_historico = total_horas_historico / max(1.0, dias_desde_inicio) if datas else 0.0
    
    if total_estudado > 0.0:
        if dias_no_ciclo >= 1.0:
            ritmo_diario = total_estudado / dias_no_ciclo
            origem_ritmo = "Ciclo Atual"
        else:
            if ritmo_diario_historico > 0.0:
                ritmo_diario = ritmo_diario_historico
                origem_ritmo = "Média Histórica Geral"
            else:
                ritmo_diario = total_estudado / max(0.5, dias_no_ciclo)
                origem_ritmo = "Ciclo Atual (Estimativa)"
    else:
        if ritmo_diario_historico > 0.0:
            ritmo_diario = ritmo_diario_historico
            origem_ritmo = "Média Histórica Geral"
        else:
            ritmo_diario = 0.0
            origem_ritmo = "Sem dados de estudo"
            
    # Ritmo ideal diário para fechar o ciclo em 7 dias
    ritmo_ideal_diario = horas_totais / 7.0 if horas_totais > 0 else 0.0
    
    # Previsão de conclusão do ciclo
    if ritmo_diario > 0.0:
        dias_para_concluir = horas_restantes / ritmo_diario
        previsao_conclusao = agora + timedelta(days=dias_para_concluir)
    else:
        dias_para_concluir = None
        previsao_conclusao = None
        
    return {
        "horas_totais": horas_totais,
        "total_estudado": total_estudado,
        "horas_restantes": horas_restantes,
        "pct_concluido": pct_concluido,
        "dias_no_ciclo": dias_no_ciclo,
        "media_semanal_historica": media_semanal_historica,
        "horas_ultimos_7_dias": horas_ultimos_7_dias,
        "media_semanal_30_dias": media_semanal_30_dias,
        "ritmo_diario": ritmo_diario,
        "origem_ritmo": origem_ritmo,
        "ritmo_ideal_diario": ritmo_ideal_diario,
        "dias_para_concluir": dias_para_concluir,
        "previsao_conclusao": previsao_conclusao,
        "dt_inicio": dt_inicio
    }

def exibir_acompanhamento_ciclo(dados, pausar=True):
    clear_screen()
    print_header("PAINEL DE ACOMPANHAMENTO DO CICLO")
    
    metricas = calcular_metricas_acompanhamento(dados)
    
    # Progresso Geral
    horas_totais = metricas["horas_totais"]
    total_estudado = metricas["total_estudado"]
    horas_restantes = metricas["horas_restantes"]
    pct_concluido = metricas["pct_concluido"]
    dias_no_ciclo = metricas["dias_no_ciclo"]
    
    # Formatações de horas
    horas_totais_f = formatar_horas_minutos(horas_totais)
    total_estudado_f = formatar_horas_minutos(total_estudado)
    horas_restantes_f = formatar_horas_minutos(horas_restantes)
    
    # Barra de Progresso Visual
    largura_barra = 30
    preenchido = int((pct_concluido / 100.0) * largura_barra)
    preenchido = min(largura_barra, max(0, preenchido))
    vazio = largura_barra - preenchido
    barra_str = f"[{C_GREEN}{'█' * preenchido}{C_RESET}{'░' * vazio}] {C_BOLD}{pct_concluido:.1f}%{C_RESET}"
    
    # Dias no ciclo atual
    dias_int = int(dias_no_ciclo)
    horas_int = int((dias_no_ciclo - dias_int) * 24)
    minutos_int = int(((dias_no_ciclo - dias_int) * 24 - horas_int) * 60)
    
    if dias_int > 0:
        tempo_ciclo_str = f"{dias_int}d {horas_int}h {minutos_int}m"
    elif horas_int > 0:
        tempo_ciclo_str = f"{horas_int}h {minutos_int}m"
    else:
        tempo_ciclo_str = f"{minutos_int}m (recém-iniciado)"
        
    import partner_menu
    streak = partner_menu.calcular_streak(dados)
    
    print(f"  {C_BOLD}Progresso Geral do Ciclo Atual:{C_RESET}")
    print(f"    • Meta Total:      {C_CYAN}{horas_totais_f}{C_RESET}")
    print(f"    • Total Estudado:  {C_GREEN}{total_estudado_f}{C_RESET}")
    print(f"    • Tempo Restante:  {C_YELLOW if horas_restantes > 0 else C_GREEN}{horas_restantes_f}{C_RESET}")
    print(f"    • Barra de Status: {barra_str}")
    print(f"    • Tempo Decorrido: {C_BOLD}{tempo_ciclo_str}{C_RESET} desde o início")
    print(f"    • Sequência Atual: {C_GREEN}{streak} dias seguidos{C_RESET} 🔥")
    print_divider()
    
    # Ritmo e Médias de Estudo
    media_semanal_historica = metricas["media_semanal_historica"]
    horas_ultimos_7_dias = metricas["horas_ultimos_7_dias"]
    media_semanal_30_dias = metricas["media_semanal_30_dias"]
    ritmo_diario = metricas["ritmo_diario"]
    origem_ritmo = metricas["origem_ritmo"]
    ritmo_ideal_diario = metricas["ritmo_ideal_diario"]
    
    media_sem_hist_f = formatar_horas_minutos(media_semanal_historica)
    horas_7_dias_f = formatar_horas_minutos(horas_ultimos_7_dias)
    media_30_dias_f = formatar_horas_minutos(media_semanal_30_dias)
    
    print(f"  {C_BOLD}Histórico de Ritmo & Médias Semanais:{C_RESET}")
    print(f"    • Horas nesta semana (Últimos 7 dias): {C_GREEN}{horas_7_dias_f}{C_RESET}")
    print(f"    • Média semanal recente (Últimos 30 dias): {C_CYAN}{media_30_dias_f}{C_RESET}")
    print(f"    • Média semanal geral (Todo o histórico): {C_CYAN}{media_sem_hist_f}{C_RESET}")
    print_divider()
    
    # Calendário de Consistência
    partner_menu.exibir_calendario_consistencia(dados)
    print_divider()
    
    # Previsão e Diagnóstico
    print(f"  {C_BOLD}Previsão de Conclusão (Expectativa vs Realidade):{C_RESET}")
    
    if ritmo_diario <= 0.0:
        print(f"    {C_YELLOW}⚠ Não há dados de estudos suficientes para calcular a previsão de término.{C_RESET}")
        print("    Registre suas sessões de estudo para começar a ver as projeções de ritmo.")
    else:
        previsao_conclusao = metricas["previsao_conclusao"]
        dias_para_concluir = metricas["dias_para_concluir"]
        
        # Formata data da previsão
        data_previsao_str = previsao_conclusao.strftime("%d/%m/%Y %H:%M")
        
        # Calcula ritmo semanal do usuário baseado no ritmo diário atual
        ritmo_semanal_atual = ritmo_diario * 7.0
        ritmo_semanal_atual_f = formatar_horas_minutos(ritmo_semanal_atual)
        ritmo_ideal_semanal_f = formatar_horas_minutos(horas_totais)
        
        print(f"    • Ritmo Diário Atual:   {C_GREEN}{formatar_horas_minutos(ritmo_diario)}{C_RESET}/dia (Base: {origem_ritmo})")
        print(f"    • Ritmo Semanal Atual:  {C_GREEN}{ritmo_semanal_atual_f}{C_RESET}/semana")
        print(f"    • Ritmo Diário Ideal:   {C_CYAN}{formatar_horas_minutos(ritmo_ideal_diario)}{C_RESET}/dia (para fechar em 7 dias)")
        
        if horas_restantes <= 0.0:
            print(f"\n    {C_GREEN}🎉 Ciclo concluído! Vá para o menu e verifique a conclusão para reiniciar.{C_RESET}")
        else:
            print(f"    • Prazo Estimado:       {C_BOLD}{dias_para_concluir:.1f} dias{C_RESET} restantes")
            print(f"    • Data Prevista:        {C_GREEN}{data_previsao_str}{C_RESET}")
            
            # Diagnóstico Comparativo
            print()
            if ritmo_semanal_atual >= horas_totais:
                print(f"    {C_GREEN}✔ [RITMO EXCELENTE] Seu ritmo é suficiente para concluir o ciclo dentro do prazo semanal!{C_RESET}")
                print("    Você está mantendo a constância necessária. Continue assim!")
            elif ritmo_semanal_atual >= horas_totais * 0.7:
                print(f"    {C_YELLOW}⚠ [RITMO MODERADO] Seu ritmo atual está levemente abaixo do ideal.{C_RESET}")
                print(f"    Para concluir o ciclo exatamente em 7 dias, tente estudar mais {formatar_horas_minutos(ritmo_ideal_diario - ritmo_diario)} por dia.")
            else:
                print(f"    {C_RED}✘ [RITMO INSUFICIENTE] Seu ritmo está muito abaixo do planejado.{C_RESET}")
                print(f"    Realidade: Você está estudando {ritmo_semanal_atual_f}/semana (Meta: {ritmo_ideal_semanal_f}/semana).")
                print(f"    Com este ritmo, você demorará {dias_para_concluir:.1f} dias para concluir o que resta.")
                print(f"    {C_YELLOW}Recomendação: Ajuste sua rotina diária ou reduza sua meta de horas semanais no menu principal.{C_RESET}")
                
    if pausar:
        print_divider()
        input(f"Pressione {C_GREEN}Enter{C_RESET} para voltar ao menu...")

def menu_ciclo_progresso(dados):
    """Submenu para gerenciar o ciclo de estudos e progresso."""
    import partner_menu
    while True:
        try:
            clear_screen()
            print_header("CICLO DE ESTUDOS & PROGRESSO")
            
            horas = dados.get("horas_semanais", 0.0)
            total_estudado = sum(dados.get("progresso_atual", {}).values())
            streak = partner_menu.calcular_streak(dados)
            carga_formatada = formatar_horas_minutos(horas)
            estudado_formatado = formatar_horas_minutos(total_estudado)
            print(f"  {C_BOLD}Carga Semanal:{C_RESET} {C_GREEN}{carga_formatada}{C_RESET} | {C_BOLD}Estudado:{C_RESET} {C_GREEN}{estudado_formatado}{C_RESET} | {C_BOLD}Sequência:{C_RESET} {C_GREEN}{streak} dias{C_RESET} 🔥")
            print_divider()
            
            print(f"  [{C_CYAN}1{C_RESET}] 📅 Ver Ciclo de Estudos Atual")
            print(f"  [{C_CYAN}2{C_RESET}] 📝 Registrar Progresso de Estudos")
            print(f"  [{C_CYAN}3{C_RESET}] ⚙️  Ajustar Progresso Acumulado")
            print(f"  [{C_CYAN}4{C_RESET}] ⏱️  Alterar Horas Semanais")
            print(f"  [{C_CYAN}5{C_RESET}] 📊 Painel de Acompanhamento do Ciclo")
            print(f"  [{C_CYAN}0{C_RESET}] ↩️  Voltar ao Menu Principal")
            print_divider()
            
            opcao = input("Escolha uma opção: ").strip()
            try:
                if opcao == "1":
                    exibir_ciclo(dados, pausar=True)
                elif opcao == "2":
                    registrar_progresso(dados)
                elif opcao == "3":
                    ajustar_progresso(dados)
                elif opcao == "4":
                    alterar_horas(dados)
                elif opcao == "5":
                    exibir_acompanhamento_ciclo(dados)
                elif opcao == "0":
                    break
                else:
                    print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 5.{C_RESET}")
                    input("\nPressione Enter para tentar novamente...")
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            break

def menu_materias(dados):
    """Submenu para gerenciamento de matérias."""
    while True:
        try:
            clear_screen()
            print_header("GERENCIAR MATÉRIAS")
            
            num_materias = len(dados.get("materias", []))
            print(f"  {C_BOLD}Matérias Cadastradas:{C_RESET} {C_GREEN}{num_materias}{C_RESET}")
            print_divider()
            
            print(f"  [{C_CYAN}1{C_RESET}] ➕ Adicionar Nova Matéria")
            print(f"  [{C_CYAN}2{C_RESET}] ✏️  Editar Matéria Existente")
            print(f"  [{C_CYAN}3{C_RESET}] ❌ Remover Matéria")
            print(f"  [{C_CYAN}0{C_RESET}] ↩️  Voltar ao Menu Principal")
            print_divider()
            
            opcao = input("Escolha uma opção: ").strip()
            try:
                if opcao == "1":
                    adicionar_materia(dados)
                elif opcao == "2":
                    editar_materia(dados)
                elif opcao == "3":
                    remover_materia(dados)
                elif opcao == "0":
                    break
                else:
                    print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 3.{C_RESET}")
                    input("\nPressione Enter para tentar novamente...")
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            break

def verificar_atualizacao(dados):
    """Verifica se há atualizações do script no GitHub e atualiza via git pull."""
    import urllib.request
    import subprocess
    import sys
    import os

    clear_screen()
    print_header("VERIFICAR ATUALIZAÇÕES")

    # 1. Obter versão local
    versao_local = "1.0.0"
    if os.path.exists("version.txt"):
        try:
            with open("version.txt", "r", encoding="utf-8") as f:
                versao_local = f.read().strip()
        except Exception as e:
            print(f"{C_RED}Erro ao ler versão local:{C_RESET} {e}")
            
    print(f"Versão local: {C_GREEN}{versao_local}{C_RESET}")
    print("Verificando versão no GitHub...")

    # 2. Obter versão remota
    url_remota = "https://raw.githubusercontent.com/nissincjs/Gerencicador-de-estudos/main/version.txt"
    try:
        req = urllib.request.Request(url_remota, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            versao_remota = response.read().decode('utf-8').strip()
    except Exception as e:
        print(f"\n{C_RED}Não foi possível conectar ao GitHub para verificar atualizações.{C_RESET}")
        print(f"Erro: {e}")
        input("\nPressione Enter para voltar ao menu...")
        return

    # 3. Comparar versões
    if versao_local == versao_remota:
        print(f"\n{C_GREEN}✔ Você já possui a versão mais recente ({versao_local})!{C_RESET}")
        input("\nPressione Enter para retornar...")
        return

    # Se a versão for diferente
    print(f"\n{C_YELLOW}⚠ Uma nova versão está disponível!{C_RESET}")
    print(f"  • Versão Local:  {C_RED}{versao_local}{C_RESET}")
    print(f"  • Versão Remota: {C_GREEN}{versao_remota}{C_RESET}")
    print_divider()
    
    opcao = obter_input_str("Deseja atualizar o script agora? (S/N): ").strip().upper()
    if opcao == "S":
        print(f"\n{C_CYAN}Executando atualização via 'git pull'...{C_RESET}\n")
        try:
            # Tenta executar o git pull
            resultado = subprocess.run(["git", "pull"], capture_output=True, text=True, check=True)
            print(f"{C_GREEN}✔ Atualização via git concluída com sucesso!{C_RESET}")
            if resultado.stdout:
                print(f"{C_CYAN}Saída do Git:{C_RESET}\n{resultado.stdout}")
            
            print(f"\n{C_YELLOW}A aplicação será encerrada para aplicar as atualizações. Por favor, inicie o script novamente.{C_RESET}")
            input("\nPressione Enter para fechar...")
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"{C_RED}Erro ao executar 'git pull':{C_RESET}")
            if e.stderr:
                print(e.stderr)
            else:
                print(e)
            print(f"\n{C_YELLOW}Tente rodar 'git pull' manualmente no seu terminal.{C_RESET}")
            input("\nPressione Enter para retornar...")
        except FileNotFoundError:
            print(f"{C_RED}Erro: O comando 'git' não foi encontrado no seu sistema.{C_RESET}")
            print(f"Por favor, instale o Git ou atualize os arquivos manualmente baixando do repositório.")
            input("\nPressione Enter para retornar...")
        except Exception as e:
            print(f"{C_RED}Erro inesperado ao atualizar:{C_RESET} {e}")
            input("\nPressione Enter para retornar...")
    else:
        print(f"\n{C_YELLOW}Atualização cancelada.{C_RESET}")
        input("\nPressione Enter para retornar...")
