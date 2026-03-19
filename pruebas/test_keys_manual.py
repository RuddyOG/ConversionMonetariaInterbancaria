from app.security.keys import KeyManager


def main():
    km = KeyManager()
    print(km.get_bank_config(1))
    print(km.get_algorithm(1))
    print(km.get_encryption_key(1))
    print(km.get_hmac_key(1))


if __name__ == "__main__":
    main()