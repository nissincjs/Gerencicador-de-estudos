"""Módulo de lógica pura de cálculo (SM2, streak, metas, tempo, métricas).

Contém apenas funções de cálculo sem I/O, sem UI e sem dependência do Supabase,
para que possam ser testadas isoladamente. Depende somente de stdlib e constants.
"""
import re
from datetime import datetime, date, timedelta
from constants import C_YELLOW, C_RED, C_RESET

# ---------------------------------------------------------------------------
# Fator de prioridade de matérias
# ---------------------------------------------------------------------------

def obter_fator(m):
    """Calcula o fator de prioridade da matéria."""
    qp = m.get("questoes_prova", 10.0)
    pq = m.get("peso_questao", 1.0)
    dif = m.get("dificuldade", 1.0)
    return qp * pq * dif

# ---------------------------------------------------------------------------
# Tempo (parse e formatação)
# ---------------------------------------------------------------------------

def parse_tempo_input(entrada):
    """Interpreta formatos de tempo flexíveis como '1.5', '1:30', '1:30:12', '90m', '1h30m12s', etc."""
    entrada = entrada.strip().lower()
    if not entrada:
        raise ValueError("Entrada vazia")

    # 1. Formato com dois pontos (ex: 1:30:12 ou 1:30)
    if ":" in entrada:
        partes = entrada.split(":")
        if len(partes) == 3:
            h = float(partes[0])
            m = float(partes[1])
            s = float(partes[2])
            if h < 0 or m < 0 or m >= 60 or s < 0 or s >= 60:
                raise ValueError("Valores de horas/minutos/segundos inválidos.")
            return h + m / 60.0 + s / 3600.0
        elif len(partes) == 2:
            h = float(partes[0])
            m = float(partes[1])
            if h < 0 or m < 0 or m >= 60:
                raise ValueError("Minutos devem estar entre 0 e 59.")
            return h + m / 60.0

    # 2. Formato com sufixos (h, m, s)
    if any(char in entrada for char in ['h', 'm', 's']):
        horas = 0.0
        minutos = 0.0
        segundos = 0.0

        match_h = re.search(r'(\d+(?:\.\d+)?)\s*(?:h|hs|hora|horas)', entrada)
        if match_h:
            horas = float(match_h.group(1))

        match_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|min|minuto|minutos)', entrada)
        if match_m:
            minutos = float(match_m.group(1))

        match_s = re.search(r'(\d+(?:\.\d+)?)\s*(?:s|seg|segundo|segundos)', entrada)
        if match_s:
            segundos = float(match_s.group(1))

        # Validar se conseguimos extrair alguma coisa válida
        if not match_h and not match_m and not match_s:
            raise ValueError("Não foi possível extrair tempo válido do formato com sufixos.")

        return horas + minutos / 60.0 + segundos / 3600.0

    # 3. Decimal simples (ex: 1.5)
    return float(entrada)


def formatar_horas_minutos(horas_decimais):
    """Converte horas decimais em formato legível como 'Xh YYm ZZs', 'YYm ZZs' ou 'ZZs'."""
    if horas_decimais <= 0:
        return "0s"

    total_segundos = round(horas_decimais * 3600)
    if total_segundos <= 0:
        return "0s"

    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

    partes = []
    if horas > 0:
        partes.append(f"{horas}h")
    if minutos > 0:
        partes.append(f"{minutos}m")
    if segundos > 0:
        partes.append(f"{segundos}s")

    if not partes:
        return "0s"

    return " ".join(partes)


