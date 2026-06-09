from datetime import datetime, timedelta
import re
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, DB_FILE, UI_WIDTH
)
from utils import (
    clear_screen, print_header, print_divider,
    obter_input_float, obter_input_str
)
from database import salvar_dados

def obter_input_data(prompt, default_hoje=True):
    """Lê uma data no formato DD/MM/YYYY e valida. Se deixada em branco, retorna hoje ou vazio."""
    default_str = datetime.now().strftime("%d/%m/%Y")
    while True:
        entrada = input(prompt).strip()
        if not entrada:
            if default_hoje:
                return default_str
            else:
                return ""
        # Valida formato DD/MM/YYYY
        try:
            datetime.strptime(entrada, "%d/%m/%Y")
            return entrada
        except ValueError:
            print(f"{C_RED}Erro: Por favor, insira a data no formato DD/MM/YYYY (ex: 09/06/2026).{C_RESET}")

def calcular_status_e_dias(data_proxima_str):
    """Calcula a quantidade de dias restantes e retorna uma descrição formatada (com cor)."""
    hoje = datetime.now().date()
    try:
        dt_rev = datetime.strptime(data_proxima_str, "%d/%m/%Y").date()
        delta = (dt_rev - hoje).days
        if delta == 0:
            return f"{C_YELLOW}Hoje{C_RESET}", delta
        elif delta < 0:
            return f"{C_RED}Atrasado ({abs(delta)}d){C_RESET}", delta
        else:
            return f"Em {delta} dias", delta
    except ValueError:
        return "N/A", 0

def calcular_proxima_revisao(data_base_str, acertos_pct, intervalo_dias_atual=None, revisoes_feitas=0):
    """
    Calcula a data e intervalo da próxima revisão baseando-se no desempenho.
    - Se acertos_pct for None: multiplicador é 1.0 (neutro)
    - >= 85%: multiplicador 2.0 (excelente domínio, dobra o intervalo)
    - >= 70%: multiplicador 1.5 (bom domínio, aumenta 1.5x)
    - >= 50%: multiplicador 1.0 (médio domínio, repete o intervalo)
    - < 50%: multiplicador 0.5 (baixo domínio, reduz pela metade)
    """
    if acertos_pct is None:
        multiplier = 1.0
    elif acertos_pct >= 85.0:
        multiplier = 2.0
    elif acertos_pct >= 70.0:
        multiplier = 1.5
    elif acertos_pct >= 50.0:
        multiplier = 1.0
    else:
        multiplier = 0.5

    # Determina o intervalo base antes do multiplicador
    if revisoes_feitas == 0 or intervalo_dias_atual is None:
        intervalo_anterior = 10
    else:
        intervalo_anterior = intervalo_dias_atual

    novo_intervalo = int(round(intervalo_anterior * multiplier))
    if novo_intervalo < 1:
        novo_intervalo = 1

    data_base = datetime.strptime(data_base_str, "%d/%m/%Y")
    data_proxima = data_base + timedelta(days=novo_intervalo)
    data_proxima_str = data_proxima.strftime("%d/%m/%Y")

    return data_proxima_str, novo_intervalo, intervalo_anterior

