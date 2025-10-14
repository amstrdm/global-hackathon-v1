import React, { useState } from "react";
import { KeyManager } from "./KeyManager";

type SignatureMode = "choice" | "browser" | "external";

interface SignatureModalProps {
  isOpen: boolean;
  messageToSign: string;
  isKeyLoaded: boolean;
  onClose: () => void;
  // 1. Update the prop type to allow null for resetting the key
  onLoadKey: (key: string | null) => void;
  onSignWithBrowser: () => Promise<void>;
  onSubmitExternalSignature: (signature: string) => void;
}

export const SignatureModal = ({
  isOpen,
  messageToSign,
  isKeyLoaded,
  onClose,
  onLoadKey,
  onSignWithBrowser,
  onSubmitExternalSignature,
}: SignatureModalProps) => {
  const [mode, setMode] = useState<SignatureMode>("choice");
  const [externalSignature, setExternalSignature] = useState("");
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(messageToSign);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // 2. Add a handler to reset the key
  const handleChangeKey = () => {
    onLoadKey(null); // This resets the key in the useCryptoSigner hook
  };

  const renderContent = () => {
    switch (mode) {
      case "external":
        // ... (this part remains the same)
        return (
          <div>
            <h3 className="text-lg font-semibold mb-2">Sign Manually</h3>
            <p className="text-sm text-gray-400 mb-4">
              Copy the message below and sign it using your preferred tool
              (e.g., OpenSSL, a hardware wallet). Then, paste the resulting
              hexadecimal signature.
            </p>
            <div className="p-3 bg-gray-900 rounded-md mb-4">
              <p className="font-mono text-sm break-all">{messageToSign}</p>
              <button
                onClick={handleCopyToClipboard}
                className="text-cyan-400 hover:text-cyan-300 mt-2 text-xs"
              >
                {copied ? "Copied!" : "Copy Message"}
              </button>
            </div>
            <textarea
              value={externalSignature}
              onChange={(e) => setExternalSignature(e.target.value)}
              placeholder="Paste the hex-encoded signature here"
              className="w-full h-24 p-2 bg-gray-700 border border-gray-600 rounded-md font-mono text-xs"
            />
            <button
              onClick={() => onSubmitExternalSignature(externalSignature)}
              disabled={!externalSignature.trim()}
              className="w-full mt-4 py-2 bg-green-600 hover:bg-green-700 rounded-md disabled:opacity-50"
            >
              Submit Signature
            </button>
            <button
              onClick={() => setMode("choice")}
              className="w-full mt-2 text-sm text-gray-400 hover:text-white"
            >
              Back
            </button>
          </div>
        );
      case "browser":
        return (
          <div>
            <h3 className="text-lg font-semibold mb-2">Sign in Browser</h3>
            {isKeyLoaded ? (
              // 3. This is the updated UI for when a key is loaded
              <div>
                <div className="p-3 mb-4 bg-gray-900 border border-green-500 rounded-md flex justify-between items-center">
                  <p className="text-green-400 font-semibold">
                    ✓ Private Key Loaded
                  </p>
                  <button
                    onClick={handleChangeKey}
                    className="text-xs text-gray-400 hover:text-white underline"
                  >
                    Change Key
                  </button>
                </div>
                <button
                  onClick={onSignWithBrowser}
                  className="w-full py-2 bg-cyan-600 hover:bg-cyan-700 rounded-md"
                >
                  Sign and Submit
                </button>
              </div>
            ) : (
              <KeyManager onKeyLoad={onLoadKey} />
            )}
            <button
              onClick={() => setMode("choice")}
              className="w-full mt-4 text-sm text-gray-400 hover:text-white"
            >
              Back
            </button>
          </div>
        );
      case "choice":
      default:
        return (
          <div className="space-y-4">
            <button
              onClick={() => setMode("browser")}
              className="w-full py-3 bg-cyan-600 hover:bg-cyan-700 rounded-md"
            >
              Sign with Loaded Key
            </button>
            <button
              onClick={() => setMode("external")}
              className="w-full py-3 bg-gray-600 hover:bg-gray-500 rounded-md"
            >
              Sign Manually (External)
            </button>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Confirm Action</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            &times;
          </button>
        </div>
        {renderContent()}
      </div>
    </div>
  );
};
