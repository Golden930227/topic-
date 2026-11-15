"""Tests use temporary local directories; never modify D:\\接收區."""
import asyncio
import hashlib
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
from starlette.requests import Request

from receive_csv import create_app


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.app = create_app(self.folder)
        self.client = TestClient(self.app)

    def test_csv_bytes_and_unique_names(self):
        original = b'\xef\xbb\xbftimestamp,value,note\r\n2026-11-15T08:00:00Z,12.34,"a,b"\r\n2026-11-15T08:00:01Z,-2.5,test\r\n'
        filenames = set()
        for _ in range(2):
            result = self.client.post('/upload-csv', content=original, headers={'Content-Type':'text/csv'})
            self.assertEqual(result.status_code,201)
            payload = result.json()
            saved = (self.folder/payload['file']).read_bytes()
            self.assertEqual(payload['bytes'],len(original))
            self.assertEqual(saved,original)
            self.assertEqual(hashlib.sha256(saved).hexdigest(),hashlib.sha256(original).hexdigest())
            filenames.add(payload['file'])
        self.assertEqual(len(filenames),2)
        self.assertFalse(list(self.folder.glob('*.part')))

    def test_empty_upload_rejected_without_leftover(self):
        self.assertEqual(self.client.post('/upload-csv', content=b'').status_code,400)
        self.assertEqual(list(self.folder.iterdir()),[])

    def test_disconnect_removes_partial_file(self):
        chunks = iter([{'type':'http.request','body':b'partial,content\r\n','more_body':True}, {'type':'http.disconnect'}])
        async def receive(): return next(chunks)
        endpoint = next(route.endpoint for route in self.app.routes if getattr(route,'path','')=='/upload-csv')
        request = Request({'type':'http','method':'POST','path':'/upload-csv','headers':[]},receive)
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as interrupted:
            asyncio.run(endpoint(request))
        self.assertEqual(interrupted.exception.status_code,400)
        self.assertEqual(list(self.folder.iterdir()),[])


if __name__ == '__main__': unittest.main()