def desenhar_tabela_revisoes(lista_revisoes, titulo):
    """Exibe um cabeçalho e desenha uma tabela estilizada com as revisões fornecidas."""
    clear_screen()
    print_header(titulo)
    
    if not lista_revisoes:
        print(f"\n{C_YELLOW}⚠ Nenhuma revisão pendente ou cadastrada.{C_RESET}")
        return False
        
    w_id = 3
    w_mat = 13
    w_ass = 15
    w_data = 10
    w_pct = 5
    w_prox = 10
    w_stat = 11
    
    border_top = C_CYAN + "┌" + "─"*(w_id+2) + "┬" + "─"*(w_mat+2) + "┬" + "─"*(w_ass+2) + "┬" + "─"*(w_data+2) + "┬" + "─"*(w_pct+2) + "┬" + "─"*(w_prox+2) + "┬" + "─"*(w_stat+2) + "┐" + C_RESET
    border_mid = C_CYAN + "├" + "─"*(w_id+2) + "┼" + "─"*(w_mat+2) + "┼" + "─"*(w_ass+2) + "┼" + "─"*(w_data+2) + "┼" + "─"*(w_pct+2) + "┼" + "─"*(w_prox+2) + "┼" + "─"*(w_stat+2) + "┤" + C_RESET
    border_bot = C_CYAN + "└" + "─"*(w_id+2) + "┴" + "─"*(w_mat+2) + "┴" + "─"*(w_ass+2) + "┴" + "─"*(w_data+2) + "┴" + "─"*(w_pct+2) + "┴" + "─"*(w_prox+2) + "┴" + "─"*(w_stat+2) + "┘" + C_RESET
    
    header = (
        C_CYAN + "│" + C_RESET + f" {'ID':<{w_id}} " +
        C_CYAN + "│" + C_RESET + f" {'Matéria':<{w_mat}} " +
        C_CYAN + "│" + C_RESET + f" {'Assunto':<{w_ass}} " +
        C_CYAN + "│" + C_RESET + f" {'Últ. Est.':<{w_data}} " +
        C_CYAN + "│" + C_RESET + f" {'%':>{w_pct}} " +
        C_CYAN + "│" + C_RESET + f" {'Próx. Rev.':<{w_prox}} " +
        C_CYAN + "│" + C_RESET + f" {'Status':<{w_stat}} " +
        C_CYAN + "│"
    )
    
    print(border_top)
    print(header)
    print(border_mid)
    
    for r in lista_revisoes:
        pct_str = f"{r['acertos_pct']:.1f}%" if r['acertos_pct'] is not None else "N/A"
        status_str, _ = calcular_status_e_dias(r['data_proxima_revisao'])
        
        mat_trunc = r['materia'][:w_mat-2] + ".." if len(r['materia']) > w_mat else r['materia']
        ass_trunc = r['assunto'][:w_ass-2] + ".." if len(r['assunto']) > w_ass else r['assunto']
        
        # Corrige o padding considerando que o status_str pode conter caracteres de escape ANSI de cor
        clean_status = re.sub(r'\033\[[0-9;]*m', '', status_str)
        padding_len = w_stat - len(clean_status)
        status_exibicao = status_str + " " * max(0, padding_len)
        
        print(
            C_CYAN + "│" + C_RESET + f" {r['id']:<{w_id}} " +
            C_CYAN + "│" + C_RESET + f" {mat_trunc:<{w_mat}} " +
            C_CYAN + "│" + C_RESET + f" {ass_trunc:<{w_ass}} " +
            C_CYAN + "│" + C_RESET + f" {r['data_ultimo_estudo']:<{w_data}} " +
            C_CYAN + "│" + C_RESET + f" {pct_str:>{w_pct}} " +
            C_CYAN + "│" + C_RESET + f" {r['data_proxima_revisao']:<{w_prox}} " +
            C_CYAN + "│" + C_RESET + f" {status_exibicao} " +
            C_CYAN + "│"
        )
        
    print(border_bot)
    return True

