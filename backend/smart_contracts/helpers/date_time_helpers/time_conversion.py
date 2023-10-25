import base64
from datetime import datetime


def convert_to_timestamp(date_time: str) -> int:
    date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    timestamp = int(date_time.timestamp())
    return timestamp


def timestamp_from_log_to_time(encoded_time_log: str) -> datetime:
    decoded_bytes = base64.b64decode(encoded_time_log)
    timestamp = int.from_bytes(decoded_bytes, byteorder='big')
    date_time = datetime.utcfromtimestamp(timestamp)

    print("Converted Date and Time:", date_time)
    return date_time
