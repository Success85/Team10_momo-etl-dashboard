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