"""
Notebook 02 — Machine Learning | Sistema de Gestão de Riscos Corporativos
Stack Microsoft: SAP · Azure Forms · Power Automate · Microsoft Fabric · Power BI
Framework: COSO ERM + ISO 31000
Autor: Rafael Reghine Munhoz | MBA Data Science & Analytics — USP

Modelos:
1. Classificação de nível de risco (COSO ERM — Avaliação)
2. Previsão de reincidência de ocorrências (ISO 31000 — Melhoria Contínua)
   → mesmo pipeline do projeto de Risco de Crédito (SMOTE + XGBoost + AUC-ROC)
"""

import sqlite3, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             ConfusionMatrixDisplay, roc_auc_score, roc_curve)
from sklearn.inspection import permutation_importance
from imblearn.over_sampling import SMOTE, RandomOverSampler
import xgboost as xgb
warnings.filterwarnings("ignore")

plt.rcParams.update({
    "figure.facecolor":"white","axes.facecolor":"white",
    "axes.grid":True,"grid.alpha":0.3,"axes.spines.top":False,
    "axes.spines.right":False,"font.family":"sans-serif",
})
MICROSOFT_BLUE = "#0078D4"

DB_PATH = Path("data/risk_management.db")
conn    = sqlite3.connect(DB_PATH)

print("="*65)
print("  ML — GESTÃO DE RISCOS CORPORATIVOS | Stack Microsoft")
print("  COSO ERM + ISO 31000")
print("="*65)

# ─────────────────────────────────────────────────────────────────────────────
# MODELO 1 — Classificação de nível de risco (COSO ERM)
# Entrada: área, categoria, histórico de ocorrências, eficácia de controles
# Saída:   Baixo / Médio / Alto / Crítico
# Uso:     ao registrar novo risco via Azure Forms, o modelo sugere o nível
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n══ MODELO 1: Classificação de Nível de Risco (COSO ERM) ══")
print("   Aplicação: ao preencher o Azure Forms, o modelo sugere o nível")
print("   automaticamente — reduz erro humano na avaliação.\n")

risks = pd.read_sql_query("""
    SELECT r.*, a.name AS area, a.department,
           COUNT(DISTINCT o.id)  AS occ_count,
           SUM(o.is_recurrence)  AS recur_count,
           SUM(CASE WHEN o.severity IN ('Grave','Gravíssimo') THEN 1 ELSE 0 END) AS severe_count,
           COUNT(DISTINCT rc.id) AS ctrl_count,
           SUM(CASE WHEN rc.effectiveness='Eficaz' THEN 1 ELSE 0 END) AS eff_ctrl,
           SUM(rc.is_automated)  AS auto_ctrl,
           COUNT(DISTINCT ap.id) AS action_count,
           SUM(CASE WHEN ap.status='Vencido' THEN 1 ELSE 0 END) AS overdue
    FROM risks r
    LEFT JOIN areas a          ON r.area_id  = a.id
    LEFT JOIN occurrences o    ON o.risk_id  = r.id
    LEFT JOIN risk_controls rc ON rc.risk_id = r.id
    LEFT JOIN action_plans ap  ON ap.risk_id = r.id
    GROUP BY r.id
""", conn)

risks["ctrl_eff_pct"]    = risks["eff_ctrl"]  / risks["ctrl_count"].replace(0,1)
risks["ctrl_auto_pct"]   = risks["auto_ctrl"] / risks["ctrl_count"].replace(0,1)
risks["overdue_pct"]     = risks["overdue"]   / risks["action_count"].replace(0,1)
risks["recur_rate"]      = risks["recur_count"]/ risks["occ_count"].replace(0,1)

CAT_FEATS = ["risk_category","risk_source","area","department"]
NUM_FEATS = ["probability","impact","occ_count","recur_count","severe_count",
             "ctrl_count","ctrl_eff_pct","ctrl_auto_pct","overdue_pct","recur_rate"]
TARGET    = "risk_level"

df = risks.copy()
for col in CAT_FEATS:
    df[col] = LabelEncoder().fit_transform(df[col].astype(str))

X = df[NUM_FEATS + CAT_FEATS]
le_target = LabelEncoder()
y = le_target.fit_transform(df[TARGET])
classes = le_target.classes_

imp = SimpleImputer(strategy="median")
X_i = imp.fit_transform(X)

ros = RandomOverSampler(random_state=42)
X_r, y_r = ros.fit_resample(X_i, y)
print(f"Distribuição original: {dict(zip(*np.unique(y, return_counts=True)))}")
print(f"Após balanceamento:    {dict(zip(*np.unique(y_r, return_counts=True)))}")

X_tr, X_te, y_tr, y_te = train_test_split(X_r, y_r, test_size=0.25,
                                            random_state=42, stratify=y_r)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

models1 = {
    "Regressão Logística": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
    "XGBoost":             xgb.XGBClassifier(n_estimators=100, random_state=42,
                                              eval_metric="mlogloss"),
}
results1 = {}
for name, model in models1.items():
    scores = cross_val_score(model, X_tr, y_tr, cv=cv, scoring="f1_macro")
    results1[name] = scores
    print(f"  {name:<25} F1-macro: {scores.mean():.3f} ± {scores.std():.3f}")

