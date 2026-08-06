from datetime import datetime, timedelta
import re
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, DB_FILE
)
from utils import (
    clear_screen, print_header, print_divider,
    obter_input_float, obter_input_str,
    print_override as print, input_override as input
)
from database import salvar_dados, obter_fator
from calculo import (
    arredondar_dias, calcular_status_e_dias, calcular_proxima_revisao,
    obter_revisoes_filtradas_e_ordenadas
)

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



def desenhar_tabela_revisoes(lista_revisoes, titulo):
    """Exibe um cabeçalho e desenha uma tabela estilizada com as revisões fornecidas."""
    clear_screen()
    
    if not lista_revisoes:
        print_header(titulo)
        print(f"\n{C_YELLOW}⚠ Nenhuma revisão pendente ou cadastrada.{C_RESET}")
        return False
        
    import shutil
    cols = shutil.get_terminal_size((80, 20)).columns
    
    w_id = 3
    w_data = 10
    w_pct = 6
    w_prox = 10
    w_stat = 10 if cols < 90 else 14
    
    colunas_fixas = w_id + w_data + w_pct + w_prox + w_stat + 22
    
    max_mat = max(13, max((len(r["materia"]) for r in lista_revisoes), default=13))
    max_ass = max(15, max((len(r["assunto"]) for r in lista_revisoes), default=15))
    
    largura_ideal = colunas_fixas + max_mat + max_ass
    largura_tabela = max(70, min(largura_ideal, cols - 4))
    
    # Distribui a largura restante entre matéria e assunto
    espaco_restante = largura_tabela - colunas_fixas
    soma_max = max_mat + max_ass
    w_mat = int(espaco_restante * (max_mat / soma_max))
    w_ass = espaco_restante - w_mat
    
    # Garante tamanhos mínimos adequados
    if w_mat < 5:
        w_mat = 5
        w_ass = max(5, espaco_restante - w_mat)
        
    import utils
    utils.set_largura_atual(largura_tabela)
    try:
        print(C_CYAN + "╔" + "═" * (largura_tabela - 2) + "╗")
        print(C_CYAN + f"║{titulo.center(largura_tabela - 2)}║")
        print(C_CYAN + "╚" + "═" * (largura_tabela - 2) + "╝" + C_RESET)
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
            
            mat_exibicao = r['materia']
            if len(mat_exibicao) > w_mat:
                mat_exibicao = mat_exibicao[:w_mat - 3] + "..."
                
            ass_exibicao = r['assunto']
            if len(ass_exibicao) > w_ass:
                ass_exibicao = ass_exibicao[:w_ass - 3] + "..."
            
            # Corrige o padding considerando que o status_str pode conter caracteres de escape ANSI de cor
            clean_status = re.sub(r'\033\[[0-9;]*m', '', status_str)
            padding_len = w_stat - len(clean_status)
            status_exibicao = status_str + " " * max(0, padding_len)
            
            print(
                C_CYAN + "│" + C_RESET + f" {r['id']:<{w_id}} " +
                C_CYAN + "│" + C_RESET + f" {mat_exibicao:<{w_mat}} " +
                C_CYAN + "│" + C_RESET + f" {ass_exibicao:<{w_ass}} " +
                C_CYAN + "│" + C_RESET + f" {r['data_ultimo_estudo']:<{w_data}} " +
                C_CYAN + "│" + C_RESET + f" {pct_str:>{w_pct}} " +
                C_CYAN + "│" + C_RESET + f" {r['data_proxima_revisao']:<{w_prox}} " +
                C_CYAN + "│" + C_RESET + f" {status_exibicao} " +
                C_CYAN + "│"
            )
            
        print(border_bot)
        return True
    finally:
        utils.reset_largura_atual()

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
    data_proxima, novo_intervalo, intervalo_anterior, novo_ef, info = calcular_proxima_revisao(
        data_ultimo_estudo, acertos_pct, revisoes_feitas=0, ease_factor=2.5, historico_acertos=[]
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
        "intervalo_anterior": intervalo_anterior,
        "ease_factor": novo_ef,
        "historico_acertos": [acertos_pct] if acertos_pct is not None else [],
        "historico_intervalos": [novo_intervalo],
        "historico_datas": [data_ultimo_estudo],
        "historico_ease_factors": [novo_ef]
    }
    revisoes.append(nova_rev)
    salvar_dados(dados)
    
    print(f"\n{C_GREEN}✔ Revisão adicionada com sucesso!{C_RESET}")
    print(f"  • Assunto: {assunto}")
    print(f"\n{C_CYAN}📊 DETALHES DO CÁLCULO DE ESPAÇAMENTO INTELIGENTE:{C_RESET}")
    print(info["detalhes"])
    print(f"\n  • Próxima revisão agendada: {C_YELLOW}{data_proxima}{C_RESET} (daqui a {novo_intervalo} dias)")
    input("\nPressione Enter para continuar...")

