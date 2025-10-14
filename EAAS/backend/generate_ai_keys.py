from routes.utils.smart_contract import CryptoUtils


def generate_and_save_keys():
    """Generates one permanent key pair for the AI Oracle and prints them."""

    crypto = CryptoUtils()
    private_key_pem, public_key_pem = crypto.generate_keypair()

    print("\n" + "=" * 60)
    print("AI ORACLE KEY PAIR GENERATED SUCCESSFULLY")
    print("=" * 60)

    print(
        "\nAI Private Key (Keep this SECRET and store it as an environment variable)\n"
    )
    # We decode for printing so it's easy to copy
    print(private_key_pem.decode("utf-8"))

    print("\n" + "-" * 60)

    print("\n AI Public Key (Store this as an environment variable)\n")
    print(public_key_pem.decode("utf-8"))

    print("=" * 60)
    print("Action Required: Copy these values and set them as environment variables.")
    print("Example: AI_PRIVATE_KEY='-----BEGIN...' and AI_PUBLIC_KEY='-----BEGIN...'")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    generate_and_save_keys()