def parse_data_hora_input(entrada, default_str):
    """
    Analisa um input de data/hora flexível com base em uma data/hora de referência.
    Formatos aceitos:
      - Apenas dia (ex: "4" -> 04/Mês/Ano Hora:Minuto:Segundo)
      - Dia e mês (ex: "4/7" -> 04/07/Ano Hora:Minuto:Segundo)
      - Dia, mês e ano (ex: "4/7/26" ou "4/7/2026")
      - Apenas hora (ex: "15:30" ou "15:30:10")
      - Data e hora (ex: "4 15:30", "4/7 15:30:10")
    """
    entrada = entrada.strip()
    if not entrada:
        return default_str

    try:
        ref = datetime.strptime(default_str, "%d/%m/%Y %H:%M:%S")
    except Exception:
        ref = datetime.now()

    dia = ref.day
    mes = ref.month
    ano = ref.year
    hora = ref.hour
    minuto = ref.minute
    segundo = ref.second

    partes = entrada.split()

    def parse_data_part(dp):
        nonlocal dia, mes, ano
        dt_partes = dp.split('/')
        if len(dt_partes) == 1:
            dia = int(dt_partes[0])
        elif len(dt_partes) == 2:
            dia = int(dt_partes[0])
            mes = int(dt_partes[1])
        elif len(dt_partes) == 3:
            dia = int(dt_partes[0])
            mes = int(dt_partes[1])
            ano_str = dt_partes[2]
            if len(ano_str) == 2:
                ano = 2000 + int(ano_str)
            else:
                ano = int(ano_str)
        else:
            raise ValueError("Formato de data inválido")

    def parse_time_part(tp):
        nonlocal hora, minuto, segundo
        tm_partes = tp.split(':')
        if len(tm_partes) == 2:
            hora = int(tm_partes[0])
            minuto = int(tm_partes[1])
            segundo = 0
        elif len(tm_partes) == 3:
            hora = int(tm_partes[0])
            minuto = int(tm_partes[1])
            segundo = int(tm_partes[2])
        else:
            raise ValueError("Formato de hora inválido")

    try:
        if len(partes) == 1:
            p = partes[0]
            if ':' in p:
                parse_time_part(p)
            else:
                parse_data_part(p)
        elif len(partes) == 2:
            p1, p2 = partes[0], partes[1]
            if ':' in p1:
                parse_time_part(p1)
                parse_data_part(p2)
            else:
                parse_data_part(p1)
                parse_time_part(p2)
        else:
            raise ValueError("Muitos espaços no formato")

        # Valida a data construindo um objeto datetime
        dt = datetime(ano, mes, dia, hora, minuto, segundo)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except ValueError as e:
        raise ValueError(f"valores inválidos ({e})")

# ---------------------------------------------------------------------------
# Revisões (SM2 adaptado)
# ---------------------------------------------------------------------------

def arredondar_dias(dias):
    """Realiza arredondamento matemático padrão (0.5 ou mais arredonda para cima)."""
    return int(dias + 0.5) if dias >= 0 else int(dias - 0.5)


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


