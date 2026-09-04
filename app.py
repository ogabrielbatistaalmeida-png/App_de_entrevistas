import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

st.set_page_config(page_title="Comitê de Ética e Mérito", page_icon="⚖️")
conn = st.connection("gsheets", type=GSheetsConnection)

SENHA_ADMIN = "12345" 

# Inicializar estados da sessão
if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []
    st.session_state.dados_pessoais = {"nome": "", "email": ""}
    st.session_state.enviado = False # TRAVA DE SEGURANÇA

def realizar_analise_rigorosa(respostas):
    texto_total = " ".join(respostas).lower()
    palavras = re.findall(r'\w+', texto_total)
    total_palavras = len(palavras)
    vocabulario_unico = len(set(palavras))
    
    score_esforco = min(40, (total_palavras / 150) * 40)
    ratio_complexo = vocabulario_unico / total_palavras if total_palavras > 0 else 0
    score_complexo = ratio_complexo * 20
    
    temas_positivos = {
        "Liderança": ["projeto", "voluntario", "ajudar", "impacto", "coletivo", "social", "comunidade"],
        "Resiliência": ["superar", "estudar", "esforço", "persistencia", "aprendi", "dificuldade", "foco"],
        "Inovação": ["criar", "ideia", "solução", "melhorar", "desenvolver", "pesquisa", "futuro"]
    }
    
    pontos_positivos = sum(texto_total.count(k) for k in sum(temas_positivos.values(), []))
    red_flags = ["odeio", "rico", "riqueza", "dinheiro", "dane", "sozinho", "individual", "preguiça", "ego", "ambicioso"]
    pontos_negativos = sum(texto_total.count(rf) for rf in red_flags) * 20
    
    score_final = max(0, (score_esforco + score_complexo + (min(40, pontos_positivos * 3))) - pontos_negativos)

    if score_final < 40 or pontos_negativos >= 20:
        resultado = "REPROVADO"
        resumo = "DESALINHAMENTO ÉTICO: Valores incompatíveis ou falta de esforço."
    elif score_final < 70:
        resultado = "EM ANÁLISE"
        resumo = "PERFIL REGULAR: Respostas genéricas."
    else:
        resultado = "SELECIONADO"
        resumo = "ALTO POTENCIAL: Excelente alinhamento ético e técnico."

    return "Identificado", resultado, round(score_final, 2), resumo

# --- INTERFACE ---
st.sidebar.title("Navegação")
aba = st.sidebar.radio("Ir para:", ["Inscrição", "Área do Gestor"])

if aba == "Inscrição":
    st.title("🎓 Processo Seletivo de Bolsas")
    
    if st.session_state.passo == 0:
        nome = st.text_input("Nome Completo:")
        email = st.text_input("E-mail:")
        if st.button("Iniciar"):
            if nome and "@" in email:
                st.session_state.dados_pessoais.update({"nome": nome, "email": email})
                st.session_state.passo = 1
                st.session_state.enviado = False # Reseta a trava ao começar novo
                st.rerun()
    
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
        
        if st.button("Próxima"):
            if len(resp.split()) < 3:
                st.error("Resposta insuficiente.")
            else:
                st.session_state.respostas.append(resp)
                st.session_state.passo += 1
                st.rerun()

    else:
        # --- BLOCO DE SALVAMENTO COM TRAVA ---
        if not st.session_state.enviado:
            with st.spinner("Analisando e salvando..."):
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
                    # Lê a planilha, junta o novo dado e atualiza
                    existente = conn.read(worksheet="Página1", ttl=0)
                    atualizado = pd.concat([existente, nova_linha], ignore_index=True)
                    conn.update(worksheet="Página1", data=atualizado)
                    st.session_state.enviado = True # ATIVA A TRAVA
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        st.success("✅ Avaliação enviada com sucesso!")
        if st.button("Concluir e Reiniciar"):
            # Reseta tudo para o próximo
            st.session_state.passo = 0
            st.session_state.respostas = []
            st.session_state.enviado = False
            st.rerun()

else:
    st.title("🔑 Painel de Auditoria")
    senha = st.text_input("Senha Admin:", type="password")
    if senha == SENHA_ADMIN:
        df = conn.read(worksheet="Página1", ttl=0)
        if not df.empty:
            st.dataframe(df.sort_values(by="Pontuacao", ascending=False))
