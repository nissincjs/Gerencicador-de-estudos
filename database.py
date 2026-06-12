import os
import json
from datetime import datetime
from constants import DB_FILE, C_RED, C_RESET

def obter_fator(m):
    """Calcula o fator de prioridade da matéria."""
    qp = m.get("questoes_prova", 10.0)
    pq = m.get("peso_questao", 1.0)
    dif = m.get("dificuldade", 1.0)
    return qp * pq * dif

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
                if "historico_sessoes" not in dados:
                    dados["historico_sessoes"] = []
                    migrou = True
                if "revisoes" not in dados:
                    dados["revisoes"] = []
                if "limite_revisoes_diarias" not in dados:
                    dados["limite_revisoes_diarias"] = 10
                    migrou = True
                
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
                
                for r in dados.get("revisoes", []):
                    if "ease_factor" not in r:
                        r["ease_factor"] = 2.5
                        migrou = True
                    if "historico_acertos" not in r:
                        r["historico_acertos"] = [r["acertos_pct"]] if r.get("acertos_pct") is not None else []
                        migrou = True
                    if "historico_intervalos" not in r:
                        r["historico_intervalos"] = [r["intervalo_dias"]] if r.get("intervalo_dias") is not None else []
                        migrou = True
                    if "historico_datas" not in r:
                        r["historico_datas"] = [r["data_ultimo_estudo"]] if r.get("data_ultimo_estudo") is not None else []
                        migrou = True
                    if "historico_ease_factors" not in r:
                        r["historico_ease_factors"] = [r.get("ease_factor", 2.5)]
                        migrou = True
                
                if migrou:
                    salvar_dados(dados)
                    
                if "materias" in dados:
                    dados["materias"].sort(key=obter_fator, reverse=True)
                return dados
        except Exception as e:
            print(f"{C_RED}Erro ao ler o arquivo {DB_FILE}: {e}{C_RESET}")
            input("Pressione Enter para iniciar com um ciclo vazio...")
            
    return {
        "horas_semanais": 0.0,
        "limite_revisoes_diarias": 10,
        "data_inicio_ciclo": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "materias": [],
        "progresso_atual": {},
        "historico_ciclos": [],
        "historico_sessoes": [],
        "revisoes": []
    }

def salvar_dados(dados):
    """Salva os dados do ciclo de estudos em formato JSON."""
    try:
        if "materias" in dados:
            dados["materias"].sort(key=obter_fator, reverse=True)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"{C_RED}Erro ao salvar os dados em {DB_FILE}: {e}{C_RESET}")
        input("Pressione Enter para continuar...")
