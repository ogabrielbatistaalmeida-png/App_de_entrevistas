import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

st.set_page_config(page_title="Triagem de Alto Rigor v3.0", page_icon="⚖️")
conn = st.connection("gsheets", type=GSheetsConnection)
SENHA_ADMIN = "suasenha123"

if "passo" not in st.session_state:
    st.session_state.passo = 0
    st.session_state.respostas = []
    st.session_state.dados_pessoais = {"nome": "", "email": ""}

# --- MOTOR DE ANÁLISE ÉTICA E TÉCNICA ---
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
        "Comunidade": ["projeto", "voluntario", "ajudar", "impacto", "coletivo", "social", "região", "compartilhar"],
        "Resiliência": ["superar", "estudar", "esforço", "persistencia", "aprendi", "desafio", "foco", "disciplina"],
        "Inovação": ["criar", "ideia", "solução", "melhorar", "desenvolver", "pesquisa", "futuro", "ciência"]
    }
    
    pontos_positivos = 0
    perfil_provavel = "Não Identificado"
    maior_ponto_tema = 0
    
    for tema, keywords in temas_positivos.items():
        count = sum(texto_total.count(k) for k in keywords)
        pontos_positivos += count
        if count > maior_ponto_tema:
            maior_ponto_tema = count
            perfil_provavel = tema

    # 4. SISTEMA DE PENALIDADES (RED FLAGS)
    # Palavras que indicam comportamento antissocial ou falta de ética
    red_flags = ["odeio", "sozinho", "individual", "rico", "riqueza", "dinheiro", "dane", "foda", "preguiça", "nada", "nenhum", "ego", "ambicioso"]
    pontos_negativos = sum(texto_total.count(rf) for rf in red_flags) * 15 # Penalidade pesada por termo
    
    # 5. CÁLCULO FINAL
    # A nota máxima é 100, mas as penalidades podem levar a nota para baixo de zero
    score_final = score_esforco + score_complexo + (min(40, pontos_positivos * 3)) - pontos_negativos
    
    # --- CRITÉRIOS DE CORTE RIGOROSOS ---
    if score_final < 40 or pontos_negativos > 20:
        resultado = "REPROVADO"
        resumo = "DESALINHAMENTO ÉTICO: O candidato expressou valores contrários aos princípios de coletividade e dedicação acadêmica do programa."
    elif score_final < 70:
        resultado = "EM ANÁLISE"
        resumo = "PERFIL MEDIANO: Respostas coerentes, mas com pouco aprofundamento ou evidências de impacto real."
    else:
        resultado = "SELECIONADO"
        resumo = f"ALTO POTENCIAL: Demonstrado em {perfil_provavel}. Excelente articulação, vocabulário e alinhamento com o bem comum."

    return perfil_provavel, resultado, round(max(0, score_final), 2), resumo

# --- INTERFACE ---
st.sidebar.title("Comitê de Avaliação")
aba = st.sidebar.radio("Navegação", ["Inscrição", "Área do Gestor"])

if aba == "Inscrição":
    st.title("🎓 Processo Seletivo de Bolsas")
    
    if st.session_state.passo == 0:
        st.info("Bem-vindo. Esta entrevista avaliará seu mérito acadêmico e compromisso social.")
        nome = st.text_input("Nome Completo:")
        email = st.text_input("E-mail:")
        if st.button("Iniciar"):
            if nome and "@" in email:
                st.session_state.dados_pessoais.update({"nome": nome, "email": email})
                st.session_state.passo = 1
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
        resp = st.text_area("Sua resposta analítica:", height=180, key=f"q{st.session_state.passo}")
        
        if st.button("Próxima"):
            if len(resp.split()) < 3:
                st.error("Resposta insuficiente para avaliação de mérito.")
            else:
                st.session_state.respostas.append(resp)
                st.session_state.passo += 1
                st.rerun()

    else:
        st.warning("Finalizando análise técnica e ética...")
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

        st.success("Dados enviados ao comitê.")
        if st.button("Co
