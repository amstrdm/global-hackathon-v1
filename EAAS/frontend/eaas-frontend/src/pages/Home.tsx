import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "../store/useStore";
import { registerUser } from "../api/api";
import GenerateKeyStep from "../components/GenerateKeyStep";
import UseExistingKeyStep from "../components/UseExistingKeyStep";

type Step = "details" | "keyChoice" | "generate" | "existing";

const Home = () => {
  const [username, setUsername] = useState("");
  const [role, setRole] = useState<"BUYER" | "SELLER">("BUYER");
  const [step, setStep] = useState<Step>("details");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useUserStore();

  const handleDetailsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || username.length < 3) {
      setError("Username must be at least 3 characters long.");
      return;
    }
    setError("");
    setStep("keyChoice");
  };

  const handleRegister = async (
    publicKey: string,
    privateKey: string | null = null
  ) => {
    setLoading(true);
    setError("");
    try {
      const response = await registerUser(
        username.toLowerCase().trim(),
        role,
        publicKey
      );
      setUser({
        user_id: response.data.user_id,
        username: response.data.username,
        role: response.data.role,
        public_key: publicKey,
        private_key: privateKey, // Will be null if user provided their own key
      });
      navigate("/dashboard");
    } catch (err: any) {
      console.error("Registration Error:", err);
      if (err.response?.status === 409) {
        setError(
          "Username is already taken. Please go back and choose a different one."
        );
      } else {
        setError(
          err.response?.data?.detail || "Registration failed. Please try again."
        );
      }
      setStep("details"); // Go back to the first step on error
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case "details":
        return (
          <form onSubmit={handleDetailsSubmit}>
            <div className="mb-4">
              <label
                htmlFor="username"
                className="block mb-2 text-sm font-medium text-gray-300"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md"
                placeholder="e.g., satoshi"
              />
            </div>
            <div className="mb-6">
              <label
                htmlFor="role"
                className="block mb-2 text-sm font-medium text-gray-300"
              >
                Role
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value as "BUYER" | "SELLER")}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md"
              >
                <option value="BUYER">Buyer</option>
                <option value="SELLER">Seller</option>
              </select>
            </div>
            <button
              type="submit"
              className="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md"
            >
              Next
            </button>
          </form>
        );
      case "keyChoice":
        return (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-center">
              Secure Your Account
            </h3>
            <p className="text-center mb-4">
              Every account needs a cryptographic key pair to sign transactions.
            </p>
            <div className="space-y-4">
              <button
                onClick={() => setStep("generate")}
                className="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md"
              >
                Generate a New Key Pair for Me
              </button>
              <button
                onClick={() => setStep("existing")}
                className="w-full py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md"
              >
                I Have an Existing Key Pair
              </button>
              <button
                onClick={() => setStep("details")}
                className="w-full mt-2 py-2 text-sm text-gray-400 hover:text-white"
              >
                Back
              </button>
            </div>
          </div>
        );
      case "generate":
        return (
          <GenerateKeyStep
            onComplete={handleRegister}
            onBack={() => setStep("keyChoice")}
          />
        );
      case "existing":
        return (
          <UseExistingKeyStep
            onComplete={handleRegister}
            onBack={() => setStep("keyChoice")}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-8 bg-gray-800 rounded-lg shadow-xl">
      <h2 className="text-2xl font-bold mb-6 text-center">Register or Login</h2>
      {error && (
        <p className="text-red-500 text-sm mb-4 text-center">{error}</p>
      )}
      {loading ? <p className="text-center">Registering...</p> : renderStep()}
    </div>
  );
};

export default Home;
