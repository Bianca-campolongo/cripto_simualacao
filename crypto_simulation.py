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

L_inicial = st.sidebar.number_input(
    "Liquidez Inicial (USD)",
    value=100000.0,
    format="%.2f",
    help="Valor inicial da liquidez no pool."
)

S_max = st.sidebar.number_input("Oferta Máxima (Max Supply)", value=1_000_000_000.0, format="%.0f", help="A quantidade máxima de tokens que pode existir.")

# Mapeamento de opções de duração para dias
duration_options = {
    "7 Dias": 7,
    "15 Dias": 15,
    "30 Dias": 30,
    "3 Meses": 90,
    "6 Meses": 183,
    "1 Ano": 365,
    "2 Anos": 730,
    "3 Anos": 1095,
    "4 Anos": 1460,
    "5 Anos": 1825,
    "10 Anos": 3650,
    "Prazo Total (Até S_max)": -1
}
# Encontrar o índice da opção padrão "1 Ano"
default_duration_index = list(duration_options.keys()).index("1 Ano")

# Criar a caixa de seleção
seleted_duration_label = st.sidebar.selectbox(
    "Duração da Simulação",
    options=list(duration_options.keys()),
    index=default_duration_index
)

# Obter o número de dias da opção selecionada
dias = duration_options[seleted_duration_label]

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

redistribution_rate = st.sidebar.slider("Taxa de Redistribuição", 0.0, 1.0, 0.30, help="Porcentagem de tokens emitidos cujo valor é reinvestido, reduzindo a emissão futura.")
burn_rate = st.sidebar.slider("Taxa de Queima", 0.0, 1.0, 0.0, help="Porcentagem de tokens emitidos que são queimados/removidos de circulação.")

# Alerta se a soma das taxas for maior que 100%
if withdrawal_rate + redistribution_rate + burn_rate > 1.0:
    st.sidebar.warning("A soma das taxas de saque, redistribuição e queima excede 100%.")

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

# Variável de estado para a lógica de redistribuição
valor_redistribuido_anterior = 0.0

M_diario_base = M_diario # Usar a emissão calculada como base

dias_list, preco_list, oferta_list, compras_list, vendas_list, market_cap_list, holder_gain_list, liquidez_list = [], [], [], [], [], [], [], []

# Modo de simulação: duração fixa ou até o fim
if dias == -1: # Simular até atingir S_max
    t = 0
    t_max = 365 * 50 # Limite de segurança de 50 anos
    while S_total_criado < S_max:
        if t >= t_max:
            st.warning(f"Simulação interrompida após {t_max/365:.0f} anos.")
            break

        m_desconto = valor_redistribuido_anterior / P if P > 0 else 0
        m_diario_ajustado = max(0, M_diario_base - m_desconto)
        M = min(m_diario_ajustado, S_max - S_total_criado)
        if S_total_criado + M > S_max: # Correção final para não ultrapassar
            M = S_max - S_total_criado

        S_total_criado += M
        tokens_sold = M * withdrawal_rate
        tokens_to_burn = M * burn_rate
        tokens_to_redistribute = M * redistribution_rate
        Sell_ext = tokens_sold * P
        Buy_ext = buy_ext_base * (1 + 0.1 * (0.5 - t / (t+1)))
        valor_redistribuido_atual = tokens_to_redistribute * P
        valor_redistribuido_anterior = valor_redistribuido_atual
        NetFlowUSD = Buy_ext - Sell_ext + valor_redistribuido_atual
        market_cap_antigo = P * S
        if t == 0: L_dinamico = float(L_inicial)
        else: L_dinamico = market_cap_antigo * k_liquidez
        L_dinamico = max(100.0, L_dinamico)
        if L_dinamico > 0: market_cap_novo = market_cap_antigo * (1 + NetFlowUSD / L_dinamico)
        else: market_cap_novo = market_cap_antigo
        oferta_nova = S + M - tokens_to_burn
        if oferta_nova > 0: P = market_cap_novo / oferta_nova
        P = max(0.000001, P)
        S = oferta_nova
        if NUM_HOLDERS > 0: holder_gain = (M * P) / NUM_HOLDERS
        else: holder_gain = 0
        dias_list.append(t + 1); preco_list.append(P); oferta_list.append(S); compras_list.append(Buy_ext); vendas_list.append(Sell_ext); market_cap_list.append(P * S); holder_gain_list.append(holder_gain); liquidez_list.append(L_dinamico)
        t += 1
    dias = t # Atualiza o número de dias para o cálculo da projeção
else: # Simular por duração fixa
    for t in range(dias):
        m_desconto = valor_redistribuido_anterior / P if P > 0 else 0
        m_diario_ajustado = max(0, M_diario_base - m_desconto)
        if S_total_criado >= S_max: M = 0.0
        else: M = min(m_diario_ajustado, S_max - S_total_criado)
        S_total_criado += M
        tokens_sold = M * withdrawal_rate
        tokens_to_burn = M * burn_rate
        tokens_to_redistribute = M * redistribution_rate
        Sell_ext = tokens_sold * P
        Buy_ext = buy_ext_base * (1 + 0.1 * (0.5 - t / dias))
        valor_redistribuido_atual = tokens_to_redistribute * P
        valor_redistribuido_anterior = valor_redistribuido_atual
        NetFlowUSD = Buy_ext - Sell_ext + valor_redistribuido_atual
        market_cap_antigo = P * S
        if t == 0: L_dinamico = float(L_inicial)
        else: L_dinamico = market_cap_antigo * k_liquidez
        L_dinamico = max(100.0, L_dinamico)
        if L_dinamico > 0: market_cap_novo = market_cap_antigo * (1 + NetFlowUSD / L_dinamico)
        else: market_cap_novo = market_cap_antigo
        oferta_nova = S + M - tokens_to_burn
        if oferta_nova > 0: P = market_cap_novo / oferta_nova
        P = max(0.000001, P)
        S = oferta_nova
        if NUM_HOLDERS > 0: holder_gain = (M * P) / NUM_HOLDERS
        else: holder_gain = 0
        dias_list.append(t + 1); preco_list.append(P); oferta_list.append(S); compras_list.append(Buy_ext); vendas_list.append(Sell_ext); market_cap_list.append(P * S); holder_gain_list.append(holder_gain); liquidez_list.append(L_dinamico)

# --- CÁLCULO DO TEMPO PROJETADO ---
projected_total_years = 0.0
total_emitted = S_total_criado - S_inicial
if dias > 0 and total_emitted > 0:
    avg_daily_emission = total_emitted / dias
    remaining_supply = S_max - S_total_criado
    if avg_daily_emission > 0:
        projected_remaining_days = remaining_supply / avg_daily_emission
        projected_total_years = (dias + projected_remaining_days) / 365
    else:
        projected_total_years = float('inf')
else:
    projected_total_years = years_to_max_input if M_diario > 0 else float('inf')

st.sidebar.divider()
st.sidebar.metric("Tempo Projetado para Oferta Máxima (Anos)", f"{projected_total_years:.2f}")

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