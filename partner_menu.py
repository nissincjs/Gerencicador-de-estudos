from datetime import datetime, date, timedelta
import supabase_client
import calendar
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, UI_WIDTH
)
from utils import (
    clear_screen, print_header, print_divider, obter_input_str, formatar_horas_minutos, obter_input_float
)
from database import salvar_dados

def calcular_streak(sessoes: list) -> int:
    """Calcula a sequência de dias seguidos estudando."""
    datas_estudadas = set()
    for s in sessoes:
        if s.get("tipo") == "registro":
            try:
                dt_str = s.get("data", "").split()[0]
                dt = datetime.strptime(dt_str, "%d/%m/%Y").date()
                datas_estudadas.add(dt)
            except Exception:
                pass
                
    if not datas_estudadas:
        return 0
        
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    
    if hoje not in datas_estudadas and ontem not in datas_estudadas:
        return 0
        
    streak = 0
    check_date = hoje if hoje in datas_estudadas else ontem
    
    while check_date in datas_estudadas:
        streak += 1
        check_date -= timedelta(days=1)
        
    return streak

def obter_estudos_hoje(sessoes: list) -> dict:
    """Retorna informações sobre os estudos realizados no dia de hoje."""
    hoje_str = date.today().strftime("%d/%m/%Y")
    sessoes_hoje = []
    for s in sessoes:
        if s.get("tipo") == "registro" and s.get("data", "").startswith(hoje_str):
            sessoes_hoje.append(s)
            
    total_horas = sum(s.get("horas", 0.0) for s in sessoes_hoje)
    materias = list(set(s.get("materia") for s in sessoes_hoje))
    
    return {
        "estudou": len(sessoes_hoje) > 0,
        "total_horas": total_horas,
        "materias": materias
    }

def obter_metas_semana(dados: dict) -> dict:
    """Calcula a quantidade de metas semanais cumpridas."""
    materias = dados.get("materias", [])
    horas_totais = dados.get("horas_semanais", 0.0)
    progresso = dados.get("progresso_atual", {})
    
    if not materias or horas_totais <= 0:
        return {"cumpridas": 0, "total": 0}
        
    fator_total = sum((m.get("questoes_prova", 10.0) * m.get("peso_questao", 1.0) * m.get("dificuldade", 1.0)) for m in materias)
    
    cumpridas = 0
    for m in materias:
        f = (m.get("questoes_prova", 10.0) * m.get("peso_questao", 1.0)) * m.get("dificuldade", 1.0)
        pct = (f / fator_total) if fator_total > 0 else 0
        meta = pct * horas_totais
        estudado = progresso.get(m["nome"], 0.0)
        if estudado >= meta - 0.016:  # Margem de 1 minuto
            cumpridas += 1
            
    return {"cumpridas": cumpridas, "total": len(materias)}

def exibir_calendario_consistencia(dados):
    """Gera e exibe um calendário de consistência estilo GitHub para o mês atual."""
    hoje = date.today()
    ano = hoje.year
    mes = hoje.month
    
    # Nome do mês em português
    nomes_meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    nome_mes = nomes_meses.get(mes, "Mês Atual")
    
    print(f"\n  {C_BOLD}📅 Calendário de Consistência - {nome_mes} / {ano}{C_RESET}")
    print(f"  {C_CYAN}{C_BOLD}DOM  SEG  TER  QUA  QUI  SEX  SAB{C_RESET}")
    
    primeiro_dia_semana, num_dias = calendar.monthrange(ano, mes)
    primeiro_dia_nossa_semana = (primeiro_dia_semana + 1) % 7
    
    sessoes = dados.get("historico_sessoes", [])
    justificativas = dados.get("justificativas", [])
    
    status_dias = {}
    for dia in range(1, num_dias + 1):
        dia_date = date(ano, mes, dia)
        dia_str = dia_date.strftime("%d/%m/%Y")
        
        # Verifica se estudou
        estudou = False
        for s in sessoes:
            if s.get("tipo") == "registro" and s.get("data", "").startswith(dia_str):
                if s.get("horas", 0.0) > 0:
                    estudou = True
                    break
        
        # Verifica se justificou
        justificou = False
        if not estudou:
            for j in justificativas:
                if j.get("data") == dia_str:
                    justificou = True
                    break
                    
        if dia_date > hoje:
            status_dias[dia] = "⬜" # Futuro
        elif estudou:
            status_dias[dia] = "🟩" # Estudou
        elif justificou:
            status_dias[dia] = "🟨" # Justificado
        else:
            status_dias[dia] = "🟥" # Não estudou
            
    linha = "  "
    for _ in range(primeiro_dia_nossa_semana):
        linha += "     "
        
    dia_atual = 1
    coluna = primeiro_dia_nossa_semana
    while dia_atual <= num_dias:
        linha += f" {status_dias[dia_atual]}  "
        dia_atual += 1
        coluna += 1
        
        if coluna == 7:
            print(linha)
            linha = "  "
            coluna = 0
            
    if coluna > 0:
        print(linha)
        
    print(f"\n  {C_BOLD}Legenda:{C_RESET} 🟩 Estudou | 🟥 Não Estudou | 🟨 Justificado | ⬜ Futuro")