def adicionar_revisao(dados):
    """Permite adicionar uma nova revisão vinculada a uma matéria do ciclo."""
    clear_screen()
    print_header("ADICIONAR NOVA REVISÃO ESTRATÉGICA")
    
    materias = dados.get("materias", [])
    if not materias:
        print(f"\n{C_YELLOW}⚠ Nenhuma matéria cadastrada no ciclo ainda!{C_RESET}")
        print("Cadastre matérias no menu principal primeiro.")
        input("\nPressione Enter para voltar...")
        return
        
    print("Escolha a matéria para associar a revisão:")
    for i, m in enumerate(materias, start=1):
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']}")
    print_divider()
    
    opcao = obter_input_float("Escolha o número da matéria (ou 0 para cancelar): ", min_val=0, max_val=len(materias))
    if opcao == 0:
        return
    idx = int(opcao) - 1
    materia_nome = materias[idx]['nome']
    
    print(f"\nMatéria selecionada: {C_BOLD}{materia_nome}{C_RESET}")
    assunto = obter_input_str("Nome/Descrição da aula ou assunto (ex: Aula 01 - Crase): ")
    
    data_ultimo_estudo = obter_input_data(f"Data do estudo (Pressione Enter para usar hoje: {datetime.now().strftime('%d/%m/%Y')}): ")
    
    print("\nInsira a porcentagem de acertos das questões resolvidas (0 a 100).")
    print(C_YELLOW + "(Pressione Enter para pular/deixar em branco se não resolveu questões)" + C_RESET)
    
    acertos_pct = None
    while True:
        entrada_pct = input("Porcentagem (%): ").strip()
        if not entrada_pct:
            acertos_pct = None
            break
        try:
            val = float(entrada_pct)
            if 0.0 <= val <= 100.0:
                acertos_pct = val
                break
            else:
                print(f"{C_RED}Erro: A porcentagem deve ser entre 0 e 100.{C_RESET}")
        except ValueError:
            print(f"{C_RED}Erro: Digite um número válido ou deixe em branco.{C_RESET}")
            
    # Aplica o cálculo inicial
    data_proxima, novo_intervalo, intervalo_anterior = calcular_proxima_revisao(
        data_ultimo_estudo, acertos_pct, revisoes_feitas=0
    )
    
    revisoes = dados.setdefault("revisoes", [])
    new_id = max([r["id"] for r in revisoes]) + 1 if revisoes else 1
    
    nova_rev = {
        "id": new_id,
        "materia": materia_nome,
        "assunto": assunto,
        "data_ultimo_estudo": data_ultimo_estudo,
        "acertos_pct": acertos_pct,
        "revisoes_feitas": 0,
        "data_proxima_revisao": data_proxima,
        "intervalo_dias": novo_intervalo,
        "intervalo_anterior": intervalo_anterior
    }
    revisoes.append(nova_rev)
    salvar_dados(dados)
    
    print(f"\n{C_GREEN}✔ Revisão adicionada com sucesso!{C_RESET}")
    print(f"  • Assunto: {assunto}")
    print(f"  • Próxima revisão agendada: {C_YELLOW}{data_proxima}{C_RESET} (daqui a {novo_intervalo} dias)")
    input("\nPressione Enter para continuar...")

def ver_revisoes_opcao(dados, apenas_pendentes=False):
    """Exibe a listagem de revisões."""
    revisoes = dados.get("revisoes", [])
    if apenas_pendentes:
        hoje = datetime.now().date()
        filtradas = []
        for r in revisoes:
            try:
                dt_rev = datetime.strptime(r["data_proxima_revisao"], "%d/%m/%Y").date()
                if dt_rev <= hoje:
                    filtradas.append(r)
            except ValueError:
                pass
        titulo = "REVISÕES PENDENTES (HOJE E ATRASADAS)"
    else:
        filtradas = revisoes
        titulo = "TODAS AS REVISÕES ESTRATÉGICAS"
        
    desenhar_tabela_revisoes(filtradas, titulo)
    input("\nPressione Enter para voltar...")

