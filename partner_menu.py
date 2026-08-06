from datetime import datetime, date, timedelta
import supabase_client
import calendar
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET
)
from utils import (
    clear_screen, print_header, print_divider, obter_input_str, formatar_horas_minutos, obter_input_float,
    print_override as print, input_override as input
)
from database import salvar_dados
from calculo import (
    calcular_estudos_por_dia, calcular_streak, obter_estudos_hoje, obter_metas_semana
)

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
    
    estudos_por_dia = calcular_estudos_por_dia(dados)
    justificativas = dados.get("justificativas", [])
    
    status_dias = {}
    for dia in range(1, num_dias + 1):
        dia_date = date(ano, mes, dia)
        dia_str = dia_date.strftime("%d/%m/%Y")
        
        # Verifica se estudou
        horas_dia = sum(estudos_por_dia.get(dia_str, {}).values())
        estudou = horas_dia >= 0.00027
        
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

def visualizar_logs_dia_membro(dados_membro):
    """Permite ao usuário visualizar os logs de estudo de um membro para um dia específico."""
    while True:
        clear_screen()
        print_header("LOGS DE ESTUDO DO MEMBRO POR DATA")
        
        ontem_str = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        print(f"Digite a data no formato {C_YELLOW}DD/MM/AAAA{C_RESET} (ou {C_CYAN}0{C_RESET} para voltar).")
        print(f"Exemplo: {ontem_str}\n")
        
        data_input = input(f"Data [{ontem_str}]: ").strip()
        if data_input == "0":
            break
        if not data_input:
            data_input = ontem_str
            
        try:
            datetime.strptime(data_input, "%d/%m/%Y")
        except ValueError:
            print(f"\n{C_RED}Erro: Data inválida! Use o formato DD/MM/AAAA.{C_RESET}")
            input("\nPressione Enter para tentar novamente...")
            continue
            
        sessoes = dados_membro.get("historico_sessoes", [])
        sessoes_do_dia = []
        for s in sessoes:
            data_s = s.get("data", "")
            if not data_s:
                continue
            dia_s = data_s.split()[0]
            if dia_s == data_input:
                sessoes_do_dia.append(s)
                
        clear_screen()
        print_header(f"LOGS DO MEMBRO EM {data_input}")
        
        if not sessoes_do_dia:
            print(f"\n{C_YELLOW}⚠ Nenhum registro de estudo ou ajuste encontrado para o dia {data_input}.{C_RESET}")
        else:
            def obter_horario(s):
                data_s = s.get("data", "")
                try:
                    return datetime.strptime(data_s, "%d/%m/%Y %H:%M:%S")
                except Exception:
                    return datetime.min
                    
            sessoes_do_dia_ordenadas = sorted(sessoes_do_dia, key=obter_horario)
            
            total_horas = 0.0
            for idx, s in enumerate(sessoes_do_dia_ordenadas, start=1):
                data_s = s.get("data", "")
                horario = "N/A"
                if len(data_s.split()) > 1:
                    horario = data_s.split()[1]
                    
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
                    
                print(f"  📅 Horário: {C_BOLD}{horario}{C_RESET}")
                if editado_em:
                    print(f"      ✏️ Editado em:   {C_YELLOW}{editado_em}{C_RESET}")
                print(f"      📚 Matéria:      {C_CYAN}{materia}{C_RESET}")
                print(f"      💬 Ação:         {msg}")
                if obs:
                    print(f"      📝 Obs:          {C_YELLOW}{obs}{C_RESET}")
                print_divider()
                
            # Calcula o tempo total real estudado no dia considerando os deltas (e ajustes)
            estudos_do_dia_dict = calcular_estudos_por_dia(dados_membro).get(data_input, {})
            total_horas = max(0.0, sum(estudos_do_dia_dict.values()))
            print(f"\n  {C_BOLD}Total de Estudo Focado no Dia:{C_RESET} {C_GREEN}{formatar_horas_minutos(total_horas)}{C_RESET}")
            
        input("\nPressione Enter para voltar à consulta por data...")

