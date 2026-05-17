-- MoMo SMS Data Processing System

CREATE DATABASE IF NOT EXISTS momo_sms_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE momo_sms_db;

-- Transaction types/ categories lookup
CREATE TABLE transaction_categories (
    category_id     INT UNSIGNED    NOT NULL AUTO_INCREMENT  COMMENT 'Category/ transaction type primary key',
    category_name   VARCHAR(50)     NOT NULL                 COMMENT 'Human-readable transaction type name',
    category_code   VARCHAR(20)     NOT NULL                 COMMENT 'Short code used in processing logic',
    description     VARCHAR(255)                             COMMENT 'Detailed description of the transaction type',
    is_debit        TINYINT(1)      NOT NULL DEFAULT 1       COMMENT '1 = money leaves wallet, 0 = money enters wallet',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_transaction_categories PRIMARY KEY (category_id),
    CONSTRAINT uq_category_code          UNIQUE (category_code),
    CONSTRAINT uq_category_name          UNIQUE (category_name),
    CONSTRAINT chk_is_debit              CHECK (is_debit IN (0, 1))
);

-- account owner and all counterparties
CREATE TABLE users (
    user_id         INT UNSIGNED    NOT NULL AUTO_INCREMENT  COMMENT 'User primary key',
    full_name       VARCHAR(100)    NOT NULL                 COMMENT 'Full name as it appears in SMS body',
    phone_number    VARCHAR(20)                              COMMENT 'Phone number with country code e.g. +250791234567',
    user_type       ENUM('account_holder', 'counterparty', 'merchant', 'bank') NOT NULL DEFAULT 'counterparty' COMMENT 'Role of this user in the system',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_users          PRIMARY KEY (user_id),
    CONSTRAINT chk_phone_format  CHECK (phone_number IS NULL OR phone_number REGEXP '^[+]?[0-9]{9,15}$')
);

-- Raw SMS data records data from XML file
CREATE TABLE sms_messages (
    sms_id          INT UNSIGNED    NOT NULL AUTO_INCREMENT  COMMENT 'Message(sms) primary key',
    protocol        TINYINT         NOT NULL DEFAULT 0       COMMENT 'SMS protocol code from XML attribute',
    address         VARCHAR(50)     NOT NULL                 COMMENT 'Sender address, always M-Money for MoMo SMS',
    date_received   BIGINT UNSIGNED NOT NULL                 COMMENT 'Unix timestamp in milliseconds from XML date attribute',
    date_sent       BIGINT UNSIGNED                          COMMENT 'Unix timestamp in milliseconds from XML date_sent attribute',
    body            TEXT            NOT NULL                 COMMENT 'Full raw SMS body text',
    service_center  VARCHAR(20)                              COMMENT 'SMS service centre number e.g. +250788110381',
    read_status     TINYINT(1)      NOT NULL DEFAULT 0       COMMENT '1 = read, 0 = unread',
    sub_id          TINYINT                                  COMMENT 'SIM subscription ID from device',
    readable_date   VARCHAR(60)                              COMMENT 'Human-readable date string from XML',
    is_processed    TINYINT(1)      NOT NULL DEFAULT 0       COMMENT '1 = parsed into transactions table, 0 = pending',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_sms_messages   PRIMARY KEY (sms_id),
    CONSTRAINT chk_read_status   CHECK (read_status IN (0, 1)),
    CONSTRAINT chk_is_processed  CHECK (is_processed IN (0, 1))
);

