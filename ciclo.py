from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, DB_FILE
)
from utils import (
    clear_screen, print_header, print_divider
)
from database import carregar_dados
from actions import (
    menu_ciclo_progresso, menu_materias, exibir_historico,
    configuracao_inicial
)
from reviews import menu_revisoes

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
        
        print(f"  [{C_CYAN}1{C_RESET}] 📅 Ciclo de Estudos & Progresso")
        print(f"  [{C_CYAN}2{C_RESET}] 📚 Gerenciar Matérias")
        print(f"  [{C_CYAN}3{C_RESET}] 🔄 Revisões Estratégicas (Repetição Espaçada)")
        print(f"  [{C_CYAN}4{C_RESET}] 📜 Históricos de Estudos (Ciclos e Sessões)")
        print(f"  [{C_CYAN}0{C_RESET}] 💾 Salvar e Sair")
        print_divider()
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            menu_ciclo_progresso(dados)
        elif opcao == "2":
            menu_materias(dados)
        elif opcao == "3":
            menu_revisoes(dados)
        elif opcao == "4":
            exibir_historico(dados)
        elif opcao == "0":
            clear_screen()
            print_header("ATÉ LOGO!")
            print(f"\n{C_GREEN}Seu ciclo de estudos foi salvo com sucesso em '{DB_FILE}'!{C_RESET}")
            print("Mantenha o foco e bons estudos! 📚🚀\n")
            break
        else:
            print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 4.{C_RESET}")
            input("\nPressione Enter para tentar novamente...")

if __name__ == "__main__":
    main()