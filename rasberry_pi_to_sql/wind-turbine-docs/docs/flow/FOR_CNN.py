import time
from datetime import datetime


CNN_START_TIME = time.time()


def _base_result(data, cnn_ok, cnn_message, ch1_latest=None, ch2_latest=None, returned_data=None):
    return {
        "created_at": datetime.now(),
        "cnn_ok": cnn_ok,
        "cnn_message": cnn_message,
        "elapsed_time": time.time() - CNN_START_TIME,
        "sample_count": 1,
        "ch1_latest": ch1_latest,
        "ch2_latest": ch2_latest,
        "received_data": data,
        "returned_data": returned_data,
    }


def for_cnn_receive_from_gateway(data):
    if not isinstance(data, dict):
        return _base_result(
            data=data,
            cnn_ok=False,
            cnn_message="FOR_CNN: received data is not a JSON object",
        )

    if "ch1" not in data:
        return _base_result(
            data=data,
            cnn_ok=False,
            cnn_message="FOR_CNN: missing ch1",
            ch2_latest=data.get("ch2"),
        )

    if "ch2" not in data:
        return _base_result(
            data=data,
            cnn_ok=False,
            cnn_message="FOR_CNN: missing ch2",
            ch1_latest=data.get("ch1"),
        )

    if not isinstance(data["ch1"], int):
        return _base_result(
            data=data,
            cnn_ok=False,
            cnn_message="FOR_CNN: ch1 is not int",
            ch2_latest=data.get("ch2") if isinstance(data.get("ch2"), int) else None,
        )

    if not isinstance(data["ch2"], int):
        return _base_result(
            data=data,
            cnn_ok=False,
            cnn_message="FOR_CNN: ch2 is not int",
            ch1_latest=data.get("ch1"),
        )

    returned_data = {
        "ch1": data["ch1"],
        "ch2": data["ch2"],
    }

    return _base_result(
        data=data,
        cnn_ok=True,
        cnn_message="FOR_CNN: data is usable; CNN model is not connected yet",
        ch1_latest=data["ch1"],
        ch2_latest=data["ch2"],
        returned_data=returned_data,
    )
