"""Read-only CNN history extends batches without changing the newest KPI row."""
import os
from contextlib import closing
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlite_live_data import _recent_measurements

class RecentHistoryTests(unittest.TestCase):
    def batch(self, folder, name, ids, stamp):
        path = folder / (name + '.sqlite3')
        with closing(sqlite3.connect(path)) as db:
            db.execute('CREATE TABLE grand_measurements (measurement_uid TEXT PRIMARY KEY, inserted_at TEXT, sample INTEGER)')
            db.executemany('INSERT INTO grand_measurements VALUES (?,?,?)', [(str(i), f'{i:06d}', i) for i in ids])
            db.commit()
        os.utime(path, ns=(stamp, stamp))
        return path

    def test_fills_fifty_from_older_batches_and_keeps_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for i in range(6):
                self.batch(folder, str(i), range(i * 10, i * 10 + 10), (i + 1) * 1000000000)
            rows = _recent_measurements(folder)
            self.assertEqual([r['measurement_uid'] for r in rows], [str(i) for i in range(10, 60)])
            self.assertEqual(rows[-1]['measurement_uid'], '59')

    def test_partial_history_and_existing_larger_batch(self):
        for count in (0, 23, 80, 220):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                self.batch(folder, 'latest', range(count), 1000000000)
                rows = _recent_measurements(folder)
                self.assertEqual(len(rows), min(count, 200))
                if count:
                    self.assertEqual(rows[-1]['measurement_uid'], str(count - 1))

    def test_deduplicates_and_skips_unreadable_old_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.batch(folder, 'old', range(50), 1000000000)
            corrupt = folder / 'bad.sqlite3'
            corrupt.write_bytes(b'not a database')
            os.utime(corrupt, ns=(2000000000, 2000000000))
            self.batch(folder, 'latest', range(40, 50), 3000000000)
            rows = _recent_measurements(folder)
            self.assertEqual([r['measurement_uid'] for r in rows], [str(i) for i in range(50)])

if __name__ == '__main__':
    unittest.main()