def calcular_proxima_revisao(
    data_base_str,
    acertos_pct,
    intervalo_dias_atual=None,
    revisoes_feitas=0,
    ease_factor=2.5,
    historico_acertos=None
):
    """
    Calcula de forma inteligente a data e intervalo da próxima revisão baseando-se no desempenho.
    - Se acertos_pct for None: mantém o ease_factor atual e multiplica o intervalo por ele.
    - Se acertos_pct for informado:
      - Calcula a média histórica recente para suavizar flutuações.
      - Convertemos em nota (0 a 5).
      - Ajustamos o ease_factor de forma contínua (estilo Anki/SM2).
      - Se a nota/porcentagem for baixa (< 50% acertos), trata como lapso (reinicia intervalo para 1 dia).
      - Se for alta, aumenta o espaçamento multiplicando o intervalo por ease_factor * performance_factor.
      - Analisa a tendência recente (melhora constante dá bônus, queda constante dá penalidade).
    """
    if historico_acertos is None:
        historico_acertos = []

    ef_atual = ease_factor if ease_factor is not None else 2.5

    # Determina o intervalo base antes do cálculo
    if revisoes_feitas == 0 or intervalo_dias_atual is None:
        intervalo_anterior = 3  # Padrão inicial
    else:
        intervalo_anterior = intervalo_dias_atual

    info_detalhes = []
    info_detalhes.append(f"• Fator de Facilidade Atual (Ease Factor): {ef_atual:.2f}")

    if acertos_pct is None:
        # Sem nota resolvida, apenas repete progressão básica baseada no Ease Factor
        multiplier = ef_atual
        intervalo_raw = intervalo_anterior * multiplier
        ef_novo = ef_atual
        novo_intervalo = arredondar_dias(intervalo_raw)

        info_detalhes.append("• Nenhum exercício resolvido nesta revisão. Mantendo progressão padrão.")
        info_detalhes.append(f"• Multiplicador aplicado: {ef_atual:.2f}x")
        info_detalhes.append(f"• Intervalo matemático: {intervalo_raw:.2f} dias -> Arredondado para: {novo_intervalo} dias")

        peff = None
        pavg = None
    else:
        # Filtra histórico válido (sem None)
        historico_validos = [val for val in historico_acertos if val is not None]

        # Média recente (últimas 3 revisões)
        if not historico_validos:
            pavg = acertos_pct
        else:
            ultimos_historico = historico_validos[-3:]
            pavg = sum(ultimos_historico) / len(ultimos_historico)

        # Suavização da porcentagem atual com a histórica
        peff = 0.7 * acertos_pct + 0.3 * pavg

        # Mapeamento para nota SM2 (0 a 5)
        grade = peff / 20.0

        # Ajuste contínuo do Ease Factor (SM2 adaptado)
        delta_ef = 0.15 - (5.0 - grade) * (0.08 + (5.0 - grade) * 0.02)
        ef_novo = ef_atual + delta_ef

        # Limita o Ease Factor entre 1.3 (padrão Anki) e 5.0
        if ef_novo < 1.3:
            ef_novo = 1.3
        elif ef_novo > 5.0:
            ef_novo = 5.0

        info_detalhes.append(f"• Porcentagem da revisão: {acertos_pct:.1f}%")
        if historico_validos:
            info_detalhes.append(f"• Média histórica recente: {pavg:.1f}%")
            info_detalhes.append(f"• Porcentagem efetiva suavizada: {peff:.1f}%")
        info_detalhes.append(f"• Ajuste no Ease Factor: {ef_atual:.2f} -> {ef_novo:.2f} (Variação: {delta_ef:+.2f})")

        # Verificação de lapso (esquecimento, acertos < 50%)
        if peff < 50.0:
            novo_intervalo = 1
            info_detalhes.append("• ⚠ Desempenho abaixo do esperado (< 50%). Classificado como LAPSO!")
            info_detalhes.append("• Intervalo reiniciado para 1 dia para reforço rápido.")
            intervalo_raw = 1.0
        else:
            # Caso de sucesso (pass)
            performance_factor = peff / 100.0

            if revisoes_feitas == 0:
                # Primeira revisão (intervalo inicial proporcional à nota)
                intervalo_raw = 3.0 * ef_novo * performance_factor
                info_detalhes.append(f"• Primeira revisão: intervalo inicial calculado como 3d * EF ({ef_novo:.2f}) * Rendimento ({performance_factor:.2f}) = {intervalo_raw:.2f} dias")
            else:
                intervalo_raw = intervalo_anterior * ef_novo * performance_factor
                info_detalhes.append(f"• Intervalo base: {intervalo_anterior}d * EF ({ef_novo:.2f}) * Rendimento ({performance_factor:.2f}) = {intervalo_raw:.2f} dias")

            # Análise de Tendência
            historico_com_atual = historico_validos + [acertos_pct]
            ultimos_3 = historico_com_atual[-3:]

            if len(ultimos_3) == 3:
                # Melhora contínua
                if ultimos_3[0] < ultimos_3[1] < ultimos_3[2]:
                    intervalo_raw *= 1.10
                    info_detalhes.append("• 📈 Bônus de Consistência (+10%): Desempenho em evolução contínua!")
                # Queda contínua
                elif ultimos_3[0] > ultimos_3[1] > ultimos_3[2]:
                    intervalo_raw *= 0.85
                    info_detalhes.append("• 📉 Penalidade de Declínio (-15%): Desempenho em queda contínua.")

                # Consistência em alta performance
                if all(val >= 90.0 for val in ultimos_3):
                    intervalo_raw *= 1.15
                    info_detalhes.append("• 🌟 Bônus de Alta Performance (+15%): Últimas 3 revisões com acertos >= 90%!")

            novo_intervalo = arredondar_dias(intervalo_raw)
            if novo_intervalo < 1:
                novo_intervalo = 1

            info_detalhes.append(f"• Intervalo matemático final: {intervalo_raw:.2f} dias -> Arredondado para: {novo_intervalo} dias")

    # Calcula a próxima data
    data_base = datetime.strptime(data_base_str, "%d/%m/%Y")
    data_proxima = data_base + timedelta(days=novo_intervalo)
    data_proxima_str = data_proxima.strftime("%d/%m/%Y")

    info_calculo = {
        "detalhes": "\n".join(info_detalhes),
        "ease_factor": ef_novo,
        "peff": peff,
        "pavg": pavg
    }

    return data_proxima_str, novo_intervalo, intervalo_anterior, ef_novo, info_calculo


