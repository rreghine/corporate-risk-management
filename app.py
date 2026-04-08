"""
App Streamlit — Sistema de Gestão de Riscos
Auditoria & Segurança do Trabalhos

Rafael Reghine Munhoz | MBA Data Science & Analytics — USP
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import date, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Risk Management System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).parent / "data" / "risk_management.db"

LEVEL_COLOR  = {"Baixo": "#3B9E6B", "Médio": "#E8A83E", "Alto": "#E07B39", "Crítico": "#C0392B"}
STATUS_COLOR = {"Normal": "#3B9E6B", "Atenção": "#E8A83E", "Crítico": "#C0392B"}

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def q(sql: str, params=()) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_conn(), params=params)

def kri_badge(value, warn, crit, invert=False):
    """Retorna (status, cor) de um KRI dado seus limiares."""
    if invert:  # menor = melhor (ex: score de conformidade)
        st = "Crítico" if value < crit else "Atenção" if value < warn else "Normal"
    else:
        st = "Crítico" if value > crit else "Atenção" if value > warn else "Normal"
    return st, STATUS_COLOR[st]

def risk_score_color(score: int) -> str:
    if score <= 4:  return LEVEL_COLOR["Baixo"]
    if score <= 9:  return LEVEL_COLOR["Médio"]
    if score <= 16: return LEVEL_COLOR["Alto"]
    return LEVEL_COLOR["Crítico"]

# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegação",
    ["🏠 Dashboard KRIs", "🗺️ Matriz de Riscos", "⚠️ Ocorrências",
     "✅ Planos de Ação", "📋 Auditorias", "➕ Registrar Risco / Ocorrência"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption("**Rafael Reghine Munhoz**\nData Analyst | MBA USP\n[linkedin.com/in/rafaelreghine](https://linkedin.com/in/rafaelreghine)")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — DASHBOARD KRIs
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard KRIs":
    st.title("🛡️ Dashboard de KRIs")
    st.caption("Key Risk Indicators")
    st.markdown("---")

    risks   = q("SELECT * FROM risks")
    occs    = q("SELECT * FROM occurrences")
    actions = q("SELECT * FROM action_plans")
    controls= q("SELECT * FROM risk_controls")
    audits  = q("SELECT * FROM audits")

    # ── Calcular KRIs ──────────────────────────────────────────────────────────
    recur_rate   = occs["is_recurrence"].mean() * 100
    avg_score    = risks["risk_score"].mean()
    overdue_rate = (actions["status"] == "Vencido").mean() * 100
    eff_rate     = (controls["effectiveness"] == "Eficaz").mean() * 100
    avg_audit    = audits["conformity_score"].mean()
    n_critical   = (risks["risk_level"] == "Crítico").sum()

    closed = actions[actions["status"] == "Concluído"].copy()
    closed["opened_at"] = pd.to_datetime(closed["opened_at"])
    closed["closed_at"] = pd.to_datetime(closed["closed_at"])
    avg_close = (closed["closed_at"] - closed["opened_at"]).dt.days.mean()

    kris = [
        ("Taxa de reincidência", f"{recur_rate:.1f}%",  *kri_badge(recur_rate, 15, 25)),
        ("Score médio de risco", f"{avg_score:.1f}",    *kri_badge(avg_score, 12, 18)),
        ("Planos vencidos",      f"{overdue_rate:.1f}%",*kri_badge(overdue_rate, 10, 20)),
        ("Controles eficazes",   f"{eff_rate:.1f}%",    *kri_badge(eff_rate, 70, 50, invert=True)),
        ("Fechamento médio",     f"{avg_close:.0f} dias",*kri_badge(avg_close, 30, 60)),
        ("Score de conformidade",f"{avg_audit:.1f}",    *kri_badge(avg_audit, 75, 60, invert=True)),
    ]

    # ── KRI cards ──────────────────────────────────────────────────────────────
    cols = st.columns(3)
    for i, (name, val, status, color) in enumerate(kris):
        with cols[i % 3]:
            emoji = "🟢" if status == "Normal" else "🟡" if status == "Atenção" else "🔴"
            st.metric(label=f"{emoji} {name}", value=val, delta=status,
                      delta_color="normal" if status == "Normal" else "inverse")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuição por nível de risco")
        level_counts = risks["risk_level"].value_counts().reindex(
            ["Baixo","Médio","Alto","Crítico"], fill_value=0)
        fig, ax = plt.subplots(figsize=(6, 3.5))
        colors = [LEVEL_COLOR[l] for l in level_counts.index]
        bars = ax.bar(level_counts.index, level_counts.values, color=colors,
                      edgecolor="white", width=0.6)
        for bar, val in zip(bars, level_counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(val), ha="center", fontweight="bold")
        ax.set_facecolor("white")
        ax.spines[["top","right"]].set_visible(False)
        ax.set_ylabel("Quantidade de riscos")
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("Ocorrências — tendência mensal")
        occs["occurred_at"] = pd.to_datetime(occs["occurred_at"])
        monthly = (occs.groupby(occs["occurred_at"].dt.to_period("M"))
                   .size().reset_index(name="n"))
        monthly["period"] = monthly["occurred_at"].astype(str)
        monthly = monthly.sort_values("period").tail(18)
        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        ax2.plot(range(len(monthly)), monthly["n"], marker="o",
                 color="#2E86AB", linewidth=2, markersize=5)
        ax2.fill_between(range(len(monthly)), monthly["n"], alpha=0.15, color="#2E86AB")
        step = max(1, len(monthly)//6)
        ax2.set_xticks(range(0, len(monthly), step))
        ax2.set_xticklabels(monthly["period"].iloc[::step], rotation=30, ha="right", fontsize=8)
        ax2.set_facecolor("white")
        ax2.spines[["top","right"]].set_visible(False)
        ax2.set_ylabel("Ocorrências")
        st.pyplot(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Mapa de calor — Probabilidade × Impacto")
    hm = risks.groupby(["probability","impact"]).size().unstack(fill_value=0)
    hm = hm.reindex(index=range(1,6), columns=range(1,6), fill_value=0)
    fig3, ax3 = plt.subplots(figsize=(7, 4))
    im = ax3.imshow(hm.values, cmap="YlOrRd", aspect="auto", vmin=0)
    ax3.set_xticks(range(5)); ax3.set_yticks(range(5))
    ax3.set_xticklabels([f"Impacto {i}" for i in range(1,6)], fontsize=9)
    ax3.set_yticklabels([f"Prob {i}" for i in range(1,6)], fontsize=9)
    ax3.set_xlabel("Impacto"); ax3.set_ylabel("Probabilidade")
    for i in range(5):
        for j in range(5):
            v = hm.values[i,j]
            if v > 0:
                ax3.text(j, i, str(v), ha="center", va="center",
                         fontweight="bold", fontsize=13,
                         color="white" if v > 2 else "black")
    plt.colorbar(im, ax=ax3, label="Nº de riscos")
    st.pyplot(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — MATRIZ DE RISCOS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Matriz de Riscos":
    st.title("🗺️ Matriz de Riscos")
    st.caption("Identificação e avaliação de riscos")
    st.markdown("---")

    risks = q("""
        SELECT r.*, a.name AS area,
               COUNT(DISTINCT o.id) AS occurrences,
               COUNT(DISTINCT ap.id) AS actions,
               SUM(CASE WHEN ap.status='Vencido' THEN 1 ELSE 0 END) AS overdue
        FROM risks r
        LEFT JOIN areas a ON r.area_id = a.id
        LEFT JOIN occurrences o ON o.risk_id = r.id
        LEFT JOIN action_plans ap ON ap.risk_id = r.id
        GROUP BY r.id
    """)

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        level_filter = st.multiselect("Nível de risco", ["Baixo","Médio","Alto","Crítico"],
                                       default=["Alto","Crítico"])
    with col2:
        cat_filter = st.multiselect("Categoria", risks["risk_category"].unique(),
                                     default=list(risks["risk_category"].unique()))
    with col3:
        area_filter = st.multiselect("Área", risks["area"].unique(),
                                      default=list(risks["area"].unique()))

    filtered = risks[
        risks["risk_level"].isin(level_filter) &
        risks["risk_category"].isin(cat_filter) &
        risks["area"].isin(area_filter)
    ].sort_values("risk_score", ascending=False)

    st.caption(f"Exibindo {len(filtered)} de {len(risks)} riscos")

    # Tabela colorida
    def highlight_level(val):
        color = LEVEL_COLOR.get(val, "")
        return f"background-color: {color}22; color: {color}; font-weight: bold"

    display_cols = ["title","area","risk_category","risk_source","risk_score",
                    "risk_level","risk_response","within_appetite","owner","occurrences","overdue"]
    rename_map = {
        "title":"Risco","area":"Área","risk_category":"Categoria",
        "risk_source":"Fonte","risk_score":"Score","risk_level":"Nível",
        "risk_response":"Resposta","within_appetite":"No apetite?",
        "owner":"Responsável","occurrences":"Ocorrências","overdue":"Ações vencidas"
    }
    styled = (filtered[display_cols].rename(columns=rename_map)
              .style.applymap(highlight_level, subset=["Nível"]))
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Scatter: riscos no plano cartesiano
    st.markdown("---")
    st.subheader("Posicionamento dos riscos — Probabilidade × Impacto")
    fig, ax = plt.subplots(figsize=(10, 6))

    # Zonas de fundo
    for i in range(1, 6):
        for j in range(1, 6):
            score = i * j
            if score <= 4:   c = "#3B9E6B22"
            elif score <= 9: c = "#E8A83E22"
            elif score <= 16:c = "#E07B3922"
            else:            c = "#C0392B22"
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, facecolor=c, edgecolor="white", lw=0.5))

    for _, row in filtered.iterrows():
        jitter_x = np.random.uniform(-0.15, 0.15)
        jitter_y = np.random.uniform(-0.15, 0.15)
        color = LEVEL_COLOR[row["risk_level"]]
        ax.scatter(row["impact"] + jitter_x, row["probability"] + jitter_y,
                   s=120, color=color, alpha=0.85, zorder=5, edgecolors="white", lw=0.8)
        ax.annotate(row["title"][:22], (row["impact"] + jitter_x, row["probability"] + jitter_y),
                    fontsize=6.5, ha="left", va="bottom",
                    xytext=(4, 4), textcoords="offset points", color="#333")

    ax.set_xlim(0.5, 5.5); ax.set_ylim(0.5, 5.5)
    ax.set_xticks(range(1,6)); ax.set_yticks(range(1,6))
    ax.set_xlabel("Impacto", fontsize=12); ax.set_ylabel("Probabilidade", fontsize=12)
    ax.set_facecolor("white")
    ax.spines[["top","right"]].set_visible(False)

    patches = [mpatches.Patch(color=c, label=l)
               for l, c in LEVEL_COLOR.items()]
    ax.legend(handles=patches, loc="upper left", fontsize=9, title="Nível")
    st.pyplot(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — OCORRÊNCIAS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚠️ Ocorrências":
    st.title("⚠️ Ocorrências e Apontamentos")
    st.caption("Registro e análise de incidentes, não-conformidades e apontamentos de auditoria")
    st.markdown("---")

    occs = q("""
        SELECT o.*, r.title AS risk_title, r.risk_level, a.name AS area
        FROM occurrences o
        LEFT JOIN risks r ON o.risk_id = r.id
        LEFT JOIN areas a ON o.area_id = a.id
        ORDER BY o.occurred_at DESC
    """)
    occs["occurred_at"] = pd.to_datetime(occs["occurred_at"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de ocorrências", len(occs))
    col2.metric("Reincidências", int(occs["is_recurrence"].sum()),
                delta=f"{occs['is_recurrence'].mean()*100:.1f}%", delta_color="inverse")
    graves = occs["severity"].isin(["Grave","Gravíssimo"]).sum()
    col3.metric("Graves / Gravíssimas", int(graves))
    col4.metric("Último mês", int((occs["occurred_at"] >= pd.Timestamp.today() - pd.Timedelta(days=30)).sum()))

    st.markdown("---")

    # Análise reincidência por causa raiz
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top causas raiz")
        causes = occs["root_cause"].value_counts().head(8)
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.barh(causes.index, causes.values, color="#2E86AB", height=0.6, alpha=0.85)
        ax.set_facecolor("white")
        ax.spines[["top","right"]].set_visible(False)
        for bar, val in zip(bars, causes.values):
            ax.text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2,
                    str(val), va="center", fontsize=9)
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("Reincidência por área (%)")
        area_r = (occs.groupby("area")
                  .agg(total=("id","count"), recur=("is_recurrence","sum"))
                  .assign(taxa=lambda d: d["recur"]/d["total"]*100)
                  .sort_values("taxa", ascending=True))
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        colors_r = ["#C0392B" if t>25 else "#E8A83E" if t>15 else "#3B9E6B"
                    for t in area_r["taxa"]]
        ax2.barh(area_r.index, area_r["taxa"], color=colors_r, height=0.6)
        ax2.axvline(20, color="red", linestyle="--", alpha=0.6, label="Limiar KRI 20%")
        ax2.set_facecolor("white")
        ax2.spines[["top","right"]].set_visible(False)
        ax2.set_xlabel("Taxa de reincidência (%)")
        ax2.legend(fontsize=9)
        st.pyplot(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Registro de ocorrências")
    severity_filter = st.multiselect("Severidade", ["Leve","Moderado","Grave","Gravíssimo"],
                                      default=["Grave","Gravíssimo"])
    filtered_occs = occs[occs["severity"].isin(severity_filter)] if severity_filter else occs
    display = filtered_occs[["occurred_at","occurrence_type","severity","area",
                              "risk_title","root_cause","is_recurrence","reported_by"]]
    display.columns = ["Data","Tipo","Severidade","Área","Risco","Causa raiz","Reincidência","Registrado por"]
    st.dataframe(display.head(50), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — PLANOS DE AÇÃO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✅ Planos de Ação":
    st.title("✅ Planos de Ação")
    st.caption("Tratamento do risco")
    st.markdown("---")

    actions = q("""
        SELECT ap.*, r.title AS risk_title, r.risk_level
        FROM action_plans ap
        LEFT JOIN risks r ON ap.risk_id = r.id
        ORDER BY ap.deadline ASC
    """)
    actions["deadline"]  = pd.to_datetime(actions["deadline"])
    actions["opened_at"] = pd.to_datetime(actions["opened_at"])
    today = pd.Timestamp.today()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de ações", len(actions))
    col2.metric("Vencidas", int((actions["status"]=="Vencido").sum()),
                delta_color="inverse", delta=f"{(actions['status']=='Vencido').mean()*100:.1f}%")
    col3.metric("Concluídas", int((actions["status"]=="Concluído").sum()))
    col4.metric("Em andamento", int((actions["status"]=="Em andamento").sum()))

    st.markdown("---")

    # Funil de status
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Status dos planos")
        status_counts = actions["status"].value_counts()
        status_colors = {
            "Aberto":"#3498DB","Em andamento":"#E8A83E",
            "Concluído":"#3B9E6B","Vencido":"#C0392B","Cancelado":"#95a5a6"
        }
        fig, ax = plt.subplots(figsize=(5, 4))
        colors_s = [status_colors.get(s, "#95a5a6") for s in status_counts.index]
        wedges, texts, autotexts = ax.pie(
            status_counts.values, labels=status_counts.index,
            autopct="%1.0f%%", colors=colors_s, startangle=90,
            pctdistance=0.8, wedgeprops={"edgecolor":"white","linewidth":1.5})
        for at in autotexts:
            at.set_fontsize(9); at.set_fontweight("bold")
        ax.set_facecolor("white")
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("% conclusão por tipo de ação")
        type_pct = actions.groupby("action_type")["completion_pct"].mean()
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        bars = ax2.barh(type_pct.index, type_pct.values,
                        color=["#2E86AB","#3B9E6B","#E8A83E"], height=0.5)
        ax2.set_xlim(0, 105)
        ax2.set_facecolor("white")
        ax2.spines[["top","right"]].set_visible(False)
        ax2.set_xlabel("% conclusão média")
        for bar, val in zip(bars, type_pct.values):
            ax2.text(bar.get_width()+1, bar.get_y()+bar.get_height()/2,
                     f"{val:.0f}%", va="center", fontweight="bold")
        st.pyplot(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Ações vencidas e em atraso — prioridade de acompanhamento")
    overdue = actions[actions["status"].isin(["Vencido","Em andamento"])].copy()
    overdue["dias_atraso"] = (today - overdue["deadline"]).dt.days.clip(lower=0)
    overdue = overdue.sort_values("dias_atraso", ascending=False)

    display = overdue[["risk_title","risk_level","action","action_type",
                        "responsible","deadline","status","completion_pct","dias_atraso"]].head(20)
    display.columns = ["Risco","Nível","Ação","Tipo","Responsável",
                       "Prazo","Status","% Conclusão","Dias de atraso"]

    def color_status(val):
        m = {"Vencido":"#C0392B22","Em andamento":"#E8A83E22"}
        return f"background-color: {m.get(val,'')}"

    styled = display.style.applymap(color_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — AUDITORIAS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Auditorias":
    st.title("📋 Auditorias")
    st.caption("Resultado de auditorias internas, SST e regulatórias · Score de conformidade")
    st.markdown("---")

    audits = q("""
        SELECT au.*, a.name AS area
        FROM audits au
        LEFT JOIN areas a ON au.area_id = a.id
        ORDER BY au.audit_date DESC
    """)
    audits["audit_date"] = pd.to_datetime(audits["audit_date"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de auditorias", len(audits))
    col2.metric("Score médio de conformidade", f"{audits['conformity_score'].mean():.1f}")
    col3.metric("Total de achados (findings)", int(audits["findings_count"].sum()))

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Score de conformidade por área")
        area_score = audits.groupby("area")["conformity_score"].mean().sort_values()
        fig, ax = plt.subplots(figsize=(6, 4))
        colors_a = ["#C0392B" if v < 65 else "#E8A83E" if v < 80 else "#3B9E6B"
                    for v in area_score.values]
        bars = ax.barh(area_score.index, area_score.values, color=colors_a, height=0.6)
        ax.axvline(75, color="red", linestyle="--", alpha=0.5, label="Limiar KRI 75")
        ax.set_xlim(0, 110)
        ax.set_facecolor("white")
        ax.spines[["top","right"]].set_visible(False)
        ax.set_xlabel("Score de conformidade (0-100)")
        ax.legend(fontsize=9)
        for bar, val in zip(bars, area_score.values):
            ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
                    f"{val:.0f}", va="center", fontsize=9, fontweight="bold")
        st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("Distribuição por tipo de auditoria")
        type_counts = audits["audit_type"].value_counts()
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        ax2.pie(type_counts.values, labels=type_counts.index, autopct="%1.0f%%",
                colors=["#2E86AB","#3B9E6B","#E8A83E","#C0392B"],
                startangle=90, pctdistance=0.8,
                wedgeprops={"edgecolor":"white","linewidth":1.5})
        ax2.set_facecolor("white")
        st.pyplot(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Histórico de auditorias")
    display = audits[["audit_date","area","audit_type","auditor",
                       "findings_count","conformity_score","status"]]
    display.columns = ["Data","Área","Tipo","Auditor","Achados","Score","Status"]
    st.dataframe(display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 6 — REGISTRO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "➕ Registrar Risco / Ocorrência":
    st.title("➕ Registro de Risco / Ocorrência")
    st.caption("Formulário de captura estruturada")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🛡️ Novo Risco", "⚠️ Nova Ocorrência"])

    with tab1:
        st.subheader("Identificação de Risco (Identificação de Risco)")
        areas_df = q("SELECT id, name FROM areas")
        area_map = dict(zip(areas_df["name"], areas_df["id"]))

        with st.form("form_risk"):
            c1, c2 = st.columns(2)
            with c1:
                title       = st.text_input("Título do risco *")
                description = st.text_area("Descrição", height=80)
                area_name   = st.selectbox("Área", list(area_map.keys()))
                category    = st.selectbox("Categoria",
                                           ["Operacional","Estratégico","Conformidade",
                                            "Financeiro","Reputacional","SST"])
            with c2:
                source      = st.selectbox("Fonte", ["Interno","Externo","Regulatório"])
                probability = st.slider("Probabilidade (1=Rara · 5=Quase certa)", 1, 5, 3)
                impact      = st.slider("Impacto (1=Insignificante · 5=Catastrófico)", 1, 5, 3)
                owner       = st.text_input("Responsável pelo risco")
                response    = st.selectbox("Resposta ao risco (Framework de Riscos)",
                                           ["Aceitar","Mitigar","Transferir","Evitar"])

            score = probability * impact
            level_map = {(1,4):"Baixo",(5,9):"Médio",(10,16):"Alto",(17,25):"Crítico"}
            level = next(l for (lo,hi),l in level_map.items() if lo <= score <= hi)
            color = LEVEL_COLOR[level]
            st.info(f"**Risk Score calculado: {score}/25 → Nível: {level}**  \n"
                    f"Resposta sugerida: {response}")

            submitted = st.form_submit_button("Salvar risco", use_container_width=True)
            if submitted and title:
                conn = get_conn()
                conn.execute("""
                    INSERT INTO risks (area_id, title, description, risk_category,
                    risk_source, probability, impact, risk_score, risk_level,
                    risk_response, within_appetite, owner, status, identified_at, next_review)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (area_map[area_name], title, description, category, source,
                      probability, impact, score, level, response,
                      level in ("Baixo","Médio"), owner, "Ativo",
                      str(date.today()), str(date.today() + timedelta(days=180))))
                conn.commit()
                st.success(f"✅ Risco registrado! Score: {score} · Nível: {level}")
                st.cache_resource.clear()

    with tab2:
        st.subheader("Registro de Ocorrência / Apontamento")
        risks_df = q("SELECT id, title FROM risks ORDER BY title")
        risk_map = dict(zip(risks_df["title"], risks_df["id"]))
        areas_df2 = q("SELECT id, name FROM areas")
        area_map2 = dict(zip(areas_df2["name"], areas_df2["id"]))

        with st.form("form_occ"):
            c1, c2 = st.columns(2)
            with c1:
                risk_title  = st.selectbox("Risco relacionado *", list(risk_map.keys()))
                area_name2  = st.selectbox("Área", list(area_map2.keys()))
                occ_type    = st.selectbox("Tipo de ocorrência",
                                           ["Incidente","Quase-acidente","Não-conformidade",
                                            "Apontamento de auditoria","Desvio de processo"])
                severity    = st.selectbox("Severidade", ["Leve","Moderado","Grave","Gravíssimo"])
            with c2:
                occurred_at = st.date_input("Data da ocorrência", value=date.today())
                description = st.text_area("Descrição da ocorrência *", height=80)
                root_cause  = st.text_input("Causa raiz identificada")
                method      = st.selectbox("Método de análise", ["5 Porquês","Ishikawa","FTA","Outro"])
                is_recur    = st.checkbox("É reincidência?")
                reported_by = st.text_input("Registrado por")

            submitted2 = st.form_submit_button("Registrar ocorrência", use_container_width=True)
            if submitted2 and description:
                conn = get_conn()
                conn.execute("""
                    INSERT INTO occurrences (risk_id, area_id, occurred_at, occurrence_type,
                    severity, description, root_cause, root_cause_method, is_recurrence, reported_by)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (risk_map[risk_title], area_map2[area_name2], str(occurred_at),
                      occ_type, severity, description, root_cause, method,
                      is_recur, reported_by))
                conn.commit()
                st.success("✅ Ocorrência registrada com sucesso!")
                st.cache_resource.clear()
