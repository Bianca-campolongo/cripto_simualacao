import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title('Simulação de Economia Cripto Interativa')

# ========================
# Parâmetros na sidebar
# ========================
st.sidebar.title("Parâmetros de Entrada")

S_inicial = st.sidebar.number_input(
    "Oferta Inicial de Tokens (S)",
    min_value=0,
    value=1_000_000,
    step=100_000,
    help="A quantidade de tokens no início da simulação."
)
P_inicial = st.sidebar.number_input(
    "Preço Inicial do Token (P) em USD",
    min_value=0.0,
    value=0.10,
    step=0.01,
    format="%.2f",
    help="O preço de cada token no início da simulação."
)
L = st.sidebar.number_input(
    "Profundidade de Liquidez (L) em USD",
    min_value=0,
    value=100_000,
    step=10_000,
    help="A quantidade de capital no pool de liquidez, que afeta a volatilidade do preço."
)
dias = st.sidebar.slider(
    "Duração da Simulação (dias)",
    min_value=1,
    max_value=365,
    value=60,
    help="Por quantos dias a simulação será executada."
)
M_diario = st.sidebar.number_input(
    "Emissão Diária de Tokens (M)",
    min_value=0,
    value=5000,
    step=500,
    help="Quantos tokens novos são criados (minted) a cada dia."
)
withdrawal_rate = st.sidebar.slider(
    "Taxa de Saque (Withdrawal Rate)",
    min_value=0.0,
    max_value=1.0,
    value=0.20,
    format="%.2f",
    help="A porcentagem das recompensas diárias que são sacadas e vendidas."
)
burn_rate = st.sidebar.slider(
    "Taxa de Queima (Burn Rate)",
    min_value=0.0,
    max_value=1.0,
    value=0.30,
    format="%.2f",
    help="A porcentagem dos tokens recém-criados que é queimada."
)
buy_ext_base = st.sidebar.number_input(
    "Compras Externas por Dia (USD)",
    min_value=0,
    value=10_000,
    step=1_000,
    help="O valor médio de compras de tokens por dia vindo de fontes externas."
)


# ========================
# Lógica da Simulação
# ========================
# Inicializa variáveis para a simulação com base nos inputs
S = float(S_inicial)
P = float(P_inicial)

# Vetores para armazenar resultados
dias_list = []
preco_list = []
oferta_list = []
compras_list = []
vendas_list = []
market_cap_list = []

for t in range(dias):
    # Tokens emitidos e queimados no dia
    M = float(M_diario)
    B = M * burn_rate
    
    # Tokens vendidos (saque)
    tokens_sold = M * withdrawal_rate
    Sell_ext = tokens_sold * P
    
    # Compras externas — pode variar levemente
    Buy_ext = float(buy_ext_base) * (1 + 0.1 * (0.5 - t / dias))
    
    # Fluxo líquido em USD
    NetFlowUSD = Buy_ext - Sell_ext
    
    # Variação do preço (sensível ao fluxo)
    if L > 0:
        PctChangePrice = NetFlowUSD / float(L)
        P = P * (1 + PctChangePrice)
    
    # !!! CORREÇÃO APLICADA AQUI !!!
    # Garante que o preço nunca fique negativo
    P = max(0, P)
    
    # Atualiza oferta total
    S = S + M - B
    
    # Salva dados
    dias_list.append(t + 1)
    preco_list.append(P)
    oferta_list.append(S)
    compras_list.append(Buy_ext)
    vendas_list.append(Sell_ext)
    market_cap_list.append(P * S)

# ========================
# Visualização dos resultados
# ========================
st.header("Resultados da Simulação")

col1, col2 = st.columns(2)

with col1:
    st.metric(label="Preço Final do Token", value=f"${preco_list[-1]:,.4f}")
with col2:
    st.metric(label="Market Cap Final", value=f"${market_cap_list[-1]:,.0f}")


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Gráfico de Preço
ax1.plot(dias_list, preco_list, label="Preço (USD/token)", color='blue')
ax1.set_title("Evolução do Preço do Token")
ax1.set_xlabel("Dias")
ax1.set_ylabel("Preço (USD)")
ax1.grid(True)
ax1.legend()

# Gráfico de Oferta
ax2.plot(dias_list, oferta_list, color="orange", label="Oferta total (tokens)")
ax2.set_title("Crescimento da Oferta de Tokens")
ax2.set_xlabel("Dias")
ax2.set_ylabel("Tokens em Circulação")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
st.pyplot(fig)

# --- GRÁFICO ADICIONAL ---
st.header("Análise de Fluxo de Capital")
fig2, ax3 = plt.subplots(figsize=(12, 5))

# Gráfico de Compras vs Vendas
ax3.plot(dias_list, compras_list, label="Pressão de Compra (USD)", color='green')
ax3.plot(dias_list, vendas_list, label="Pressão de Venda (USD)", color='red')
ax3.set_title("Fluxo de Capital Diário")
ax3.set_xlabel("Dias")
ax3.set_ylabel("Valor (USD)")
ax3.grid(True)
ax3.legend()
st.pyplot(fig2)

st.info("Ajuste os parâmetros na barra lateral à esquerda para ver como a economia reage.")