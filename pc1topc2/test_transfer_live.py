"""Actual HTTP 8001 round trip on this PC2; does not claim a PC1 cross-PC test."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

import uvicorn

from receive_csv import create_app, PORT, DEFAULT_OUTPUT_DIR
from send_csv import send_csv, tailscale_ip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pc2-ip',type=tailscale_ip,required=True)
    parser.add_argument('--output-dir',type=Path,default=DEFAULT_OUTPUT_DIR)
    args=parser.parse_args()
    sample=Path(__file__).with_name('sample.csv')
    original=sample.read_bytes()
    rows=list(csv.DictReader(io.StringIO(original.decode('utf-8-sig'))))
    server=uvicorn.Server(uvicorn.Config(create_app(args.output_dir),host=args.pc2_ip,port=PORT,log_level='warning'))
    worker=threading.Thread(target=server.run,daemon=True)
    worker.start()
    try:
        for _ in range(100):
            if server.started:break
            if not worker.is_alive():raise RuntimeError('接收器啟動失敗，請檢查位址及 8001 埠')
            time.sleep(.1)
        else:raise RuntimeError('接收器啟動逾時')
        result=send_csv(sample,args.pc2_ip,10)
        destination=args.output_dir/result['file']
        saved=destination.read_bytes()
        assert saved==original,'CSV 內容不同'
        digest=hashlib.sha256(original).hexdigest()
        assert hashlib.sha256(saved).hexdigest()==digest
        received_rows=list(csv.DictReader(io.StringIO(saved.decode('utf-8-sig'))))
        assert rows==received_rows and len(rows)==2
        # Exercise the actual PC1 command-line program as well.
        command=subprocess.run([sys.executable,str(Path(__file__).with_name('send_csv.py')),'--csv',str(sample),'--pc2-ip',args.pc2_ip,'--timeout','10'],capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=20)
        assert command.returncode==0,command.stderr
        opener=build_opener(ProxyHandler({}))
        host=f'[{args.pc2_ip}]' if ':' in args.pc2_ip else args.pc2_ip
        try:
            opener.open(Request(f'http://{host}:{PORT}/upload-csv',data=b'',method='POST'),timeout=5)
            raise AssertionError('空檔沒有被拒絕')
        except HTTPError as error:
            assert error.code==400,error.code
        assert not destination.with_suffix('.part').exists()
        print(json.dumps({'test_scope':'same PC2 through its own Tailscale IP; cross-PC1 transfer not tested','url':f'http://{host}:{PORT}/upload-csv','status':201,'stored_file':str(destination),'bytes':len(original),'sha256':digest,'identical_bytes':True,'rows_before':len(rows),'rows_after':len(received_rows),'first_timestamp':rows[0]['timestamp'],'last_timestamp':rows[-1]['timestamp'],'empty_upload_status':400,'sender_cli_output':command.stdout.strip()},ensure_ascii=True,indent=2))
    finally:
        server.should_exit=True
        worker.join(timeout=10)
    # The CLI must report a concrete connection failure after receiver shutdown.
    failed=subprocess.run([sys.executable,str(Path(__file__).with_name('send_csv.py')),'--csv',str(sample),'--pc2-ip',args.pc2_ip,'--timeout','2'],capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=10)
    assert failed.returncode==1,failed.stdout
    print('Receiver-stopped failure test: '+failed.stderr.strip())


if __name__=='__main__':main()