def ver_revisoes_opcao(dados, apenas_pendentes=False):
    """Exibe a listagem de revisões."""
    revisoes = dados.get("revisoes", [])
    if apenas_pendentes:
        filtradas = obter_revisoes_filtradas_e_ordenadas(dados)
        limite_diario = dados.get("limite_revisoes_diarias", 10)
        if limite_diario > 0:
            titulo = f"REVISÕES PENDENTES DE HOJE (LIMITADO A {limite_diario})"
        else:
            titulo = "REVISÕES PENDENTES DE HOJE"
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
            
    # Recalcula a data de revisão futura baseando-se nos novos parâmetros e no histórico anterior
    revisoes_feitas = revisao.get('revisoes_feitas', 0)
    hist_acertos = revisao.get("historico_acertos", [])
    hist_intervalos = revisao.get("historico_intervalos", [])
    hist_datas = revisao.get("historico_datas", [])
    hist_efs = revisao.get("historico_ease_factors", [])
    
    if revisoes_feitas == 0:
        # Primeiro estudo
        data_proxima, novo_intervalo, intervalo_anterior, novo_ef, info = calcular_proxima_revisao(
            revisao['data_ultimo_estudo'],
            revisao['acertos_pct'],
            intervalo_dias_atual=None,
            revisoes_feitas=0,
            ease_factor=2.5,
            historico_acertos=[]
        )
        revisao['ease_factor'] = novo_ef
        revisao['historico_acertos'] = [revisao['acertos_pct']] if revisao['acertos_pct'] is not None else []
        revisao['historico_intervalos'] = [novo_intervalo]
        revisao['historico_datas'] = [revisao['data_ultimo_estudo']]
        revisao['historico_ease_factors'] = [novo_ef]
    else:
        # Já tem revisões feitas. Pegamos o estado anterior à última conclusão.
        ef_prev = hist_efs[-2] if len(hist_efs) >= 2 else 2.5
        hist_acertos_prev = hist_acertos[:-1]
        
        # O intervalo de referência é o intervalo anterior à última revisão concluída
        intervalo_ref = revisao.get('intervalo_anterior', 3)
        
        data_proxima, novo_intervalo, intervalo_anterior, novo_ef, info = calcular_proxima_revisao(
            revisao['data_ultimo_estudo'],
            revisao['acertos_pct'],
            intervalo_dias_atual=intervalo_ref,
            revisoes_feitas=revisoes_feitas,
            ease_factor=ef_prev,
            historico_acertos=hist_acertos_prev
        )
        revisao['ease_factor'] = novo_ef
        revisao['historico_acertos'] = hist_acertos_prev + [revisao['acertos_pct']]
        revisao['historico_intervalos'] = (hist_intervalos[:-1] if hist_intervalos else []) + [novo_intervalo]
        revisao['historico_datas'] = (hist_datas[:-1] if hist_datas else []) + [revisao['data_ultimo_estudo']]
        revisao['historico_ease_factors'] = (hist_efs[:-1] if hist_efs else []) + [novo_ef]

    revisao['data_proxima_revisao'] = data_proxima
    revisao['intervalo_dias'] = novo_intervalo
    revisao['intervalo_anterior'] = intervalo_anterior
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Revisão editada com sucesso!{C_RESET}")
    print(f"\n{C_CYAN}📊 DETALHES DO RECALCULO DE ESPAÇAMENTO:{C_RESET}")
    print(info["detalhes"])
    print(f"\n  • Próxima revisão agendada: {C_YELLOW}{data_proxima}{C_RESET} (daqui a {novo_intervalo} dias)")
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
    pendentes = obter_revisoes_filtradas_e_ordenadas(dados)
    limite_diario = dados.get("limite_revisoes_diarias", 10)
            
    if pendentes:
        if limite_diario > 0:
            titulo_tabela = f"REVISÕES PENDENTES PARA HOJE (LIMITADO A {limite_diario})"
        else:
            titulo_tabela = "REVISÕES PENDENTES PARA HOJE"
        desenhar_tabela_revisoes(pendentes, titulo_tabela)
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
    
    # Recupera histórico e fator de facilidade atuais
    ef = revisao.get("ease_factor", 2.5)
    hist_acertos = revisao.get("historico_acertos", [])
    hist_intervalos = revisao.get("historico_intervalos", [])
    hist_datas = revisao.get("historico_datas", [])
    hist_efs = revisao.get("historico_ease_factors", [])
    
    # Aplica o espaçamento usando o intervalo_dias atual da revisão como base para a próxima!
    data_proxima, novo_intervalo, intervalo_anterior, novo_ef, info = calcular_proxima_revisao(
        data_revisao,
        acertos_pct,
        intervalo_dias_atual=intervalo_atual,
        revisoes_feitas=revisoes_feitas_nova,
        ease_factor=ef,
        historico_acertos=hist_acertos
    )
    
    revisao['data_ultimo_estudo'] = data_revisao
    revisao['acertos_pct'] = acertos_pct
    revisao['revisoes_feitas'] = revisoes_feitas_nova
    revisao['data_proxima_revisao'] = data_proxima
    revisao['intervalo_dias'] = novo_intervalo
    revisao['intervalo_anterior'] = intervalo_anterior
    revisao['ease_factor'] = novo_ef
    
    # Atualiza históricos
    revisao['historico_acertos'] = hist_acertos + [acertos_pct]
    revisao['historico_intervalos'] = hist_intervalos + [novo_intervalo]
    revisao['historico_datas'] = hist_datas + [data_revisao]
    revisao['historico_ease_factors'] = hist_efs + [novo_ef]
    
    salvar_dados(dados)
    print(f"\n{C_GREEN}✔ Revisão registrada com sucesso!{C_RESET}")
    print(f"  • Total de revisões concluídas: {revisoes_feitas_nova}")
    print(f"\n{C_CYAN}📊 DETALHES DO CÁLCULO DE ESPAÇAMENTO INTELIGENTE:{C_RESET}")
    print(info["detalhes"])
    print(f"\n  • Próxima revisão agendada: {C_YELLOW}{data_proxima}{C_RESET} (daqui a {novo_intervalo} dias)")
    input("\nPressione Enter para continuar...")