def exibir_status_membro(perfil_membro, dados_locais=None):
    """Exibe o painel de métricas de estudo de um membro do grupo."""
    clear_screen()
    print_header(f"ACOMPANHAMENTO: {perfil_membro['email'].upper()}")
    
    # Usa os dados locais (caso seja o próprio usuário) ou baixa do Supabase
    dados_membro = dados_locais
    if dados_membro is None:
        print(f"{C_YELLOW}Buscando dados em tempo real do membro...{C_RESET}")
        dados_membro = supabase_client.baixar_dados_membro(perfil_membro["user_id"])
    
    if not dados_membro:
        print(f"\n{C_RED}⚠ Este membro ainda não sincronizou dados na nuvem.{C_RESET}")
        input("\nPressione Enter para voltar...")
        return
        
    while True:
        clear_screen()
        print_header(f"ACOMPANHAMENTO: {perfil_membro['email'].upper()}")
        
        estudos_hoje = obter_estudos_hoje(dados_membro)
        streak = calcular_streak(dados_membro)
        metas = obter_metas_semana(dados_membro)
        justificativas = dados_membro.get("justificativas", [])
        
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
        exibir_calendario_consistencia(dados_membro)
        
        print_divider()
        print(f"  {C_BOLD}Justificativas de Ausência:{C_RESET}")
        if not justificativas:
            print("    Nenhuma justificativa registrada.")
        else:
            for j in reversed(justificativas[-5:]):  # Mostra as últimas 5
                editado_str = f" (Editado em {j['editado_em']})" if j.get("editado_em") else ""
                print(f"    • {C_YELLOW}{j.get('data')}{C_RESET}: {j.get('motivo')}{C_YELLOW}{editado_str}{C_RESET}")
                
        print_divider()
        print(f"  [{C_CYAN}1{C_RESET}] 📝 Visualizar Logs Detalhados de um Dia Específico")
        print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
        print_divider()
        
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "1":
            visualizar_logs_dia_membro(dados_membro)
        elif opcao == "0" or not opcao:
            break

def registrar_justificativa_propria(dados):
    """Permite ao usuário justificar um dia que não estudou."""
    clear_screen()
    print_header("REGISTRAR JUSTIFICATIVA")
    
    print("Justifique sua ausência para manter seu grupo de estudos informado.")
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
        try:
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
            try:
                if opcao == "1":
                    registrar_justificativa_propria(dados)
                elif opcao == "2" and justificativas:
                    editar_justificativa_propria(dados)
                elif opcao == "3" and justificativas:
                    excluir_justificativa_propria(dados)
                elif opcao == "0":
                    break
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            break

def exibir_resumo_grupo(dados):
    """Exibe o dashboard de resumo de todos os membros do grupo."""
    membros = supabase_client.listar_membros_grupo()
    if not membros:
        return False

    current_user_id = supabase_client.obter_id_usuario()

    print_divider()
    print(f"  {C_BOLD}👥 Membros do Grupo ({len(membros)}):{C_RESET}")
    print_divider()

    for i, membro in enumerate(membros, start=1):
        eh_voce = membro["user_id"] == current_user_id
        nome_exib = "VOCÊ" if eh_voce else membro["email"].split("@")[0]

        if eh_voce:
            dados_membro = dados
            status = "✅" if obter_estudos_hoje(dados_membro)["estudou"] else "❌"
            streak = calcular_streak(dados_membro)
            metas = obter_metas_semana(dados_membro)
            print(f"  [{i}] {C_CYAN}{nome_exib}{C_RESET} - Hoje: {status} | Seq.: {C_GREEN}{streak}d{C_RESET} 🔥 | Metas: {C_GREEN}{metas['cumpridas']}/{metas['total']}{C_RESET} {C_YELLOW}(você){C_RESET}")
        else:
            dados_membro = supabase_client.baixar_dados_membro(membro["user_id"])
            if dados_membro:
                status = "✅" if obter_estudos_hoje(dados_membro)["estudou"] else "❌"
                streak = calcular_streak(dados_membro)
                metas = obter_metas_semana(dados_membro)
                print(f"  [{i}] {C_CYAN}{nome_exib}{C_RESET} - Hoje: {status} | Seq.: {C_GREEN}{streak}d{C_RESET} 🔥 | Metas: {C_GREEN}{metas['cumpridas']}/{metas['total']}{C_RESET}")
            else:
                print(f"  [{i}] {C_CYAN}{nome_exib}{C_RESET} - {C_YELLOW}⚠ Sem dados sincronizados ainda{C_RESET}")

    print_divider()
    return True