def editar_revisao(dados):
    """Permite alterar parâmetros de uma revisão estratégica e recalcula as datas."""
    clear_screen()
    print_header("EDITAR REVISÃO EXISTENTE")
    
    revisoes = dados.get("revisoes", [])
    if not revisoes:
        print(f"\n{C_YELLOW}⚠ Nenhuma revisão cadastrada para editar.{C_RESET}")
        input("\nPressione Enter para voltar ao menu...")
        return
        
    desenhar_tabela_revisoes(revisoes, "ESCOLHA UMA REVISÃO PARA EDITAR")
    
    print_divider()
    id_alvo = obter_input_float("Digite o ID da revisão que deseja editar (ou 0 para cancelar): ", min_val=0)
    if id_alvo == 0:
        return
        
    revisao = None
    for r in revisoes:
        if r["id"] == int(id_alvo):
            revisao = r
            break
            
    if not revisao:
        print(f"\n{C_RED}Erro: ID {int(id_alvo)} não encontrado.{C_RESET}")
        input("\nPressione Enter para voltar...")
        return
        
    clear_screen()
    print_header(f"EDITANDO REVISÃO ID #{revisao['id']}")
    print(f"{C_YELLOW}(Deixe em branco/Pressione Enter para manter o valor atual){C_RESET}\n")
    
    # 1. Matéria
    materias = dados.get("materias", [])
    print(f"Matéria atual: {C_GREEN}{revisao['materia']}{C_RESET}")
    print("Mudar matéria?")
    for i, m in enumerate(materias, start=1):
        print(f"  [{C_CYAN}{i}{C_RESET}] {m['nome']}")
    print("  [0] Manter matéria atual")
    opcao_mat = obter_input_float("Escolha a nova matéria: ", min_val=0, max_val=len(materias), default=0)
    if opcao_mat != 0:
        revisao['materia'] = materias[int(opcao_mat) - 1]['nome']
        
    # 2. Assunto
    novo_assunto = obter_input_str(f"Assunto [{revisao['assunto']}]: ", obrigatorio=False, default=revisao['assunto'])
    revisao['assunto'] = novo_assunto
    
    # 3. Data do último estudo
    nova_data = obter_input_data(f"Data do último estudo [{revisao['data_ultimo_estudo']}]: ", default_hoje=False)
    if not nova_data:
        nova_data = revisao['data_ultimo_estudo']
    revisao['data_ultimo_estudo'] = nova_data
    
    # 4. Porcentagem de acertos
    pct_atual_str = f"{revisao['acertos_pct']}%" if revisao['acertos_pct'] is not None else "N/A"
    print(f"Porcentagem de acertos atual: {C_GREEN}{pct_atual_str}{C_RESET}")
    print(C_YELLOW + "(Digite um valor entre 0 e 100, ou pressione Enter para manter)" + C_RESET)
    print(C_YELLOW + "(Para remover a nota e deixar em branco, digite 'limpar')" + C_RESET)
    
    while True:
        entrada_pct = input(f"Nova porcentagem: ").strip()
        if not entrada_pct:
            break
        elif entrada_pct.lower() == 'limpar':
            revisao['acertos_pct'] = None
            break
        try:
            val = float(entrada_pct)
            if 0.0 <= val <= 100.0:
                revisao['acertos_pct'] = val
                break
            else:
                print(f"{C_RED}Erro: A porcentagem deve ser entre 0 e 100.{C_RESET}")
        except ValueError:
            print(f"{C_RED}Erro: Digite um número válido, 'limpar' ou deixe em branco.{C_RESET}")
            
    # Recalcula a data de revisão futura baseando-se no intervalo_anterior e nos novos parâmetros
    data_proxima, novo_intervalo, _ = calcular_proxima_revisao(
        revisao['data_ultimo_estudo'],
        revisao['acertos_pct'],
        intervalo_dias_atual=revisao.get('intervalo_anterior', 10),
        revisoes_feitas=revisao['revisoes_feitas']
    )
    revisao['data_proxima_revisao'] = data_proxima
    revisao['intervalo_dias'] = novo_intervalo
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Revisão editada com sucesso!{C_RESET}")
    print(f"  • Próxima revisão agendada: {C_YELLOW}{data_proxima}{C_RESET} (daqui a {novo_intervalo} dias)")
    input("\nPressione Enter para continuar...")

