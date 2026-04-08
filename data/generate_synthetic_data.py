"""
Gerador de dados sintéticos — Sistema de Gestão de Riscos Corporativos
Contexto: Grande empresa industrial com stack Microsoft
  ERP:       SAP (consulta de tabelas SQL via SAP HANA / SQL Server)
  Captura:   Azure Forms + Power Automate
  Storage:   Azure Data Lake / Microsoft Fabric Lakehouse
  Analytics: Microsoft Fabric + Power BI

Alinhado com COSO ERM e ISO 31000
Autor: Rafael Reghine Munhoz | MBA Data Science & Analytics — USP
"""

import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DB_PATH = Path(__file__).parent / "risk_management.db"

# ── Áreas corporativas (11 — genéricas, presentes em qualquer grande empresa) ─

AREAS = [
    # (name, department, director, manager)
    ("Operações",               "Industrial",       "Dir. Industrial",      "Gerente de Operações"),
    ("Manutenção",              "Engenharia",       "Dir. Industrial",      "Gerente de Manutenção"),
    ("Logística e Suprimentos", "Supply Chain",     "Dir. Supply Chain",    "Gerente de Logística"),
    ("Compras e Contratos",     "Supply Chain",     "Dir. Supply Chain",    "Gerente de Compras"),
    ("SST",                     "RH",               "Dir. RH",              "Coord. SST"),
    ("Meio Ambiente / ESG",     "ESG",              "Dir. ESG",             "Coord. Ambiental"),
    ("Qualidade",               "Qualidade",        "Dir. Qualidade",       "Gerente de Qualidade"),
    ("Financeiro e Compliance", "Financeiro",       "Dir. Financeiro",      "Gerente Financeiro"),
    ("TI e Segurança de Dados", "Tecnologia",       "Dir. TI",              "Gerente de TI"),
    ("Recursos Humanos",        "RH",               "Dir. RH",              "Gerente de RH"),
    ("Gestão Corporativa",      "Corporativo",      "CEO",                  "Gerente Corporativo"),
]

# ── Responsáveis (perfis reais de uma empresa industrial) ─────────────────────

OWNERS = [
    "Carlos Henrique Mendes",   "Ana Paula Rodrigues",  "Bruno Ferreira Lima",
    "Fernanda Costa Souza",     "Juliana Martins",      "Thiago Oliveira",
    "Ricardo Alves Pereira",    "Marcos Antonio Silva", "Patrícia Rocha",
    "Eduardo Nascimento",       "Camila Torres",        "Felipe Gomes",
]

# ── Riscos por área — temáticos e realistas ───────────────────────────────────
# (title, category, source, description, sap_process, prob_range, impact_range)