def selecionar_membro_para_acompanhar(dados):
    """Mostra a lista de membros e permite escolher um para acompanhar em detalhes."""
    membros = supabase_client.listar_membros_grupo()
    if not membros:
        return

    clear_screen()
    print_header("ACOMPANHAR MEMBRO DO GRUPO")

    current_user_id = supabase_client.obter_id_usuario()
    print("  Escolha qual membro deseja acompanhar:\n")
    for i, membro in enumerate(membros, start=1):
        eh_voce = membro["user_id"] == current_user_id
        nome_exib = "VOCÊ" if eh_voce else membro["email"].split("@")[0]
        print(f"  [{C_CYAN}{i}{C_RESET}] {nome_exib}{C_YELLOW} (você){C_RESET}" if eh_voce else f"  [{C_CYAN}{i}{C_RESET}] {nome_exib}")
    print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
    print_divider()

    escolha = obter_input_float("Escolha o número do membro (ou 0 para voltar): ", min_val=0, max_val=len(membros))
    if escolha == 0:
        return

    idx = int(escolha) - 1
    membro = membros[idx]

    if membro["user_id"] == current_user_id:
        exibir_status_membro(membro, dados_locais=dados)
    else:
        exibir_status_membro(membro)

def criar_grupo_flow():
    """Fluxo de criação de um novo grupo de estudos."""
    clear_screen()
    print_header("CRIAR GRUPO DE ESTUDOS")

    confirmar = obter_input_str("Deseja criar um novo grupo de estudos? (S/N): ").upper()
    if confirmar != 'S':
        print(f"\n{C_YELLOW}Criação cancelada.{C_RESET}")
        input("\nPressione Enter para continuar...")
        return

    print(f"\n{C_YELLOW}Criando grupo...{C_RESET}")
    try:
        codigo = supabase_client.criar_grupo()
        print(f"\n{C_GREEN}✔ Grupo criado com sucesso! Você é o administrador.{C_RESET}")
        print(f"  Código de convite: {C_BOLD}{C_GREEN}{codigo}{C_RESET}")
        print("  Compartilhe este código para outros entrarem no grupo.\n")
    except Exception as e:
        print(f"\n{C_RED}Erro ao criar grupo: {e}{C_RESET}")
    input("\nPressione Enter para continuar...")

def entrar_grupo_flow():
    """Fluxo para entrar em um grupo existente pelo código de convite."""
    clear_screen()
    print_header("ENTRAR EM UM GRUPO DE ESTUDOS")

    codigo = input("\nDigite o código de convite do grupo (ex: GR-XXXXXX): ").strip()
    if not codigo:
        return

    print(f"\n{C_YELLOW}Entrando no grupo...{C_RESET}")
    try:
        supabase_client.entrar_grupo(codigo)
        print(f"\n{C_GREEN}✔ Você entrou no grupo com sucesso! Bons estudos em equipe!{C_RESET}")
    except Exception as e:
        print(f"\n{C_RED}Erro ao entrar no grupo: {e}{C_RESET}")
    input("\nPressione Enter para continuar...")

def sair_grupo_flow():
    """Fluxo para o usuário sair do grupo atual."""
    confirmar = input(f"\n{C_RED}Deseja realmente sair do grupo de estudos? (S/N): {C_RESET}").strip().upper()
    if confirmar == "S":
        supabase_client.sair_grupo()
        print(f"\n{C_GREEN}Você saiu do grupo com sucesso.{C_RESET}")
    else:
        print(f"\n{C_YELLOW}Ação cancelada.{C_RESET}")
    input("\nPressione Enter para continuar...")

def remover_membro_flow():
    """Fluxo para o admin remover um membro do grupo."""
    clear_screen()
    print_header("REMOVER MEMBRO DO GRUPO")

    membros = supabase_client.listar_membros_grupo()
    current_user_id = supabase_client.obter_id_usuario()
    outros = [m for m in membros if m["user_id"] != current_user_id]

    if not outros:
        print(f"\n{C_YELLOW}Não há outros membros para remover.{C_RESET}")
        input("\nPressione Enter para continuar...")
        return

    print("  Selecione o membro a ser removido:\n")
    for i, m in enumerate(outros, start=1):
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['email']}")
    print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
    print_divider()

    escolha = obter_input_float("Escolha o número do membro (ou 0 para voltar): ", min_val=0, max_val=len(outros))
    if escolha == 0:
        return

    idx = int(escolha) - 1
    alvo = outros[idx]

    confirmar = input(f"\n{C_RED}Deseja realmente remover {alvo['email']} do grupo? (S/N): {C_RESET}").strip().upper()
    if confirmar == "S":
        try:
            supabase_client.remover_membro(alvo["user_id"])
            print(f"\n{C_GREEN}✔ Membro {alvo['email']} removido com sucesso.{C_RESET}")
        except Exception as e:
            print(f"\n{C_RED}Erro ao remover membro: {e}{C_RESET}")
    else:
        print(f"\n{C_YELLOW}Ação cancelada.{C_RESET}")
    input("\nPressione Enter para continuar...")