def alterar_limite_revisoes(dados):
    """Altera o limite diário de revisões pendentes exibidas."""
    clear_screen()
    print_header("AJUSTAR LIMITE DIÁRIO DE REVISÕES")
    
    limite_atual = dados.get("limite_revisoes_diarias", 10)
    limite_str = f"{limite_atual} revisões" if limite_atual > 0 else "Sem Limite"
    print(f"Limite diário atual: {C_GREEN}{limite_str}{C_RESET}\n")
    
    print("Digite a quantidade de revisões diárias que deseja ver (limite geral).")
    print(C_YELLOW + "(Digite 0 para desativar o limite e mostrar todas as pendentes)" + C_RESET)
    
    novo_limite = obter_input_float("Novo limite diário: ", min_val=0)
    
    dados["limite_revisoes_diarias"] = int(novo_limite)
    salvar_dados(dados)
    
    if int(novo_limite) == 0:
        print(f"\n{C_GREEN}✔ Limite diário desativado (todas as pendentes serão exibidas)!{C_RESET}")
    else:
        print(f"\n{C_GREEN}✔ Limite diário de revisões atualizado para {int(novo_limite)}!{C_RESET}")
        
    input("\nPressione Enter para continuar...")

def menu_revisoes(dados):
    """Submenu de controle de revisões estratégicas."""
    while True:
        try:
            clear_screen()
            print_header("REVISÕES ESTRATÉGICAS (REPETIÇÃO ESPAÇADA)")
            
            hoje = datetime.now().date()
            pendentes_totais_qtd = 0
            for r in dados.get("revisoes", []):
                try:
                    dt_rev = datetime.strptime(r["data_proxima_revisao"], "%d/%m/%Y").date()
                    if dt_rev <= hoje:
                        pendentes_totais_qtd += 1
                except ValueError:
                    pass
                    
            revisoes_totais = len(dados.get("revisoes", []))
            
            # Obtém a lista limitada
            pendentes_limitados = obter_revisoes_filtradas_e_ordenadas(dados)
            pendentes_lim_qtd = len(pendentes_limitados)
            
            limite_diario = dados.get("limite_revisoes_diarias", 10)
            limite_str = f"{limite_diario}" if limite_diario > 0 else "Sem Limite"
            
            if limite_diario > 0 and pendentes_totais_qtd > limite_diario:
                pendentes_exibicao = f"{C_YELLOW}{pendentes_lim_qtd} (Total: {pendentes_totais_qtd}){C_RESET}"
            else:
                pendentes_exibicao = f"{C_GREEN if pendentes_lim_qtd == 0 else C_YELLOW}{pendentes_lim_qtd}{C_RESET}"
            
            print(f"  {C_BOLD}Pendentes para Hoje:{C_RESET} {pendentes_exibicao}   |   {C_BOLD}Total Cadastrado:{C_RESET} {C_GREEN}{revisoes_totais}{C_RESET}   |   {C_BOLD}Limite Diário:{C_RESET} {C_GREEN}{limite_str}{C_RESET}")
            print_divider()
            
            print(f"  [{C_CYAN}1{C_RESET}] 📋 Ver Revisões Pendentes para Hoje")
            print(f"  [{C_CYAN}2{C_RESET}] 📚 Ver Todas as Revisões Cadastradas")
            print(f"  [{C_CYAN}3{C_RESET}] ➕ Adicionar Nova Revisão")
            print(f"  [{C_CYAN}4{C_RESET}] ✏️  Editar Revisão Existente")
            print(f"  [{C_CYAN}5{C_RESET}] ❌ Remover Revisão")
            print(f"  [{C_CYAN}6{C_RESET}] ✅ Marcar Revisão como Concluída (Estudar)")
            print(f"  [{C_CYAN}7{C_RESET}] ⚙️  Ajustar Limite Diário de Revisões")
            print(f"  [{C_CYAN}0{C_RESET}] ↩️  Voltar ao Menu Principal")
            print_divider()
            
            opcao = input("Escolha uma opção: ").strip()
            
            try:
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
                elif opcao == "7":
                    alterar_limite_revisoes(dados)
                elif opcao == "0":
                    break
                else:
                    print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 7.{C_RESET}")
                    input("\nPressione Enter para tentar novamente...")
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            break
