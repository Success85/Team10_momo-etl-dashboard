Transaction_categories maps to transactionCategory in JSON with fields like category_id, category_name, category_code, is_debit, created_at, updated_at. users maps to user with user_id, full_name, phone_number, account_number, user_type, and timestamps such as created_at and updated_at. 

sms_messages maps to smsMessage with sms_id, protocol, address, date_received,date_sent, body, service_center, sub_id,readable_date and flags like read_status and is_processed. 

Transactions maps to transaction with transaction_id, external_tx_id, amount, fee, catagory_id, sms_id, balance_after, status, notes, and timestamps such as transaction_date, created_at, updated_at.

Transaction_participants maps to transactionParticipant, capturing participation_id, role (sender/receiver), and links to user and transaction. system_logs maps to systemLog with log_id, log_level, event_type, message, created_at, and optional related transaction or sms data. 
 
 Primary keys stay as *_id, and foreign keys become nested objects for API responses and references the objects incase of the schema.