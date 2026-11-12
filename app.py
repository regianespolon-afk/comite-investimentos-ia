import streamlit as st
import requests
import json
import time
import pandas as pd

st.set_page_config(
    page_title="Comitê AI de Investimentos",
    page_icon="💼",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stMetric {
        background: #131b2e;
        padding: 12px 18px;
        border-radius: 12px;
        border: 1px solid #1e293b;
    }
    .agent-card {
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 14px;
        border: 1px solid #334155;
    }
    .alpha-card { background: rgba(99, 102, 241, 0.08); border-color: rgba(99, 102, 241, 0.3); }
    .shield-card { background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.3); }
    .oracle-card { background: rgba(16, 185, 129, 0.08); border-color: rgba(16, 185, 129, 0.3); }
</style>
""", unsafe_allow_html=True)

# ----------------- FUNÇÕES DE MERCADO (BACEN) -----------------
@st.cache_data(ttl=3600)
def carregar_indicadores_bacen():
    """Busca os indicadores mais recentes do Banco Central do Brasil (SGS)."""
    dados = {"selic": 12.25, "ipca": 4.68, "cdi": 12.15}
    try:
        r = requests.get("https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json", timeout=3)
        if r.status_code == 200:
            dados["selic"] = float(r.json()[0]["valor"])
            dados["cdi"] = round(dados["selic"] - 0.10, 2)
    except Exception:
        pass
    return dados

indicadores = carregar_indicadores_bacen()

# ----------------- SIDEBAR: PERFIL DO INVESTIDOR -----------------
st.sidebar.header("🎯 Perfil do Investidor")

# Aporte a partir de R$ 10,00!
capital = st.sidebar.number_input(
    "Capital a Investir (R$)",
    min_value=10.0,
    value=100.0,
    step=10.0,
    format="%.2f",
    help="Você pode simular desde pequenos aportes (a partir de R$ 10,00) até grandes patrimônios."
)

perfil = st.sidebar.selectbox("Perfil de Risco", ["Conservador", "Moderado", "Arrojado"], index=1)
prazo = st.sidebar.selectbox("Prazo Desejado", ["Curto Prazo (< 1 ano)", "Médio Prazo (1 a 3 anos)", "Longo Prazo (> 3 anos)"], index=1)
objetivo = st.sidebar.selectbox("Objetivo Principal", [
    "Renda Passiva Mensal (Dividendos/FIIs)",
    "Crescimento e Valorização Acima da Inflação",
    "Preservação e Reserva de Liquidez"
], index=1)

st.sidebar.divider()
st.sidebar.header("⚙️ Motor de Inteligência")
modo = st.sidebar.radio("Modo de Operação", ["IAs Reais (Groq API Gratuita)", "Simulação Grátis (Instantâneo)"])

groq_api_key = ""
modelos_padrao = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]

if "modelos_disponiveis" not in st.session_state:
    st.session_state.modelos_disponiveis = modelos_padrao

modelo_escolhido = modelos_padrao[0]

# Chave padrão vinda de segredos da nuvem (se configurada)
chave_secreta = ""
try:
    if "GROQ_API_KEY" in st.secrets:
        chave_secreta = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if modo == "IAs Reais (Groq API Gratuita)":
    groq_api_key = st.sidebar.text_input(
        "Chave Groq API",
        value=chave_secreta,
        type="password",
        placeholder="gsk_..."
    ).strip()
    
    # Botão para listar e testar os modelos da conta do usuário
    col_btn_test, col_btn_list = st.sidebar.columns([1, 1])
    
    if col_btn_test.button("🔍 Testar Chave"):
        if not groq_api_key:
            st.sidebar.error("Cole sua chave no campo acima primeiro!")
        else:
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                
                # Buscar modelos reais que a conta tem acesso
                dados_modelos = client.models.list()
                modelos_chat = [
                    m.id for m in dados_modelos.data
                    if not any(skip in m.id.lower() for skip in ["whisper", "guard", "vision", "tool"])
                ]
                
                if modelos_chat:
                    st.session_state.modelos_disponiveis = modelos_chat
                    modelo_teste = modelos_chat[0]
                else:
                    modelo_teste = "llama-3.3-70b-versatile"

                # Testar uma resposta simples
                res = client.chat.completions.create(
                    messages=[{"role": "user", "content": "Diga OK."}],
                    model=modelo_teste,
                    max_tokens=10
                )
                st.sidebar.success(f"✅ Conectado com sucesso usando o modelo: {modelo_teste}")
            except Exception as e:
                st.sidebar.error(f"❌ Erro ao conectar: {str(e)}")

    modelo_escolhido = st.sidebar.selectbox(
        "Modelo Ativo da Groq",
        st.session_state.modelos_disponiveis,
        index=0,
        help="Modelos disponíveis na sua conta da Groq."
    )
    
    st.sidebar.caption("👉 Obtenha sua chave gratuita em [console.groq.com/keys](https://console.groq.com/keys)")

# ----------------- CABEÇALHO E INDICADORES -----------------
st.title("💼 Comitê AI de Investimentos")
st.caption("Arquitetura Multi-Agente de Consenso: IAs debatem e criticam teses para guiar sua decisão financeira.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Taxa Selic Meta", f"{indicadores['selic']:.2f}% a.a.")
with col2:
    st.metric("Taxa CDI Estimada", f"{indicadores['cdi']:.2f}% a.a.")
with col3:
    st.metric("IPCA Acumulado (12m)", f"{indicadores['ipca']:.2f}%")
with col4:
    juro_real = round(indicadores['selic'] - indicadores['ipca'], 2)
    st.metric("Juro Real Líquido Est.", f"+{juro_real:.2f}% a.a.")

st.divider()

# ----------------- FUNÇÃO DE CHAMADA GROQ -----------------
def chamar_groq(api_key, system_prompt, user_prompt, model):
    from groq import Groq
    client = Groq(api_key=api_key.strip())
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt + " IMPORTANTE: Conclua sempre todas as suas frases e raciocínios até o ponto final, sem deixar nada incompleto."},
            {"role": "user", "content": user_prompt}
        ],
        model=model,
        temperature=0.6,
        max_tokens=2048  # Limite ampliado para permitir textos longos e análises completas
    )
    return chat_completion.choices[0].message.content

# ----------------- ÁREA DO DEBATE -----------------
if st.button("🚀 Iniciar Debate do Comitê de IAs", type="primary", use_container_width=True):
    if modo == "IAs Reais (Groq API Gratuita)" and not groq_api_key:
        st.error("⚠️ Por favor, cole sua chave da Groq na barra lateral à esquerda ou selecione o modo 'Simulação Grátis'!")
    else:
        st.subheader("🗣️ Sala de Reunião do Comitê Virtual")
        
        macro_info = f"Cenário Macroeconômico: Selic {indicadores['selic']}% a.a., CDI {indicadores['cdi']}% a.a., IPCA {indicadores['ipca']}%. Juro real acima de 7%."
        user_info = f"Investidor: Capital de R$ {capital:,.2f}, Perfil: {perfil}, Prazo: {prazo}, Objetivo: {objetivo}. Note que para valores a partir de R$ 10 a R$ 100, mencione opções viáveis como Tesouro Direto Fracionado (~R$ 30), CDBs com aplicação mínima de R$ 1 e Fundos/FIIs acessíveis."

        try:
            with st.status(f"Convocando os analistas ({modelo_escolhido}) e iniciando rodadas de debate...", expanded=True) as status:
                # 1. Agente Alpha
                st.write("📈 **Agente Alpha:** Estruturando tese de oportunidade e retorno...")
                if modo == "IAs Reais (Groq API Gratuita)":
                    sys_alpha = "Você é o Agente Alpha, analista de investimentos arrojado. Foco em oportunidades com desconto (FIIs, Tesouro IPCA+ e Ações). Seja direto e adeque os produtos ao capital informado pelo investidor (mesmo que seja pequeno, como R$ 10 a R$ 100). Tópicos curtos."
                    prompt_alpha = f"{macro_info}\n{user_info}\nApresente sua tese de alocação de carteira."
                    tese_alpha = chamar_groq(groq_api_key, sys_alpha, prompt_alpha, modelo_escolhido)
                else:
                    time.sleep(0.8)
                    tese_alpha = f"""
                    **Tese de Oportunidade e Assimetria:**
                    - **Renda Fixa / CDBs de R$ 1 a R$ 30:** Mesmo com capital inicial de R$ {capital:,.2f}, é possível acessar CDBs com liquidez diária e Tesouro Selic fracionado rendendo 12,15% a.a.
                    - **Fundos Imobiliários de Base 10:** Fundos com cotas negociadas a cerca de R$ 10 (ex: MXRF11, VGIR11) permitem ao investidor iniciar em imóveis e receber dividendos isentos todo mês.
                    - **Títulos IPCA+:** Para horizontes mais longos, travar taxas acima de 6,5% de juro real protege o poder de compra da inflação.
                    """
                
                # 2. Agente Guardião
                st.write("🛡️ **Agente Guardião:** Auditando fragilidades, volatilidade e liquidez...")
                if modo == "IAs Reais (Groq API Gratuita)":
                    sys_shield = "Você é o Agente Guardião, auditor de risco e compliance financeiro. Critica com firmeza a proposta do Alpha. Destaque o custo de oportunidade do CDI sem risco, taxas de custódia e a necessidade de reserva de emergência antes de correr risco em bolsa."
                    prompt_shield = f"{macro_info}\n{user_info}\nTese do Alpha:\n{tese_alpha}\nAponte todos os riscos e por que devemos ser cautelosos."
                    tese_shield = chamar_groq(groq_api_key, sys_shield, prompt_shield, modelo_escolhido)
                else:
                    time.sleep(0.8)
                    tese_shield = f"""
                    **Alerta de Risco e Auditoria:**
                    - **Prioridade para Reserva de Emergência:** Para o capital de R$ {capital:,.2f}, o foco primário deve ser segurança total e liquidez imediata (D+0).
                    - **Custo de Oportunidade:** Com o CDI pagando mais de 1% ao mês sem oscilação, não há razão para o perfil **{perfil}** arriscar oscilações negativas de curto prazo na bolsa.
                    - **Sem taxa de corretagem:** Certifique-se de escolher corretoras com taxa zero para pequenas aplicações não serem corroídas por custos.
                    """

                # 3. Agente Oráculo
                st.write("⚖️ **Agente Oráculo:** Mediando convergências e sintetizando o veredito final...")
                if modo == "IAs Reais (Groq API Gratuita)":
                    sys_oracle = "Você é o Agente Oráculo, juiz do comitê. Ouviu o Alpha e o Guardião. Entregue um veredito equilibrado indicando: 1) O que aproveitou do Alpha, 2) O que acolheu do Guardião, 3) Recomendação prática percentual e em Reais para o capital informado."
                    prompt_oracle = f"{macro_info}\n{user_info}\nAlpha disse:\n{tese_alpha}\nGuardião disse:\n{tese_shield}\nEntregue o veredito final."
                    tese_oracle = chamar_groq(groq_api_key, sys_oracle, prompt_oracle, modelo_escolhido)
                else:
                    time.sleep(0.8)
                    tese_oracle = f"""
                    **Veredito e Matriz de Consenso:**
                    - O **Guardião** acerta ao enfatizar que com R$ {capital:,.2f}, a preservação do poder de compra e liquidez diária é o primeiro pilar.
                    - O **Alpha** acerta ao mostrar que hoje não existe barreira de entrada: ativos de R$ 10 já permitem diversificar com qualidade.
                    - **Ajuste Final para R$ {capital:,.2f}:** Carteira calibrada com foco em rentabilidade sem abrir mão da segurança.
                    """

                status.update(label="Debate concluído com sucesso!", state="complete", expanded=False)

            # Exibir a discussão completa com o componente nativo de Chat do Streamlit
            st.markdown("### 🗣️ Transcrição Completa das Rodadas de Debate")
            
            with st.chat_message("Alpha", avatar="📈"):
                st.markdown("**Rodada 1: Agente Alpha (Oportunidades & Retorno)**")
                st.markdown(tese_alpha)
            
            with st.chat_message("Guardião", avatar="🛡️"):
                st.markdown("**Rodada 2: Agente Guardião (Auditoria de Riscos & Liquidez)**")
                st.markdown(tese_shield)
            
            with st.chat_message("Oráculo", avatar="⚖️"):
                st.markdown("**Rodada 3: Agente Oráculo (Consenso & Veredito Final)**")
                st.markdown(tese_oracle)

            # ----------------- CALIBRAÇÃO PERCENTUAL DA CARTEIRA -----------------
            if perfil == "Conservador":
                dist = {"Renda Fixa Pós-Fixada (CDI / Selic)": 70, "Renda Fixa Inflação (IPCA+)": 20, "Fundos Imobiliários (FIIs)": 10, "Ações / ETFs": 0}
            elif perfil == "Moderado":
                dist = {"Renda Fixa Pós-Fixada (CDI / Selic)": 50, "Renda Fixa Inflação (IPCA+)": 25, "Fundos Imobiliários (FIIs)": 15, "Ações / ETFs": 10}
            else: # Arrojado
                dist = {"Renda Fixa Pós-Fixada (CDI / Selic)": 30, "Renda Fixa Inflação (IPCA+)": 25, "Fundos Imobiliários (FIIs)": 25, "Ações / ETFs": 20}

            df_alloc = pd.DataFrame([
                {"Classe": k, "Percentual (%)": v, "Valor Alocado (R$)": capital * (v / 100)}
                for k, v in dist.items() if v > 0
            ])

            st.divider()
            st.subheader(f"📊 Alocação Sugerida para R$ {capital:,.2f}")

            col_left, col_right = st.columns([1, 1])
            with col_left:
                st.bar_chart(df_alloc.set_index("Classe")["Percentual (%)"], color="#10b981")
            with col_right:
                st.dataframe(
                    df_alloc.style.format({
                        "Percentual (%)": "{:.0f}%",
                        "Valor Alocado (R$)": lambda x: f"R$ {x:,.2f}"
                    }),
                    use_container_width=True
                )

            st.info("ℹ️ **Aviso Legal (CVM):** Este software é um assistente experimental de Inteligência Artificial para estudo de cenários. Não constitui recomendação formal ou consultoria de valores mobiliários.")

        except Exception as e:
            st.error(f"❌ Ocorreu um erro na execução com a Groq: {str(e)}")
            st.warning("Dica: Clique no botão '🔍 Testar Chave' na barra lateral para verificar quais modelos estão ativos na sua conta!")
