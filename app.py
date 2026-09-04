import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# Configurações de Interface
st.set_page_config(page_title="Comitê de Ética e Mérito", page_icon="⚖️")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONFIGURAÇÃO ---
SENHA_ADMIN = "12345" 

# Inicializar estados da sessão
if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []
    st.session_state.dados_pessoais = {"nome": "", "email": ""}
    st.session_state.enviado = False

# --- MOTOR DE ANÁLISE BALANCEADA (v4.0) ---
def realizar_analise_rigorosa(respostas):
    texto_total = " ".join(respostas).lower()
    palavras = re.findall(r'\w+', texto_total)
    total_palavras = len(palavras)
    vocabulario_unico = len(set(palavras))
    
    # 1. Pontuação de Esforço (0 a 40) - Mais generoso: 100 palavras já garantem nota máxima
    score_esforco = min(40, (total_palavras / 100) * 40)
    
    # 2. Complexidade (0 a 20)
    ratio_complexo = vocabulario_unico / total_palavras if total_palavras > 0 else 0
    score_complexo = ratio_complexo * 20
    
    # 3. Mapeamento de Valores Positivos (0 a 40) - Dicionário ampliado
    temas_positivos = {
        "Liderança": ["projeto", "voluntario", "ajudar", "impacto", "coletivo", "social", "comunidade", "liderar", "grupo", "equipe", "servir", "uniao"],
        "Resiliência": ["superar", "estudar", "esforço", "persistencia", "aprendi", "dificuldade", "foco", "disciplina", "venci", "luta", "dedicação", "sonho"],
        "Inovação": ["criar", "ideia", "solução", "melhorar", "desenvolver", "pesquisa", "futuro", "tecnologia", "mudança", "evoluir", "ciência", "novo"]
    }
    
    pontos_positivos = 0
    perfil_provavel = "Geral"
    max_pontos_tema = 0
    
    for tema, keywords in temas_positivos.items():
        count = sum(texto_total.count(k) for k in keywords)
        pontos_positivos += count
        if count > max_pontos_tema:
            max_pontos_tema = count
            perfil_provavel = tema
    
    # 4. RED FLAGS (Rigor mantido para o que é ruim)
    red_flags = ["odeio", "rico", "riqueza", "dinheiro", "dane", "sozinho", "individual", "preguiça", "ego", "ambicioso", "foda"]
    pontos_negativos = sum(texto_total.count(rf) for rf in red_flags) * 30
    
    # 5. Cálculo Final com Bônus de Alinhamento
    # Candidatos que escrevem sobre o bem comum ganham bônus de peso
    score_final = (score_esforco + score_complexo + (min(40, pontos_positivos * 4))) - pontos_negativos
    score_final = max(0, score_final)

    # --- CRITÉRIOS DE CORTE BALANCEADOS ---
    if score_final < 35 or pontos_negativos >= 25 or total_palavras < 25:
        resultado = "REPROVADO"
        resumo = "DESALINHAMENTO: Respostas muito superficiais ou valores contrários ao programa."
    elif score_final < 60: # Baixei o sarrafo de 70 para 60 para ser mais generoso
        resultado = "EM ANÁLISE"
        resumo = "POTENCIAL: Apresenta coerência e esforço, mas pode aprofundar mais os exemplos práticos."
    else:
        resultado = "SELECIONADO"
        resumo = f"EXCELENTE: Perfil focado em {perfil_provavel}. Demonstra alto engajamento, ética e clareza."

    return perfil_provavel, resultado, round(score_final, 2), resumo

# --- INTERFACE ---
st.sidebar.title("Navegação")
aba = st.sidebar.radio("Ir para:", ["Inscrição", "Área do Gestor"])

if aba == "Inscrição":
    st.title("🎓 Processo Seletivo de Bolsas")
    
    if st.session_state.passo == 0:
        st.markdown("### Identificação")
        nome = st.text_input("Nome Completo:")
        email = st.text_input("E-mail:")
        if st.button("Iniciar Avaliação"):
            if nome and "@" in email:
                st.session_state.dados_pessoais.update({"nome": nome, "email": email})
                st.session_state.passo = 1
                st.session_state.enviado = False
                st.rerun()
            else:
                st.error("Preencha os dados corretamente.")
    
    elif 1 <= st.session_state.passo <= 5:
        perguntas = [
            "Descreva sua motivação para os estudos e sua trajetória escolar até aqui.",
            "Relate um desafio de vida e como sua resiliência foi testada.",
            "Como você descreve sua capacidade de trabalhar em grupos e servir ao próximo?",
            "De que forma prática você pretende retribuir este investimento à sua região?",
            "Por que o comitê deve confiar em sua ética e persistência para esta vaga?"
        ]
        st.subheader(f"Questão {st.session_state.passo} de 5")
