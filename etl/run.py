from config import BATCH_SIZE, INITIALIZE_DB, LOG_PATH, OUTPUT_PATH, XML_PATH
from load_db import import_sms_to_database

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

XML_PATH = BASE_DIR / "data" / "raw" / "modified_sms_v2.xml"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "dashboard.json"
LOG_PATH = BASE_DIR / "data" / "logs" / "etl.log"
BATCH_SIZE = 300
INITIALIZE_DB = True

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
