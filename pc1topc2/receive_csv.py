"""PC2: receive raw CSV bytes, commit locally, and never forward to PC3."""
import argparse
import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from starlette.requests import ClientDisconnect

PORT = 8001
DEFAULT_OUTPUT_DIR = r'D:\接收區'


def create_app(output_dir=None):
    receiver = FastAPI(title='PC2 CSV Receiver')
    receiver.state.output_dir = Path(output_dir or os.getenv('CSV_OUTPUT_DIR', DEFAULT_OUTPUT_DIR)).expanduser()

    @receiver.post('/upload-csv', status_code=201)
    async def upload_csv(request: Request):
        directory = receiver.state.output_dir
        identifier = uuid4().hex
        temporary = directory / f'{identifier}.part'
        destination = directory / f'{identifier}.csv'
        size = 0
        try:
            directory.mkdir(parents=True, exist_ok=True)
            with temporary.open('xb') as target:
                async for chunk in request.stream():
                    if chunk:
                        target.write(chunk)
                        size += len(chunk)
                if not size:
                    raise HTTPException(400, 'CSV is empty')
                target.flush()
                os.fsync(target.fileno())
            # Same-directory rename: final .csv appears only after a full upload.
            temporary.replace(destination)
        except ClientDisconnect as error:
            raise HTTPException(400, 'CSV upload interrupted before completion') from error
        except OSError as error:
            raise HTTPException(500, f'無法儲存到 {directory}：{error}') from error
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logging.exception('無法清除未完成的上傳檔案：%s', temporary)
        return {'file': destination.name, 'bytes': size}

    return receiver


app = create_app()


def main(argv=None):
    parser = argparse.ArgumentParser(description='PC2 收檔到本機，固定使用 TCP 8001')
    parser.add_argument('--output-dir', type=Path, default=os.getenv('CSV_OUTPUT_DIR', DEFAULT_OUTPUT_DIR), help=r'本機收檔資料夾，預設 D:\接收區')
    parser.add_argument('--host', default='0.0.0.0', help='監聽位址，可指定 PC2 的 Tailscale IP')
    args = parser.parse_args(argv)
    import uvicorn
    print(f'PC2 接收器：http://{args.host}:{PORT}/upload-csv；儲存位置：{args.output_dir}', flush=True)
    uvicorn.run(create_app(args.output_dir), host=args.host, port=PORT)


if __name__ == '__main__':
    main()