def obter_revisoes_filtradas_e_ordenadas(dados):
    """
    Filtra as revisões pendentes para hoje, limitando o total diário e distribuindo
    de forma proporcional à importância das matérias no ciclo.
    Retorna a lista final de revisões a serem exibidas hoje.
    """
    revisoes = dados.get("revisoes", [])
    limite_diario = dados.get("limite_revisoes_diarias", 10)

    hoje = datetime.now().date()

    # 1. Filtra todas as revisões pendentes (vencidas ou hoje)
    pendentes_todas = []
    for r in revisoes:
        try:
            dt_rev = datetime.strptime(r["data_proxima_revisao"], "%d/%m/%Y").date()
            if dt_rev <= hoje:
                # Calcula atraso em dias
                atraso = (hoje - dt_rev).days
                pendentes_todas.append((r, atraso))
        except ValueError:
            pass

    if not pendentes_todas:
        return []

    # Se o limite diário for <= 0, o limite está desativado. Retorna todas ordenadas.
    if limite_diario <= 0:
        materias_dict = {m["nome"]: obter_fator(m) for m in dados.get("materias", [])}
        pendentes_todas.sort(key=lambda x: (materias_dict.get(x[0]["materia"], 0.0), x[1]), reverse=True)
        return [item[0] for item in pendentes_todas]

    # Se o total de pendentes for menor ou igual ao limite, exibe todas
    if len(pendentes_todas) <= limite_diario:
        materias_dict = {m["nome"]: obter_fator(m) for m in dados.get("materias", [])}
        pendentes_todas.sort(key=lambda x: (materias_dict.get(x[0]["materia"], 0.0), x[1]), reverse=True)
        return [item[0] for item in pendentes_todas]

    # 2. Agrupa pendentes por matéria
    pendentes_por_materia = {}
    for r, atraso in pendentes_todas:
        pendentes_por_materia.setdefault(r["materia"], []).append((r, atraso))

    # Ordena as revisões de cada matéria por atraso decrescente
    for mat in pendentes_por_materia:
        pendentes_por_materia[mat].sort(key=lambda x: x[1], reverse=True)

    # 3. Calcula fatores de relevância das matérias
    materias = dados.get("materias", [])
    fator_total = sum(obter_fator(m) for m in materias)

    # Se não houver matérias ou fator total for 0, distribui igualmente
    if fator_total == 0:
        fator_total = len(materias) if materias else 1
        materias_pesos = {m["nome"]: 1.0 / fator_total for m in materias}
    else:
        materias_pesos = {m["nome"]: obter_fator(m) / fator_total for m in materias}

    # 4. Seleção inicial por cotas
    selecionados = []
    restantes_backlog = []

    for mat, lista in pendentes_por_materia.items():
        peso = materias_pesos.get(mat, 0.0)
        cota = max(1, arredondar_dias(limite_diario * peso))

        # Seleciona até a cota
        selecionados_mat = lista[:cota]
        restantes_mat = lista[cota:]

        selecionados.extend(selecionados_mat)
        restantes_backlog.extend(restantes_mat)

    # Se a seleção de cotas estourar o limite diário (devido a arredondamentos para cima ou mínimos de 1)
    if len(selecionados) > limite_diario:
        materias_dict = {m["nome"]: obter_fator(m) for m in materias}
        selecionados.sort(key=lambda x: (materias_dict.get(x[0]["materia"], 0.0), x[1]), reverse=True)
        selecionados = selecionados[:limite_diario]
        return [item[0] for item in selecionados]

    # Se faltar espaço para atingir o limite diário, preenche com o backlog restante
    vagas_restantes = limite_diario - len(selecionados)
    if vagas_restantes > 0 and restantes_backlog:
        materias_dict = {m["nome"]: obter_fator(m) for m in materias}
        restantes_backlog.sort(key=lambda x: (materias_dict.get(x[0]["materia"], 0.0), x[1]), reverse=True)
        selecionados.extend(restantes_backlog[:vagas_restantes])

    # Ordena a lista final selecionada por relevância e depois por atraso
    materias_dict = {m["nome"]: obter_fator(m) for m in materias}
    selecionados.sort(key=lambda x: (materias_dict.get(x[0]["materia"], 0.0), x[1]), reverse=True)

    return [item[0] for item in selecionados]

