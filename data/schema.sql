-- ============================================================
-- Sistema de Gestão de Riscos Corporativos
-- Contexto: Grande empresa industrial com stack Microsoft
-- ERP: SAP | Captura: Azure Forms + Power Automate
-- Analytics: Microsoft Fabric + Power BI
-- Alinhado com COSO ERM e ISO 31000
-- Autor: Rafael Reghine Munhoz
-- ============================================================

CREATE TABLE IF NOT EXISTS areas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    department  TEXT NOT NULL,
    director    TEXT,
    manager     TEXT
);

-- Registro central de riscos (COSO ERM — Identificação e Avaliação)
CREATE TABLE IF NOT EXISTS risks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id         INTEGER REFERENCES areas(id),
    title           TEXT NOT NULL,
    description     TEXT,
    risk_category   TEXT CHECK(risk_category IN (
                        'Operacional','Estratégico','Conformidade',
                        'Financeiro','Reputacional','SST')),
    risk_source     TEXT CHECK(risk_source IN ('Interno','Externo','Regulatório')),
    probability     INTEGER CHECK(probability BETWEEN 1 AND 5),
    impact          INTEGER CHECK(impact BETWEEN 1 AND 5),
    risk_score      INTEGER,
    risk_level      TEXT CHECK(risk_level IN ('Baixo','Médio','Alto','Crítico')),
    risk_response   TEXT CHECK(risk_response IN ('Aceitar','Mitigar','Transferir','Evitar')),
    within_appetite INTEGER DEFAULT 0,
    owner           TEXT,
    status          TEXT DEFAULT 'Ativo' CHECK(status IN ('Ativo','Monitorado','Encerrado')),
    identified_at   DATE,
    next_review     DATE,
    sap_process_id  TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ocorrências — captura via Azure Forms → Power Automate → banco