def exibir_status_parceiro(perfil_parceiro):
    """Exibe o painel de métricas de estudo do parceiro."""
    clear_screen()
    print_header(f"ACOMPANHAMENTO: {perfil_parceiro['email'].upper()}")
    
    # Baixa os dados do parceiro no Supabase
    print(f"{C_YELLOW}Buscando dados em tempo real do parceiro...{C_RESET}")
    dados_parceiro = supabase_client.baixar_dados_parceiro(perfil_parceiro["user_id"])
    
    if not dados_parceiro:
        print(f"\n{C_RED}⚠ O parceiro ainda não sincronizou dados na nuvem.{C_RESET}")
        input("\nPressione Enter para voltar...")
        return
        
    sessoes = dados_parceiro.get("historico_sessoes", [])
    estudos_hoje = obter_estudos_hoje(sessoes)
    streak = calcular_streak(sessoes)
    metas = obter_metas_semana(dados_parceiro)
    justificativas = dados_parceiro.get("justificativas", [])
    
    print_divider()
    print(f"  {C_BOLD}Status Hoje:{C_RESET}", end=" ")
    if estudos_hoje["estudou"]:
        print(f"{C_GREEN}ESTUDOU! 📚{C_RESET}")
        print(f"  • Tempo Estudado: {C_GREEN}{formatar_horas_minutos(estudos_hoje['total_horas'])}{C_RESET}")
        print(f"  • Matérias: {C_CYAN}{', '.join(estudos_hoje['materias'])}{C_RESET}")
    else:
        print(f"{C_RED}Ainda não registrou estudos hoje ⏳{C_RESET}")
        
    print(f"\n  {C_BOLD}Sequência de Consistência:{C_RESET} {C_GREEN}{streak} dias seguidos{C_RESET} 🔥")
    print(f"  {C_BOLD}Metas da Semana:{C_RESET} {C_GREEN}{metas['cumpridas']}/{metas['total']}{C_RESET} matérias concluídas 🎯")
    
    print_divider()
    # Exibe o calendário de consistência
    exibir_calendario_consistencia(dados_parceiro)
    
    print_divider()
    print(f"  {C_BOLD}Justificativas de Ausência:{C_RESET}")
    if not justificativas:
        print("    Nenhuma justificativa registrada.")
    else:
        for j in reversed(justificativas[-5:]):  # Mostra as últimas 5
            editado_str = f" (Editado em {j['editado_em']})" if j.get("editado_em") else ""
            print(f"    • {C_YELLOW}{j.get('data')}{C_RESET}: {j.get('motivo')}{C_YELLOW}{editado_str}{C_RESET}")
            
    print_divider()
    input("\nPressione Enter para voltar...")