-- parsed transaction records
CREATE TABLE transactions (
    transaction_id      INT UNSIGNED    NOT NULL AUTO_INCREMENT  COMMENT 'Transaction primary key',
    external_tx_id      VARCHAR(30)                              COMMENT 'TxId or Financial Transaction Id from SMS body',
    category_id         INT UNSIGNED    NOT NULL                 COMMENT 'FK to transaction_categories',
    sms_id              INT UNSIGNED                             COMMENT 'FK to source sms_messages record, nullable in case SMS is deleted',
    amount              DECIMAL(15, 2)  NOT NULL                 COMMENT 'Transaction amount in RWF',
    fee                 DECIMAL(15, 2)  NOT NULL DEFAULT 0.00    COMMENT 'Transaction fee in RWF',
    balance_after       DECIMAL(15, 2)  NOT NULL                 COMMENT 'Wallet balance immediately after transaction',
    transaction_date    DATETIME        NOT NULL                 COMMENT 'Timestamp of the actual financial event',
    status              ENUM('completed', 'pending', 'failed', 'reversed') NOT NULL DEFAULT 'completed' COMMENT 'Current state of the transaction',
    notes               VARCHAR(500)                             COMMENT 'Optional sender message or processing note',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_transactions           PRIMARY KEY (transaction_id),
    CONSTRAINT uq_external_tx_id         UNIQUE (external_tx_id),
    CONSTRAINT fk_transactions_category  FOREIGN KEY (category_id) REFERENCES transaction_categories(category_id) ON UPDATE CASCADE,
    CONSTRAINT fk_transactions_sms       FOREIGN KEY (sms_id) REFERENCES sms_messages(sms_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_amount_positive       CHECK (amount > 0),
    CONSTRAINT chk_fee_non_negative      CHECK (fee >= 0),
    CONSTRAINT chk_balance_non_negative  CHECK (balance_after >= 0)
);

-- junction table: resolves M:N between transactions and users
CREATE TABLE transaction_participants (
    participation_id    INT UNSIGNED    NOT NULL AUTO_INCREMENT  COMMENT 'Transaction initiators primary key',
    transaction_id      INT UNSIGNED    NOT NULL                 COMMENT 'FK to transactions',
    user_id             INT UNSIGNED    NOT NULL                 COMMENT 'FK to users',
    role                ENUM('sender', 'receiver') NOT NULL      COMMENT 'Role of this user in the transaction',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_transaction_participants PRIMARY KEY (participation_id),
    CONSTRAINT fk_tp_transaction           FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tp_user                  FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE,
    CONSTRAINT uq_transaction_role         UNIQUE (transaction_id, role)
);

-- processing audit log
CREATE TABLE system_logs (
    log_id          INT UNSIGNED    NOT NULL AUTO_INCREMENT  COMMENT 'System logs/ process audit primary key',
    transaction_id  INT UNSIGNED                             COMMENT 'FK to related transaction, nullable for system-level events',
    sms_id          INT UNSIGNED                             COMMENT 'FK to related SMS record, nullable',
    log_level       ENUM('INFO', 'WARNING', 'ERROR', 'DEBUG') NOT NULL DEFAULT 'INFO' COMMENT 'Severity level of the log entry',
    event_type      VARCHAR(50)     NOT NULL                 COMMENT 'Processing stage: IMPORT, PARSE, VALIDATE, CRUD, SYSTEM',
    message         TEXT            NOT NULL                 COMMENT 'Detailed log message',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_system_logs        PRIMARY KEY (log_id),
    CONSTRAINT fk_logs_transaction   FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_logs_sms           FOREIGN KEY (sms_id) REFERENCES sms_messages(sms_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_event_type        CHECK (event_type IN ('IMPORT', 'PARSE', 'VALIDATE', 'CRUD', 'SYSTEM'))
);

-- indexes
CREATE INDEX idx_transactions_date     ON transactions(transaction_date);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_status   ON transactions(status);
CREATE INDEX idx_transactions_amount   ON transactions(amount);
CREATE INDEX idx_sms_is_processed      ON sms_messages(is_processed);
CREATE INDEX idx_sms_date_received     ON sms_messages(date_received);
CREATE INDEX idx_tp_user_id            ON transaction_participants(user_id);
CREATE INDEX idx_tp_transaction_id     ON transaction_participants(transaction_id);
CREATE INDEX idx_logs_level            ON system_logs(log_level);
CREATE INDEX idx_logs_event_type       ON system_logs(event_type);
CREATE INDEX idx_logs_created_at       ON system_logs(created_at);
CREATE INDEX idx_users_full_name       ON users(full_name);

-- sample data that shows what is the raw data looks like
INSERT INTO transaction_categories (category_name, category_code, description, is_debit) VALUES
('Incoming Money',   'INCOMING',     'Money received into wallet from another MoMo user',       0),
('Merchant Payment', 'MERCHANT_PAY', 'Payment to a registered MoMo merchant or agent code',    1),
('Bank Deposit',     'BANK_DEP',     'Cash deposited from a bank account into MoMo wallet',     0),
('Mobile Transfer',  'MOB_TRANSFER', 'Direct transfer sent to another mobile number via MoMo',  1),
('Airtime Purchase', 'AIRTIME',      'Airtime or data bundle purchased through MoMo wallet',    1),
('Cash Withdrawal',  'WITHDRAWAL',   'Cash withdrawn from MoMo wallet at an agent',             1),
('Utility Payment',  'UTILITY',      'Bill payment for utilities such as electricity or water', 1);

INSERT INTO users (full_name, phone_number, user_type) VALUES
('Account Owner', '+250791234567', 'account_holder'),
('Jane Smith',     NULL,           'merchant'),
('Samuel Carter', '+250791666666', 'counterparty'),
('Alex Doe',       NULL,           'merchant'),
('Robert Brown',   NULL,           'merchant'),
('Linda Green',    NULL,           'merchant'),
('MTN Bank',       NULL,           'bank');

INSERT INTO sms_messages (protocol, address, date_received, date_sent, body, service_center, read_status, sub_id, readable_date, is_processed) VALUES
(0, 'M-Money', 1715351458724, 1715351451000, 'You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. Message from sender: . Your new balance:2000 RWF. Financial Transaction Id: 76662021700.', '+250788110381', 1, 6, '10 May 2024 4:30:58 PM', 1),
(0, 'M-Money', 1715351506754, 1715351498000, 'TxId: 73214484437. Your payment of 1,000 RWF to Jane Smith 12845 has been completed at 2024-05-10 16:31:39. Your new balance: 1,000 RWF. Fee was 0 RWF.', '+250788110381', 1, 6, '10 May 2024 4:31:46 PM', 1),
(0, 'M-Money', 1715445936412, 1715445829000, '*113*R*A bank deposit of 40000 RWF has been added to your mobile money account at 2024-05-11 18:43:49. Your NEW BALANCE :40400 RWF. Cash Deposit::CASH::::0::250795963036.', '+250788110381', 1, 6, '11 May 2024 6:45:36 PM', 1),
(0, 'M-Money', 1715446129409, 1715446122000, 'TxId: 17818959211. Your payment of 2,000 RWF to Samuel Carter 14965 has been completed at 2024-05-11 18:48:42. Your new balance: 38,400 RWF. Fee was 0 RWF.', '+250788110381', 1, 6, '11 May 2024 6:48:49 PM', 1),
(0, 'M-Money', 1715452495316, 1715452487000, '*165*S*10000 RWF transferred to Samuel Carter (250791666666) from 36521838 at 2024-05-11 20:34:47. Fee was: 100 RWF. New balance: 28300 RWF.', '+250788110381', 1, 6, '11 May 2024 8:34:55 PM', 1),
(0, 'M-Money', 1715506895734, 1715506888000, '*162*TxId:13913173274*S*Your payment of 2000 RWF to Airtime with token has been completed at 2024-05-12 11:41:28. Fee was 0 RWF. Your new balance: 25280 RWF.', '+250788110381', 1, 6, '12 May 2024 11:41:35 AM', 1),
(0, 'M-Money', 1715513180213, 1715513173000, 'TxId: 45434420466. Your payment of 10,900 RWF to Jane Smith 59543 has been completed at 2024-05-12 13:26:13. Your new balance: 14,380 RWF. Fee was 0 RWF.', '+250788110381', 1, 6, '12 May 2024 1:26:20 PM', 1),
(0, 'M-Money', 1715513672603, 1715513665000, 'TxId: 82113964658. Your payment of 3,500 RWF to Alex Doe 43810 has been completed at 2024-05-12 13:34:25. Your new balance: 10,880 RWF. Fee was 0 RWF.', '+250788110381', 1, 6, '12 May 2024 1:34:32 PM', 1),
(0, 'M-Money', 1715529514868, 1715529495000, 'TxId: 26614842768. Your payment of 1,000 RWF to Robert Brown 41193 has been completed at 2024-05-12 17:58:15. Your new balance: 9,880 RWF. Fee was 0 RWF.', '+250788110381', 1, 6, '12 May 2024 5:58:34 PM', 1),
(0, 'M-Money', 1715530145794, 1715530138000, 'TxId: 70497610538. Your payment of 5,000 RWF to Linda Green 75028 has been completed at 2024-05-12 18:08:58. Your new balance: 4,880 RWF. Fee was 0 RWF.', '+250788110381', 1, 6, '12 May 2024 6:09:05 PM', 1);

INSERT INTO transactions (external_tx_id, category_id, sms_id, amount, fee, balance_after, transaction_date, status, notes) VALUES
('76662021700',  1,  1,  2000.00,    0.00,   2000.00, '2024-05-10 16:30:51', 'completed', NULL),
('73214484437',  2,  2,  1000.00,    0.00,   1000.00, '2024-05-10 16:31:39', 'completed', NULL),
('BANK_DEP_001', 3,  3, 40000.00,    0.00,  40400.00, '2024-05-11 18:43:49', 'completed', 'Cash deposit via MTN Bank agent 250795963036'),
('17818959211',  2,  4,  2000.00,    0.00,  38400.00, '2024-05-11 18:48:42', 'completed', NULL),
('MOB_TRF_001',  4,  5, 10000.00,  100.00,  28300.00, '2024-05-11 20:34:47', 'completed', NULL),
('13913173274',  5,  6,  2000.00,    0.00,  25280.00, '2024-05-12 11:41:28', 'completed', NULL),
('45434420466',  2,  7, 10900.00,    0.00,  14380.00, '2024-05-12 13:26:13', 'completed', NULL),
('82113964658',  2,  8,  3500.00,    0.00,  10880.00, '2024-05-12 13:34:25', 'completed', NULL),
('26614842768',  2,  9,  1000.00,    0.00,   9880.00, '2024-05-12 17:58:15', 'completed', NULL),
('70497610538',  2, 10,  5000.00,    0.00,   4880.00, '2024-05-12 18:08:58', 'completed', NULL);

INSERT INTO transaction_participants (transaction_id, user_id, role) VALUES
(1,  2, 'sender'),   (1,  1, 'receiver'),
(2,  1, 'sender'),   (2,  2, 'receiver'),
(3,  7, 'sender'),   (3,  1, 'receiver'),
(4,  1, 'sender'),   (4,  3, 'receiver'),
(5,  1, 'sender'),   (5,  3, 'receiver'),
(6,  1, 'sender'),
(7,  1, 'sender'),   (7,  2, 'receiver'),
(8,  1, 'sender'),   (8,  4, 'receiver'),
(9,  1, 'sender'),   (9,  5, 'receiver'),
(10, 1, 'sender'),   (10, 6, 'receiver');

INSERT INTO system_logs (transaction_id, sms_id, log_level, event_type, message) VALUES
(NULL, NULL, 'INFO',    'IMPORT',   'XML backup imported successfully. Total SMS records in file: 1693.'),
(NULL, 1,    'INFO',    'PARSE',    'sms_id=1 parsed as INCOMING transaction. TxId: 76662021700.'),
(NULL, 2,    'INFO',    'PARSE',    'sms_id=2 parsed as MERCHANT_PAY transaction. TxId: 73214484437.'),
(NULL, 3,    'INFO',    'PARSE',    'sms_id=3 parsed as BANK_DEP transaction. No TxId, synthetic ID assigned.'),
(NULL, 5,    'WARNING', 'PARSE',    'sms_id=5 used non-standard *165*S* format. Fallback parser applied successfully.'),
(1,   NULL,  'INFO',    'VALIDATE', 'Transaction 76662021700: all FK constraints and balance checks passed.'),
(2,   NULL,  'INFO',    'VALIDATE', 'Transaction 73214484437: all FK constraints and balance checks passed.'),
(NULL, NULL, 'ERROR',   'PARSE',    'Could not identify transaction type for 3 SMS records. Flagged for manual review.'),
(3,   NULL,  'INFO',    'CRUD',     'Bank deposit BANK_DEP_001 inserted into transactions table.'),
(NULL, NULL, 'INFO',    'IMPORT',   'Batch processing complete. 10 records processed: 9 passed, 1 WARNING, 0 failures.');

-- views
CREATE VIEW vw_transaction_details AS
SELECT
    t.transaction_id,
    t.external_tx_id,
    tc.category_name,
    tc.category_code,
    tc.is_debit,
    t.amount,
    t.fee,
    (t.amount + t.fee) AS total_deducted,
    t.balance_after,
    t.transaction_date,
    t.status,
    t.notes,
    sender.full_name   AS sender_name,
    sender.user_type   AS sender_type,
    receiver.full_name AS receiver_name,
    receiver.user_type AS receiver_type
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
LEFT JOIN transaction_participants tp_s ON t.transaction_id = tp_s.transaction_id AND tp_s.role = 'sender'
LEFT JOIN users sender ON tp_s.user_id = sender.user_id
LEFT JOIN transaction_participants tp_r ON t.transaction_id = tp_r.transaction_id AND tp_r.role = 'receiver'
LEFT JOIN users receiver ON tp_r.user_id = receiver.user_id;

CREATE VIEW vw_spending_by_category AS
SELECT
    tc.category_name,
    tc.is_debit,
    COUNT(t.transaction_id) AS num_transactions,
    SUM(t.amount)           AS total_amount_rwf,
    SUM(t.fee)              AS total_fees_rwf,
    MIN(t.transaction_date) AS first_transaction,
    MAX(t.transaction_date) AS last_transaction
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
GROUP BY tc.category_id, tc.category_name, tc.is_debit
ORDER BY total_amount_rwf DESC;

CREATE VIEW vw_user_transaction_history AS
SELECT
    u.user_id,
    u.full_name,
    u.user_type,
    tp.role,
    t.external_tx_id,
    tc.category_name,
    t.amount,
    t.fee,
    t.transaction_date,
    t.status
FROM users u
JOIN transaction_participants tp ON u.user_id = tp.user_id
JOIN transactions t              ON tp.transaction_id = t.transaction_id
JOIN transaction_categories tc   ON t.category_id = tc.category_id
ORDER BY t.transaction_date DESC;