best1 = models1["XGBoost"]
best1.fit(X_tr, y_tr)
y_pred1 = best1.predict(X_te)

print(f"\nXGBoost — Classificação de Nível de Risco:\n")
print(classification_report(y_te, y_pred1, target_names=classes))

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
bp = axes[0].boxplot([results1[m] for m in models1],
                     labels=list(models1.keys()), patch_artist=True, widths=0.5)
for patch, color in zip(bp["boxes"], ["#95a5a6", MICROSOFT_BLUE, "#C0392B"]):
    patch.set_facecolor(color); patch.set_alpha(0.75)
axes[0].set_title("Comparação de modelos — F1-macro (CV 5-fold)\nClassificação de Nível de Risco (COSO ERM)")
axes[0].set_ylabel("F1-macro"); axes[0].set_ylim(0, 1.05)

cm1 = confusion_matrix(y_te, y_pred1)
ConfusionMatrixDisplay(cm1, display_labels=classes).plot(ax=axes[1], colorbar=False, cmap="Blues")
axes[1].set_title("Matriz de confusão — XGBoost\nNível de risco: Baixo / Médio / Alto / Crítico")
plt.tight_layout()
plt.savefig("outputs/09_model1_risk_classification.png", dpi=150, bbox_inches="tight")
plt.show()

# Feature importance
perm = permutation_importance(best1, X_te, y_te, n_repeats=10,
                               random_state=42, scoring="f1_macro")
feat_df = pd.DataFrame({
    "feature":    NUM_FEATS + CAT_FEATS,
    "importance": perm.importances_mean,
    "std":        perm.importances_std,
}).sort_values("importance", ascending=True)

fig, ax = plt.subplots(figsize=(10, 6))
clrs_f = ["#C0392B" if v>0.05 else MICROSOFT_BLUE if v>0.01 else "#95a5a6"
          for v in feat_df["importance"]]
ax.barh(feat_df["feature"], feat_df["importance"],
        xerr=feat_df["std"], color=clrs_f, height=0.6,
        error_kw={"elinewidth":1,"capsize":3})
ax.axvline(0, color="black", linewidth=0.5)
ax.set_title("Feature Importance — Permutation (XGBoost)\nClassificação de nível de risco | COSO ERM")
ax.set_xlabel("Redução médio no F1-macro ao permutar a feature")
plt.tight_layout()
plt.savefig("outputs/10_feature_importance.png", dpi=150, bbox_inches="tight")
plt.show()

# ─────────────────────────────────────────────────────────────────────────────
# MODELO 2 — Previsão de reincidência (ISO 31000 — Melhoria Contínua)
# Mesmo pipeline do projeto de Risco de Crédito:
#   dataset desbalanceado → SMOTE → XGBoost → AUC-ROC
# Uso: priorizar ações preventivas para ocorrências com alta prob. de recorrência
# ─────────────────────────────────────────────────────────────────────────────
print("\n\n══ MODELO 2: Previsão de Reincidência (ISO 31000) ══")
print("   Mesmo pipeline do projeto de Risco de Crédito:")
print("   dataset desbalanceado → SMOTE → XGBoost → AUC-ROC\n")

occs = pd.read_sql_query("""
    SELECT o.*,
           r.risk_category, r.risk_source, r.risk_score, r.risk_level,
           a.name AS area,
           COUNT(ap.id) AS n_actions,
           SUM(CASE WHEN ap.status='Concluído' THEN 1 ELSE 0 END) AS closed_actions,
           AVG(CASE WHEN ap.status='Concluído'
               THEN JULIANDAY(ap.closed_at) - JULIANDAY(ap.opened_at) END) AS avg_action_days
    FROM occurrences o
    LEFT JOIN risks r          ON o.risk_id  = r.id
    LEFT JOIN areas a          ON o.area_id  = a.id
    LEFT JOIN action_plans ap  ON ap.occurrence_id = o.id
    GROUP BY o.id
""", conn)

sev_map  = {"Leve":1,"Moderado":2,"Grave":3,"Gravíssimo":4}
type_map = {t:i for i,t in enumerate(occs["occurrence_type"].unique())}
ch_map   = {c:i for i,c in enumerate(occs["capture_channel"].unique())}

occs["severity_num"]        = occs["severity"].map(sev_map)
occs["occurrence_type_num"] = occs["occurrence_type"].map(type_map)
occs["capture_channel_num"] = occs["capture_channel"].map(ch_map)
occs["closure_rate"]        = occs["closed_actions"] / occs["n_actions"].replace(0,1)

for col in ["risk_category","risk_source","risk_level","area","root_cause"]:
    occs[col+"_enc"] = LabelEncoder().fit_transform(occs[col].astype(str))

OCC_FEATS = ["severity_num","occurrence_type_num","capture_channel_num",
             "risk_score","n_actions","closure_rate","avg_action_days",
             "risk_category_enc","risk_source_enc","risk_level_enc",
             "area_enc","root_cause_enc"]

