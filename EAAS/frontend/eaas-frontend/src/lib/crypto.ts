/**
 * Converts an ArrayBuffer to a Base64 string.
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/**
 * Generates an RSA-PSS key pair and returns them in multiple formats.
 */
export async function generateKeyPair(): Promise<{
  privateKeyPem: string;
  publicKeyPem: string;
}> {
  const keyPair = await window.crypto.subtle.generateKey(
    {
      name: "RSA-PSS",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true,
    ["sign", "verify"]
  );

  const privateKeyDer = await window.crypto.subtle.exportKey(
    "pkcs8",
    keyPair.privateKey
  );
  const privateKeyBase64 = arrayBufferToBase64(privateKeyDer);
  const privateKeyPem = `-----BEGIN PRIVATE KEY-----\n${privateKeyBase64}\n-----END PRIVATE KEY-----`;

  const publicKeyDer = await window.crypto.subtle.exportKey(
    "spki",
    keyPair.publicKey
  );
  const publicKeyBase64 = arrayBufferToBase64(publicKeyDer);
  const publicKeyPem = `-----BEGIN PUBLIC KEY-----\n${publicKeyBase64}\n-----END PUBLIC KEY-----`;

  return { privateKeyPem, publicKeyPem };
}

/**
 * Validates a given public key in PEM format.
 * Returns true if valid, false otherwise.
 */
export async function validatePublicKey(
  publicKeyPem: string
): Promise<boolean> {
  try {
    const pemHeader = "-----BEGIN PUBLIC KEY-----";
    const pemFooter = "-----END PUBLIC KEY-----";
    const pemContents = publicKeyPem
      .replace(pemHeader, "")
      .replace(pemFooter, "")
      .replace(/\s/g, "");

    const binaryDer = window.atob(pemContents);
    const keyData = new Uint8Array(binaryDer.length).map((_, i) =>
      binaryDer.charCodeAt(i)
    );

    await window.crypto.subtle.importKey(
      "spki",
      keyData.buffer,
      { name: "RSA-PSS", hash: "SHA-256" },
      true,
      ["verify"]
    );
    return true;
  } catch (error) {
    console.error("Public key validation failed:", error);
    return false;
  }
}

/**
 * Triggers a browser download for the given text content.
 */
export function downloadTextFile(content: string, filename: string) {
  const element = document.createElement("a");
  const file = new Blob([content], { type: "text/plain" });
  element.href = URL.createObjectURL(file);
  element.download = filename;
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}
