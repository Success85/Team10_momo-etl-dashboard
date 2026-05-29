from config import BATCH_SIZE, INITIALIZE_DB, LOG_PATH, OUTPUT_PATH, XML_PATH
from load_db import import_sms_to_database


def main() -> None:
    summary = import_sms_to_database(
        xml_path=XML_PATH,
        output_path=OUTPUT_PATH,
        batch_size=BATCH_SIZE,
        log_path=LOG_PATH,
        initialize_db=INITIALIZE_DB,
    )
    print(summary)


if __name__ == "__main__":
    main()
