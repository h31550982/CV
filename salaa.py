"""Salaa lahde/cv.html -tiedoston sisällön index.html-sivulle.

Käyttö:  python3 salaa.py
Skripti kysyy salasanan. Salasanaa ei tallenneta mihinkään.

Salaus: PBKDF2-SHA256 (600 000 kierrosta) -> AES-256-CBC + HMAC-SHA256.
Selain purkaa saman Web Crypto API:lla (ks. index.html).
"""

import base64
import getpass
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(ROOT, "lahde")
SOURCE = os.path.join(SOURCE_DIR, "cv.html")
TARGET = os.path.join(ROOT, "index.html")
ITERATIONS = 600_000

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def inline_images(html):
    """Upottaa lahde-kansion kuvat sivuun, jotta ne salataan sisällön mukana."""

    def replace(match):
        name = match.group(1)
        path = os.path.join(SOURCE_DIR, name)
        ext = os.path.splitext(name)[1].lower()
        if ext not in IMAGE_TYPES or not os.path.isfile(path):
            return match.group(0)
        data = base64.b64encode(open(path, "rb").read()).decode("ascii")
        return f'src="data:{IMAGE_TYPES[ext]};base64,{data}"'

    return re.sub(r'src="([^":/]+)"', replace, html)


def aes_cbc_encrypt(key, iv, plaintext):
    result = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-K", key.hex(), "-iv", iv.hex()],
        input=plaintext,
        capture_output=True,
        check=True,
    )
    return result.stdout


def main():
    if not os.path.isfile(SOURCE):
        sys.exit(f"Lähdetiedostoa ei löydy: {SOURCE}")

    password = getpass.getpass("Salasana: ")
    if not password:
        sys.exit("Salasana ei voi olla tyhjä.")
    if getpass.getpass("Salasana uudelleen: ") != password:
        sys.exit("Salasanat eivät täsmää.")

    plaintext = inline_images(open(SOURCE, encoding="utf-8").read()).encode("utf-8")

    salt = os.urandom(16)
    iv = os.urandom(16)
    keys = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, dklen=64)
    enc_key, mac_key = keys[:32], keys[32:]

    ciphertext = aes_cbc_encrypt(enc_key, iv, plaintext)
    tag = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()

    b64 = lambda b: base64.b64encode(b).decode("ascii")
    payload = json.dumps(
        {"iterations": ITERATIONS, "salt": b64(salt), "iv": b64(iv), "tag": b64(tag), "data": b64(ciphertext)}
    )

    page = open(TARGET, encoding="utf-8").read()
    pattern = r'(<script id="cv-data" type="application/json">).*?(</script>)'
    if not re.search(pattern, page, flags=re.S):
        sys.exit('index.html-tiedostosta puuttuu <script id="cv-data">-elementti.')
    page = re.sub(pattern, lambda m: m.group(1) + payload + m.group(2), page, count=1, flags=re.S)
    open(TARGET, "w", encoding="utf-8").write(page)

    print("Valmis: index.html päivitetty salatulla sisällöllä.")


if __name__ == "__main__":
    main()
