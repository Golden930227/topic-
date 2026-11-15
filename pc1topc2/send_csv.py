"""PC1: stream the original CSV bytes directly to PC2 over HTTP."""
import argparse
import ipaddress
import json
from pathlib import Path
import socket
import sys
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

PORT = 8001


def tailscale_ip(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('請填 PC2 的 Tailscale IP，不是網址或埠號') from error
    network = ipaddress.ip_network('100.64.0.0/10' if address.version == 4 else 'fd7a:115c:a1e0::/48')
    if address not in network:
        raise argparse.ArgumentTypeError('IP 不在 Tailscale 位址範圍，請先核對 PC2 的 tailscale ip')
    return str(address)


def send_csv(csv_path, pc2_ip, timeout=60):
    path = Path(csv_path).expanduser()
    if not path.is_file():
        raise ValueError(f'找不到 CSV 檔案：{path}')
    size = path.stat().st_size
    host = f'[{pc2_ip}]' if ':' in pc2_ip else pc2_ip
    url = f'http://{host}:{PORT}/upload-csv'
    # Tailnet traffic must go directly to PC2, not via an HTTP proxy or PC3.
    opener = build_opener(ProxyHandler({}))
    try:
        with path.open('rb') as source:
            request = Request(url, data=source, method='POST', headers={
                'Content-Type': 'text/csv', 'Content-Length': str(size),
            })
            with opener.open(request, timeout=timeout) as response:
                if response.status != 201:
                    raise ValueError(f'PC2 回傳非預期狀態 HTTP {response.status}，預期 201')
                result = json.load(response)
    except HTTPError as error:
        body = error.read(8192).decode('utf-8', errors='replace')
        try:
            detail = json.loads(body).get('detail', body)
        except (ValueError, AttributeError):
            detail = body
        raise ValueError(f'PC2 拒絕收檔：HTTP {error.code}，{detail}；目的地 {url}') from error
    except URLError as error:
        raise ValueError(f'無法連線到 PC2 {url}：{error.reason}') from error
    except (TimeoutError, socket.timeout) as error:
        raise ValueError(f'連線或傳輸逾時（{timeout} 秒）：{url}') from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f'PC2 {url} 未回傳有效 JSON') from error
    if not isinstance(result, dict) or not isinstance(result.get('file'), str) or not result['file']:
        raise ValueError('PC2 回應缺少儲存檔名 file')
    if type(result.get('bytes')) is not int or result['bytes'] != size:
        raise ValueError(f'位元組數不一致：送出 {size}，PC2 回報 {result.get("bytes")}')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='PC1 直接發送 CSV 到 PC2:8001，不轉傳 PC3')
    parser.add_argument('--csv', type=Path, required=True, help='PC1 上待傳 CSV 的完整路徑')
    parser.add_argument('--pc2-ip', type=tailscale_ip, required=True, help='已核對的 PC2 Tailscale IP')
    parser.add_argument('--timeout', type=float, default=60, help='連線／讀取逾時秒數，預設 60')
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error('--timeout 必須大於 0')
    try:
        result = send_csv(args.csv, args.pc2_ip, args.timeout)
    except (ValueError, OSError) as error:
        print(f'傳送失敗：{error}', file=sys.stderr)
        return 1
    print(f'傳送成功：PC2 儲存檔名={result["file"]}，位元組數={result["bytes"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
