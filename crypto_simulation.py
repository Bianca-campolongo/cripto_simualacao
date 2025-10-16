import streamlit as st
import matplotlib.pyplot as plt
import numpy as np # Importado para cálculos

st.set_page_config(layout="wide")
st.title('Simulação de Economia Cripto Interativa')

# ========================
# Parâmetros na sidebar (AGORA APENAS MANUAIS)
# ========================
st.sidebar.title("Parâmetros de Entrada")

# --- Dados Base (Extraídos da Imagem) ---
# MetaQ: $0.03408, Holders: 18.12K, Max/Total Supply: 1B, Circulating: 2.57M
# Usaremos 2.57M como Oferta Inicial para um cenário mais realista de circulação.
st.sidebar.subheader("Dados Base do Token")

# Novos valores padrão baseados na imagem e na sua simulação
P_inicial_manual = 0.03411
S_inicial_manual = 2_570_000.0 # Usando Circulating Supply como base inicial
buy_ext_base_manual = 715.96 # Usando Volume (24h)

# NOVO PARÂMETRO: Holders
HOLDERS = st.sidebar.number_input(
    "Total de Holders (K)",
    value=18.12, # Valor em K
    format="%.2f",
    help="Quantidade de holders do token (em milhares)."
)
NUM_HOLDERS = int(HOLDERS * 1000) # Convertendo K para número inteiro

st.sidebar.divider()
st.sidebar.subheader("Parâmetros da Simulação")

S_inicial = st.sidebar.number_input(
    "Oferta Inicial em Circulação (S)",
    value=S_inicial_manual,
    format="%.0f"
)
P_inicial = st.sidebar.number_input(
    "Preço Inicial do Token (P) em USD",
    value=P_inicial_manual,
    format="%.4f"
)
buy_ext_base = st.sidebar.number_input(
    "Pressão de Compra Externa por Dia (USD)",
    value=buy_ext_base_manual,
    format="%.2f"
)

# Outros parâmetros
S_max = st.sidebar.number_input("Oferta Máxima (Max Supply)", value=1_000_000_000.0, format="%.0f", help="A quantidade máxima de tokens que pode existir.")
L = st.sidebar.number_input("Profundidade de Liquidez (L) em USD", value=10_000.0, step=1_000.0, help="Representa o capital disponível para absorver mudanças de preço.")
dias = st.sidebar.slider("Duração da Simulação (dias)", 1, 3650, 365)

# NOVO: Input de anos para atingir a oferta máxima
years_to_max_input = st.sidebar.number_input(
    "Anos para Atingir Oferta Máxima", 
    value=10.0, min_value=0.1, step=0.5, format="%.1f", 
    help="Defina em quantos anos a oferta máxima deve ser atingida. A emissão diária será calculada com base neste valor."
)

withdrawal_rate = st.sidebar.slider("Taxa de Saque/Venda (Withdrawal Rate)", 0.0, 1.0, 0.20, help="Porcentagem de tokens emitidos que são vendidos imediatamente.")
burn_rate = st.sidebar.slider("Taxa de Queima (Burn Rate)", 0.0, 1.0, 0.30, help="Porcentagem de tokens emitidos que são queimados/removidos de circulação.")

# --- CÁLCULO DA EMISSÃO DIÁRIA ---
st.sidebar.divider()
st.sidebar.subheader("Emissão Calculada")

M_diario = 0
if burn_rate < 1.0 and years_to_max_input > 0:
    days_total = years_to_max_input * 365
    supply_a_emitir = float(S_max - S_inicial)
    
    if supply_a_emitir > 0 and days_total > 0:
        emissao_liquida_diaria = supply_a_emitir / days_total
        # A emissão bruta (M_diario) menos a queima deve ser igual à emissão líquida necessária.
        # M_diario - (M_diario * burn_rate) = emissao_liquida_diaria
        # M_diario * (1 - burn_rate) = emissao_liquida_diaria
        M_diario = emissao_liquida_diaria / (1 - burn_rate)

st.sidebar.metric("Emissão Diária de Tokens (M) Calculada", f"{M_diario:,.0f}")
if M_diario <= 0:
    st.sidebar.warning("A emissão é zero ou negativa. A oferta não crescerá.")

# ========================
# Lógica da Simulação
# ========================
S = float(S_inicial)
P = float(P_inicial)

