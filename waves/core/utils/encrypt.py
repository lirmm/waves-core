"""
Encryption for Service Adaptors init_params values
"""


import base64

from cryptography.fernet import Fernet

from waves.core.settings import waves_settings


class Encrypt(object):
    """ Encrypt values based on Django settings secret key substring """
    def __init__(self):
        raise RuntimeError('This class is intended to be used statically')

    @staticmethod
    def encrypt(to_encode):
        """ Crypt 'to_encode'
        :param to_encode: value to encode
        :return: base64 based encoded string
        """
        if len(waves_settings.SECRET_KEY) < 32:
            raise RuntimeError('Encoded values must use a key at least a 32 chars length secret')
        encoder = Fernet(base64.urlsafe_b64encode(waves_settings.SECRET_KEY))
        encoded = encoder.encrypt(bytes(to_encode))
        return encoded

    @staticmethod
    def decrypt(to_decode):
        """ Decrypt previously encoded 'to_decode'
        :param to_decode: value to decode
        :return: string initial value
        """
        if len(waves_settings.SECRET_KEY) < 32:
            raise RuntimeError('Encoded values must use a key at least a 32 chars length secret')
        encoder = Fernet(base64.urlsafe_b64encode(waves_settings.SECRET_KEY))
        return encoder.decrypt(bytes(to_decode))
