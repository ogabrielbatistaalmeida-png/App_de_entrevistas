import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# Configurações de Interface
st.set_page_config(page_title="Comitê de Ética e Mérito", page_icon="⚖️")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONFIGURAÇÃO ---
SENHA_ADMIN = "12345"  # Altere sua senha aqui

# Inicializar estados da sessão
if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []
    st.session_state.dados_pessoais = {"nome": "", "email": ""}
    st.session_state.enviado = False

# --- MOTOR DE ANÁLISE RIGOROSA ---
def realizar_analise_rigorosa(respostas):
    texto_total = " ".join(respostas).lower()
    palavras = re.findall(r'\w+', texto_total)
    total_palavras = len(palavras)
    vocabulario_unico = len(set(palavras))
    
    # 1. Pontuação de Esforço (0 a 40) - Severo: menos de 60 palavras ganha quase 0
    score_esforco = min(40, (total_palavras / 150) * 40)
    
    # 2. Complexidade (0 a 20)
    ratio_complexo = vocabulario_unico / total_palavras if total_palavras > 0 else 0
    score_complexo = ratio_complexo * 20
    
    # 3. Mapeamento de Valores Positivos (0 a 40)
    temas_positivos = {
        "Liderança": ["projeto", "voluntario", "ajudar", "impacto", "coletivo", "social", "comunidade"],
        "Resiliência": ["superar", "estudar", "esforço", "persistencia", "aprendi", "dificuldade", "foco"],
        "Inovação": ["criar", "ideia", "solução", "melhorar", "desenvolver", "pesquisa", "futuro"]
    }
    
    pontos_positivos = sum(texto_total.count(k) for k in sum(temas_positivos.values(), []))
    
    # 4. RED FLAGS (Penalidade máxima)
    red_flags = ["odeio", "rico", "riqueza", "dinheiro", "dane", "sozinho", "individual", "preguiça", "ego", "ambicioso"]
    pontos_negativos = sum(texto_total.count(rf) for rf in red_flags) * 25 # Aumentei o rigor
    
    # 5. Cálculo Final
    score_final = (score_esforco + score_complexo + (min(40, pontos_positivos * 3))) - pontos_negativos
    score_final = max(0, score_final)

    # Critério de Seleção
    if score_final < 45 or pontos_negativos >= 20 or total_palavras < 30:
        resultado = "REPROVADO"
        resumo = "DESALINHAMENTO: Respostas superficiais ou valores contrários ao programa."
    elif score_final < 70:
        resultado = "EM ANÁLISE"
        resumo = "REGULAR: Atende aos requisitos básicos, mas sem brilho ou impacto."
    else:
        resultado = "SELECIONADO"
        resumo = "ALTO POTENCIAL: Perfil sólido, articulado e alinhado aos valores."

    return "Identificado", resultado, round(score_final, 2), resumo

# --- INTERFACE ---
st.sidebar.title("Menu de Navegação")
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
                st.error("Preencha nome e e-mail corretamente.")
    
    elif 1 <= st.session_state.passo <= 5:
        perguntas = [
            "Descreva sua motivação para os estudos e sua trajetória escolar até aqui.",
            "Relate um desafio de vida e como sua resiliência foi testada.",
            "Como você descreve sua capacidade de trabalhar em grupos e servir ao próximo?",
            "De que forma prática você pretende retribuir este investimento à sua região?",
            "Por que o comitê deve confiar em sua ética e persistência para esta vaga?"
        ]
        st.subheader(f"Questão {st.session_state.passo} de 5")
        st.markdown(f"#### {perguntas[st.session_state.passo - 1]}")
        resp = st.text_area("Sua resposta:", height=180, key=f"q{st.session_state.passo}")
        
        if st.button("Próxima Pergunta"):
            # Agora não há aviso de "insuficiente". O sistema aceita qualquer coisa.
            st.session_state.respostas.append(resp if resp else "Sem resposta")
            st.session_state.passo += 1
            st.rerun()

    else:
        # SALVAMENTO COM TRAVA
        if not st.session_state.enviado:
            with st.spinner("Enviando dados ao comitê..."):
                classe, result, nota, res = realizar_analise_rigorosa(st.session_state.respostas)
                
                nova_linha = pd.DataFrame([{
                    "Nome": st.session_state.dados_pessoais["nome"],
                    "Email": st.session_state.dados_pessoais["email"],
                    "Pergunta1": st.session_state.respostas[0],
                    "Pergunta2": st.session_state.respostas[1],
                    "Pergunta3": st.session_state.respostas[2],
                    "Pergunta4": st.session_state.respostas[3],
                    "Pergunta5": st.session_state.respostas[4],
                    "Classificacao": classe,
                    "Resultado": result,
                    "Pontuacao": nota,
                    "Resumo": res
                }])
                
                try:
                    existente = conn.read(worksheet="Página1", ttl=0)
                    atualizado = pd.concat([existente, nova_linha], ignore_index=True)
                    conn.update(worksheet="Página1", data=atualizado)
                    st.session_state.enviado = True
                except Exception as e:
                    st.error(f"Erro na conexão: {e}")

        st.success("✅ Sua participação foi registrada. O comitê entrará em contato se necessário.")
        if st.button("Finalizar"):
            st.session_state.p
