import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title('Simulação de Economia Cripto Interativa')

# ========================
# Parâmetros na sidebar
# ========================
st.sidebar.title("Parâmetros de Entrada")

# --- Dados Base ---
st.sidebar.subheader("Dados Base do Token")

# Novos valores padrão baseados na imagem e na sua simulação
P_inicial_manual = 0.03411
S_inicial_manual = 2_570_000.0
buy_ext_base_manual = 715.96

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

S_max = st.sidebar.number_input("Oferta Máxima (Max Supply)", value=1_000_000_000.0, format="%.0f", help="A quantidade máxima de tokens que pode existir.")
dias = st.sidebar.slider("Duração da Simulação (dias)", 1, 3650, 365)

# ⭐️ MUDANÇA PRINCIPAL: LIQUIDEZ DINÂMICA
# O L fixo foi removido e substituído pelo 'k'.
k_liquidez = st.sidebar.slider(
    "Razão de Liquidez (k) - % do Market Cap", 
    0.001, 0.50, 0.05, 
    format="%.3f",
    help="Define o Market Cap que a Profundidade de Liquidez (L) representa. L = Market Cap * k."
)

# Outros parâmetros
years_to_max_input = st.sidebar.number_input(
    "Anos para Atingir Oferta Máxima", 
    value=10.0, min_value=0.1, step=0.5, format="%.1f", 
    help="Defina em quantos anos a oferta máxima deve ser atingida. A emissão diária será calculada com base neste valor."
)

withdrawal_rate = st.sidebar.slider("Taxa de Saque/Venda (Withdrawal Rate)", 0.0, 1.0, 0.20, help="Porcentagem de tokens emitidos que são vendidos imediatamente.")
burn_rate = st.sidebar.slider("Taxa de Queima (Burn Rate)", 0.0, 1.0, 0.30, help="Porcentagem de tokens emitidos que são queimados/removidos de circulação.")

burn_type = st.sidebar.radio(
    "Mecanismo de Queima (Burn)",
    ('Redistribuição de Valor', 'Redução de Oferta'),
    index=0,
    help="""
    - **Redistribuição de Valor:** O valor dos tokens queimados impulsiona o preço (efeito de recompra).
    - **Redução de Oferta:** Os tokens são apenas removidos de circulação para criar escassez.
    """
)

# --- CÁLCULO DA EMISSÃO DIÁRIA ---
st.sidebar.divider()
st.sidebar.subheader("Emissão Calculada")

M_diario = 0
if years_to_max_input > 0:
    days_total = years_to_max_input * 365
    supply_a_criar = float(S_max - S_inicial)
    
    if supply_a_criar > 0 and days_total > 0:
        M_diario = supply_a_criar / days_total

st.sidebar.metric("Emissão Diária de Tokens (M) Calculada", f"{M_diario:,.0f}")
if M_diario <= 0:
    st.sidebar.warning("A emissão é zero ou negativa. A oferta não crescerá.")

# ========================
# Lógica da Simulação
# ========================
S = float(S_inicial)
P = float(P_inicial)
S_total_criado = float(S_inicial) # Variável para rastrear o total de tokens já criados.

dias_list, preco_list, oferta_list, compras_list, vendas_list, market_cap_list, holder_gain_list, liquidez_list = [], [], [], [], [], [], [], []

for t in range(dias):
    # LÓGICA DE EMISSÃO COM TETO
    # Verifica se o total de tokens criados já atingiu o máximo.
    if S_total_criado >= S_max:
        M = 0.0 # Interrompe novas emissões.
    else:
        # Garante que a emissão do dia não ultrapasse o S_max.
        M = min(float(M_diario), S_max - S_total_criado)
    
    S_total_criado += M # Atualiza o contador de tokens totais criados.

    B = M * burn_rate
    tokens_sold = M * withdrawal_rate
    
    # 1. Pressão de Venda (USD)
    Sell_ext = tokens_sold * P
    
    # 2. Pressão de Compra (USD) - com leve variação
    Buy_ext = buy_ext_base * (1 + 0.1 * (0.5 - t / dias))
    
    # 3. Lógica de Queima
    if burn_type == 'Redistribuição de Valor':
        valor_queimado = B * P
        NetFlowUSD = Buy_ext - Sell_ext + valor_queimado
    else: # 'Redução de Oferta'
        NetFlowUSD = Buy_ext - Sell_ext
    
    # 4. FÓRMULA DE VARIAÇÃO DE PREÇO (COM LIQUIDEZ DINÂMICA)
    market_cap_antigo = P * S
    
    # ⭐️ CÁLCULO DINÂMICO DE LIQUIDEZ (L)
    # L é uma porcentagem (k_liquidez) do Market Cap anterior.
    L_dinamico = market_cap_antigo * k_liquidez
    L_dinamico = max(100.0, L_dinamico) # Garante que L não seja muito baixo ou zero para evitar divisões por zero ou grandes distorções
    
    if L_dinamico > 0:
        market_cap_novo = market_cap_antigo * (1 + NetFlowUSD / L_dinamico)
    else:
        market_cap_novo = market_cap_antigo

    # 5. Atualização de Oferta e Preço
    oferta_nova = S + M - B
    
    if oferta_nova > 0:
        P = market_cap_novo / oferta_nova
    
    P = max(0.000001, P)
    S = oferta_nova
    
    # 6. Cálculo de Ganho por Holder
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
    liquidez_list.append(L_dinamico)

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
    ax2.ticklabel_format(style='plain', axis='y') # Evita notação científica no eixo Y
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout()
    st.pyplot(fig)
    
    # GRÁFICO 2: Fluxo de Capital e Profundidade de Liquidez
    st.header("Análise de Fluxo e Liquidez")
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(15, 6))

    # Fluxo de Capital
    ax3.plot(dias_list, compras_list, label="Pressão de Compra (USD)", color='green')
    ax3.plot(dias_list, vendas_list, label="Pressão de Venda (USD)", color='red')
    ax3.set_title("Fluxo de Capital Diário (Buy vs. Sell)")
    ax3.set_xlabel("Dias")
    ax3.set_ylabel("Valor (USD)")
    ax3.grid(True)
    ax3.legend()
    
    # Profundidade de Liquidez
    ax4.plot(dias_list, liquidez_list, label=f"Profundidade de Liquidez (L)", color='purple')
    ax4.set_title(f"Liquidez Dinâmica (L = MC * {k_liquidez*100:.1f}%)")
    ax4.set_xlabel("Dias")
    ax4.set_ylabel("Valor (USD)")
    ax4.ticklabel_format(style='plain', axis='y')
    ax4.grid(True)
    ax4.legend()

    plt.tight_layout()
    st.pyplot(fig2)

st.info("Ajuste a **Razão de Liquidez (k)** na barra lateral para ver como a resistência do preço à compra/venda muda à medida que o Market Cap evolui.")