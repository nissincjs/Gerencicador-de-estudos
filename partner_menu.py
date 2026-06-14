from datetime import datetime, date, timedelta
import supabase_client
from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, UI_WIDTH
)
from utils import (
    clear_screen, print_header, print_divider, obter_input_str, formatar_horas_minutos
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
    print(f"  {C_BOLD}Justificativas de Ausência:{C_RESET}")
    if not justificativas:
        print("    Nenhuma justificativa registrada.")
    else:
        for j in reversed(justificativas[-5:]):  # Mostra as últimas 5
            print(f"    • {C_YELLOW}{j.get('data')}{C_RESET}: {j.get('motivo')}")
            
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
            # Com parceiro vinculado
            perfil_parceiro = supabase_client.obter_perfil_por_id(parceiro_id)
            parceiro_email = perfil_parceiro["email"] if perfil_parceiro else "Parceiro"
            
            print(f"  Parceiro vinculado: {C_GREEN}{parceiro_email}{C_RESET}\n")
            print(f"  [{C_CYAN}1{C_RESET}] 📊 Acompanhar Consistência do Parceiro")
            print(f"  [{C_CYAN}2{C_RESET}] 📝 Registrar Justificativa de Ausência (Para Você)")
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
                registrar_justificativa_propria(dados)
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
