import json
import math
import random
import sys
import threading
import time
from datetime import datetime


def listen_from_gateway():
    while True:
        line = sys.stdin.readline()
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
            print(
                f"[fake_esp32] Gateway message: {json.dumps(message, ensure_ascii=False)} "
                f"| {datetime.now():%Y-%m-%d %H:%M:%S}",
                file=sys.stderr,
                flush=True,
            )
        except json.JSONDecodeError:
            print(
                f"[fake_esp32] Non-JSON Gateway message: {line}",
                file=sys.stderr,
                flush=True,
            )


def build_sensor_data(count):
    if count % 5 == 0:
        return {
            "ch1": "a",
            "ch2": "b",
        }

    now = time.time()
    ch1 = int(2048 + 1000 * math.sin(2 * math.pi * now))
    ch2 = int(2048 + 800 * math.sin(2 * math.pi * 2 * now) + random.randint(-50, 50))

    return {
        "ch1": ch1,
        "ch2": ch2,
    }


def main():
    threading.Thread(target=listen_from_gateway, daemon=True).start()

    count = 0
    while True:
        count += 1
        print(json.dumps(build_sensor_data(count)), flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
