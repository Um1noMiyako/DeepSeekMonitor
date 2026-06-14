"""API Key 加解密 — 基于机器指纹的 Fernet 加密"""
import uuid
import socket
import hashlib
import base64
from cryptography.fernet import Fernet


def _derive_key() -> bytes:
    """从机器指纹派生加密密钥（MAC + hostname + salt）"""
    machine_id = uuid.getnode()
    hostname = socket.gethostname()
    seed = f"{machine_id}:{hostname}:deepseek-monitor-salt"
    digest = hashlib.sha256(seed.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt(plaintext: str) -> str:
    """加密明文 API Key → base64 密文"""
    if not plaintext:
        return ""
    f = Fernet(_derive_key())
    token = f.encrypt(plaintext.encode())
    return token.decode()


def decrypt(ciphertext: str) -> str:
    """解密 base64 密文 → 明文 API Key"""
    if not ciphertext:
        return ""
    f = Fernet(_derive_key())
    return f.decrypt(ciphertext.encode()).decode()