def registrar_justificativa_propria(dados):
    """Permite ao usuário justificar um dia que não estudou."""
    clear_screen()
    print_header("REGISTRAR JUSTIFICATIVA")
    
    print("Justifique sua ausência para manter seu parceiro de estudos informado.")
    print("Exemplos: 'Fiquei doente', 'Viagem de trabalho', 'Emergência familiar'.\n")
    
    # Data da justificativa
    default_data = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
    data_just = obter_input_str(f"Data da ausência [{default_data}]: ", obrigatorio=False, default=default_data)
    
    # Valida formato da data
    try:
        datetime.strptime(data_just, "%d/%m/%Y")
    except ValueError:
        print(f"\n{C_RED}Erro: Data inválida! Use o formato DD/MM/AAAA.{C_RESET}")
        input("\nPressione Enter para voltar...")
        return
        
    motivo = obter_input_str("Motivo / Justificativa: ")
    
    # Salva no dicionário local
    justificativas = dados.setdefault("justificativas", [])
    
    # Evita duplicidade para o mesmo dia
    justificativas = [j for j in justificativas if j.get("data") != data_just]
    justificativas.append({
        "data": data_just,
        "motivo": motivo,
        "registrado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    dados["justificativas"] = justificativas
    
    # Salva e sincroniza
    salvar_dados(dados)
    
    print(f"\n{C_GREEN}✔ Justificativa registrada para o dia {data_just} com sucesso!{C_RESET}")
    input("\nPressione Enter para continuar...")

def editar_justificativa_propria(dados):
    """Permite editar uma justificativa registrada."""
    clear_screen()
    print_header("EDITAR JUSTIFICATIVA DE AUSÊNCIA")
    
    justificativas = dados.get("justificativas", [])
    if not justificativas:
        print(f"\n{C_YELLOW}Nenhuma justificativa para editar.{C_RESET}")
        input("\nPressione Enter para retornar...")
        return
        
    opcao = obter_input_float("Escolha o número da justificativa para editar (ou 0 para cancelar): ", min_val=0, max_val=len(justificativas))
    if opcao == 0:
        return
        
    idx = int(opcao) - 1
    j = justificativas[idx]
    
    clear_screen()
    print_header("EDITANDO JUSTIFICATIVA")
    print(f"{C_YELLOW}(Deixe em branco/Pressione Enter para manter o valor atual){C_RESET}\n")
    
    # Data
    while True:
        nova_data = input(f"Data da ausência [{j.get('data')}]: ").strip()
        if not nova_data:
            nova_data = j.get('data')
            break
        try:
            datetime.strptime(nova_data, "%d/%m/%Y")
            # Evita duplicar se mudar para um dia que já tem justificativa
            duplicado = False
            for k_idx, k in enumerate(justificativas):
                if k_idx != idx and k.get("data") == nova_data:
                    duplicado = True
                    break
            if duplicado:
                print(f"{C_RED}Erro: Já existe uma justificativa para o dia {nova_data}.{C_RESET}")
                continue
            break
        except ValueError:
            print(f"{C_RED}Erro: Data inválida! Use o formato DD/MM/AAAA.{C_RESET}")
            
    # Motivo
    novo_motivo = obter_input_str(f"Motivo / Justificativa [{j.get('motivo')}]: ", obrigatorio=False, default=j.get('motivo'))
    
    j["data"] = nova_data
    j["motivo"] = novo_motivo
    j["editado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Justificativa editada com sucesso!{C_RESET}")
    input("\nPressione Enter para continuar...")

def excluir_justificativa_propria(dados):
    """Permite excluir uma justificativa registrada."""
    clear_screen()
    print_header("EXCLUIR JUSTIFICATIVA DE AUSÊNCIA")
    
    justificativas = dados.get("justificativas", [])
    if not justificativas:
        print(f"\n{C_YELLOW}Nenhuma justificativa para excluir.{C_RESET}")
        input("\nPressione Enter para retornar...")
        return
        
    opcao = obter_input_float("Escolha o número da justificativa para excluir (ou 0 para cancelar): ", min_val=0, max_val=len(justificativas))
    if opcao == 0:
        return
        
    idx = int(opcao) - 1
    j = justificativas[idx]
    
    confirmar = obter_input_str(f"Deseja realmente excluir a justificativa do dia {j.get('data')}? (S/N): ").upper()
    if confirmar == 'S':
        justificativas.pop(idx)
        salvar_dados(dados)
        print(f"\n{C_GREEN}✔ Justificativa excluída com sucesso!{C_RESET}")
    else:
        print(f"\n{C_YELLOW}Exclusão cancelada.{C_RESET}")
        
    input("\nPressione Enter para continuar...")

def menu_justificativas(dados):
    """Menu CRUD para gerenciamento de justificativas de ausência."""
    while True:
        clear_screen()
        print_header("GERENCIAR JUSTIFICATIVAS DE AUSÊNCIA")
        
        justificativas = dados.get("justificativas", [])
        
        if not justificativas:
            print(f"\n{C_YELLOW}⚠ Nenhuma justificativa cadastrada.{C_RESET}\n")
        else:
            for i, j in enumerate(justificativas, start=1):
                editado_str = f" (Editado em: {j['editado_em']})" if j.get("editado_em") else ""
                print(f"  [{C_CYAN}{i}{C_RESET}] 📅 {C_BOLD}{j.get('data')}{C_RESET} - {j.get('motivo')}{C_YELLOW}{editado_str}{C_RESET}")
                print(f"      Criado em: {j.get('registrado_em', 'N/A')}")
                print_divider()
                
        print(f"  [{C_CYAN}1{C_RESET}] ➕ Registrar Nova Justificativa")
        if justificativas:
            print(f"  [{C_CYAN}2{C_RESET}] ✏️  Editar Justificativa")
            print(f"  [{C_CYAN}3{C_RESET}] ❌ Excluir Justificativa")
        print(f"  [{C_CYAN}0{C_RESET}] ↩️  Voltar")
        print_divider()
        
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "1":
            registrar_justificativa_propria(dados)
        elif opcao == "2" and justificativas:
            editar_justificativa_propria(dados)
        elif opcao == "3" and justificativas:
            excluir_justificativa_propria(dados)
        elif opcao == "0":
            break

def menu_parceria(dados):
    """Menu principal do sistema de parceiros."""
    while True:
        clear_screen()
        print_header("PARCEIRO DE ESTUDOS (RESPONSABILIDADE MÚTUA)")
        
        # Busca o perfil do usuário logado
        perfil = supabase_client.obter_perfil()
        if not perfil:
            print(f"\n{C_RED}Não foi possível carregar seu perfil. Verifique sua conexão.{C_RESET}")
            input("\nPressione Enter para voltar...")
            return
            
        parceiro_id = perfil.get("parceiro_id")
        
        if not parceiro_id:
            # Sem parceiro vinculado
            print(f"  Seu código de convite: {C_BOLD}{C_GREEN}{perfil.get('codigo_convite')}{C_RESET}")
            print("  Compartilhe este código com seu parceiro de estudos para se vincularem!\n")
            print(f"  [{C_CYAN}1{C_RESET}] 🤝 Vincular Parceiro (Inserir código)")
            print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
            print_divider()
            
            opcao = input("Escolha uma opção: ").strip()
            if opcao == "1":
                codigo = input("\nDigite o código de convite do seu parceiro (ex: ST-XXXXXX): ").strip()
                if not codigo:
                    continue
                print(f"\n{C_YELLOW}Tentando estabelecer vínculo...{C_RESET}")
                try:
                    supabase_client.vincular_parceiro(codigo)
                    print(f"\n{C_GREEN}✔ Vínculo realizado com sucesso! Bons estudos em equipe!{C_RESET}")
                except Exception as e:
                    print(f"\n{C_RED}Erro ao vincular: {e}{C_RESET}")
                input("\nPressione Enter para continuar...")
            elif opcao == "0":
                break
        else:
            # Com parceiro vinculado (pode estar pendente de confirmação mútua)
            perfil_parceiro = supabase_client.obter_perfil_por_id(parceiro_id)
            eh_mutuo = perfil_parceiro and perfil_parceiro.get("parceiro_id") == perfil.get("user_id")
            
            if eh_mutuo:
                parceiro_email = perfil_parceiro["email"] if perfil_parceiro else "Parceiro"
                
                print(f"  Parceiro vinculado: {C_GREEN}{parceiro_email}{C_RESET}\n")
                print(f"  [{C_CYAN}1{C_RESET}] 📊 Acompanhar Consistência do Parceiro")
                print(f"  [{C_CYAN}2{C_RESET}] 📝 Gerenciar Justificativas de Ausência (CRUD)")
                print(f"  [{C_CYAN}9{C_RESET}] ❌ Desvincular Parceiro de Estudos")
                print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
                print_divider()
                
                opcao = input("Escolha uma opção: ").strip()
                if opcao == "1":
                    if perfil_parceiro:
                        exibir_status_parceiro(perfil_parceiro)
                    else:
                        print(f"\n{C_RED}Erro ao obter perfil do parceiro.{C_RESET}")
                        input("\nPressione Enter para continuar...")
                elif opcao == "2":
                    menu_justificativas(dados)
                elif opcao == "9":
                    confirmar = input(f"\n{C_RED}Deseja realmente remover o vínculo com {parceiro_email}? (S/N): {C_RESET}").strip().upper()
                    if confirmar == "S":
                        supabase_client.desvincular_parceiro()
                        print(f"\n{C_GREEN}Parceiro desvinculado com sucesso.{C_RESET}")
                    else:
                        print(f"\n{C_YELLOW}Ação cancelada.{C_RESET}")
                    input("\nPressione Enter para continuar...")
                elif opcao == "0":
                    break
            else:
                # Vínculo pendente (Usuário atual vinculou o parceiro, mas o parceiro ainda não vinculou de volta)
                parceiro_email = perfil_parceiro["email"] if perfil_parceiro else "Parceiro"
                print(f"  Solicitação de vínculo enviada para: {C_GREEN}{parceiro_email}{C_RESET}")
                print(f"  {C_YELLOW}Aguardando que ele insira seu código de convite para ativar o vínculo.{C_RESET}")
                print(f"  Seu código de convite para passar para ele: {C_BOLD}{C_GREEN}{perfil.get('codigo_convite')}{C_RESET}\n")
                print(f"  [{C_CYAN}9{C_RESET}] ❌ Cancelar Solicitação de Vínculo")
                print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
                print_divider()
                
                opcao = input("Escolha uma opção: ").strip()
                if opcao == "9":
                    confirmar = input(f"\n{C_RED}Deseja realmente cancelar a solicitação para {parceiro_email}? (S/N): {C_RESET}").strip().upper()
                    if confirmar == "S":
                        supabase_client.desvincular_parceiro()
                        print(f"\n{C_GREEN}Solicitação cancelada com sucesso.{C_RESET}")
                    else:
                        print(f"\n{C_YELLOW}Ação cancelada.{C_RESET}")
                    input("\nPressione Enter para continuar...")
                elif opcao == "0":
                    break
