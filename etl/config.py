from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

XML_PATH = BASE_DIR / "data" / "raw" / "modified_sms_v2.xml"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "dashboard.json"
LOG_PATH = BASE_DIR / "data" / "logs" / "etl.log"
BATCH_SIZE = 300
INITIALIZE_DB = True