def dissolver_grupo_flow():
    """Fluxo para o admin dissolver o grupo inteiro."""
    confirmar = input(f"\n{C_RED}Deseja realmente dissolver o grupo inteiro? Todos os membros serão removidos. (S/N): {C_RESET}").strip().upper()
    if confirmar == "S":
        supabase_client.dissolver_grupo()
        print(f"\n{C_GREEN}Grupo dissolvido com sucesso.{C_RESET}")
    else:
        print(f"\n{C_YELLOW}Ação cancelada.{C_RESET}")
    input("\nPressione Enter para continuar...")

def menu_grupo(dados):
    """Menu principal do sistema de grupos de estudos."""
    while True:
        try:
            clear_screen()
            print_header("GRUPO DE ESTUDOS (RESPONSABILIDADE MÚTUA)")

            info = supabase_client.obter_grupo_do_usuario()

            if not info:
                # Sem grupo vinculado
                print("  Você ainda não está em nenhum grupo de estudos.")
                print("  Crie um grupo e compartilhe o código, ou entre em um grupo existente!\n")
                print(f"  [{C_CYAN}1{C_RESET}] ➕ Criar Novo Grupo")
                print(f"  [{C_CYAN}2{C_RESET}] 🎟️  Entrar em um Grupo (Inserir código)")
                print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
                print_divider()

                opcao = input("Escolha uma opção: ").strip()
                try:
                    if opcao == "1":
                        criar_grupo_flow()
                    elif opcao == "2":
                        entrar_grupo_flow()
                    elif opcao == "0":
                        break
                except KeyboardInterrupt:
                    pass
            else:
                # Com grupo vinculado
                grupo = info["grupo"]
                current_user_id = supabase_client.obter_id_usuario()
                eh_admin = grupo["criador_id"] == current_user_id

                print(f"  Código do grupo: {C_BOLD}{C_GREEN}{grupo['codigo_convite']}{C_RESET}")
                print("  Compartilhe este código para outros entrarem no grupo!\n")

                exibir_resumo_grupo(dados)

                if eh_admin:
                    print(f"  Você é o {C_MAGENTA}administrador{C_RESET} do grupo. 👑")
                    print(f"  [{C_CYAN}1{C_RESET}] 📊 Acompanhar Consistência de um Membro")
                    print(f"  [{C_CYAN}2{C_RESET}] 📝 Gerenciar Justificativas de Ausência (CRUD)")
                    print(f"  [{C_CYAN}8{C_RESET}] 🚫 Remover Membro do Grupo")
                    print(f"  [{C_CYAN}9{C_RESET}] 💥 Dissolver Grupo")
                else:
                    print(f"  [{C_CYAN}1{C_RESET}] 📊 Acompanhar Consistência de um Membro")
                    print(f"  [{C_CYAN}2{C_RESET}] 📝 Gerenciar Justificativas de Ausência (CRUD)")
                    print(f"  [{C_CYAN}9{C_RESET}] 🚪 Sair do Grupo")
                print(f"  [{C_CYAN}0{C_RESET}] ↩️ Voltar")
                print_divider()

                opcao = input("Escolha uma opção: ").strip()
                try:
                    if opcao == "1":
                        selecionar_membro_para_acompanhar(dados)
                    elif opcao == "2":
                        menu_justificativas(dados)
                    elif opcao == "8" and eh_admin:
                        remover_membro_flow()
                    elif opcao == "9":
                        if eh_admin:
                            dissolver_grupo_flow()
                        else:
                            sair_grupo_flow()
                    elif opcao == "0":
                        break
                except KeyboardInterrupt:
                    pass
        except KeyboardInterrupt:
            break
