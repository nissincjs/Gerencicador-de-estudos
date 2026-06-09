from constants import (
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_MAGENTA, C_BLUE, C_BOLD, C_RESET, DB_FILE
)
from utils import (
    clear_screen, print_header, print_divider
)
from database import carregar_dados
from actions import (
    exibir_ciclo, adicionar_materia, editar_materia, remover_materia,
    alterar_horas, registrar_progresso, ajustar_progresso, exibir_historico,
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
        
        print(f"  [{C_CYAN}1{C_RESET}] 📅 Ver Ciclo de Estudos Atual")
        print(f"  [{C_CYAN}2{C_RESET}] ➕ Adicionar Nova Matéria")
        print(f"  [{C_CYAN}3{C_RESET}] ✏️  Editar Matéria Existente")
        print(f"  [{C_CYAN}4{C_RESET}] ❌ Remover Matéria")
        print(f"  [{C_CYAN}5{C_RESET}] ⏱️  Alterar Horas Semanais")
        print(f"  [{C_CYAN}6{C_RESET}] 📝 Registrar Progresso de Estudos")
        print(f"  [{C_CYAN}7{C_RESET}] ⚙️  Ajustar Progresso Acumulado")
        print(f"  [{C_CYAN}8{C_RESET}] 📜 Ver Histórico de Ciclos Completados")
        print(f"  [{C_CYAN}9{C_RESET}] 🔄 Gerenciar Revisões Estratégicas")
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
        elif opcao == "9":
            menu_revisoes(dados)
        elif opcao == "0":
            clear_screen()
            print_header("ATÉ LOGO!")
            print(f"\n{C_GREEN}Seu ciclo de estudos foi salvo com sucesso em '{DB_FILE}'!{C_RESET}")
            print("Mantenha o foco e bons estudos! 📚🚀\n")
            break
        else:
            print(f"\n{C_RED}Opção inválida! Escolha um número entre 0 e 9.{C_RESET}")
            input("\nPressione Enter para tentar novamente...")

if __name__ == "__main__":
    main()