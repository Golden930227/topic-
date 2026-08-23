"""Mr. SU CSV 掃描與資料用途摘要器。

此程式只讀取來源 CSV，不會修改 D:\蘇崇維 內的任何檔案。
執行後會在本檔案旁的 ``output_test`` 資料夾產生：

* csv_catalog.csv：每個 CSV 的用途、欄位、大小與抽樣資訊
* csv_catalog.json：相同內容的完整 JSON 版本
* data_routes.json：網站功能應該讀取哪些 CSV
* samples/*.json：每個 CSV 的前 10 筆資料（避免檔名衝突，以雜湊命名）
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_AI_ROOT = Path(r"D:\蘇崇維\讀取結果")
DEFAULT_CNN_ROOT = Path(r"D:\蘇崇維\蘇格蘭\2024\tblGrid")
DEFAULT_OUTPUT_test_ROOT = Path(__file__).resolve().parent / "output"

# 實體檔案與資料夾只使用穩定 ASCII ID；中文名稱僅存在報告內容中。
PAGE_FOLDER_IDS = {
    "人工智能模型": "ai_model",
    "CNN監測": "cnn_monitor",
}

FEATURE_FOLDER_IDS = {
    "AI目前判斷": "latest_prediction",
    "四分類機率": "class_probabilities",
    "Confidence": "confidence",
    "異常事件": "events",
    "歷史 AI 結果": "prediction_history",
    "資料品質": "data_quality",
    "三相電壓": "three_phase_voltage",
    "三相電流": "three_phase_current",
    "即時曲線": "realtime_chart",
    "Raspberry Pi 狀態": "pi_status",
    "WebSocket 狀態": "websocket_status",
    "即時監測結果": "realtime_result",
    "最近一次模型判斷": "latest_model_result",
    "資料品質／監測狀態": "monitor_status",
}


# 網站每個功能實際需要的資料。source_routes 對應下方自動分類結果；
# columns 是網站讀取時應優先挑出的欄位，不必把整份 CSV 全部交給前端。
PAGE_FEATURES = {
    "人工智能模型": {
        "AI目前判斷": {
            "source_routes": ["ai_predictions"],
            "columns": ["prediction_time", "final_result", "raw_predicted_class_zh"],
            "selection": "依 prediction_time 取最新一筆",
        },
        "四分類機率": {
            "source_routes": ["ai_predictions"],
            "columns": [
                "prediction_time", "probability_normal", "probability_voltage_sag",
                "probability_load_spike", "probability_severe_anomaly",
            ],
            "selection": "目前畫面取最新一筆；趨勢圖可取時間範圍",
        },
        "Confidence": {
            "source_routes": ["ai_predictions"],
            "columns": ["prediction_time", "confidence", "probability_margin", "confidence_passed"],
            "selection": "依 prediction_time 取最新一筆",
        },
        "異常事件": {
            "source_routes": ["ai_events"],
            "columns": [
                "event_group_id", "class_name_zh", "first_detection_time",
                "last_detection_time", "detection_span_minutes", "mean_confidence",
                "maximum_confidence", "source_files",
            ],
            "selection": "依 first_detection_time 由新到舊",
        },
        "歷史 AI 結果": {
            "source_routes": ["ai_predictions"],
            "columns": [
                "prediction_time", "station", "final_result", "confidence",
                "probability_normal", "probability_voltage_sag",
                "probability_load_spike", "probability_severe_anomaly",
            ],
            "selection": "依 prediction_time 查詢指定時間範圍",
        },
        "資料品質": {
            "source_routes": ["data_quality"],
            "columns": [
                "file_name", "status", "original_rows", "valid_rows",
                "removed_invalid_rows", "duplicate_rows_removed", "message",
            ],
            "selection": "顯示全部檔案，或依 file_name 篩選",
        },
    },
    "CNN監測": {
        "三相電壓": {
            "source_routes": ["cnn_measurements"],
            "columns": ["TimeStamp", "Station", "VoltageL1", "VoltageL2", "VoltageL3"],
            "selection": "依 TimeStamp 讀取指定時間範圍",
        },
        "三相電流": {
            "source_routes": ["cnn_measurements"],
            "columns": ["TimeStamp", "Station", "CurrentL1", "CurrentL2", "CurrentL3"],
            "selection": "依 TimeStamp 讀取指定時間範圍",
        },
        "即時曲線": {
            "source_routes": [],
            "columns": [],
            "selection": "目前沒有即時來源；tblGrid CSV 只能做歷史回放",
        },
        "Raspberry Pi 狀態": {
            "source_routes": [],
            "columns": [],
            "selection": "目前缺少 Raspberry Pi 心跳或裝置狀態資料",
        },
        "WebSocket 狀態": {
            "source_routes": [],
            "columns": [],
            "selection": "目前缺少 WebSocket 連線狀態資料",
        },
        "即時監測結果": {
            "source_routes": [],
            "columns": [],
            "selection": "目前只有離線 AI 結果，尚無即時推論資料流",
        },
        "最近一次模型判斷": {
            "source_routes": ["ai_predictions"],
            "columns": ["prediction_time", "final_result", "confidence", "confirmed_event"],
            "selection": "依 prediction_time 取最新一筆（目前是離線結果）",
        },
        "資料品質／監測狀態": {
            "source_routes": ["data_quality"],
            "columns": [
                "file_name", "status", "original_rows", "valid_rows",
                "removed_invalid_rows", "duplicate_rows_removed", "message",
            ],
            "selection": "資料品質可用；即時監測連線狀態目前沒有來源",
        },
    },
}


ROUTE_DEFINITIONS = {
    "ai_predictions": {
        "name": "AI 判斷明細",
        "features": ["AI目前判斷", "四分類機率", "Confidence", "歷史 AI 結果"],
        "filename_tokens": ["all_diagnosis_results"],
    },
    "ai_events": {
        "name": "異常事件",
        "features": ["異常事件"],
        "filename_tokens": ["detected_event_groups"],
    },
    "data_quality": {
        "name": "資料品質",
        "features": ["資料品質"],
        "filename_tokens": ["data_quality", "feature_quality"],
    },
    "diagnosis_summary": {
        "name": "AI 診斷摘要",
        "features": ["AI 結果統計", "正常與異常比例"],
        "filename_tokens": ["diagnosis_summary"],
    },
    "file_predictions": {
        "name": "各檔案預測摘要",
        "features": ["月份比較", "各檔案異常比例"],
        "filename_tokens": ["prediction_by_file"],
    },
    "cnn_measurements": {
        "name": "CNN 三相歷史監測",
        "features": ["三相電壓", "三相電流", "歷史資料曲線"],
        "filename_tokens": ["tblgrid_"],
    },
}


def json_safe(value: Any) -> Any:
    """把 CSV 值轉成能穩定寫入 JSON 的內容。"""
    if value is None:
        return None
    return str(value)


def detect_encoding(path: Path) -> str:
    """以常見編碼嘗試讀取標題；回傳第一個可用編碼。"""
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                file.readline()
            return encoding
        except UnicodeDecodeError:
            continue
    return "utf-8"


def classify_file(path: Path, columns: list[str]) -> tuple[str, list[str]]:
    """依檔名與欄位辨識 CSV 可以供應的網站功能。"""
    lower_name = path.name.lower()
    lower_columns = {column.lower() for column in columns}

    # 原始 tblGrid 檔必須具備三相電壓與電流，避免誤把摘要檔分類為監測資料。
    raw_columns = {
        "voltagel1", "voltagel2", "voltagel3",
        "currentl1", "currentl2", "currentl3",
    }
    if lower_name.startswith("tblgrid_") and raw_columns.issubset(lower_columns):
        route = ROUTE_DEFINITIONS["cnn_measurements"]
        return "cnn_measurements", route["features"]

    for route_key, definition in ROUTE_DEFINITIONS.items():
        if route_key == "cnn_measurements":
            continue
        if any(token in lower_name for token in definition["filename_tokens"]):
            return route_key, definition["features"]

    return "unknown", []


def read_head(path: Path, encoding: str, limit: int) -> tuple[list[str], list[dict[str, Any]]]:
    """只讀標題和前幾筆，確保掃描大型 CSV 時仍然快速。"""
    with path.open("r", encoding=encoding, errors="replace", newline="") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []
        rows = []
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append({key: json_safe(value) for key, value in row.items()})
    return columns, rows


def sample_id(path: Path) -> str:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    safe_stem = "".join(char if char.isalnum() else "_" for char in path.stem)
    return f"{safe_stem[:60]}_{digest}.json"


def scan_csv(path: Path, source_group: str, samples_dir: Path, sample_rows: int) -> dict[str, Any]:
    stat = path.stat()
    encoding = detect_encoding(path)
    columns, rows = read_head(path, encoding, sample_rows)
    route, features = classify_file(path, columns)
    sample_path = samples_dir / sample_id(path)

    sample_document = {
        "source_file": str(path),
        "encoding": encoding,
        "columns": columns,
        "sample_rows": rows,
    }
    sample_path.write_text(
        json.dumps(sample_document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "path": str(path),
        "source_group": source_group,
        "route": route,
        "route_name": ROUTE_DEFINITIONS.get(route, {}).get("name", "尚未分類"),
        "website_features": features,
        "columns": columns,
        "column_count": len(columns),
        "sample_count": len(rows),
        "sample_file": str(sample_path),
        "encoding": encoding,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "scan_error": "",
    }


def error_record(path: Path, source_group: str, error: Exception) -> dict[str, Any]:
    return {
        "path": str(path),
        "source_group": source_group,
        "route": "error",
        "route_name": "讀取失敗",
        "website_features": [],
        "columns": [],
        "column_count": 0,
        "sample_count": 0,
        "sample_file": "",
        "encoding": "",
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "modified_at": "",
        "scan_error": f"{type(error).__name__}: {error}",
    }


def discover_csv(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*.csv") if path.is_file())


def write_catalog_csv(records: list[dict[str, Any]], output_test_path: Path) -> None:
    fields = [
        "path", "source_group", "route", "route_name", "website_features",
        "columns", "column_count", "sample_count", "sample_file", "encoding",
        "size_bytes", "modified_at", "scan_error",
    ]
    with output_test_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["website_features"] = "｜".join(record["website_features"])
            row["columns"] = "｜".join(record["columns"])
            writer.writerow(row)


def build_routes(records: list[dict[str, Any]]) -> dict[str, Any]:
    routes: dict[str, Any] = {}
    for route_key, definition in ROUTE_DEFINITIONS.items():
        matched = [record["path"] for record in records if record["route"] == route_key]
        routes[route_key] = {
            "name": definition["name"],
            "website_features": definition["features"],
            "source_files": matched,
            "file_count": len(matched),
        }
    routes["unknown"] = {
        "name": "尚未分類",
        "source_files": [record["path"] for record in records if record["route"] == "unknown"],
    }
    return routes


def build_page_feature_map(records: list[dict[str, Any]]) -> dict[str, Any]:
    """建立「網站頁面 → 功能 → CSV/欄位」的清楚對照。"""
    pages: dict[str, Any] = {}
    for page_name, features in PAGE_FEATURES.items():
        pages[page_name] = {}
        for feature_name, definition in features.items():
            source_routes = definition["source_routes"]
            matched = [
                record for record in records
                if record["route"] in source_routes and not record["scan_error"]
            ]
            pages[page_name][feature_name] = {
                "available": bool(matched),
                "status": "可使用" if matched else "目前缺少資料來源",
                "source_routes": source_routes,
                "source_files": [record["path"] for record in matched],
                "required_columns": definition["columns"],
                "selection": definition["selection"],
                "sample_files": [record["sample_file"] for record in matched],
            }
    return pages


def write_page_feature_csv(pages: dict[str, Any], output_test_path: Path) -> None:
    fields = [
        "page", "feature", "available", "status", "required_columns",
        "selection", "source_file_count", "source_files", "sample_files",
    ]
    with output_test_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for page_name, features in pages.items():
            for feature_name, detail in features.items():
                writer.writerow({
                    "page": page_name,
                    "feature": feature_name,
                    "available": detail["available"],
                    "status": detail["status"],
                    "required_columns": "｜".join(detail["required_columns"]),
                    "selection": detail["selection"],
                    "source_file_count": len(detail["source_files"]),
                    "source_files": "｜".join(detail["source_files"]),
                    "sample_files": "｜".join(detail["sample_files"]),
                })


def write_page_folders(pages: dict[str, Any], output_root: Path) -> None:
    """以 ASCII ID 建立網站資料夾；中文標籤只寫入 JSON。"""
    pages_root = output_root / "pages"
    for page_name, features in pages.items():
        for feature_name, detail in features.items():
            page_id = PAGE_FOLDER_IDS[page_name]
            feature_id = FEATURE_FOLDER_IDS[feature_name]
            feature_dir = pages_root / page_id / feature_id
            feature_dir.mkdir(parents=True, exist_ok=True)
            document = {
                "page_id": page_id,
                "page_label": page_name,
                "feature_id": feature_id,
                "feature_label": feature_name,
                **detail,
            }
            (feature_dir / "data_source.json").write_text(
                json.dumps(document, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="掃描 Mr. SU 的 AI 與 CNN CSV 資料")
    parser.add_argument("--ai-root", type=Path, default=DEFAULT_AI_ROOT)
    parser.add_argument("--cnn-root", type=Path, default=DEFAULT_CNN_ROOT)
    parser.add_argument("--output_test", type=Path, default=DEFAULT_OUTPUT_test_ROOT)
    parser.add_argument("--sample-rows", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.sample_rows < 1 or args.sample_rows > 100:
        raise ValueError("--sample-rows 必須介於 1 到 100。")

    args.output_test.mkdir(parents=True, exist_ok=True)
    samples_dir = args.output_test / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    sources = [
        ("ai_results", args.ai_root),
        ("cnn_raw_tblGrid", args.cnn_root),
    ]
    records: list[dict[str, Any]] = []
    for source_group, root in sources:
        for path in discover_csv(root):
            try:
                records.append(scan_csv(path, source_group, samples_dir, args.sample_rows))
            except Exception as error:  # 單一壞檔不應中止整批掃描
                records.append(error_record(path, source_group, error))

    catalog_document = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "ai_root": str(args.ai_root),
        "cnn_root": str(args.cnn_root),
        "sample_rows_per_file": args.sample_rows,
        "total_files": len(records),
        "records": records,
    }
    (args.output_test / "csv_catalog.json").write_text(
        json.dumps(catalog_document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_catalog_csv(records, args.output_test / "csv_catalog.csv")
    (args.output_test / "data_routes.json").write_text(
        json.dumps(build_routes(records), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    page_features = build_page_feature_map(records)
    (args.output_test / "page_feature_map.json").write_text(
        json.dumps(page_features, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_page_feature_csv(page_features, args.output_test / "page_feature_map.csv")
    write_page_folders(page_features, args.output_test)

    route_counts: dict[str, int] = {}
    for record in records:
        route_counts[record["route"]] = route_counts.get(record["route"], 0) + 1

    print(f"掃描完成：{len(records)} 個 CSV")
    print(f"輸出位置：{args.output_test}")
    for route, count in sorted(route_counts.items()):
        print(f"  {route}: {count}")


if __name__ == "__main__":
    main()
