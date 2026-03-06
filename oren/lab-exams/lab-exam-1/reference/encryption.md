Based on your request for both encryption setups, here are the implementations.
1. Symmetric Encryption ("One Key Setup")

Concept: The same key is used to both encrypt and decrypt.

Relevance: This is the method explicitly taught in your course slides using the cryptography.fernet library. It is fast and efficient for IoT devices.


```python
from cryptography.fernet import Fernet

# --- SETUP (Run once) ---
# Generate a key (In a real app, save this securely!)
key = Fernet.generate_key() 
cipher = Fernet(key) # Initialize the cipher suite [cite: 449, 450]

# --- SENDER (Publisher) ---
message = "Secret MQTT Payload"
# Encrypt: Convert string -> bytes -> encrypted bytes
encrypted_payload = cipher.encrypt(message.encode('utf-8')) [cite: 451]

print(f"Sending (Encrypted): {encrypted_payload}")

# --- RECEIVER (Subscriber) ---
# The receiver MUST have the exact same 'key'
try:
    # Decrypt: Encrypted bytes -> bytes -> string
    decrypted_payload = cipher.decrypt(encrypted_payload).decode('utf-8') [cite: 452]
    print(f"Received (Decrypted): {decrypted_payload}")
except Exception as e:
    print("Decryption failed! Keys might not match.")
```

2. Asymmetric Encryption ("Private/Public Setup")

Concept: You have two keys.

    Public Key: Shared with everyone. Used to encrypt messages.

    Private Key: Kept secret. Used to decrypt messages. Relevance: Useful when you want many devices to send data to a central server without sharing a secret key across the network.

Code Example: Note: This uses the rsa module from the same cryptography library.

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# --- SETUP (Run once by the Receiver/Server) ---
# Generate Private Key (Keep this SAFE)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Generate Public Key (Share this with everyone/Publishers)
public_key = private_key.public_key()

# --- SENDER (Publisher) ---
# The sender uses the PUBLIC key to encrypt
message = b"Secret Data for Server Only"

encrypted_payload = public_key.encrypt(
    message,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print(f"Sending (Encrypted): {encrypted_payload.hex()[:20]}...")

# --- RECEIVER (Subscriber) ---
# The receiver uses the PRIVATE key to decrypt
try:
    decrypted_payload = private_key.decrypt(
        encrypted_payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    print(f"Received (Decrypted): {decrypted_payload.decode('utf-8')}")
except Exception as e:
    print("Decryption failed!")
```