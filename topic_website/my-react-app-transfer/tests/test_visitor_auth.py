"""Removing registration must not bypass identity or employee authorization."""
import base64
import io
import json
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
import windmind_auth as auth


class VisitorAuthenticationTests(unittest.TestCase):
    def setUp(self):
        auth._cache.clear()

    def test_new_and_previously_registered_visitors_never_read_firestore(self):
        for uid in ('new-visitor', 'previously-registered-visitor'):
            payload = base64.urlsafe_b64encode(json.dumps({'exp':time.time()+3600}).encode()).decode().rstrip('=')
            token = f'{uid}.{payload}.validated-by-firebase-fixture'
            user = {'localId':uid,'email':f'{uid}@example.com','emailVerified':True}
            with patch.object(auth, 'urlopen', return_value=io.BytesIO(json.dumps({'users':[user]}).encode())) as network:
                identity = auth.firebase_identity(token)
            self.assertEqual(identity['role'],'visitor')
            self.assertEqual(identity['uid'],uid)
            self.assertEqual(network.call_count,1)
            self.assertIn('identitytoolkit.googleapis.com/v1/accounts:lookup',network.call_args.args[0].full_url)

    def test_allowlisted_employee_still_requires_verified_identity(self):
        payload = base64.urlsafe_b64encode(json.dumps({'exp':time.time()+3600}).encode()).decode().rstrip('=')
        token = f'employee.{payload}.validated-by-firebase-fixture'
        user = {'localId':'staff','email':'g99226@gmail.com','emailVerified':True}
        with patch.object(auth, 'urlopen', return_value=io.BytesIO(json.dumps({'users':[user]}).encode())):
            self.assertEqual(auth.firebase_identity(token)['role'],'member')
        auth._cache.clear()
        user['emailVerified'] = False
        with patch.object(auth, 'urlopen', return_value=io.BytesIO(json.dumps({'users':[user]}).encode())):
            with self.assertRaises(HTTPException) as denied:
                auth.firebase_identity(token)
        self.assertEqual(denied.exception.status_code,403)


if __name__ == '__main__': unittest.main()
