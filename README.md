# Corporate Risk Management System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square)
![XGBoost](https://img.shields.io/badge/XGBoost-Classifier-orange?style=flat-square)
![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-yellow?style=flat-square)
![Microsoft Fabric](https://img.shields.io/badge/Microsoft_Fabric-Lakehouse-purple?style=flat-square)
![Azure](https://img.shields.io/badge/Azure_Forms-Captura-blue?style=flat-square)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen?style=flat-square)

Sistema completo de **gestão de riscos corporativos orientado a dados** - captura estruturada de dados até modelos preditivos de Machine Learning entregues via Power BI.

---

## Stack Tecnológico

| Camada | Tecnologia | Papel no sistema |
|---|---|---|
| **ERP** | SAP (MM, PM, FI, HR, QM, PP, SD) | Fonte de dados estruturada; IDs de processo rastreáveis |
| **Captura** | Azure Forms + Power Automate | Registro de ocorrências e apontamentos (40% do volume) |
| **Storage** | Azure Data Lake / SQLite (dev) | Persistência de riscos, ocorrências, ações e KRIs |
| **Analytics** | Microsoft Fabric Lakehouse | Pipeline de dados para Power BI |
| **Visualização** | Power BI (DAX + relatórios) | Dashboard de KRIs, mapa de riscos, planos de ação |
| **Machine Learning** | Python (XGBoost, Random Forest, SMOTE) | Classificação de risco + previsão de reincidência |
| **Automação** | Power Automate | Alertas de KRI, notificação de prazo, aprovação de planos |

---

## Contexto de negócio

Empresas industriais de grande porte enfrentam:
- **Riscos distribuídos em 10+ áreas** — sem visão consolidada e acionável
- **KRIs calculados manualmente** em planilhas, sem rastreabilidade
- **Reincidência de ocorrências** — sem análise preditiva para antecipar recorrência
- **Planos de ação sem visibilidade** — vencidos sem alerta, aprovações manuais

**Pergunta central:** qual a probabilidade de reincidência — e como priorizar as ações preventivas antes que o risco se materialize novamente?

---



### 7 Componentes

| Componente | Implementação |
|---|---|
| Ambiente interno | Apetite a risco definido por área; campo `risk_response` (Aceitar/Mitigar/Transferir/Evitar) |
| Identificação | Formulário + SAP como canal de captura |
| Avaliação | Matriz Probabilidade × Impacto → `risk_score` (1–25) + `risk_level` automático |
| Resposta | Tabela `action_plans` com tipo, responsável, prazo, evidência e aprovador |
| Atividades de controle | Tabela `risk_controls` com tipo, eficácia e flag de automação (SAP / Power Automate) |
| Informação e comunicação | Dashboard Power BI via Fabric + série histórica de KRIs por área |
| Monitoramento | 12 KRIs calculados automaticamente + alertas via Power Automate + 2 modelos ML preditivos |

### Processo

```
Identificar → Analisar → Avaliar → Tratar → Monitorar → Melhorar (ciclo contínuo)
```

---

## Áreas cobertas — 11 áreas corporativas

| # | Área | Departamento | Foco COSO |
|---|---|---|---|
| 1 | Operações | Industrial | Operacional |
| 2 | Manutenção | Engenharia | Operacional / SST |
| 3 | Logística e Suprimentos | Supply Chain | Operacional / Conformidade |
| 4 | **Compras e Contratos** | Supply Chain | Estratégico / Operacional |
| 5 | SST | RH | SST / Conformidade |
| 6 | Meio Ambiente / ESG | ESG | Conformidade / Reputacional |
| 7 | Qualidade | Qualidade | Conformidade / Operacional |
| 8 | **Financeiro e Compliance** | Financeiro | Financeiro / Conformidade |
| 9 | **TI e Segurança de Dados** | Tecnologia | Operacional / Conformidade (LGPD) |
| 10 | **Recursos Humanos** | Pessoas | Operacional / Reputacional |
| 11 | **Gestão Corporativa** | Corporativo | Estratégico / Conformidade |

---

## Pipeline do projeto

```
Forms / SAP → SQLite → Python EDA → KRIs → ML → Power BI (via Fabric)
```

### 1. Modelo de dados SQL
- 6 tabelas: `risks`, `occurrences`, `risk_controls`, `action_plans`, `audits`, `kri_history`
- 3 views: `v_risk_matrix`, `v_kri_dashboard`, `v_capture_pipeline`
- Campos de rastreabilidade: `sap_process_id`, `capture_channel`, `is_automated`, `automation_tool`

### 2. Captura multi-canal
- **Forms (40%)** — principal canal de registro de ocorrências
- **SAP (26%)** — integração direta com módulos MM, PM, FI, HR
- **Auditoria (18%)** — apontamentos formais de auditorias internas
- **E-mail / Manual (16%)** — fluxo de contingência

### 3. KRIs — 12 indicadores-chave

| KRI | Fonte | Limiar Atenção | Limiar Crítico |
|---|---|---|---|
| Taxa de reincidência (%) | Forms | > 15% | > 25% |
| Score médio de risco | Power BI | > 12 | > 18 |
| Planos de ação vencidos (%) | Power Automate | > 10% | > 20% |
| Controles eficazes (%) | SAP GRC | < 70% | < 50% |
| Tempo médio de fechamento (dias) | Power Automate | > 30 dias | > 60 dias |
| Score de conformidade (auditorias) | Power BI | < 75 | < 60 |
| Riscos críticos sem plano | Power BI | > 0 | > 2 |
| Controles automatizados (%) | SAP / PA | < 40% | < 20% |
| % Fornecedores sem homologação | SAP MM | > 10% | > 20% |
| % Treinamentos NR vencidos | SAP HR | > 10% | > 20% |
| LTIF | SAP HR | > 2 | > 5 |
| Nº incidentes de SI | Azure Sentinel | > 2 | > 5 |

### 4. Machine Learning

#### Modelo 1 — Classificação de Nível de Risco (COSO ERM)
- **Aplicação prática:** ao preencher Azure Forms, o modelo sugere o nível automaticamente
- **Features:** histórico de ocorrências, eficácia e automação de controles
- **Balanceamento:** RandomOverSampler
- **Algoritmos:** Regressão Logística · Random Forest · **XGBoost ⭐**
- **Métrica:** F1-macro

| Modelo | F1-macro |
|---|---|
| Regressão Logística | ~0.87 |
| Random Forest | ~0.72 |
| **XGBoost ⭐** | **~0.79** |

#### Modelo 2 — Previsão de Reincidência (ISO 31000)
> Mesmo pipeline do projeto [Credit Risk Prediction](https://github.com/reghine/credit-risk-prediction) — classificação binária com dados desbalanceados

- **Aplicação prática:** score de prioridade entregue no Power BI para orientar planos preventivos
- **Features:** severidade, tipo de ocorrência, canal de captura (Azure Forms vs SAP), histórico de ações
- **Balanceamento:** SMOTE (dataset com 17.5% de reincidências)
- **Algoritmos:** Regressão Logística · **Random Forest ⭐** · XGBoost
- **Métrica:** AUC-ROC

| Modelo | AUC-ROC |
|---|---|
| Regressão Logística | 0.853 |
| **Random Forest ⭐** | **0.976** |
| XGBoost | 0.946 |

---

## Estrutura do repositório

```
corporate-risk-management/
│
├── data/
│   ├── schema.sql                    ← DDL completo (COSO ERM + ISO 31000)
│   ├── generate_synthetic_data.py    ← Gerador de dados realistas (11 áreas)
│   └── risk_management.db            ← Banco SQLite gerado
│
├── notebooks/
│   ├── 01_eda_kri.ipynb              ← EDA + KRIs + canal de captura Azure Forms
│   └── 02_ml_models.ipynb            ← Modelos ML (classificação + reincidência)
│
├── app/
│   └── app.py                        ← App Streamlit: dashboard + registro
│
├── outputs/                          ← Visualizações geradas (Power BI-ready)
│
├── requirements.txt
└── README.md
```

---

## Tecnologias utilizadas

| Categoria | Ferramentas |
|---|---|
| Linguagem | Python 3.12 |
| Banco de dados | SQLite (dev) / Azure SQL (prod) |
| Manipulação de dados | Pandas, NumPy |
| Machine Learning | Scikit-learn, XGBoost |
| Balanceamento | imbalanced-learn (SMOTE / RandomOverSampler) |
| Visualização | Matplotlib, Seaborn |
| App | Streamlit |
| Stack corporativo | SAP · Azure Forms · Power Automate · Microsoft Fabric · Power BI |
| Frameworks de risco | COSO ERM · ISO 31000 |

---

## Conexão com o projeto de Risco de Crédito

| [Credit Risk Prediction](https://github.com/reghine/credit-risk-prediction) | Corporate Risk Management (este projeto) |
|---|---|
| Dataset desbalanceado (~6.7% inadimplentes) | Dataset desbalanceado (17.5% reincidências) |
| SMOTE para balanceamento | SMOTE para balanceamento |
| XGBoost com AUC-ROC ~0.87 | Random Forest com AUC-ROC **0.976** |
| Score de inadimplência (0–1000) | Score de prioridade de reincidência (0–100%) |
| Mapa de sensibilidade interativo | Dashboard de KRIs via Power BI + Fabric |
| Dados financeiros de clientes | Dados operacionais de 11 áreas corporativas |

---

## Autor

**Rafael Reghine Munhoz**
Data Analyst | Digital Transformation | Python · SQL · Power BI · Azure · SAP | MBA USP

[![LinkedIn](https://img.shields.io/badge/LinkedIn-rafaelreghine-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/rafaelreghine)
[![GitHub](https://img.shields.io/badge/GitHub-rreghine-black?style=flat-square&logo=github)](https://github.com/rreghine)
