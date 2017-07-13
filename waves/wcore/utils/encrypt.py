"""
Encryption for Service Adaptors init_params values
"""
from __future__ import unicode_literals

from waves.wcore.settings import waves_settings
from Crypto.Cipher import XOR
import base64


class Encrypt(object):
    """ Encrypt values based on Django settings secret key substring """
    def __init__(self):
        raise RuntimeError('This class is intended to be used statically')

    @staticmethod
    def encrypt(to_encode):
        """ Crypt 'to_encode'
        :param secret: secret key use to encode/decode values
        :param to_encode: value to encode
        :return: base64 based encoded string
        """
        if len(waves_settings.SECRET_KEY) != 32:
            raise RuntimeError('Encoded values must use a key at least a 32 chars length secret')
        cipher = XOR.new(waves_settings.SECRET_KEY)
        encoded = base64.b64encode(cipher.encrypt(to_encode))
        return encoded

    @staticmethod
    def decrypt(to_decode):
        """ Decrypt previously encoded 'to_decode'
        :param secret: secret key used to encode/decode values
        :param to_decode: value to decode
        :return: string initial value
        """
        if len(waves_settings.SECRET_KEY) != 32:
            raise RuntimeError('Encoded values must use a key at least a 32 chars length secret')
        cipher = XOR.new(waves_settings.SECRET_KEY)
        return cipher.decrypt(base64.b64decode(to_decode))
