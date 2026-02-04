import unittest

from cryptography.exceptions import InvalidTag

from . import aes


class TestAes(unittest.TestCase):
    def test_aes_ok(self):
        tk = aes.new_token()
        em = aes.encrypt("test_aes_ok", tk)
        cm = aes.decrypt(em, tk)
        self.assertEqual("test_aes_ok", cm)

    def test_aes_nok(self):
        tk = aes.new_token()
        em = aes.encrypt("test_aes_nok", tk)
        tk2 = aes.new_token()
        with self.assertRaises(InvalidTag):
            _ = aes.decrypt(em, tk2)
