import os
import json
import math
import sys
import re
from datetime import datetime

# Habilita codificação UTF-8 no stdout para evitar erros de caractere no Windows CMD/PowerShell
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Habilita suporte a cores ANSI no console do Windows se necessário
if os.name == 'nt':
    os.system('')

# Constantes de cores ANSI para um CLI moderno e bonito
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_MAGENTA = "\033[95m"
C_BLUE = "\033[94m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

DB_FILE = "ciclo_estudos.json"
UI_WIDTH = 80

def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    """Exibe um cabeçalho estilizado com bordas duplas (largura de UI_WIDTH colunas)."""
    print(C_CYAN + "╔" + "═" * (UI_WIDTH - 2) + "╗")
    print(f"║{title.center(UI_WIDTH - 2)}║")
    print("╚" + "═" * (UI_WIDTH - 2) + "╝" + C_RESET)

def print_divider():
    """Exibe uma linha divisória sólida em ciano (largura de UI_WIDTH colunas)."""
    print(C_CYAN + "─" * UI_WIDTH + C_RESET)

def mostrar_guia_dificuldade():
    """Exibe uma legenda explicativa sobre os níveis de dificuldade com base em acertos."""
    inner_width = UI_WIDTH - 2
    print(C_YELLOW + "┌" + "─" * inner_width + "┐")
    print("│" + " GUIA DE ESTIMATIVA DE DIFICULDADE (Baseado em acertos):".ljust(inner_width) + "│")
    print("│" + "   1 - Ótimo domínio (>85% de acertos em questões)".ljust(inner_width) + "│")
    print("│" + "   2 - Bom domínio (75% - 85% de acertos)".ljust(inner_width) + "│")
    print("│" + "   3 - Domínio médio (60% - 75% de acertos)".ljust(inner_width) + "│")
    print("│" + "   4 - Baixo rendimento (45% - 60% de acertos)".ljust(inner_width) + "│")
    print("│" + "   5 - Sem base ou assunto novo (<45% de acertos)".ljust(inner_width) + "│")
    print("└" + "─" * inner_width + "┘" + C_RESET)

def carregar_dados():
    """Carrega os dados salvos do ciclo de estudos e realiza migrações de dados se necessário."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if "horas_semanais" not in dados:
                    dados["horas_semanais"] = 0.0
                if "materias" not in dados:
                    dados["materias"] = []
                if "data_inicio_ciclo" not in dados:
                    dados["data_inicio_ciclo"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                if "progresso_atual" not in dados:
                    dados["progresso_atual"] = {}
                if "historico_ciclos" not in dados:
                    dados["historico_ciclos"] = []
                
                # Migração de dados do formato antigo para o formato estratégico (sem aulas)
                migrou = False
                for m in dados["materias"]:
                    if "aulas" in m:
                        del m["aulas"]
                        migrou = True
                    if "questoes_prova" not in m:
                        m["questoes_prova"] = 10.0
                        migrou = True
                    if "peso_questao" not in m:
                        m["peso_questao"] = m.get("peso", 1.0)
                        migrou = True
                    if "peso" in m:
                        del m["peso"]
                        migrou = True
                
                if migrou:
                    salvar_dados(dados)
                    
                return dados
        except Exception as e:
            print(f"{C_RED}Erro ao ler o arquivo {DB_FILE}: {e}{C_RESET}")
            input("Pressione Enter para iniciar com um ciclo vazio...")
            
    return {
        "horas_semanais": 0.0,
        "data_inicio_ciclo": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "materias": [],
        "progresso_atual": {},
        "historico_ciclos": []
    }

def salvar_dados(dados):
    """Salva os dados do ciclo de estudos em formato JSON."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"{C_RED}Erro ao salvar os dados em {DB_FILE}: {e}{C_RESET}")
        input("Pressione Enter para continuar...")

def obter_input_float(prompt, min_val=None, max_val=None, default=None):
    """Lê e valida uma entrada decimal."""
    while True:
        try:
            entrada = input(prompt).strip()
            if not entrada and default is not None:
                return default
            val = float(entrada)
            if min_val is not None and val < min_val:
                print(f"{C_RED}Erro: O valor deve ser no mínimo {min_val}.{C_RESET}")
                continue
            if max_val is not None and val > max_val:
                print(f"{C_RED}Erro: O valor não deve ultrapassar {max_val}.{C_RESET}")
                continue
            return val
        except ValueError:
            print(f"{C_RED}Erro: Por favor, insira um número válido.{C_RESET}")

