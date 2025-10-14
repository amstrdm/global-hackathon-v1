import { useState } from "react";
import { useRoomStore, useUserStore } from "../store/useStore";
import { sendMessage } from "../api/websocket";

// --- Helper Functions ---

/**
 * Converts a string to an ArrayBuffer.
 * @param {string} str The string to convert.
 * @returns {ArrayBuffer}
 */
function str2ab(str: string): ArrayBuffer {
  const buf = new ArrayBuffer(str.length);
  const bufView = new Uint8Array(buf);
  for (let i = 0, strLen = str.length; i < strLen; i++) {
    bufView[i] = str.charCodeAt(i);
  }
  return buf;
}

/**
 * Converts an ArrayBuffer to a hexadecimal string.
 * @param {ArrayBuffer} buffer The buffer to convert.
 * @returns {string}
 */
function bufferToHex(buffer: ArrayBuffer): string {
  return [...new Uint8Array(buffer)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * A hook to manage the entire signing process, including user choices for
 * in-browser or external signing.
 */
export const useCryptoSigner = () => {
  const { room } = useRoomStore();
  const { user } = useUserStore();

  // The hook now manages the private key state for the session.
  // It's initialized from the user store if available.
  const [privateKey, setPrivateKey] = useState<string | null>(
    user?.private_key || null
  );

  const [signingContext, setSigningContext] = useState<{
    isOpen: boolean;
    messageToSign: string;
    messageType:
      | "transaction_successfull"
      | "product_delivered"
      | "init_dispute"
      | null;
    decision: "RELEASE_TO_SELLER" | "REFUND_TO_BUYER" | null;
  }>({
    isOpen: false,
    messageToSign: "",
    messageType: null,
    decision: null,
  });

  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Step 1: Called by UI to begin a signing action.
   * It constructs the message and opens the signature modal.
   */
  const initiateSigning = (
    decision: "RELEASE_TO_SELLER" | "REFUND_TO_BUYER",
    messageType:
      | "transaction_successfull"
      | "product_delivered"
      | "init_dispute"
  ) => {
    if (!room?.contract || !user) {
      setError("Cannot sign: contract or user data is missing.");
      return;
    }
    const party = user.user_id === room.buyer_id ? "BUYER" : "SELLER";
    const message = `${room.contract.contract_id}:${party}:${decision}`;
    setSigningContext({
      isOpen: true,
      messageToSign: message,
      messageType,
      decision,
    });
  };

  /**
   * Closes the signature modal and resets any errors.
   */
  const closeModal = () => {
    setSigningContext({
      isOpen: false,
      messageToSign: "",
      messageType: null,
      decision: null,
    });
    setError(null);
  };

  /**
   * Step 2 (Option A): Signs the message using the loaded private key.
   * This contains the core cryptographic operations.
   */
  const signWithLoadedKey = async () => {
    if (
      !privateKey ||
      !signingContext.messageType ||
      !signingContext.messageToSign
    ) {
      setError("Cannot sign: Private key or message context is missing.");
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Import the PEM-formatted private key
      const pemHeader = "-----BEGIN PRIVATE KEY-----";
      const pemFooter = "-----END PRIVATE KEY-----";
      const pemContents = privateKey
        .replace(pemHeader, "")
        .replace(pemFooter, "")
        .replace(/\s/g, "");
      const binaryDer = window.atob(pemContents);
      const keyData = str2ab(binaryDer);
      const cryptoKey = await window.crypto.subtle.importKey(
        "pkcs8",
        keyData,
        { name: "RSA-PSS", hash: "SHA-256" },
        true,
        ["sign"]
      );

      // Encode the message to sign
      const encodedMessage = new TextEncoder().encode(
        signingContext.messageToSign
      );

      // Perform the signing operation
      const signatureBuffer = await window.crypto.subtle.sign(
        { name: "RSA-PSS", saltLength: 32 },
        cryptoKey,
        encodedMessage
      );

      const signatureHex = bufferToHex(signatureBuffer);

      // Send the signature to the backend
      sendMessage({
        type: signingContext.messageType,
        signed_message: signatureHex,
      });

      closeModal();
    } catch (e) {
      console.error("In-browser signing failed:", e);
      setError(e instanceof Error ? e.message : "A signing error occurred.");
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Step 2 (Option B): Submits a pre-signed, user-provided hex signature.
   */
  const submitExternalSignature = (signatureHex: string) => {
    if (!signingContext.messageType || !signatureHex.trim()) {
      setError("Cannot submit: Signature is empty.");
      return;
    }

    sendMessage({
      type: signingContext.messageType,
      signed_message: signatureHex.trim(),
    });

    closeModal();
  };

  return {
    // Functions to control the flow
    initiateSigning,
    closeModal,
    setPrivateKey,

    // Functions for the modal to call
    signWithLoadedKey,
    submitExternalSignature,

    // State for the UI to consume
    signingContext,
    isProcessing,
    error,
    privateKey, // Expose for checking if a key is loaded
  };
};
