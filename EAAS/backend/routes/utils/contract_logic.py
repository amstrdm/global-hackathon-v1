from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

from .smart_contract import CryptoUtils, Decision, Party


def create_contract(
    buyer_id: str,
    seller_id: str,
    amount: float,
    buyer_public_key_hex: str,
    seller_public_key_hex: str,
    ai_public_key_hex: str,
) -> Dict[str, Any]:
    """Creates a new contract dictionary. Does not store it."""
    contract_id = (
        CryptoUtils.generate_id()
    )  # Assuming you move _generate_id to CryptoUtils

    contract = {
        "contract_id": contract_id,
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "amount": amount,
        "public_keys": {
            Party.BUYER.value: buyer_public_key_hex,
            Party.SELLER.value: seller_public_key_hex,
            Party.AI_ORACLE.value: ai_public_key_hex,
        },
        "status": "ACTIVE",
        "signatures": {
            Party.BUYER.value: {
                "decision": None,
                "signature_hex": None,
                "verified": False,
            },
            Party.SELLER.value: {
                "decision": None,
                "signature_hex": None,
                "verified": False,
            },
            Party.AI_ORACLE.value: {
                "decision": None,
                "signature_hex": None,
                "verified": False,
            },
        },
        "created_at": datetime.now().isoformat(),
        "timeout_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        "released_to": None,
        "released_at": None,
    }
    return contract


def sign(
    contract: Dict[str, Any], party: Party, decision: Decision, signature_hex: str
) -> Dict[str, Any]:
    """Applies a signature to a contract dictionary and returns the updated dictionary."""
    if contract["status"] != "ACTIVE":
        raise ValueError("Contract is not active.")

    # 1. Get the public key PEM string and encode it to bytes.
    public_key_pem_string = contract["public_keys"][party.value]
    public_key_bytes = public_key_pem_string.encode("utf-8")

    # 2. Convert the signature from a hex string to bytes.
    signature_bytes = bytes.fromhex(signature_hex)

    # The message that was signed
    message = f"{contract['contract_id']}:{party.value}:{decision.value}"

    # Verify the signature using the public key bytes
    is_valid = CryptoUtils.verify_signature(message, signature_bytes, public_key_bytes)
    if not is_valid:
        raise ValueError(f"Invalid signature for {party.value}")

    # Update the signature data
    contract["signatures"][party.value] = {
        "decision": decision.value,
        "signature_hex": signature_hex,
        "verified": True,
        "signed_at": datetime.now().isoformat(),
    }

    # Try to execute the contract
    return _try_execute(contract)


def _try_execute(contract: Dict[str, Any]) -> Dict[str, Any]:
    """Checks for 2-of-3 signatures and updates contract status if met."""
    if contract["status"] != "ACTIVE":
        return contract

    decision_counts = {}
    for sig_data in contract["signatures"].values():
        if sig_data.get("verified") and sig_data.get("decision"):
            decision = sig_data["decision"]
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

    for decision, count in decision_counts.items():
        if count >= 2:
            # Decision reached, execute the contract
            if decision == Decision.RELEASE_TO_SELLER.value:
                recipient = contract["seller_id"]
            elif decision == Decision.REFUND_TO_BUYER.value:
                recipient = contract["buyer_id"]
            else:
                continue  # Should not happen

            contract["status"] = "COMPLETED"
            contract["released_to"] = recipient
            contract["released_at"] = datetime.now().isoformat()
            break  # Stop after executing

    return contract