RISK_TEMPLATES = {

    "Operações": [
        ("Parada não programada de linha de produção",
         "Operacional","Interno",
         "Falha mecânica ou elétrica causa interrupção da produção sem aviso prévio, gerando perdas de OEE e atraso de entrega.",
         "PP-001",(2,4),(4,5)),
        ("Desvio de parâmetro de processo fora da especificação",
         "Operacional","Interno",
         "Variável de processo (temperatura, pressão, pH) fora do range especificado no SAP PP, risco de produto não conforme.",
         "PP-002",(3,4),(3,4)),
        ("Falta de matéria-prima crítica",
         "Operacional","Externo",
         "Ruptura de estoque de insumo crítico por falha de previsão no SAP MM ou atraso de fornecedor, impactando o plano de produção.",
         "MM-001",(2,3),(4,5)),
        ("Produto fora de especificação liberado ao cliente",
         "Reputacional","Interno",
         "Falha no controle de qualidade no SAP QM resulta em lote não conforme sendo despachado, gerando risco de recall e multa contratual.",
         "QM-001",(1,2),(5,5)),
        ("Excesso de retrabalho na linha",
         "Operacional","Interno",
         "Alto índice de reprocesso eleva custo de produção e reduz capacidade disponível.",
         "PP-003",(3,4),(2,3)),
    ],

    "Manutenção": [
        ("Manutenção preventiva não realizada no prazo",
         "Operacional","Interno",
         "Plano de manutenção do SAP PM vencido sem execução, aumentando risco de falha catastrófica de equipamento crítico.",
         "PM-001",(3,4),(3,5)),
        ("Equipamento crítico sem sobressalente em estoque",
         "Operacional","Interno",
         "Ausência de peça de reposição para ativo crítico no almoxarifado SAP MM, prolongando tempo de parada em caso de falha.",
         "PM-002",(2,3),(4,5)),
        ("Execução de trabalho sem Permissão de Trabalho (PT)",
         "SST","Interno",
         "Colaboradores realizando atividades de risco sem emissão e aprovação de PT no sistema de gestão.",
         "PM-003",(2,4),(3,5)),
        ("Vida útil de equipamento crítico excedida",
         "Operacional","Interno",
         "Ativo com vida útil esgotada ainda em operação por falta de plano de substituição ou capex aprovado.",
         "PM-004",(2,3),(3,4)),
        ("Terceiro executando manutenção sem qualificação comprovada",
         "Conformidade","Externo",
         "Empresa prestadora de serviços sem habilitação técnica adequada para o escopo contratado.",
         "PM-005",(2,3),(3,4)),
    ],

    "Logística e Suprimentos": [
        ("Atraso de entrega ao cliente por falha logística",
         "Operacional","Interno",
         "Ruptura na cadeia de distribuição — veículo, rota ou armazém — causando descumprimento de SLA contratual.",
         "SD-001",(3,4),(3,4)),
        ("Avaria de produto em trânsito",
         "Operacional","Externo",
         "Dano ao produto durante transporte por acondicionamento inadequado ou acidente, gerando devolução e retrabalho.",
         "SD-002",(2,3),(3,4)),
        ("Ruptura de estoque de produto acabado",
         "Operacional","Interno",
         "Demanda acima do previsto ou falha no planejamento SAP MM/PP gera stockout e perda de faturamento.",
         "MM-002",(2,3),(3,4)),
        ("Desvio de inventário — diferença entre SAP e físico",
         "Financeiro","Interno",
         "Divergência entre estoque físico e sistema SAP MM acima da tolerância, indicando possível desvio ou erro de processo.",
         "MM-003",(2,4),(2,4)),
        ("Transporte de produto perigoso sem documentação legal",
         "Conformidade","Regulatório",
         "Emissão incorreta ou ausente de documentos fiscais e de segurança (FISPQ, ONU) para transporte de carga perigosa.",
         "SD-003",(1,3),(4,5)),
    ],

    "Compras e Contratos": [
        ("Dependência de fornecedor único para insumo crítico",
         "Estratégico","Externo",
         "Ausência de fornecedor alternativo homologado para item crítico de produção, gerando vulnerabilidade de desabastecimento.",
         "MM-004",(2,3),(4,5)),
        ("Contrato de fornecimento vencido sem renovação",
         "Conformidade","Interno",
         "Prestação de serviço ou fornecimento de material sem contrato vigente, expondo a empresa a riscos jurídicos e fiscais.",
         "MM-005",(3,5),(3,4)),
        ("Fornecedor sem homologação técnica ou ESG",
         "Reputacional","Externo",
         "Fornecedor ativo na base SAP MM sem aprovação nos critérios de homologação técnica, trabalhista ou socioambiental.",
         "MM-006",(3,4),(2,4)),
        ("Compra sem processo licitatório ou aprovação de alçada",
         "Financeiro","Interno",
         "Aquisição realizada fora das alçadas de aprovação definidas no SAP SRM, violando política de compras.",
         "MM-007",(2,3),(3,4)),
        ("Risco de subcontratação sem cláusula de responsabilidade",
         "Conformidade","Externo",
         "Fornecedor subcontrata serviço sem ciência da empresa e sem cláusula contratual, gerando responsabilidade solidária.",
         "MM-008",(2,3),(3,4)),
    ],

    "SST": [
        ("Acidente com afastamento por ausência de procedimento",
         "SST","Interno",
         "Colaborador se acidenta executando atividade de risco sem POP ou treinamento formal documentado no sistema de SST.",
         "HR-001",(2,3),(4,5)),
        ("Trabalho em altura sem PTRA e linha de vida",
         "SST","Interno",
         "Atividade em altura executada sem Permissão de Trabalho em Altura, equipamentos de proteção e técnico habilitado (NR-35).",
         "HR-002",(1,3),(5,5)),
        ("Espaço confinado sem atendimento à NR-33",
         "SST","Regulatório",
         "Entrada em espaço confinado sem vigia, médico do trabalho, equipamentos de monitoramento de atmosfera e emergência.",
         "HR-003",(1,2),(5,5)),
        ("EPI não fornecido ou utilizado incorretamente",
         "SST","Interno",
         "Colaboradores operando sem EPI adequado ao risco da atividade ou com uso incorreto — sem registro no sistema.",
         "HR-004",(3,5),(3,4)),
        ("Alto índice de acidentes de trajeto",
         "SST","Externo",
         "Elevada incidência de acidentes no deslocamento casa-trabalho, impactando o LTIF e gerando custo previdenciário.",
         "HR-005",(3,4),(2,3)),
        ("Colaborador sem treinamento obrigatório em dia",
         "Conformidade","Interno",
         "Vencimento de treinamentos NR sem renovação tempestiva — descumprimento de requisito legal.",
         "HR-006",(3,5),(2,4)),
    ],

    "Meio Ambiente / ESG": [
        ("Vazamento de efluente com potencial de contaminação",
         "Conformidade","Interno",
         "Derramamento de efluente industrial em área não impermeabilizada, com risco de contaminação de solo e lençol freático.",
         "ENV-001",(1,3),(4,5)),
        ("Descarte irregular de resíduo perigoso",
         "Conformidade","Regulatório",
         "Destinação de resíduo Classe I sem manifesto eletrônico (SINIR) e para empresa não licenciada — risco de multa IBAMA/CETESB.",
         "ENV-002",(1,3),(4,5)),
        ("Licença ambiental de operação vencida",
         "Conformidade","Regulatório",
         "Licença de Operação com prazo expirado e renovação não protocolada, expondo a empresa a embargo e multa.",
         "ENV-003",(1,2),(5,5)),
        ("Emissão atmosférica acima do limite legal",
         "Conformidade","Regulatório",
         "Resultado de monitoramento de chaminés acima dos limites da licença ambiental e da Resolução CONAMA.",
         "ENV-004",(1,3),(4,5)),
        ("Meta ESG não atingida — desvio de reporte",
         "Reputacional","Interno",
         "Indicador de sustentabilidade reportado no GRI fora da meta comprometida, gerando risco reputacional com investidores e clientes.",
         "ENV-005",(2,3),(3,4)),
    ],

    "Qualidade": [
        ("Reclamação de cliente não tratada dentro do SLA",
         "Reputacional","Externo",
         "Reclamação de cliente (SAP CRM / portal) sem resposta formal dentro do prazo contratual — risco de escalada e perda de contrato.",
         "QM-002",(3,4),(3,4)),
        ("Auditoria de certificação com risco de descredenciamento",
         "Conformidade","Regulatório",
         "Não conformidades críticas identificadas em auditoria ISO 9001/14001 com risco de suspensão do certificado.",
         "QM-003",(1,2),(5,5)),
        ("Indicador de qualidade (PPM) fora da meta contratual",
         "Operacional","Interno",
         "PPM de defeitos ao cliente acima do nível máximo contratado, gerando cláusula de penalidade e risco de perda do cliente.",
         "QM-004",(2,3),(4,5)),
        ("Calibração de instrumento de medição vencida",
         "Conformidade","Interno",
         "Instrumentos usados em pontos críticos de controle sem certificado de calibração vigente — rastreabilidade comprometida.",
         "QM-005",(3,5),(2,4)),
        ("Documento de qualidade desatualizado em uso",
         "Operacional","Interno",
         "Operadores utilizando versão obsoleta de instrução de trabalho ou especificação técnica não controlada no sistema.",
         "QM-006",(3,4),(2,3)),
    ],

    "Financeiro e Compliance": [
        ("Fraude interna em processo de pagamento",
         "Financeiro","Interno",
         "Pagamento a fornecedor inexistente ou duplicado por falha no controle de alçadas SAP FI — risco de desvio financeiro.",
         "FI-001",(1,2),(5,5)),
        ("Erro de provisão financeira com impacto no resultado",
         "Financeiro","Interno",
         "Provisão incorreta no SAP CO gerando distorção do EBITDA reportado — risco de reapresentação de resultados.",
         "FI-002",(2,3),(4,5)),
        ("Multa por descumprimento de obrigação fiscal",
         "Conformidade","Regulatório",
         "Entrega fora do prazo ou incorreta de obrigação acessória (SPED, EFD, DCTF) gerando multa e juros de mora.",
         "FI-003",(2,3),(3,4)),
        ("Conflito de interesse não declarado em processo de compra",
         "Conformidade","Interno",
         "Colaborador com relacionamento com fornecedor participando de processo de aprovação sem declaração formal.",
         "FI-004",(2,4),(3,4)),
        ("Ausência de controle de alçadas em aprovações SAP",
         "Financeiro","Interno",
         "Usuário SAP com perfil de aprovação acima do nível adequado à sua alçada — risco de aprovação indevida.",
         "FI-005",(2,3),(3,4)),
        ("Inadimplência de cliente impactando fluxo de caixa",
         "Financeiro","Externo",
         "Concentração de recebíveis em poucos clientes com histórico de atraso — risco de liquidez.",
         "FI-006",(2,3),(3,4)),
    ],

    "TI e Segurança de Dados": [
        ("Vazamento de dados pessoais — não conformidade LGPD",
         "Conformidade","Regulatório",
         "Exposição de dados pessoais de colaboradores ou clientes por falha de acesso ou integração — multa ANPD de até 2% do faturamento.",
         "TI-001",(1,3),(5,5)),
        ("Ataque ransomware a sistema crítico",
         "Operacional","Externo",
         "Infecção por ransomware em servidor SAP ou banco de dados crítico — risco de parada total e perda de dados.",
         "TI-002",(1,2),(5,5)),
        ("Sistema ERP (SAP) indisponível em horário de produção",
         "Operacional","Interno",
         "Indisponibilidade do SAP por falha de infraestrutura Azure ou atualização mal planejada, impedindo registros de produção e faturamento.",
         "TI-003",(1,3),(4,5)),
        ("Acesso privilegiado sem revisão periódica",
         "Conformidade","Interno",
         "Perfis de acesso SAP com permissões elevadas não revisados semestralmente — risco SOX e de fraude interna.",
         "TI-004",(3,4),(3,4)),
        ("Backup de sistemas críticos sem teste de restore",
         "Operacional","Interno",
         "Rotina de backup executada sem validação de integridade — em caso de incidente, restauração pode falhar.",
         "TI-005",(2,4),(4,5)),
        ("Shadow IT — sistemas não homologados em uso",
         "Conformidade","Interno",
         "Colaboradores utilizando ferramentas SaaS não aprovadas pela TI para processar dados corporativos sensíveis.",
         "TI-006",(4,5),(2,3)),
    ],

    "Recursos Humanos": [
        ("Alto turnover em área operacional crítica",
         "Operacional","Interno",
         "Saída frequente de colaboradores em funções-chave da produção gerando perda de conhecimento e custo de reposição elevado.",
         "HR-007",(3,4),(3,4)),
        ("Processo trabalhista por conduta inadequada",
         "Conformidade","Interno",
         "Reclamação trabalhista por assédio, horas extras não pagas ou demissão indevida — risco financeiro e reputacional.",
         "HR-008",(2,4),(3,4)),
        ("Folha de pagamento com erros de cálculo SAP HCM",
         "Financeiro","Interno",
         "Inconsistência no cálculo de benefícios, horas extras ou verbas rescisórias no SAP HCM gerando passivo trabalhista.",
         "HR-009",(2,3),(3,4)),
        ("Ausência de plano de sucessão para cargos críticos",
         "Estratégico","Interno",
         "Cargos de liderança e especialistas-chave sem sucessor mapeado — risco de continuidade operacional em caso de saída.",
         "HR-010",(3,4),(3,4)),
        ("Pesquisa de clima com engajamento crítico",
         "Reputacional","Interno",
         "Resultado de pesquisa de clima abaixo do limiar mínimo em área crítica — risco de saída em massa e impacto na marca empregadora.",
         "HR-011",(2,3),(3,4)),
    ],

    "Gestão Corporativa": [
        ("Decisão estratégica sem análise de risco formal",
         "Estratégico","Interno",
         "Aprovação de projeto de expansão, aquisição ou parceria sem análise de risco estruturada pelo Comitê de Riscos.",
         "CORP-001",(2,3),(4,5)),
        ("Ausência de canal de denúncias estruturado",
         "Conformidade","Interno",
         "Empresa sem mecanismo formal e anônimo de reporte de condutas inadequadas — risco de não detecção de fraudes e desvios.",
         "CORP-002",(2,3),(3,4)),
        ("Mapa de riscos corporativo não atualizado no ciclo anual",
         "Conformidade","Interno",
         "Ciclo anual de revisão do mapa de riscos não concluído dentro do prazo definido pela política de GRC.",
         "CORP-003",(2,4),(2,3)),
        ("Não conformidade em auditoria de certificação corporativa",
         "Reputacional","Regulatório",
         "Achados críticos em auditoria externa ISO ou de cliente estratégico com risco de suspensão de certificado.",
         "CORP-004",(1,2),(4,5)),
        ("Ausência de plano de continuidade de negócios (BCP)",
         "Estratégico","Interno",
         "Empresa sem plano formalizado de continuidade para cenários críticos — pandemia, desastre natural, falha de TI.",
         "CORP-005",(1,2),(5,5)),
    ],
}

