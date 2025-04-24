from typing import Tuple, List, Union
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from Crypto.Protocol.SecretSharing import Shamir as PyCryptodomeShamir


# RSA2048
def generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    public_numbers = public_key.public_numbers()
    n = public_numbers.n
    e = public_numbers.e

    private_numbers = private_key.private_numbers()
    d = private_numbers.d

    return (n, e), (n, d)


def create_shamir_shares(secret_int: int, k_threshold: int, n_shares: int) -> List[Tuple[int, int]]:
    if k_threshold > n_shares:
        raise ValueError("Threshold k cannot be greater than total shares n")

    shares = PyCryptodomeShamir.split(k_threshold, n_shares, secret_int)
    return shares


def combine_shamir_shares(shares_list: List[Tuple[int, int]]) -> int:
    if not shares_list:
        raise ValueError("Shares list cannot be empty.")
    if len(shares_list) < 2:
        raise ValueError("Need at least k (must be > 1) shares to combine.")

    reconstructed_secret_int = PyCryptodomeShamir.combine(shares_list)
    return reconstructed_secret_int


def encrypt_vote(public_key_tuple: Tuple[int, int], vote_string: str):
    n, e = public_key_tuple

    public_numbers = rsa.RSAPublicNumbers(e, n)
    public_key = public_numbers.public_key()

    vote_bytes = vote_string.encode('utf-8')

    encrypted_bytes = public_key.encrypt(
        vote_bytes,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_bytes


def decrypt_vote(private_key_tuple: Tuple[int, int], encrypted_bytes: bytes):
    n, d = private_key_tuple

    encrypted_int = int.from_bytes(encrypted_bytes, 'big')
    decrypted_int = pow(encrypted_int, d, n)

    num_bytes = (decrypted_int.bit_length() + 7) // 8

    decrypted_bytes_padded = decrypted_int.to_bytes(num_bytes, 'big')
    decrypted_string = decrypted_bytes_padded.decode('utf-8')

    return decrypted_string
