import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "../store/useStore";
import { createRoom, registerUser } from "../api/api";
// Import your full crypto library
import {
  generateKeyPair,
  validatePublicKey,
  downloadTextFile,
} from "../lib/crypto";
import AnimatedBackground from "./AnimatedBackground";

// 1. Add the new steps to the Step type
type Step =
  | "welcome"
  | "username"
  | "role"
  | "keyChoice"
  | "generateKey"
  | "useExistingKey"
  | "room";

interface FlowData {
  username: string;
  role: "BUYER" | "SELLER";
  publicKey: string | null;
  privateKey: string | null;
}

const SimpleFlow: React.FC = () => {
  const navigate = useNavigate();
  const { setUser } = useUserStore();
  const [currentStep, setCurrentStep] = useState<Step>("welcome");
  const [flowData, setFlowData] = useState<FlowData>({
    username: "",
    role: "BUYER",
    publicKey: null,
    privateKey: null,
  });

  const [inputValue, setInputValue] = useState("");
  const [hasSavedKey, setHasSavedKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Animation states
  const [textVisible, setTextVisible] = useState(false);
  const [contentVisible, setContentVisible] = useState(false);

  useEffect(() => {
    setTextVisible(false);
    setContentVisible(false);
    const timer1 = setTimeout(() => setTextVisible(true), 100);
    const timer2 = setTimeout(() => setContentVisible(true), 800);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, [currentStep]);

  // 2. Separate registration logic into its own function
  const handleRegister = async (
    publicKey: string,
    privateKey: string | null
  ) => {
    setLoading(true);
    setError("");
    try {
      const response = await registerUser(
        flowData.username,
        flowData.role,
        publicKey
      );
      setUser({
        user_id: response.data.user_id,
        username: response.data.username,
        role: response.data.role,
        public_key: publicKey,
      });
      // Store keys in flowData for the final step
      setFlowData((prev) => ({ ...prev, publicKey, privateKey }));
      setCurrentStep("room"); // Proceed to room step after successful registration
    } catch (err: any) {
      console.error("Registration Error:", err);
      setError(
        err.response?.data?.detail || "Registration failed. Please try again."
      );
      // On failure (e.g., username taken), go back to the username step
      setCurrentStep("username");
    } finally {
      setLoading(false);
    }
  };

  // 3. Update the main "next" handler
  const handleNext = async () => {
    setError("");
    if (currentStep === "welcome") {
      setCurrentStep("username");
    } else if (currentStep === "username") {
      if (inputValue.length < 3) {
        setError("Username must be at least 3 characters");
        return;
      }
      setFlowData((prev) => ({
        ...prev,
        username: inputValue.trim().toLowerCase(),
      }));
      setInputValue("");
      setCurrentStep("role");
    } else if (currentStep === "role") {
      const role = inputValue.toLowerCase();
      if (role !== "buyer" && role !== "seller") {
        setError('Please type "buyer" or "seller"');
        return;
      }
      setFlowData((prev) => ({
        ...prev,
        role: role.toUpperCase() as "BUYER" | "SELLER",
      }));
      setInputValue("");
      setCurrentStep("keyChoice"); // Go to key selection
    } else if (currentStep === "room") {
      if (!inputValue.trim()) {
        setError("An input is required");
        return;
      }
      setLoading(true);
      try {
        if (flowData.role === "SELLER") {
          const amount = parseFloat(inputValue);
          if (isNaN(amount) || amount <= 0) {
            setError("Please enter a valid amount.");
            setLoading(false);
            return;
          }
          const user = useUserStore.getState().user;
          const response = await createRoom(user!.user_id, amount);
          navigate(`/room/${response.data.room.room_phrase}`);
        } else {
          navigate(`/room/${inputValue.trim().toLowerCase()}`);
        }
      } catch (err) {
        setError("Could not create or join the room.");
        setLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleNext();
  };

  // --- Handlers for new steps ---
  const handleGenerateKeys = async () => {
    setLoading(true);
    const { publicKeyPem, privateKeyPem } = await generateKeyPair();
    setFlowData((prev) => ({
      ...prev,
      publicKey: publicKeyPem,
      privateKey: privateKeyPem,
    }));
    setLoading(false);
    setCurrentStep("generateKey");
  };

  const handleCopyKey = () => {
    navigator.clipboard.writeText(flowData.privateKey!);
    setHasSavedKey(true);
  };

  const handleDownloadKey = () => {
    downloadTextFile(flowData.privateKey!, "eaas-private-key.pem");
    setHasSavedKey(true);
  };

  const handleValidateExistingKey = async () => {
    const isValid = await validatePublicKey(inputValue);
    if (isValid) {
      handleRegister(inputValue, null); // Register with public key, no private key
    } else {
      setError("Invalid Public Key format. Please check and paste it again.");
    }
  };

  // 4. Create a dynamic content renderer for complex steps
  const renderStepContent = () => {
    const commonInput = (
      <input
        type={stepInfo.inputType}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={stepInfo.placeholder}
        className="w-full max-w-2xl mx-auto px-8 py-6 text-2xl text-center bg-white/5 backdrop-blur-sm border border-white/20 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:border-white/60 focus:bg-white/10 focus:ring-4 focus:ring-white/10 transition-all duration-300 font-light"
        autoFocus
      />
    );

    switch (currentStep) {
      case "keyChoice":
        return (
          <div className="space-y-6">
            <button
              onClick={handleGenerateKeys}
              className="px-12 py-5 text-2xl text-white border-2 border-white/50 hover:border-white hover:bg-white/10 transition-all duration-300 font-light"
            >
              Generate New Keys
            </button>
            <button
              onClick={() => setCurrentStep("useExistingKey")}
              className="px-12 py-5 text-2xl text-white border-2 border-white/50 hover:border-white hover:bg-white/10 transition-all duration-300 font-light"
            >
              Use Existing Key
            </button>
          </div>
        );

      case "generateKey":
        return (
          <div className="max-w-2xl w-full text-left space-y-4">
            <p className="text-yellow-300 text-lg">
              ⚠️ IMPORTANT: Save your private key securely. This is the only
              time you will see it.
            </p>
            <textarea
              readOnly
              value={flowData.privateKey || ""}
              className="w-full h-40 p-4 font-mono text-xs bg-black/20 border border-white/20 rounded-lg text-gray-300"
            />
            <div className="flex gap-4">
              <button
                onClick={handleCopyKey}
                className="flex-1 py-3 text-lg text-white border-2 border-white/50 hover:border-white hover:bg-white/10 transition-all duration-300"
              >
                Copy Key
              </button>
              <button
                onClick={handleDownloadKey}
                className="flex-1 py-3 text-lg text-white border-2 border-white/50 hover:border-white hover:bg-white/10 transition-all duration-300"
              >
                Download
              </button>
            </div>
            <button
              onClick={() =>
                handleRegister(flowData.publicKey!, flowData.privateKey!)
              }
              disabled={!hasSavedKey}
              className="w-full py-4 text-xl text-white bg-green-500/20 border-2 border-green-500/50 hover:border-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              I have saved my key. Continue.
            </button>
          </div>
        );

      case "useExistingKey":
        return (
          <div className="max-w-2xl w-full space-y-4">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="-----BEGIN PUBLIC KEY-----..."
              className="w-full h-40 p-4 font-mono text-xs bg-black/20 border border-white/20 rounded-lg text-white"
            />
            <button
              onClick={handleValidateExistingKey}
              className="w-full py-4 text-xl text-white bg-green-500/20 border-2 border-green-500/50 hover:border-green-400 transition-all"
            >
              Validate & Continue
            </button>
          </div>
        );

      default:
        return currentStep === "welcome" ? (
          <button
            onClick={handleNext}
            className="px-16 py-6 text-3xl text-white border-2 border-white/50 hover:border-white hover:bg-white/10 transition-all duration-300 font-light"
          >
            Continue
          </button>
        ) : (
          commonInput
        );
    }
  };

  const getStepInfo = () => {
    switch (currentStep) {
      case "welcome":
        return {
          title: "Welcome to EAAS",
          subtitle: "Escrow as a Service",
          inputType: "text",
          placeholder: "",
        };
      case "username":
        return {
          title: "What is your username?",
          subtitle: "",
          inputType: "text",
          placeholder: "Enter your username",
        };
      case "role":
        return {
          title: "Are you a buyer or seller?",
          subtitle: "",
          inputType: "text",
          placeholder: 'Type "buyer" or "seller"',
        };
      case "keyChoice":
        return {
          title: "Secure Your Account",
          subtitle: "Choose a key option",
          inputType: "text",
          placeholder: "",
        };
      case "generateKey":
        return {
          title: "Save Your New Key",
          subtitle: "",
          inputType: "text",
          placeholder: "",
        };
      case "useExistingKey":
        return {
          title: "Provide Your Public Key",
          subtitle: "",
          inputType: "text",
          placeholder: "",
        };
      case "room":
        return {
          title:
            flowData.role === "SELLER"
              ? "Set Transaction Amount"
              : "Join a Room",
          subtitle: "",
          inputType: flowData.role === "SELLER" ? "number" : "text",
          placeholder:
            flowData.role === "SELLER" ? "e.g., 500" : "word-word-word-word",
        };
      default:
        return { title: "", subtitle: "", inputType: "text", placeholder: "" };
    }
  };

  const stepInfo = getStepInfo();

  return (
    <div className="relative min-h-screen overflow-hidden">
      <AnimatedBackground status={currentStep} />
      <div className="relative z-10 flex items-center justify-center min-h-screen">
        <div className="text-center space-y-16 max-w-6xl px-8 w-full">
          <div
            className={`transition-all duration-1000 ease-out ${
              textVisible
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-8"
            }`}
          >
            <h1
              className="text-8xl md:text-9xl lg:text-[10rem] font-light text-white leading-none tracking-tight"
              style={{
                fontFamily: "Inter, system-ui, -apple-system, sans-serif",
              }}
            >
              {stepInfo.title}
            </h1>
            {stepInfo.subtitle && (
              <p className="text-4xl md:text-5xl text-gray-300 mt-8 font-light">
                {stepInfo.subtitle}
              </p>
            )}
          </div>

          <div
            className={`transition-all duration-800 ease-out ${
              contentVisible ? "opacity-100" : "opacity-0"
            }`}
          >
            {loading ? (
              <p className="text-2xl text-white">Loading...</p>
            ) : (
              renderStepContent()
            )}
            {error && (
              <p className="text-red-400 text-xl mt-6 font-light">{error}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleFlow;
