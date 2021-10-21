"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import base64

from cryptography.fernet import Fernet

from waves.settings import waves_settings


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
        encoder = Fernet(base64.urlsafe_b64encode(waves_settings.SECRET_KEY.encode()))

        # to_encode casted as bytes
        encoded = encoder.encrypt(to_encode.encode()).decode()

        # return str to store in db
        return encoded

    @staticmethod
    def decrypt(to_decode):
        """ Decrypt previously encoded 'to_decode'
        :param to_decode: value to decode
        :return: string initial value
        """
        if len(waves_settings.SECRET_KEY) < 32:
            raise RuntimeError('Encoded values must use a key at least a 32 chars length secret')
        encoder = Fernet(base64.urlsafe_b64encode(waves_settings.SECRET_KEY.encode()))

        # encode to cast as bytes
        decoded = encoder.decrypt(to_decode.encode()).decode()

        return decoded