dias_list, preco_list, oferta_list, compras_list, vendas_list, market_cap_list, holder_gain_list = [], [], [], [], [], [], []

for t in range(dias):
    M = float(M_diario)
    B = M * burn_rate
    tokens_sold = M * withdrawal_rate
    
    # Pressão de Venda (USD)
    Sell_ext = tokens_sold * P
    
    # Pressão de Compra (USD) - com leve variação
    Buy_ext = buy_ext_base * (1 + 0.1 * (0.5 - t / dias))
    
    # LÓGICA DE QUEIMA CORRIGIDA:
    # O valor dos tokens queimados (B * P) é tratado como uma força positiva no mercado.
    # Isso simula o efeito de escassez, onde a queima beneficia o preço.
    valor_queimado = B * P
    NetFlowUSD = Buy_ext - Sell_ext + valor_queimado
    
    # FÓRMULA DE VARIAÇÃO DE PREÇO
    if L > 0:
        PctChangePrice = NetFlowUSD / float(L)
        P = P * (1 + PctChangePrice)
        
    P = max(0.000001, P) # Preço não pode ser zero
    
    # ATUALIZAÇÃO DA OFERTA
    S = S + M - B
    
    # CÁLCULO DE GANHO POR HOLDER (NOVA MÉTRICA)
    # Valor total emitido (M * P) dividido pelo número de holders.
    if NUM_HOLDERS > 0:
        value_emitted = M * P
        holder_gain = value_emitted / NUM_HOLDERS
    else:
        holder_gain = 0
        
    # Armazenamento dos dados
    dias_list.append(t + 1)
    preco_list.append(P)
    oferta_list.append(S)
    compras_list.append(Buy_ext)
    vendas_list.append(Sell_ext)
    market_cap_list.append(P * S)
    holder_gain_list.append(holder_gain)

# ========================
# Visualização dos resultados
# ========================
st.header("Resultados da Simulação")

if not preco_list or not market_cap_list:
    st.warning("A simulação não produziu resultados. Verifique os parâmetros de entrada.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Preço Final do Token", value=f"${preco_list[-1]:,.4f}")
    with col2:
        st.metric(label="Oferta Final em Circulação", value=f"{oferta_list[-1]:,.0f}")
    with col3:
        st.metric(label="Market Cap Final", value=f"${market_cap_list[-1]:,.0f}")
    with col4:
        st.metric(label="Ganho Final p/ Holder (Diário)", value=f"${holder_gain_list[-1]:,.4f}")

    # GRÁFICO 1: Preço e Oferta
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.plot(dias_list, preco_list, label="Preço (USD/token)", color='blue')
    ax1.set_title("Evolução do Preço do Token")
    ax1.set_xlabel("Dias")
    ax1.set_ylabel("Preço (USD)")
    ax1.grid(True)
    ax1.legend()

    ax2.plot(dias_list, oferta_list, color="orange", label="Oferta Total (tokens)")
    ax2.set_title("Crescimento da Oferta de Tokens")
    ax2.set_xlabel("Dias")
    ax2.set_ylabel("Tokens em Circulação")
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout()
    st.pyplot(fig)
    
    # ---
    
    # GRÁFICO 2: Fluxo de Capital e Ganho por Holder
    st.header("Análise de Fluxo e Ganhos")
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(15, 6))

    # Fluxo de Capital
    ax3.plot(dias_list, compras_list, label="Pressão de Compra (USD)", color='green')
    ax3.plot(dias_list, vendas_list, label="Pressão de Venda (USD)", color='red')
    ax3.set_title("Fluxo de Capital Diário (Buy vs. Sell)")
    ax3.set_xlabel("Dias")
    ax3.set_ylabel("Valor (USD)")
    ax3.grid(True)
    ax3.legend()
    
    # Ganho por Holder (NOVO GRÁFICO)
    ax4.plot(dias_list, holder_gain_list, label="Valor Ganho p/ Holder (USD)", color='purple')
    ax4.set_title("Incentivo Diário por Holder")
    ax4.set_xlabel("Dias")
    ax4.set_ylabel("Valor Distribuído (USD)")
    ax4.grid(True)
    ax4.legend()

    plt.tight_layout()
    st.pyplot(fig2)

st.info("Ajuste os parâmetros na barra lateral à esquerda, incluindo o **Total de Holders**, para ver como o incentivo de ganho e a economia reagem.")
