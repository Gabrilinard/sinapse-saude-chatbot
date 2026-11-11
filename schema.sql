-- =====================================================================
-- Sinapse Saúde · schema.sql
-- Tabelas + dados FICTÍCIOS para a demonstração (premissa da P1).
-- Os horários são gerados a partir da data atual (CURDATE), então basta
-- rodar este script de novo para ter a agenda das próximas semanas.
-- =====================================================================
SET NAMES utf8mb4;
SET time_zone = '-03:00';  -- horário de Teresina

DROP DATABASE IF EXISTS sinapse;
CREATE DATABASE sinapse CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE sinapse;

-- ---------------------------------------------------------------------
-- Tabelas
-- ---------------------------------------------------------------------
CREATE TABLE pacientes (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    nome             VARCHAR(120) NOT NULL,
    cpf              CHAR(11)     NOT NULL UNIQUE,      -- só dígitos
    data_nascimento  DATE         NOT NULL,
    telefone         VARCHAR(20),
    email            VARCHAR(120),
    convenio         VARCHAR(60),                       -- NULL = particular
    excluido_em      DATETIME NULL
);

CREATE TABLE profissionais (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(120) NOT NULL,
    especialidade   VARCHAR(60)  NOT NULL,
    conselho        VARCHAR(30)  NOT NULL,              -- CRM
    valor_consulta  DECIMAL(8,2) NOT NULL,
    endereco        VARCHAR(200) NOT NULL,
    lat             DECIMAL(9,6) NOT NULL,
    lng             DECIMAL(9,6) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    senha_hash      VARCHAR(100) NOT NULL               -- bcrypt
);

CREATE TABLE profissional_convenios (
    profissional_id INT NOT NULL,
    convenio        VARCHAR(60) NOT NULL,
    PRIMARY KEY (profissional_id, convenio),
    FOREIGN KEY (profissional_id) REFERENCES profissionais(id)
);

CREATE TABLE horarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    profissional_id INT NOT NULL,
    data_hora       DATETIME NOT NULL,
    livre           BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE KEY uq_prof_horario (profissional_id, data_hora),
    FOREIGN KEY (profissional_id) REFERENCES profissionais(id)
);

CREATE TABLE consultas (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id       INT NOT NULL,
    horario_id        INT NOT NULL,
    status            ENUM('agendada','remarcada','cancelada','realizada') NOT NULL DEFAULT 'agendada',
    observacoes       VARCHAR(500),
    lembrete_enviado  BOOLEAN NOT NULL DEFAULT FALSE,   -- usado pelo fluxo do n8n (RF08)
    criado_em         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (horario_id)  REFERENCES horarios(id)
);

CREATE TABLE exames (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id     INT NOT NULL,
    profissional_id INT NOT NULL,
    data            DATE NOT NULL,
    descricao       VARCHAR(500) NOT NULL,
    FOREIGN KEY (paciente_id)     REFERENCES pacientes(id),
    FOREIGN KEY (profissional_id) REFERENCES profissionais(id)
);

CREATE TABLE receitas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id     INT NOT NULL,
    profissional_id INT NOT NULL,
    data            DATE NOT NULL,
    descricao       VARCHAR(500) NOT NULL,
    FOREIGN KEY (paciente_id)     REFERENCES pacientes(id),
    FOREIGN KEY (profissional_id) REFERENCES profissionais(id)
);

CREATE TABLE faq (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    pergunta        VARCHAR(255) NOT NULL,
    resposta        TEXT NOT NULL,
    palavras_chave  VARCHAR(255) NOT NULL
);