def remover_revisao(dados):
    """Permite deletar uma revisão estratégica."""
    clear_screen()
    print_header("REMOVER REVISÃO ESTRATÉGICA")
    
    revisoes = dados.get("revisoes", [])
    if not revisoes:
        print(f"\n{C_YELLOW}⚠ Nenhuma revisão cadastrada para remover.{C_RESET}")
        input("\nPressione Enter para voltar ao menu...")
        return
        
    desenhar_tabela_revisoes(revisoes, "ESCOLHA UMA REVISÃO PARA REMOVER")
    
    print_divider()
    id_alvo = obter_input_float("Digite o ID da revisão que deseja remover (ou 0 para cancelar): ", min_val=0)
    if id_alvo == 0:
        return
        
    idx_alvo = -1
    for i, r in enumerate(revisoes):
        if r["id"] == int(id_alvo):
            idx_alvo = i
            break
            
    if idx_alvo == -1:
        print(f"\n{C_RED}Erro: ID {int(id_alvo)} não encontrado.{C_RESET}")
        input("\nPressione Enter para voltar...")
        return
        
    materia_nome = revisoes[idx_alvo]['materia']
    assunto_nome = revisoes[idx_alvo]['assunto']
    
    confirmar = obter_input_str(f"Deseja realmente remover a revisão ID #{int(id_alvo)} ({materia_nome} - {assunto_nome})? (S/N): ").upper()
    if confirmar == 'S':
        revisoes.pop(idx_alvo)
        salvar_dados(dados)
        print(f"\n{C_GREEN}✔ Revisão removida com sucesso!{C_RESET}")
    else:
        print(f"\n{C_YELLOW}Remoção cancelada.{C_RESET}")
        
    input("\nPressione Enter para continuar...")

def concluir_revisao(dados):
    """Registra a realização de uma revisão pendente ou adianta uma futura, calculando o novo espaçamento."""
    clear_screen()
    print_header("CONCLUIR REVISÃO ESTRATÉGICA")
    
    revisoes = dados.get("revisoes", [])
    if not revisoes:
        print(f"\n{C_YELLOW}⚠ Nenhuma revisão cadastrada.{C_RESET}")
        input("\nPressione Enter para voltar ao menu...")
        return
        
    # Agrupa pendentes
    hoje = datetime.now().date()
    pendentes = []
    for r in revisoes:
        try:
            dt_rev = datetime.strptime(r["data_proxima_revisao"], "%d/%m/%Y").date()
            if dt_rev <= hoje:
                pendentes.append(r)
        except ValueError:
            pass
            
    if pendentes:
        desenhar_tabela_revisoes(pendentes, "REVISÕES PENDENTES PARA HOJE")
    else:
        print(f"\n{C_GREEN}✔ Nenhuma revisão pendente para hoje!{C_RESET}")
        print("Caso queira adiantar alguma revisão, escolha pelo ID na tabela abaixo:")
        desenhar_tabela_revisoes(revisoes, "TODAS AS REVISÕES CADASTRADAS")
        
    print_divider()
    id_alvo = obter_input_float("Digite o ID da revisão concluída (ou 0 para cancelar): ", min_val=0)
    if id_alvo == 0:
        return
        
    revisao = None
    for r in revisoes:
        if r["id"] == int(id_alvo):
            revisao = r
            break
            
    if not revisao:
        print(f"\n{C_RED}Erro: ID {int(id_alvo)} não encontrado.{C_RESET}")
        input("\nPressione Enter para voltar...")
        return
        
    clear_screen()
    print_header(f"CONCLUINDO REVISÃO ID #{revisao['id']} - {revisao['materia']}")
    print(f"Assunto: {C_BOLD}{revisao['assunto']}{C_RESET}")
    print(f"Intervalo anterior: {revisao['intervalo_dias']} dias")
    print_divider()
    
    data_revisao = obter_input_data(f"Data de realização da revisão (Pressione Enter para usar hoje: {datetime.now().strftime('%d/%m/%Y')}): ")
    
    print("\nInsira a porcentagem de acertos das questões resolvidas nesta revisão (0 a 100).")
    print(C_YELLOW + "(Pressione Enter para pular/deixar em branco se não resolveu questões)" + C_RESET)
    
    acertos_pct = None
    while True:
        entrada_pct = input("Porcentagem (%): ").strip()
        if not entrada_pct:
            acertos_pct = None
            break
        try:
            val = float(entrada_pct)
            if 0.0 <= val <= 100.0:
                acertos_pct = val
                break
            else:
                print(f"{C_RED}Erro: A porcentagem deve ser entre 0 e 100.{C_RESET}")
        except ValueError:
            print(f"{C_RED}Erro: Digite um número válido ou deixe em branco.{C_RESET}")
            
    intervalo_atual = revisao['intervalo_dias']
    revisoes_feitas_nova = revisao['revisoes_feitas'] + 1
    
    # Aplica o espaçamento usando o intervalo_dias atual da revisão como base para a próxima!
    data_proxima, novo_intervalo, intervalo_anterior = calcular_proxima_revisao(
        data_revisao,
        acertos_pct,
        intervalo_dias_atual=intervalo_atual,
        revisoes_feitas=revisoes_feitas_nova
    )
    
    revisao['data_ultimo_estudo'] = data_revisao
    revisao['acertos_pct'] = acertos_pct
    revisao['revisoes_feitas'] = revisoes_feitas_nova
    revisao['data_proxima_revisao'] = data_proxima
    revisao['intervalo_dias'] = novo_intervalo
    revisao['intervalo_anterior'] = intervalo_anterior
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Revisão registrada com sucesso!{C_RESET}")
    print(f"  • Total de revisões concluídas: {revisoes_feitas_nova}")
    print(f"  • Próxima revisão agendada: {C_YELLOW}{data_proxima}{C_RESET} (daqui a {novo_intervalo} dias)")
    input("\nPressione Enter para continuar...")

