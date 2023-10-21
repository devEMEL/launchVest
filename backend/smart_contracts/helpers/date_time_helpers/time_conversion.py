import base64
from datetime import datetime
import time


def convert_to_timestamp(date_time: str):
    date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    timestamp = int(date_time.timestamp())
    return timestamp


def timestamp_from_log_to_time(encoded_time_log: str) -> datetime:
    base64_encoded = encoded_time_log
    decoded_bytes = base64.b64decode(base64_encoded)

    timestamp = int.from_bytes(decoded_bytes, byteorder='big')
    date_time = datetime.utcfromtimestamp(timestamp)

    print("Converted Date and Time:", date_time)
    return date_time
