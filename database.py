import os
import json
from datetime import datetime
from constants import *

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
