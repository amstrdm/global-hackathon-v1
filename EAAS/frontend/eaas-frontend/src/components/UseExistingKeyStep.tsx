import { useState } from "react";
import { validatePublicKey } from "../lib/crypto";

interface Props {
  onComplete: (publicKey: string) => void;
  onBack: () => void;
}

const UseExistingKeyStep = ({ onComplete, onBack }: Props) => {
  const [publicKey, setPublicKey] = useState("");
  const [error, setError] = useState("");

  const handleValidateAndSubmit = async () => {
    setError("");
    const isValid = await validatePublicKey(publicKey);
    if (isValid) {
      onComplete(publicKey);
    } else {
      setError("Invalid Public Key format. Please check and paste it again.");
    }
  };

  return (
    <div>
      <p className="mb-2">Paste your existing public key in PEM format.</p>
      <textarea
        value={publicKey}
        onChange={(e) => setPublicKey(e.target.value)}
        placeholder="-----BEGIN PUBLIC KEY-----..."
        className="w-full h-32 p-2 bg-gray-700 border border-gray-600 rounded-md font-mono text-xs"
      />
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      <button
        onClick={handleValidateAndSubmit}
        disabled={!publicKey.trim()}
        className="w-full mt-4 py-2 px-4 bg-green-600 hover:bg-green-700 rounded-md disabled:opacity-50"
      >
        Use This Key & Register
      </button>
      <button
        onClick={onBack}
        className="w-full mt-2 py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md"
      >
        Back
      </button>
    </div>
  );
};

export default UseExistingKeyStep;