X_o = occs[OCC_FEATS]
y_o = occs["is_recurrence"].astype(int)

print(f"Target — reincidência:")
print(f"  Não reincide (0): {(y_o==0).sum()} ({(y_o==0).mean()*100:.1f}%)")
print(f"  Reincide    (1): {(y_o==1).sum()} ({(y_o==1).mean()*100:.1f}%)")
print(f"  Dataset desbalanceado → aplicando SMOTE (igual ao projeto de crédito)\n")

imp2 = SimpleImputer(strategy="median")
X_o2 = imp2.fit_transform(X_o)

smote = SMOTE(random_state=42, k_neighbors=4)
X_r2, y_r2 = smote.fit_resample(X_o2, y_o)
print(f"Após SMOTE: Não={( y_r2==0).sum()} | Sim={(y_r2==1).sum()}")

X_tr2, X_te2, y_tr2, y_te2 = train_test_split(X_r2, y_r2, test_size=0.25,
                                                random_state=42, stratify=y_r2)
models2 = {
    "Regressão Logística": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
    "XGBoost":             xgb.XGBClassifier(n_estimators=100, random_state=42,
                                              eval_metric="logloss"),
}
results2 = {}
for name, model in models2.items():
    model.fit(X_tr2, y_tr2)
    y_s  = model.predict_proba(X_te2)[:,1]
    auc  = roc_auc_score(y_te2, y_s)
    results2[name] = {"auc": auc, "y_score": y_s, "model": model}
    print(f"  {name:<25} AUC-ROC: {auc:.3f}")

best_name2  = max(results2, key=lambda k: results2[k]["auc"])
best_model2 = results2[best_name2]["model"]
print(f"\nMelhor modelo: {best_name2} (AUC = {results2[best_name2]['auc']:.3f})")
print(f"\nRelatório de classificação ({best_name2}):\n")
y_pred2 = best_model2.predict(X_te2)
print(classification_report(y_te2, y_pred2, target_names=["Não reincide","Reincide"]))

# Plot ROC + confusion matrix
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for (name, res), color in zip(results2.items(), ["#95a5a6", MICROSOFT_BLUE, "#C0392B"]):
    fpr, tpr, _ = roc_curve(y_te2, res["y_score"])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={res['auc']:.3f})",
                 color=color, linewidth=2)
axes[0].plot([0,1],[0,1],"k--", alpha=0.4, linewidth=1)
axes[0].set_xlabel("Taxa de Falsos Positivos")
axes[0].set_ylabel("Taxa de Verdadeiros Positivos")
axes[0].set_title("Curvas ROC — Previsão de Reincidência\nISO 31000: Melhoria Contínua | mesmo pipeline do Risco de Crédito")
axes[0].legend(fontsize=9)

cm2 = confusion_matrix(y_te2, y_pred2)
ConfusionMatrixDisplay(cm2, display_labels=["Não reincide","Reincide"]).plot(
    ax=axes[1], colorbar=False, cmap="Oranges")
axes[1].set_title(f"Matriz de confusão — {best_name2}\nPrevisão de reincidência de ocorrências")
plt.tight_layout()
plt.savefig("outputs/11_model2_recurrence_roc.png", dpi=150, bbox_inches="tight")
plt.show()

# Saída acionável: score de prioridade por ocorrência
print("\n📋 Score de reincidência por ocorrência — saída para Power BI:")
sample = occs.sample(10, random_state=42).copy()
proba  = best_model2.predict_proba(imp2.transform(sample[OCC_FEATS]))[:,1]
sample["reincidence_proba"] = proba
sample["priority_flag"] = sample["reincidence_proba"].apply(
    lambda p: "🔴 Prioridade Alta" if p>0.7 else "🟡 Prioridade Média" if p>0.4 else "🟢 Baixa")
print(sample[["occurrence_type","severity","area","capture_channel",
              "reincidence_proba","priority_flag"]].to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
print("""
\n╔══════════════════════════════════════════════════════════════════╗
║  ALINHAMENTO DOS MODELOS COM COSO ERM E ISO 31000               ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  MODELO 1 — Classificação de Nível de Risco                     ║
║  → COSO ERM: Avaliação de Riscos (componente 3)                 ║
║  → Integração: Azure Forms → modelo → sugestão automática        ║
║  → Output via Power BI: nível sugerido + probabilidade           ║
║                                                                  ║
║  MODELO 2 — Previsão de Reincidência de Ocorrências             ║
║  → ISO 31000: Monitoramento e melhoria contínua (Seção 6.7)     ║
║  → Mesmo pipeline do projeto de Risco de Crédito:               ║
║    desbalanceado → SMOTE → XGBoost → AUC-ROC                   ║
║  → Output: score de prioridade para plano de ação preventivo    ║
║  → Integrado ao Power BI via Microsoft Fabric Lakehouse          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
conn.close()
print("✅ Notebooks concluídos. Outputs salvos em /outputs/")