CREATE TABLE IF NOT EXISTS occurrences (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id                 INTEGER REFERENCES risks(id),
    area_id                 INTEGER REFERENCES areas(id),
    occurred_at             DATE NOT NULL,
    occurrence_type         TEXT CHECK(occurrence_type IN (
                                'Incidente','Quase-acidente','Não-conformidade',
                                'Apontamento de auditoria','Desvio de processo',
                                'Falha de controle')),
    severity                TEXT CHECK(severity IN ('Leve','Moderado','Grave','Gravíssimo')),
    description             TEXT,
    root_cause              TEXT,
    root_cause_method       TEXT CHECK(root_cause_method IN ('5 Porquês','Ishikawa','FTA','Outro')),
    is_recurrence           INTEGER DEFAULT 0,
    previous_occurrence_id  INTEGER REFERENCES occurrences(id),
    capture_channel         TEXT CHECK(capture_channel IN (
                                'Azure Forms','SAP','E-mail','Auditoria','Sistema legado','Manual')),
    reported_by             TEXT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Controles (COSO ERM — Atividades de Controle)
CREATE TABLE IF NOT EXISTS risk_controls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id         INTEGER REFERENCES risks(id),
    control_name    TEXT NOT NULL,
    control_type    TEXT CHECK(control_type IN ('Preventivo','Detectivo','Corretivo')),
    description     TEXT,
    effectiveness   TEXT CHECK(effectiveness IN ('Eficaz','Parcial','Ineficaz','Não testado')),
    is_automated    INTEGER DEFAULT 0,
    automation_tool TEXT,
    test_date       DATE,
    next_review     DATE,
    responsible     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Planos de ação (ISO 31000 — Tratamento do risco)
CREATE TABLE IF NOT EXISTS action_plans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id         INTEGER REFERENCES risks(id),
    occurrence_id   INTEGER REFERENCES occurrences(id),
    action          TEXT NOT NULL,
    action_type     TEXT CHECK(action_type IN ('Corretiva','Preventiva','Melhoria')),
    responsible     TEXT,
    area_id         INTEGER REFERENCES areas(id),
    deadline        DATE,
    status          TEXT DEFAULT 'Aberto' CHECK(status IN (
                        'Aberto','Em andamento','Concluído','Vencido','Cancelado')),
    completion_pct  INTEGER DEFAULT 0 CHECK(completion_pct BETWEEN 0 AND 100),
    evidence        TEXT,
    approved_by     TEXT,
    opened_at       DATE,
    closed_at       DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auditorias periódicas (6 tipos — todos presentes em empresa de grande porte)
CREATE TABLE IF NOT EXISTS audits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id         INTEGER REFERENCES areas(id),
    audit_type      TEXT CHECK(audit_type IN (
                        'Interna','Regulatória','SST',
                        'Fornecedores','TI / Segurança da Informação',
                        'Processos / Compliance')),
    audit_date      DATE NOT NULL,
    auditor         TEXT,
    scope           TEXT,
    findings_count  INTEGER DEFAULT 0,
    conformity_score INTEGER CHECK(conformity_score BETWEEN 0 AND 100),
    status          TEXT CHECK(status IN ('Planejada','Em andamento','Concluída')),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Histórico KRIs — série temporal para Power BI via Fabric
CREATE TABLE IF NOT EXISTS kri_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kri_name        TEXT NOT NULL,
    area_id         INTEGER REFERENCES areas(id),
    period          TEXT,
    value           REAL,
    threshold_warn  REAL,
    threshold_crit  REAL,
    status          TEXT CHECK(status IN ('Normal','Atenção','Crítico')),
    data_source     TEXT,
    calculated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Views para Power BI via Microsoft Fabric ─────────────────────────────────

CREATE VIEW IF NOT EXISTS v_risk_matrix AS
SELECT
    r.id, r.title, r.sap_process_id,
    a.name AS area, a.department,
    r.risk_category, r.risk_source,
    r.probability, r.impact, r.risk_score, r.risk_level,
    r.risk_response, r.within_appetite, r.owner, r.status,
    COUNT(DISTINCT o.id)    AS occurrence_count,
    COUNT(DISTINCT ap.id)   AS action_count,
    SUM(CASE WHEN ap.status='Vencido'   THEN 1 ELSE 0 END) AS overdue_actions,
    SUM(CASE WHEN ap.status='Concluído' THEN 1 ELSE 0 END) AS closed_actions,
    COUNT(DISTINCT rc.id)   AS control_count,
    SUM(CASE WHEN rc.effectiveness='Eficaz' THEN 1 ELSE 0 END) AS effective_controls,
    MAX(o.occurred_at)      AS last_occurrence
FROM risks r
LEFT JOIN areas a          ON r.area_id  = a.id
LEFT JOIN occurrences o    ON o.risk_id  = r.id
LEFT JOIN action_plans ap  ON ap.risk_id = r.id
LEFT JOIN risk_controls rc ON rc.risk_id = r.id
GROUP BY r.id;

CREATE VIEW IF NOT EXISTS v_kri_dashboard AS
SELECT
    a.id AS area_id, a.name AS area, a.department,
    COUNT(DISTINCT r.id)    AS total_risks,
    AVG(r.risk_score)       AS avg_risk_score,
    SUM(CASE WHEN r.risk_level='Crítico' THEN 1 ELSE 0 END) AS critical_risks,
    SUM(CASE WHEN r.risk_level='Alto'    THEN 1 ELSE 0 END) AS high_risks,
    SUM(CASE WHEN r.within_appetite=0    THEN 1 ELSE 0 END) AS out_of_appetite,
    COUNT(DISTINCT o.id)    AS total_occurrences,
    SUM(CASE WHEN o.is_recurrence=1 THEN 1 ELSE 0 END) AS recurrences,
    COUNT(DISTINCT ap.id)   AS total_actions,
    SUM(CASE WHEN ap.status='Vencido'    THEN 1 ELSE 0 END) AS overdue_actions,
    SUM(CASE WHEN ap.status='Concluído'  THEN 1 ELSE 0 END) AS closed_actions,
    AVG(CASE WHEN ap.status='Concluído'
        THEN JULIANDAY(ap.closed_at) - JULIANDAY(ap.opened_at) END) AS avg_closure_days,
    AVG(au.conformity_score) AS avg_conformity_score,
    COUNT(DISTINCT au.id)    AS audit_count
FROM areas a
LEFT JOIN risks r          ON r.area_id  = a.id
LEFT JOIN occurrences o    ON o.area_id  = a.id
LEFT JOIN action_plans ap  ON ap.area_id = a.id
LEFT JOIN audits au        ON au.area_id  = a.id
GROUP BY a.id;

CREATE VIEW IF NOT EXISTS v_capture_pipeline AS
SELECT
    capture_channel,
    COUNT(*)           AS total,
    SUM(is_recurrence) AS recurrences,
    SUM(CASE WHEN severity IN ('Grave','Gravíssimo') THEN 1 ELSE 0 END) AS severe_count
FROM occurrences
GROUP BY capture_channel;
