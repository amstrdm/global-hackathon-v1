import { useState } from "react";

interface KeyManagerProps {
  onKeyLoad: (key: string) => void;
}

export const KeyManager = ({ onKeyLoad }: KeyManagerProps) => {
  const [keyInput, setKeyInput] = useState("");
  const [isKeyLoaded, setIsKeyLoaded] = useState(false);

  const handleLoadKey = () => {
    if (keyInput.trim()) {
      onKeyLoad(keyInput.trim());
      setIsKeyLoaded(true);
      // Do not clear keyInput here, user might need to see it
    }
  };

  if (isKeyLoaded) {
    return (
      <div className="p-4 bg-gray-800 rounded-md border border-green-500">
        <p className="text-green-400 font-semibold">
          ✓ Private Key Loaded for Session
        </p>
        <p className="text-xs text-gray-400 mt-1">
          This key is stored in memory and will be gone on page refresh.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-900 rounded-md border border-yellow-500 space-y-3">
      <h3 className="font-semibold text-yellow-300">
        Action Required: Load Your Private Key
      </h3>
      <p className="text-sm text-gray-400">
        To sign transactions, please paste your private key below. It will not
        be saved anywhere and is only used for this session.
      </p>
      <textarea
        value={keyInput}
        onChange={(e) => setKeyInput(e.target.value)}
        placeholder="-----BEGIN PRIVATE KEY----- ... -----END PRIVATE KEY-----"
        className="w-full h-24 p-2 bg-gray-800 border border-gray-600 rounded-md font-mono text-xs"
      />
      <button
        onClick={handleLoadKey}
        disabled={!keyInput.trim()}
        className="w-full py-2 px-4 bg-yellow-600 hover:bg-yellow-700 rounded-md font-semibold transition disabled:opacity-50"
      >
        Load Key for Session
      </button>
    </div>
  );
};
