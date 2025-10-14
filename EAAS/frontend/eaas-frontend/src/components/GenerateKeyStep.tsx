import { useState } from "react";
import { generateKeyPair, downloadTextFile } from "../lib/crypto";

interface Props {
  onComplete: (publicKey: string, privateKey: string) => void;
  onBack: () => void;
}

const GenerateKeyStep = ({ onComplete, onBack }: Props) => {
  const [keys, setKeys] = useState<{ pub: string; priv: string } | null>(null);
  const [hasCopied, setHasCopied] = useState(false);
  const [hasDownloaded, setHasDownloaded] = useState(false);

  const handleGenerate = async () => {
    const { publicKeyPem, privateKeyPem } = await generateKeyPair();
    setKeys({ pub: publicKeyPem, priv: privateKeyPem });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(keys!.priv);
    setHasCopied(true);
  };

  const handleDownload = () => {
    downloadTextFile(keys!.priv, "escrow-private-key.pem");
    setHasDownloaded(true);
  };

  if (!keys) {
    return (
      <div>
        <p className="mb-4">We'll now generate a secure key pair for you.</p>
        <button
          onClick={handleGenerate}
          className="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md"
        >
          Generate Keys
        </button>
        <button
          onClick={onBack}
          className="w-full mt-2 py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md"
        >
          Back
        </button>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-bold text-yellow-400 mb-2">
        IMPORTANT: Save Your Private Key!
      </h3>
      <p className="mb-4 text-sm">
        This is the ONLY time you will see your private key. Store it securely.
        If you lose it, your funds are lost forever.
      </p>
      <textarea
        readOnly
        value={keys.priv}
        className="w-full h-32 p-2 bg-gray-900 border border-gray-600 rounded-md font-mono text-xs"
      />
      <div className="flex gap-4 my-4">
        <button
          onClick={handleCopy}
          className="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md"
        >
          {hasCopied ? "Copied!" : "Copy Key"}
        </button>
        <button
          onClick={handleDownload}
          className="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md"
        >
          Download Key
        </button>
      </div>
      <button
        onClick={() => onComplete(keys.pub, keys.priv)}
        disabled={!hasCopied && !hasDownloaded}
        className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 rounded-md disabled:opacity-50"
      >
        I have saved my key. Complete Registration
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

export default GenerateKeyStep;
