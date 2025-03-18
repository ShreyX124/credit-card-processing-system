from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
from config.settings import Config

# AES encryption for sensitive data
def encrypt_data(data):
    """
    Encrypt sensitive data using AES-256
    """
    if not data:
        return None
        
    key = Config.ENCRYPTION_KEY.encode('utf-8')[:32]
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return f"{iv}:{ct}"

def decrypt_data(encrypted_data):
    """
    Decrypt data that was encrypted with AES-256
    """
    if not encrypted_data:
        return None
        
    try:
        iv, ct = encrypted_data.split(':')
        key = Config.ENCRYPTION_KEY.encode('utf-8')[:32]
        iv = base64.b64decode(iv)
        ct = base64.b64decode(ct)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

def mask_card_number(card_number):
    """
    Mask a credit card number to show only the last 4 digits
    """
    if not card_number or len(card_number) < 4:
        return "****"
    return "*" * (len(card_number) - 4) + card_number[-4:]