def menu_revisoes(dados):
    """Submenu de controle de revisões estratégicas."""
    while True:
        clear_screen()
        print_header("REVISÕES ESTRATÉGICAS (REPETIÇÃO ESPAÇADA)")
        
        hoje = datetime.now().date()
        pendentes_qtd = 0
        for r in dados.get("revisoes", []):
            try:
                dt_rev = datetime.strptime(r["data_proxima_revisao"], "%d/%m/%Y").date()
                if dt_rev <= hoje:
                    pendentes_qtd += 1
            except ValueError:
                pass
                
        revisoes_totais = len(dados.get("revisoes", []))
        
        print(f"  {C_BOLD}Pendentes para Hoje:{C_RESET} {C_YELLOW if pendentes_qtd > 0 else C_GREEN}{pendentes_qtd}{C_RESET}   |   {C_BOLD}Total Cadastrado:{C_RESET} {C_GREEN}{revisoes_totais}{C_RESET}")
        print_divider()
        
        print(f"  [{C_CYAN}1{C_RESET}] 📋 Ver Revisões Pendentes para Hoje")
        print(f"  [{C_CYAN}2{C_RESET}] 📚 Ver Todas as Revisões Cadastradas")
        print(f"  [{C_CYAN}3{C_RESET}] ➕ Adicionar Nova Revisão")
        print(f"  [{C_CYAN}4{C_RESET}] ✏️  Editar Revisão Existente")
        print(f"  [{C_CYAN}5{C_RESET}] ❌ Remover Revisão")
        print(f"  [{C_CYAN}6{C_RESET}] ✅ Marcar Revisão como Concluída (Estudar)")
        print(f"  [{C_CYAN}0{C_RESET}] ↩️  Voltar ao Menu Principal")
        print_divider()
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            ver_revisoes_opcao(dados, apenas_pendentes=True)
        elif opcao == "2":
            ver_revisoes_opcao(dados, apenas_pendentes=False)
        elif opcao == "3":
            adicionar_revisao(dados)
        elif opcao == "4":
            editar_revisao(dados)
        elif opcao == "5":
            remover_revisao(dados)
        elif opcao == "6":
            concluir_revisao(dados)
        elif opcao == "0":
            break
        else:
            print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 6.{C_RESET}")
            input("\nPressione Enter para tentar novamente...")