# ── Controles por categoria de risco ─────────────────────────────────────────

CONTROLS_BY_CATEGORY = {
    "Operacional": [
        ("Procedimento Operacional Padrão (POP) no SAP", "Preventivo"),
        ("Monitoramento de OEE em tempo real — Power BI", "Detectivo"),
        ("Inspeção periódica de equipamentos", "Preventivo"),
        ("Alarme de parâmetro fora de spec — SCADA", "Detectivo"),
    ],
    "SST": [
        ("Sistema de Permissão de Trabalho digital", "Preventivo"),
        ("Treinamento NR obrigatório com registro no SAP HR", "Preventivo"),
        ("Auditoria comportamental mensal", "Detectivo"),
        ("Inspeção de EPI com checklist Azure Forms", "Detectivo"),
    ],
    "Conformidade": [
        ("Calendário de obrigações legais no Power Automate", "Preventivo"),
        ("Auditoria interna trimestral", "Detectivo"),
        ("Controle de documentos no SharePoint", "Preventivo"),
        ("Alerta automático de vencimento — Power Automate", "Detectivo"),
    ],
    "Financeiro": [
        ("Controle de alçadas no SAP FI/SRM", "Preventivo"),
        ("Conciliação bancária automatizada SAP", "Detectivo"),
        ("Auditoria de Compliance semestral", "Detectivo"),
        ("Segregação de funções no SAP (SoD)", "Preventivo"),
    ],
    "Estratégico": [
        ("Comitê de Riscos trimestral", "Preventivo"),
        ("Análise de cenários no planejamento estratégico", "Preventivo"),
        ("Monitoramento de KRIs no Power BI", "Detectivo"),
    ],
    "Reputacional": [
        ("Gestão de reclamações no SAP CRM", "Detectivo"),
        ("Monitoramento de redes sociais", "Detectivo"),
        ("Política de comunicação de crise", "Preventivo"),
    ],
}

