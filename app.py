import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# Configurações de Interface
st.set_page_config(page_title="Comitê de Ética e Mérito", page_icon="⚖️")
conn = st.connection("gsheets", type=GSheetsConnection)

# Defina sua senha aqui
SENHA_ADMIN = "12345" 

# Inicializar estados da sessão
if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []
    st.session_state.dados_pessoais = {"nome": "", "email": ""}

# --- MOTOR DE ANÁLISE RIGOROSA (TÉCNICA E ÉTICA) ---
def realizar_analise_rigorosa(respostas):
    texto_total = " ".join(respostas).lower()
    palavras = re.findall(r'\w+', texto_total)
    total_palavras = len(palavras)
    vocabulario_unico = len(set(palavras))
    
    # 1. Pontuação de Esforço (0 a 40)
    score_esforco = min(40, (total_palavras / 150) * 40)
    
    # 2. Complexidade e Vocabulário (0 a 20)
    ratio_complexo = vocabulario_unico / total_palavras if total_palavras > 0 else 0
    score_complexo = ratio_complexo * 20
    
    # 3. Mapeamento de Valores Positivos (0 a 40)
    temas_positivos = {
        "Liderança": ["projeto", "voluntario", "ajudar", "impacto", "coletivo", "social", "comunidade"],
        "Resiliência": ["superar", "estudar", "esforço", "persistencia", "aprendi", "dificuldade", "foco"],
        "Inovação": ["criar", "ideia", "solução", "melhorar", "desenvolver", "pesquisa", "futuro"]
    }
    
    pontos_positivos = 0
    perfil_vencedor = "Não Identificado"
    maior_ponto_tema = 0
    
    for tema, keywords in temas_positivos.items():
        count = sum(texto_total.count(k) for k in keywords)
        pontos_positivos += count
        if count > maior_ponto_tema:
            maior_ponto_tema = count
            perfil_vencedor = tema

    # 4. SISTEMA DE PENALIDADES (RED FLAGS - RIGOR MÁXIMO)
    # Termos que indicam egoísmo, individualismo ou desprezo pela educação
    red_flags = ["odeio", "rico", "riqueza", "dinheiro", "dane", "sozinho", "individual", "preguiça", "ego", "ambicioso", "nada", "foda"]
    # Cada red flag retira 20 pontos da nota final
    pontos_negativos = sum(texto_total.count(rf) for rf in red_flags) * 20
    
    # 5. CÁLCULO FINAL
    score_final = (score_esforco + score_complexo + (min(40, pontos_positivos * 3))) - pontos_negativos
    score_final = max(0, score_final) # Garante que a nota não seja menor que zero

    # --- CRITÉRIOS DE CORTE ---
    if score_final < 40 or pontos_negativos >= 20:
        resultado = "REPROVADO"
        resumo = "DESALINHAMENTO ÉTICO/TÉCNICO: O candidato apresentou valores incompatíveis com o programa ou falta de esforço acadêmico."
    elif score_final < 70:
        resultado = "EM ANÁLISE"
        resumo = "PERFIL REGULAR: Possui coerência, mas as respostas são genéricas ou demonstram pouco impacto social."
    else:
        resultado = "SELECIONADO"
        resumo = f"ALTO POTENCIAL: Perfil focado em {perfil_vencedor}. Excelente articulação e alinhamento com os valores do comitê."

    return perfil_vencedor, resultado, round(score_final, 2), resumo

# --- INTERFACE ---
st.sidebar.title("Navegação")
aba = st.sidebar.radio("Ir para:", ["Inscrição", "Área do Gestor"])

if aba == "Inscrição":
    st.title("🎓 Processo Seletivo de Bolsas")
    
    if st.session_state.passo == 0:
        st.markdown("### Bem-vindo. Identifique-se para iniciar.")
        nome = st.text_input("Nome Completo:")
        email = st.text_input("E-mail:")
        if st.button("Iniciar Avaliação"):
            if nome and "@" in email:
                st.session_state.dados_pessoais.update({"nome": nome, "email": email})
                st.session_state.passo = 1
                st.rerun()
            else:
                st.error("Por favor, preencha nome e e-mail válidos.")
    
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
        resp = st.text_area("Sua resposta analítica:", height=180, key=f"q{st.session_state.passo}")
        
        if st.button("Confirmar Resposta"):
            if len(resp.split()) < 3:
                st.error("Resposta insuficiente para análise de mérito.")
            else:
                st.session_state.respostas.append(resp)
                st.session_state.passo += 1
                st.rerun()

    else:
        st.info("Processando sua análise final...")
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
            conn.update(worksheet="Página1", data=pd.concat([existente, nova_linha], ignore_index=True))
        except:
            conn.update(worksheet="Página1", data=nova_linha)

        st.success("✅ Avaliação enviada com sucesso!")
        if st.button("Concluir e Reiniciar"):
            st.session_state.passo = 0
            st.session_state.respostas = []
            st.rerun()

else:
    st.title("🔑 Painel de Auditoria")
    senha = st.text_input("Senha Admin:", type="password")
    if senha == SENHA_ADMIN:
        df = conn.read(worksheet="Página1", ttl=0)
        if not df.empty:
            df["Pontuacao"] = pd.to_numeric(df["Pontuacao"])
            st.metric("Média Geral de Qualidade", round(df['Pontuacao'].mean(), 2))
            st.dataframe(df.sort_values(by="Pontuacao", ascending=False), use_container_width=True)
        else:
            st.info("Nenhum registro encontrado na planilha.")
