import xml.etree.ElementTree as ET


def load_sms_xml(xml_file_path: str) -> list[dict]:
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    sms_list = []

    for sms in root.findall("sms"):
        sms_data = {
            "protocol": sms.get("protocol"),
            "address": sms.get("address"),
            "date": int(sms.get("date")),
            "type": sms.get("type"),
            "subject": sms.get("subject"),
            "toa": sms.get("toa"),
            "sc_toa": sms.get("sc_toa"),
            "body": sms.get("body"),
            "service_center": sms.get("service_center"),
            "read": int(sms.get("read")),
            "date_sent": int(sms.get("date_sent")),
            "sub_id": int(sms.get("sub_id")),
            "readable_date": sms.get("readable_date"),
            "status": sms.get("status"),
            "locked": sms.get("locked"),
            "contact_name": sms.get("contact_name"),
        }

        sms_list.append(sms_data)

    return sms_list