# ── Causas raiz — temáticas por categoria ────────────────────────────────────

ROOT_CAUSES = {
    "Operacional":   ["Falha de equipamento","Procedimento desatualizado","Falta de treinamento","Planejamento inadequado","Sobrecarga de trabalho"],
    "SST":           ["Comportamento inseguro","Ausência de EPI","Supervisão inadequada","Falta de treinamento","Condição insegura não corrigida"],
    "Conformidade":  ["Controle interno ineficaz","Falta de monitoramento","Desconhecimento da norma","Processo manual sem automação"],
    "Financeiro":    ["Controle de alçada insuficiente","Segregação de funções inadequada","Processo manual suscetível a erro"],
    "Estratégico":   ["Decisão sem análise estruturada","Monitoramento inadequado de KRIs","Falta de governança de riscos"],
    "Reputacional":  ["Falha de comunicação","Processo de atendimento deficiente","Não conformidade de produto/serviço"],
}

# ── Ações de melhoria por categoria ──────────────────────────────────────────

ACTIONS_BY_CATEGORY = {
    "Operacional":   [
        "Revisar e atualizar POP no SAP com nova versão aprovada",
        "Implementar alerta automático no Power Automate para desvio de parâmetro",
        "Realizar treinamento prático com registro no SAP HR",
        "Incluir item no plano de manutenção preventiva SAP PM",
        "Criar dashboard de acompanhamento em Power BI",
    ],
    "SST":           [
        "Reforçar treinamento de SST com registro obrigatório no SAP HR",
        "Implementar checklist digital de inspeção via Azure Forms",
        "Emitir Permissão de Trabalho para a atividade identificada",
        "Realizar DDS (Diálogo Diário de Segurança) sobre o tema",
        "Revisar APR (Análise Preliminar de Risco) da atividade",
    ],
    "Conformidade":  [
        "Configurar alerta de vencimento no Power Automate (30 dias antes)",
        "Atualizar documento no SharePoint e comunicar às áreas",
        "Agendar auditoria interna para verificação de conformidade",
        "Contratar consultoria especializada para adequação normativa",
        "Registrar obrigação no calendário de Compliance corporativo",
    ],
    "Financeiro":    [
        "Revisar perfis de acesso SAP e segregação de funções (SoD)",
        "Implementar aprovação de segunda alçada no SAP SRM",
        "Automatizar conciliação via SAP com relatório Power BI",
        "Realizar auditoria de Compliance nos processos financeiros",
        "Atualizar política de compras e comunicar gestores",
    ],
    "Estratégico":   [
        "Incluir análise de risco formal no processo de aprovação do Comitê",
        "Criar KRI de monitoramento e incluir no dashboard Power BI",
        "Realizar workshop de risk assessment com lideranças da área",
        "Atualizar mapa de riscos corporativo na próxima revisão anual",
    ],
    "Reputacional":  [
        "Implementar SLA de resposta a cliente no SAP CRM",
        "Criar protocolo de gestão de crise e comunicação",
        "Treinar equipe de atendimento em gestão de conflitos",
        "Monitorar NPS mensalmente com dashboard Power BI",
    ],
}