CREATE TABLE otp (
    paciente_id    INT PRIMARY KEY,
    codigo_hash    VARCHAR(100) NULL,                   -- bcrypt do código de 6 dígitos
    expira_em      DATETIME NULL,
    tentativas     INT NOT NULL DEFAULT 0,
    bloqueado_ate  DATETIME NULL,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE auditoria (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_tipo  ENUM('paciente','profissional','anonimo','sistema') NOT NULL,
    usuario_id    INT NULL,
    acao          VARCHAR(60) NOT NULL,
    detalhe       VARCHAR(1000),
    data_hora     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE atendimentos_humanos (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id  INT NULL,                              -- pode ser visitante sem login
    motivo       VARCHAR(500) NOT NULL,
    status       ENUM('aberto','em_atendimento','encerrado') NOT NULL DEFAULT 'aberto',
    criado_em    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE solicitacoes_exclusao (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id  INT NOT NULL,
    status       ENUM('pendente','em_analise','concluida','negada') NOT NULL DEFAULT 'pendente',
    criado_em    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

-- ---------------------------------------------------------------------
-- Dados fictícios
-- ---------------------------------------------------------------------

SET @senha = '$2b$10$1a12OmSvGXFSaeW/7b/.EehN6x95NTNeJZ5xbkDoAxXj2Yo.9dvKy';

INSERT INTO profissionais (id, nome, especialidade, conselho, valor_consulta, endereco, lat, lng, email, senha_hash) VALUES
 (1,  'Dra. Ana Carvalho',    'Cardiologia',   'CRM-PI 10001', 180.00, 'Av. Nossa Sra. de Fátima, 1200 - Jóquei',          -5.074500, -42.787500, 'ana.carvalho@sinapse.demo',    @senha),
 (2,  'Dr. Bruno Meireles',   'Cardiologia',   'CRM-PI 10002', 250.00, 'Rua Álvaro Mendes, 900 - Centro',                   -5.089200, -42.801600, 'bruno.meireles@sinapse.demo',  @senha),
 (3,  'Dra. Carla Nogueira',  'Dermatologia',  'CRM-PI 10003', 200.00, 'Av. Dom Severino, 1500 - Fátima',                   -5.071000, -42.796000, 'carla.nogueira@sinapse.demo',  @senha),
 (4,  'Dr. Diego Barros',     'Clínica Geral', 'CRM-PI 10004', 120.00, 'Av. Joaquim Nelson, 300 - Dirceu Arcoverde',        -5.106000, -42.738000, 'diego.barros@sinapse.demo',    @senha),
 (5,  'Dra. Elisa Moura',     'Pediatria',     'CRM-PI 10005', 150.00, 'Av. Universitária, 750 - Ininga',                   -5.058000, -42.792000, 'elisa.moura@sinapse.demo',     @senha),
 (6,  'Dr. Felipe Rocha',     'Ortopedia',     'CRM-PI 10006', 220.00, 'Rua Prof. Joca Vieira, 400 - São Cristóvão',        -5.064000, -42.770000, 'felipe.rocha@sinapse.demo',    @senha),
 (7,  'Dra. Gabriela Lins',   'Ginecologia',   'CRM-PI 10007', 190.00, 'Av. Miguel Rosa, 2100 - Piçarra',                   -5.100000, -42.798000, 'gabriela.lins@sinapse.demo',   @senha),
 (8,  'Dr. Henrique Sales',   'Psiquiatria',   'CRM-PI 10008', 300.00, 'Rua Hugo Napoleão, 650 - Horto Florestal',          -5.062000, -42.781000, 'henrique.sales@sinapse.demo',  @senha),
 (9,  'Dra. Isabela Prado',   'Cardiologia',   'CRM-PI 10009', 160.00, 'Av. Prefeito Freitas Neto, 80 - Mocambinho',        -5.023000, -42.810000, 'isabela.prado@sinapse.demo',   @senha),
 (10, 'Dr. João Teles',       'Oftalmologia',  'CRM-PI 10010', 170.00, 'Av. Barão de Gurgueia, 3000 - Cristo Rei',          -5.117000, -42.807000, 'joao.teles@sinapse.demo',      @senha);

INSERT INTO profissional_convenios (profissional_id, convenio) VALUES
 (1,'Unimed'),(1,'Bradesco Saúde'),
 (2,'Unimed'),(2,'SulAmérica'),
 (3,'Hapvida'),(3,'Unimed'),
 (4,'Hapvida'),(4,'Unimed'),(4,'Bradesco Saúde'),
 (5,'Unimed'),(5,'Hapvida'),
 (6,'SulAmérica'),(6,'Bradesco Saúde'),
 (7,'Unimed'),(7,'Hapvida'),
 (9,'Hapvida'),
 (10,'Unimed'),(10,'SulAmérica');

INSERT INTO pacientes (id, nome, cpf, data_nascimento, telefone, email, convenio) VALUES
 (1, 'Maria da Silva',   '11122233344', '1985-03-12', '86999990001', 'maria.silva@exemplo.demo',   'Unimed'),
 (2, 'José Pereira',     '22233344455', '1972-07-25', '86999990002', 'jose.pereira@exemplo.demo',  'Hapvida'),
 (3, 'Francisca Sousa',  '33344455566', '1990-11-02', '86999990003', 'francisca.sousa@exemplo.demo', NULL),
 (4, 'Antônio Lima',     '44455566677', '1960-01-30', '86999990004', 'antonio.lima@exemplo.demo',  'Bradesco Saúde');

INSERT INTO horarios (profissional_id, data_hora, livre)
WITH RECURSIVE dias AS (
    SELECT 0 AS d
    UNION ALL
    SELECT d + 1 FROM dias WHERE d < 29
)
SELECT p.id,
       TIMESTAMP(CURDATE() + INTERVAL dias.d DAY, MAKETIME(hh.h, 0, 0)),
       (MOD(p.id * 7 + dias.d * 3 + hh.h, 5) <> 0)
FROM profissionais p
CROSS JOIN dias
CROSS JOIN (SELECT 8 AS h UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11
            UNION ALL SELECT 14 UNION ALL SELECT 15 UNION ALL SELECT 16) hh
WHERE DAYOFWEEK(CURDATE() + INTERVAL dias.d DAY) NOT IN (1, 7);

-- Consultas de teste (horários fora da grade: 12h, 13h e 17h)
-- Maria: consulta realizada há 30 dias e outra amanhã com a Dra. Ana
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() - INTERVAL 30 DAY, '09:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (1, LAST_INSERT_ID(), 'realizada', 'Check-up cardiológico de rotina');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '13:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (1, LAST_INSERT_ID(), 'agendada');

-- José: consulta realizada há 60 dias com o Dr. Diego e outra amanhã com a Dra. Ana
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (4, TIMESTAMP(CURDATE() - INTERVAL 60 DAY, '10:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (2, LAST_INSERT_ID(), 'realizada', 'Consulta clínica geral');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '17:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (2, LAST_INSERT_ID(), 'agendada');

-- Francisca: consulta realizada há 45 dias com a Dra. Gabriela
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (7, TIMESTAMP(CURDATE() - INTERVAL 45 DAY, '14:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (3, LAST_INSERT_ID(), 'realizada', 'Consulta ginecológica anual');

-- Antônio: consulta realizada há 90 dias com o Dr. Bruno e outra em 4 dias com o Dr. Felipe
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (2, TIMESTAMP(CURDATE() - INTERVAL 90 DAY, '08:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (4, LAST_INSERT_ID(), 'realizada', 'Acompanhamento de hipertensão');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (6, TIMESTAMP(CURDATE() + INTERVAL 4 DAY, '12:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (4, LAST_INSERT_ID(), 'agendada');

INSERT INTO exames (paciente_id, profissional_id, data, descricao) VALUES
 (1, 1, CURDATE() - INTERVAL 30 DAY, 'Eletrocardiograma: ritmo sinusal, sem alterações'),
 (1, 1, CURDATE() - INTERVAL 28 DAY, 'Perfil lipídico: colesterol LDL levemente elevado'),
 (2, 4, CURDATE() - INTERVAL 60 DAY, 'Hemograma completo: dentro da normalidade'),
 (3, 7, CURDATE() - INTERVAL 45 DAY, 'Citopatológico: resultado normal'),
 (4, 2, CURDATE() - INTERVAL 90 DAY, 'MAPA 24h: média pressórica acima do alvo');

INSERT INTO receitas (paciente_id, profissional_id, data, descricao) VALUES
 (1, 1, CURDATE() - INTERVAL 30 DAY, 'Orientação de dieta e atividade física; retorno em 6 meses'),
 (2, 4, CURDATE() - INTERVAL 60 DAY, 'Vitamina D 7.000 UI, 1 cápsula por semana por 8 semanas'),
 (4, 2, CURDATE() - INTERVAL 90 DAY, 'Losartana 50 mg, 1 comprimido ao dia');

INSERT INTO faq (pergunta, resposta, palavras_chave) VALUES
 ('Quais convênios vocês aceitam?',
  'Trabalhamos com Unimed, Hapvida, Bradesco Saúde e SulAmérica. Cada profissional aceita convênios diferentes; posso filtrar a busca pelo seu convênio. Também há atendimento particular.',
  'convenio convenios plano saude unimed hapvida bradesco sulamerica particular aceita'),
 ('Que documentos devo levar na consulta?',
  'Leve um documento oficial com foto, a carteirinha do convênio (se tiver) e exames anteriores relacionados à consulta.',
  'documento documentos levar rg carteirinha identidade exames anteriores'),
 ('Como faço para cancelar ou remarcar?',
  'Pelo próprio chat, depois de entrar com CPF, data de nascimento e código. Pedimos que cancele com pelo menos 24 horas de antecedência.',
  'cancelar cancelamento remarcar remarcacao desmarcar mudar horario'),
 ('Qual o horário de atendimento?',
  'Os consultórios atendem de segunda a sexta, das 8h às 12h e das 14h às 17h. O chat funciona 24 horas.',
  'horario funcionamento atendimento abre fecha sabado domingo'),
 ('Quanto custa uma consulta?',
  'O valor depende do profissional e da especialidade. Posso buscar profissionais dentro do valor que você quiser pagar.',
  'preco valor custa quanto pagamento pagar consulta particular'),
 ('Como vocês usam meus dados?',
  'Seus dados são usados apenas para atendimento e agendamento (LGPD, art. 6º). Você pode pedir correção ou exclusão pelo chat a qualquer momento.',
  'dados lgpd privacidade excluir exclusao apagar seguranca informacoes'),
 ('E se eu me atrasar?',
  'A tolerância é de 15 minutos. Depois disso a consulta pode ser remarcada, conforme a agenda do profissional.',
  'atraso atrasar atrasado tolerancia chegar tarde'),
 ('Como recebo o lembrete da consulta?',
  'Enviamos um lembrete por e-mail ou mensagem para o contato cadastrado, um dia antes da consulta.',
  'lembrete aviso notificacao mensagem email whatsapp'),
 ('Como entro na minha conta?',
  'Informe seu CPF e sua data de nascimento na barra lateral. Você recebe um código de 6 dígitos válido por 5 minutos.',
  'login entrar conta acesso codigo otp senha cpf');

-- ---------------------------------------------------------------------
-- Agenda cheia da Dra. Ana Carvalho (login de profissional da demo)
-- ---------------------------------------------------------------------
INSERT INTO pacientes (nome, cpf, data_nascimento, telefone, email, convenio) VALUES
 ('Lucas Andrade',   '55566677788', '1995-06-18', '86999990005', 'lucas.andrade@exemplo.demo',   'Unimed'),
 ('Beatriz Rocha',   '66677788899', '1988-09-04', '86999990006', 'beatriz.rocha@exemplo.demo',   'Bradesco Saúde'),
 ('Carlos Mendes',   '77788899900', '1950-02-11', '86999990007', 'carlos.mendes@exemplo.demo',   'Unimed'),
 ('Patrícia Nunes',  '88899900011', '1979-12-23', '86999990008', 'patricia.nunes@exemplo.demo',  NULL);

SET @lucas    = (SELECT id FROM pacientes WHERE cpf = '55566677788');
SET @beatriz  = (SELECT id FROM pacientes WHERE cpf = '66677788899');
SET @carlos   = (SELECT id FROM pacientes WHERE cpf = '77788899900');
SET @patricia = (SELECT id FROM pacientes WHERE cpf = '88899900011');
SET @francisca = 3;
SET @antonio   = 4;

-- Consultas já realizadas (histórico)
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() - INTERVAL 120 DAY, '09:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (@carlos, LAST_INSERT_ID(), 'realizada', 'Primeira consulta: hipertensão e palpitações');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() - INTERVAL 60 DAY, '10:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (@carlos, LAST_INSERT_ID(), 'realizada', 'Retorno: ajuste de medicação');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() - INTERVAL 40 DAY, '14:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (@beatriz, LAST_INSERT_ID(), 'realizada', 'Avaliação pré-operatória');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() - INTERVAL 20 DAY, '15:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (@patricia, LAST_INSERT_ID(), 'realizada', 'Queixa de cansaço aos esforços');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() - INTERVAL 15 DAY, '08:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (@lucas, LAST_INSERT_ID(), 'realizada', 'Check-up para atividade física');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() - INTERVAL 10 DAY, '11:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status, observacoes) VALUES (@antonio, LAST_INSERT_ID(), 'realizada', 'Segunda opinião sobre hipertensão');

-- Próximas consultas (horários fora da grade: 7h, 12h e 18h)
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE(), '18:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@lucas, LAST_INSERT_ID(), 'agendada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '07:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@beatriz, LAST_INSERT_ID(), 'agendada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '12:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@carlos, LAST_INSERT_ID(), 'agendada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 1 DAY, '18:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@antonio, LAST_INSERT_ID(), 'remarcada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 2 DAY, '07:00:00'), 1);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@carlos, LAST_INSERT_ID(), 'cancelada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 2 DAY, '12:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@patricia, LAST_INSERT_ID(), 'agendada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 2 DAY, '18:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@francisca, LAST_INSERT_ID(), 'agendada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 3 DAY, '12:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@lucas, LAST_INSERT_ID(), 'agendada');
INSERT INTO horarios (profissional_id, data_hora, livre) VALUES (1, TIMESTAMP(CURDATE() + INTERVAL 5 DAY, '07:00:00'), 0);
INSERT INTO consultas (paciente_id, horario_id, status) VALUES (@beatriz, LAST_INSERT_ID(), 'agendada');

INSERT INTO exames (paciente_id, profissional_id, data, descricao) VALUES
 (@carlos,   1, CURDATE() - INTERVAL 118 DAY, 'Ecocardiograma: hipertrofia ventricular esquerda leve'),
 (@carlos,   1, CURDATE() - INTERVAL 62 DAY,  'Holter 24h: extrassístoles ventriculares isoladas'),
 (@carlos,   1, CURDATE() - INTERVAL 58 DAY,  'Creatinina e potássio: dentro da normalidade'),
 (@beatriz,  1, CURDATE() - INTERVAL 40 DAY,  'Eletrocardiograma: ritmo sinusal, sem alterações'),
 (@beatriz,  1, CURDATE() - INTERVAL 38 DAY,  'Risco cirúrgico: baixo'),
 (@patricia, 1, CURDATE() - INTERVAL 18 DAY,  'Teste ergométrico: boa capacidade funcional, sem isquemia'),
 (@patricia, 1, CURDATE() - INTERVAL 18 DAY,  'Hemograma: anemia leve (Hb 11,2 g/dL)'),
 (@lucas,    1, CURDATE() - INTERVAL 15 DAY,  'Eletrocardiograma: normal para a idade'),
 (@antonio,  1, CURDATE() - INTERVAL 9 DAY,   'Ecocardiograma: função sistólica preservada');

INSERT INTO receitas (paciente_id, profissional_id, data, descricao) VALUES
 (@carlos,   1, CURDATE() - INTERVAL 120 DAY, 'Losartana 50 mg, 1 comprimido ao dia'),
 (@carlos,   1, CURDATE() - INTERVAL 60 DAY,  'Losartana 100 mg, 1 comprimido ao dia; Atenolol 25 mg, 1 comprimido ao dia'),
 (@patricia, 1, CURDATE() - INTERVAL 20 DAY,  'Sulfato ferroso 40 mg, 1 comprimido ao dia por 90 dias'),
 (@lucas,    1, CURDATE() - INTERVAL 15 DAY,  'Liberado para atividade física; retorno em 1 ano'),
 (@antonio,  1, CURDATE() - INTERVAL 10 DAY,  'Manter Losartana 50 mg; acrescentar Anlodipino 5 mg ao dia');

-- ---------------------------------------------------------------------
-- Usuário da aplicação: só SELECT, INSERT e UPDATE (permissão mínima)
-- ---------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'sinapse_app'@'%' IDENTIFIED BY 'sinapse_app_2026';
GRANT SELECT, INSERT, UPDATE ON sinapse.* TO 'sinapse_app'@'%';
FLUSH PRIVILEGES;