def obter_input_str(prompt, obrigatorio=True, default=None):
    """Lê e valida uma entrada de texto."""
    while True:
        entrada = input(prompt).strip()
        if not entrada:
            if default is not None:
                return default
            if not obrigatorio:
                return ""
            print(f"{C_RED}Erro: Este campo não pode ficar vazio.{C_RESET}")
            continue
        return entrada

def parse_tempo_input(entrada):
    """Interpreta formatos de tempo flexíveis como '1.5', '1:30', '90m' ou '90min'."""
    entrada = entrada.strip().lower()
    if not entrada:
        raise ValueError("Entrada vazia")
        
    # 1. Formato H:MM (ex: 1:30, 0:45)
    if ":" in entrada:
        partes = entrada.split(":")
        if len(partes) == 2:
            h = float(partes[0])
            m = float(partes[1])
            if m < 0 or m >= 60 or h < 0:
                raise ValueError("Minutos devem estar entre 0 e 59.")
            return h + m / 60.0
            
    # 2. Formato com h e m (ex: 1h30m, 1h 30min, 45m)
    if 'h' in entrada or 'm' in entrada:
        horas = 0.0
        minutos = 0.0
        
        match_h = re.search(r'(\d+(?:\.\d+)?)\s*h', entrada)
        if match_h:
            horas = float(match_h.group(1))
            
        match_m = re.search(r'(\d+(?:\.\d+)?)\s*m', entrada)
        if match_m:
            minutos = float(match_m.group(1))
            
        if 'h' not in entrada and 'm' in entrada:
            # Caso o usuário digite apenas minutos (ex: 45m ou 45min)
            match_so_m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:m|min)', entrada)
            if match_so_m:
                return float(match_so_m.group(1)) / 60.0
                
        return horas + minutos / 60.0
        
    # 3. Decimal simples (ex: 1.5)
    return float(entrada)