CAPTURE_CHANNELS = ["Azure Forms", "SAP", "E-mail", "Auditoria", "Manual"]
CAPTURE_WEIGHTS  = [0.40, 0.25, 0.15, 0.15, 0.05]   # Azure Forms é o canal principal

AUTOMATION_TOOLS = ["Power Automate", "SAP GRC", "Azure Logic Apps", None, None]


# ── Funções auxiliares ────────────────────────────────────────────────────────

def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))

def calc_level(score: int) -> str:
    if score <= 4:  return "Baixo"
    if score <= 9:  return "Médio"
    if score <= 16: return "Alto"
    return "Crítico"

def calc_response(level: str) -> str:
    return {"Baixo": random.choice(["Aceitar","Aceitar","Mitigar"]),
            "Médio": random.choice(["Mitigar","Mitigar","Aceitar"]),
            "Alto":  random.choice(["Mitigar","Evitar"]),
            "Crítico": "Evitar"}[level]

def weighted_choice(items, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    cum = 0
    for item, w in zip(items, weights):
        cum += w
        if r <= cum:
            return item
    return items[-1]


# ── Geração principal ─────────────────────────────────────────────────────────

def generate(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()

    today = date.today()
    start_date = date(2023, 1, 1)

    # 1. Áreas ─────────────────────────────────────────────────────────────────
    area_ids   = {}
    area_cats  = {}   # area_name → lista de categorias dos riscos

    for name, dept, director, manager in AREAS:
        cur.execute(
            "INSERT INTO areas (name, department, director, manager) VALUES (?,?,?,?)",
            (name, dept, director, manager)
        )
        area_ids[name] = cur.lastrowid
    conn.commit()

    # 2. Riscos ────────────────────────────────────────────────────────────────
    risk_meta = []   # (risk_id, area_id, risk_level, risk_category)

    for area_name, templates in RISK_TEMPLATES.items():
        area_id = area_ids[area_name]
        for tpl in templates:
            title, cat, src, desc, sap_id, p_range, i_range = tpl
            prob   = random.randint(*p_range)
            impact = random.randint(*i_range)
            score  = prob * impact
            level  = calc_level(score)
            ident  = rand_date(start_date, date(2024, 6, 1))

            cur.execute("""
                INSERT INTO risks
                (area_id, title, description, risk_category, risk_source,
                 probability, impact, risk_score, risk_level, risk_response,
                 within_appetite, owner, status, identified_at, next_review, sap_process_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                area_id, title, desc, cat, src,
                prob, impact, score, level, calc_response(level),
                1 if level in ("Baixo","Médio") and random.random() > 0.3 else 0,
                random.choice(OWNERS), "Ativo",
                str(ident), str(ident + timedelta(days=180)), sap_id
            ))
            rid = cur.lastrowid
            risk_meta.append((rid, area_id, level, cat))

    conn.commit()
    print(f"✅ Riscos: {len(risk_meta)} registrados em {len(AREAS)} áreas")

    # 3. Controles ─────────────────────────────────────────────────────────────
    n_controls = 0
    for rid, area_id, level, cat in risk_meta:
        controls = CONTROLS_BY_CATEGORY.get(cat, CONTROLS_BY_CATEGORY["Operacional"])
        for ctrl_name, ctrl_type in random.sample(controls, min(2, len(controls))):
            test_d = rand_date(date(2023, 6, 1), today)
            is_auto = 1 if "Power Automate" in ctrl_name or "SAP" in ctrl_name or "Power BI" in ctrl_name else 0
            auto_tool = "Power Automate" if "Power Automate" in ctrl_name else ("SAP" if "SAP" in ctrl_name else None)
            cur.execute("""
                INSERT INTO risk_controls
                (risk_id, control_name, control_type, description,
                 effectiveness, is_automated, automation_tool,
                 test_date, next_review, responsible)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                rid, ctrl_name, ctrl_type,
                f"Controle aplicado ao processo {area_id} — avaliado em {test_d}.",
                random.choice(["Eficaz","Eficaz","Parcial","Ineficaz"]),
                is_auto, auto_tool,
                str(test_d), str(test_d + timedelta(days=90)),
                random.choice(OWNERS)
            ))
            n_controls += 1
    conn.commit()
    print(f"✅ Controles: {n_controls} registrados")

    # 4. Ocorrências ───────────────────────────────────────────────────────────
    occ_ids  = []
    occ_risk = []   # (occ_id, risk_id, area_id, cat)
    occ_types = ["Incidente","Quase-acidente","Não-conformidade",
                 "Apontamento de auditoria","Desvio de processo","Falha de controle"]

    # distribuição de severidade por nível de risco
    SEV_BY_LEVEL = {
        "Crítico": ["Grave","Gravíssimo","Grave","Moderado"],
        "Alto":    ["Grave","Moderado","Moderado","Grave"],
        "Médio":   ["Moderado","Leve","Leve","Grave"],
        "Baixo":   ["Leve","Leve","Moderado"],
    }

    for _ in range(160):
        rid, area_id, level, cat = random.choice(risk_meta)
        occ_date = rand_date(start_date, today)
        is_recur = 1 if occ_ids and random.random() < 0.22 else 0
        prev_id  = random.choice(occ_ids) if is_recur else None

        cur.execute("""
            INSERT INTO occurrences
            (risk_id, area_id, occurred_at, occurrence_type, severity,
             description, root_cause, root_cause_method,
             is_recurrence, previous_occurrence_id,
             capture_channel, reported_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            rid, area_id, str(occ_date),
            random.choice(occ_types),
            random.choice(SEV_BY_LEVEL[level]),
            f"Ocorrência registrada via {weighted_choice(CAPTURE_CHANNELS, CAPTURE_WEIGHTS)} em {occ_date}.",
            random.choice(ROOT_CAUSES.get(cat, ROOT_CAUSES["Operacional"])),
            random.choice(["5 Porquês","5 Porquês","Ishikawa","FTA","Outro"]),
            is_recur, prev_id,
            weighted_choice(CAPTURE_CHANNELS, CAPTURE_WEIGHTS),
            random.choice(OWNERS)
        ))
        oid = cur.lastrowid
        occ_ids.append(oid)
        occ_risk.append((oid, rid, area_id, cat))

    conn.commit()
    print(f"✅ Ocorrências: {len(occ_ids)} registradas")

    # 5. Planos de ação ────────────────────────────────────────────────────────
    status_pool = ["Aberto","Em andamento","Em andamento","Concluído","Concluído","Vencido"]
    n_actions = 0

    for _ in range(120):
        rid, area_id, level, cat = random.choice(risk_meta)
        oid     = random.choice(occ_ids) if random.random() > 0.3 else None
        opened  = rand_date(start_date, date(2024, 9, 1))
        deadline= opened + timedelta(days=random.randint(15, 90))
        status  = random.choice(status_pool)
        closed  = None
        pct     = 0
        approved = random.choice(OWNERS)

        if status == "Concluído":
            closed = str(deadline - timedelta(days=random.randint(0, 15)))
            pct    = 100
        elif status == "Em andamento":
            pct    = random.randint(20, 80)
        elif status == "Vencido":
            pct    = random.randint(0, 55)

        actions = ACTIONS_BY_CATEGORY.get(cat, ACTIONS_BY_CATEGORY["Operacional"])
        cur.execute("""
            INSERT INTO action_plans
            (risk_id, occurrence_id, action, action_type, responsible,
             area_id, deadline, status, completion_pct,
             approved_by, opened_at, closed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            rid, oid,
            random.choice(actions),
            random.choice(["Corretiva","Corretiva","Preventiva","Melhoria"]),
            random.choice(OWNERS), area_id,
            str(deadline), status, pct,
            approved, str(opened), closed
        ))
        n_actions += 1

    conn.commit()
    print(f"✅ Planos de ação: {n_actions} registrados")

    # 6. Auditorias — 6 tipos, distribuídas pelas áreas ───────────────────────
    audit_config = [
        # (tipo, áreas-alvo, quantidade, score_range)
        ("Interna",                    list(area_ids.values()),           10, (65, 100)),
        ("Regulatória",                [area_ids["Meio Ambiente / ESG"],
                                        area_ids["SST"],
                                        area_ids["Qualidade"]],            8, (60, 98)),
        ("SST",                        [area_ids["SST"],
                                        area_ids["Operações"],
                                        area_ids["Manutenção"]],           6, (62, 97)),
        ("Fornecedores",               [area_ids["Compras e Contratos"],
                                        area_ids["Logística e Suprimentos"]], 6, (60, 95)),
        ("TI / Segurança da Informação",[area_ids["TI e Segurança de Dados"],
                                        area_ids["Financeiro e Compliance"]],  5, (58, 95)),
        ("Processos / Compliance",     [area_ids["Financeiro e Compliance"],
                                        area_ids["Gestão Corporativa"],
                                        area_ids["Recursos Humanos"]],     5, (65, 100)),
    ]

    n_audits = 0
    for audit_type, target_areas, qty, score_range in audit_config:
        for _ in range(qty):
            area_id   = random.choice(target_areas)
            audit_d   = rand_date(start_date, today)
            score     = random.randint(*score_range)
            findings  = max(0, int((100 - score) / 10) + random.randint(-1, 2))
            cur.execute("""
                INSERT INTO audits
                (area_id, audit_type, audit_date, auditor, scope,
                 findings_count, conformity_score, status)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                area_id, audit_type, str(audit_d),
                random.choice(OWNERS),
                f"Auditoria de {audit_type.lower()} — verificação de conformidade e controles internos.",
                findings, score, "Concluída"
            ))
            n_audits += 1

    conn.commit()
    print(f"✅ Auditorias: {n_audits} registradas ({len(audit_config)} tipos)")

    # 7. Histórico de KRIs por mês (últimos 18 meses) ─────────────────────────
    kri_config = [
        # (nome, warn, crit, área_alvo, fonte_dado, direção)
        ("Taxa de reincidência de ocorrências (%)",      15, 25, None,       "Azure Forms",  "up"),
        ("Score médio de risco por área",                12, 18, None,       "Power BI",     "up"),
        ("% Planos de ação vencidos",                    10, 20, None,       "Power Automate","up"),
        ("% Controles eficazes",                         70, 50, None,       "SAP GRC",      "down"),
        ("Tempo médio de fechamento de ação (dias)",     30, 60, None,       "Power Automate","up"),
        ("Score médio de conformidade em auditorias",    75, 60, None,       "Power BI",     "down"),
        ("Nº de riscos críticos sem plano de ação",       0,  2, None,       "Power BI",     "up"),
        ("Taxa de fornecedores sem homologação (%)",     10, 20,
         area_ids["Compras e Contratos"],                                     "SAP MM",       "up"),
        ("% Treinamentos NR vencidos",                   10, 20,
         area_ids["SST"],                                                    "SAP HR",       "up"),
        ("LTIF (Índice de freq. de lesões com afastamento)",2, 5,
         area_ids["SST"],                                                    "SAP HR",       "up"),
        ("% Contratos vencidos em uso",                   5, 15,
         area_ids["Compras e Contratos"],                                     "SAP MM",       "up"),
        ("Nº de incidentes de segurança da informação",   2,  5,
         area_ids["TI e Segurança de Dados"],                                "Azure Sentinel","up"),
    ]

    n_kris = 0
    for months_back in range(18, 0, -1):
        period_date = today.replace(day=1) - timedelta(days=months_back * 30)
        period      = period_date.strftime("%Y-%m")

        for kri_name, warn, crit, area_id, source, direction in kri_config:
            # simular tendência com ruído
            base = warn * 0.8 if direction == "up" else warn * 1.2
            trend_factor = 1 + (18 - months_back) * 0.01 * random.uniform(-1, 1)
            value = max(0, base * trend_factor + random.uniform(-base * 0.2, base * 0.2))
            value = round(value, 1)

            if direction == "up":
                status = "Crítico" if value > crit else "Atenção" if value > warn else "Normal"
            else:
                status = "Crítico" if value < crit else "Atenção" if value < warn else "Normal"

            cur.execute("""
                INSERT INTO kri_history
                (kri_name, area_id, period, value, threshold_warn, threshold_crit,
                 status, data_source)
                VALUES (?,?,?,?,?,?,?,?)
            """, (kri_name, area_id, period, value, warn, crit, status, source))
            n_kris += 1

    conn.commit()
    print(f"✅ KRI History: {n_kris} pontos registrados ({len(kri_config)} KRIs × 18 meses)")

    # Resumo final
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  BANCO GERADO — Sistema de Gestão de Riscos Corporativos    ║
╠══════════════════════════════════════════════════════════════╣
║  Áreas:          {len(AREAS):>4}  (11 áreas corporativas)            ║
║  Riscos:         {len(risk_meta):>4}  (por área, temáticos e realistas)  ║
║  Controles:      {n_controls:>4}  (incluindo automações SAP/Power Automate)  ║
║  Ocorrências:   {len(occ_ids):>4}  (multi-canal: Azure Forms, SAP...)  ║
║  Planos de ação:{n_actions:>4}  (com % conclusão e aprovação)       ║
║  Auditorias:     {n_audits:>4}  (6 tipos distintos)                ║
║  KRI History:   {n_kris:>4}  (12 KRIs × 18 meses)               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    conn.close()


if __name__ == "__main__":
    generate()