# ---------------------------------------------------------------------------
# Consistência de estudos (streak e estudos por dia)
# ---------------------------------------------------------------------------

def calcular_estudos_por_dia(dados: dict) -> dict:
    """
    Processa todas as sessões cronologicamente para calcular a variação real
    de horas estudadas por dia e por matéria, considerando ajustes e reinícios de ciclo.
    Retorna um dicionário: { dia_str: { materia: delta_horas } }
    """
    sessoes = dados.get("historico_sessoes", [])
    historico_ciclos = dados.get("historico_ciclos", [])

    # Coleta e ordena os marcos de reinício de ciclo
    datas_fim_ciclos = []
    for c in historico_ciclos:
        dt_fim_str = c.get("data_fim")
        if dt_fim_str:
            try:
                datas_fim_ciclos.append(datetime.strptime(dt_fim_str, "%d/%m/%Y %H:%M:%S"))
            except Exception:
                pass
    datas_fim_ciclos.sort()

    # Ordena as sessões por data
    def obter_data_sessao(s):
        try:
            return datetime.strptime(s.get("data", ""), "%d/%m/%Y %H:%M:%S")
        except Exception:
            try:
                return datetime.strptime(s.get("data", "").split()[0], "%d/%m/%Y")
            except Exception:
                return datetime.min

    sessoes_ordenadas = sorted(sessoes, key=obter_data_sessao)

    progresso = {}  # { materia: total_acumulado }
    estudos_por_dia = {}  # { dia_str: { materia: delta_horas } }

    ciclos_processados = 0

    for s in sessoes_ordenadas:
        materia = s.get("materia")
        horas = s.get("horas", 0.0)
        tipo = s.get("tipo", "registro")
        data_completa = s.get("data", "")
        if not data_completa:
            continue

        try:
            dt_sessao = datetime.strptime(data_completa, "%d/%m/%Y %H:%M:%S")
        except Exception:
            try:
                dt_sessao = datetime.strptime(data_completa.split()[0], "%d/%m/%Y")
            except Exception:
                dt_sessao = datetime.min

        # Verifica se essa sessão cruzou a linha de fim de algum ciclo concluído
        while (ciclos_processados < len(datas_fim_ciclos) and
               dt_sessao > datas_fim_ciclos[ciclos_processados]):
            progresso = {}
            ciclos_processados += 1

        dia_str = data_completa.split()[0]
        anterior = progresso.get(materia, 0.0)

        if tipo == "registro":
            delta = horas
            progresso[materia] = anterior + horas
        elif tipo == "ajuste":
            delta = max(-anterior, horas - anterior)
            progresso[materia] = horas
        else:
            continue

        if dia_str not in estudos_por_dia:
            estudos_por_dia[dia_str] = {}

        estudos_por_dia[dia_str][materia] = estudos_por_dia[dia_str].get(materia, 0.0) + delta

    return estudos_por_dia


def calcular_streak(dados: dict) -> int:
    """Calcula a sequência de dias seguidos estudando."""
    estudos_por_dia = calcular_estudos_por_dia(dados)

    datas_estudadas = set()
    for dia_str, materias_estudo in estudos_por_dia.items():
        if sum(materias_estudo.values()) >= 0.00027:  # Mais de 1 segundo estudado
            try:
                dt = datetime.strptime(dia_str, "%d/%m/%Y").date()
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


def obter_estudos_hoje(dados: dict) -> dict:
    """Retorna informações sobre os estudos realizados no dia de hoje."""
    hoje_str = date.today().strftime("%d/%m/%Y")
    estudos_por_dia = calcular_estudos_por_dia(dados)

    materias_hoje = []
    total_horas = 0.0

    estudos_hoje = estudos_por_dia.get(hoje_str, {})
    for mat, horas in estudos_hoje.items():
        if horas >= 0.00027:  # Mais de 1 segundo estudado
            total_horas += horas
            materias_hoje.append(mat)

    return {
        "estudou": total_horas >= 0.00027,
        "total_horas": total_horas,
        "materias": materias_hoje
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
        if estudado >= meta - 0.00027:  # Margem de 1 segundo
            cumpridas += 1

    return {"cumpridas": cumpridas, "total": len(materias)}

# ---------------------------------------------------------------------------
# Métricas de acompanhamento do ciclo
# ---------------------------------------------------------------------------

def calcular_metricas_acompanhamento(dados):
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