def formatar_horas_minutos(horas_decimais):
    """Converte horas decimais em formato legível como 'Xh YYmin'."""
    if horas_decimais <= 0:
        return "0h 00min"
    horas = int(horas_decimais)
    minutos = round((horas_decimais - horas) * 60)
    if minutos == 60:
        horas += 1
        minutos = 0
    return f"{horas}h {minutos:02d}min"

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
    w_meta = 9
    w_estudado = 9
    w_restante = 9
    
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
    print(f"  {C_BOLD}Total de Horas do Ciclo:{C_RESET} {C_GREEN}{horas_totais}h{C_RESET}")
    
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
        if restante_horas <= 0.016:  # Limiar de 1 minuto de margem
            restante_formatada = "Concluído"
        else:
            restante_formatada = formatar_horas_minutos(restante_horas)
        
        # Como w_materia agora é dinâmica para caber a matéria mais longa, não truncamos a menos que passe de w_materia
        if len(mc["nome"]) > w_materia:
            nome_trunc = mc["nome"][:w_materia - 2] + ".."
        else:
            nome_trunc = mc["nome"]
        
        restante_exibicao = f"{C_GREEN}{restante_formatada:>{w_restante}}{C_RESET}" if restante_formatada == "Concluído" else f"{restante_formatada:>{w_restante}}"
        
        print(
            C_CYAN + "│" + C_RESET + f" {nome_trunc:<{w_materia}} " +
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
    print(f"\n{C_BOLD}Progresso Geral do Ciclo:{C_RESET} {C_GREEN}{total_estudado:.1f}h / {horas_totais}h ({pct_concluido:.1f}% concluído){C_RESET}")
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
    
    # Se mudar o nome da matéria, também precisamos ajustar o progresso_atual
    velho_nome = materia['nome']
    if novo_nome != velho_nome and velho_nome in dados.get("progresso_atual", {}):
        dados["progresso_atual"][novo_nome] = dados["progresso_atual"].pop(velho_nome)

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
        # Se restarem mais de 1 minuto (0.016 horas)
        if meta - estudado > 0.016:
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
        print(C_GREEN + "╔" + "═" * (UI_WIDTH - 2) + "╗")
        print("║" + "🎉 PARABÉNS! VOCÊ CONCLUIU SEU CICLO DE ESTUDOS! 🎉".center(UI_WIDTH - 2) + "║")
        print("╚" + "═" * (UI_WIDTH - 2) + "╝" + C_RESET)
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
    print(f"Formatos aceitos: {C_YELLOW}1.5{C_RESET} (1h30min), {C_YELLOW}1:30{C_RESET} (1h30min), {C_YELLOW}45m{C_RESET} (45 minutos)")
    
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
    print(f"Formatos aceitos: {C_YELLOW}1.5{C_RESET} (1h30min), {C_YELLOW}1:30{C_RESET} (1h30min), {C_YELLOW}45m{C_RESET} (45 minutos)")
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
    salvar_dados(dados)
    
    tempo_novo_formatado = formatar_horas_minutos(novas_horas)
    print(f"\n{C_GREEN}✔ Progresso de '{materia_nome}' ajustado com sucesso para {tempo_novo_formatado}!{C_RESET}")
    
    # --- Verificação de Conclusão do Ciclo ---
    verificar_conclusao_ciclo(dados)
    input("\nPressione Enter para continuar...")

def exibir_historico(dados):
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
        
    input("Pressione Enter para voltar ao menu...")

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

def main():
    dados = carregar_dados()
    
    # Se for o primeiro acesso (sem horas configuradas e sem matérias)
    if dados["horas_semanais"] == 0.0 and not dados["materias"]:
        configuracao_inicial(dados)
        
    while True:
        clear_screen()
        print_header("MENU PRINCIPAL - CICLO DE ESTUDOS ESTRATÉGICO")
        
        horas = dados.get("horas_semanais", 0.0)
        num_materias = len(dados.get("materias", []))
        total_estudado = sum(dados.get("progresso_atual", {}).values())
        
        print(f"  {C_BOLD}Carga Semanal:{C_RESET} {C_GREEN}{horas}h{C_RESET}   |   {C_BOLD}Estudado:{C_RESET} {C_GREEN}{total_estudado:.1f}h{C_RESET}   |   {C_BOLD}Matérias:{C_RESET} {C_GREEN}{num_materias}{C_RESET}")
        print_divider()
        
        print(f"  [{C_CYAN}1{C_RESET}] 📅 Ver Ciclo de Estudos Atual")
        print(f"  [{C_CYAN}2{C_RESET}] ➕ Adicionar Nova Matéria")
        print(f"  [{C_CYAN}3{C_RESET}] ✏️  Editar Matéria Existente")
        print(f"  [{C_CYAN}4{C_RESET}] ❌ Remover Matéria")
        print(f"  [{C_CYAN}5{C_RESET}] ⏱️  Alterar Horas Semanais")
        print(f"  [{C_CYAN}6{C_RESET}] 📝 Registrar Progresso de Estudos")
        print(f"  [{C_CYAN}7{C_RESET}] ⚙️  Ajustar Progresso Acumulado")
        print(f"  [{C_CYAN}8{C_RESET}] 📜 Ver Histórico de Ciclos Completados")
        print(f"  [{C_CYAN}0{C_RESET}] 💾 Salvar e Sair")
        print_divider()
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            exibir_ciclo(dados, pausar=True)
        elif opcao == "2":
            adicionar_materia(dados)
        elif opcao == "3":
            editar_materia(dados)
        elif opcao == "4":
            remover_materia(dados)
        elif opcao == "5":
            alterar_horas(dados)
        elif opcao == "6":
            registrar_progresso(dados)
        elif opcao == "7":
            ajustar_progresso(dados)
        elif opcao == "8":
            exibir_historico(dados)
        elif opcao == "0":
            clear_screen()
            print_header("ATÉ LOGO!")
            print(f"\n{C_GREEN}Seu ciclo de estudos foi salvo com sucesso em '{DB_FILE}'!{C_RESET}")
            print("Mantenha o foco e bons estudos! 📚🚀\n")
            break
        else:
            print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 8.{C_RESET}")
            input("\nPressione Enter para tentar novamente...")

if __name__ == "__main__":
    main()