import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "../store/useStore";
import { registerUser } from "../api/api";
import { generateKeyPair } from "../lib/crypto";

const Home = () => {
  const [username, setUsername] = useState("");
  const [role, setRole] = useState<"BUYER" | "SELLER">("BUYER");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useUserStore();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) {
      setError("Username is required.");
      return;
    }
    
    if (username.length < 3) {
      setError("Username must be at least 3 characters long.");
      return;
    }
    
    setLoading(true);
    setError("");

    try {
      const { publicKey, publicKeyHex, privateKeyHex } = generateKeyPair();
      const response = await registerUser(
        username.toLowerCase().trim(),
        role,
        publicKey
      );

      setUser({
        user_id: response.data.user_id,
        username: response.data.username,
        role: response.data.role,
        public_key: publicKeyHex, // Store hex format for localStorage
        private_key: privateKeyHex, // Store hex format for localStorage
      });

      navigate("/dashboard");
    } catch (err: any) {
      console.error("Registration Error:", err);
      
      if (err.response?.status === 409) {
        setError("Username is already taken. Please choose a different one.");
      } else if (err.response?.status === 400) {
        setError("Invalid input. Please check your details and try again.");
      } else if (err.code === 'NETWORK_ERROR' || !err.response) {
        setError("Unable to connect to server. Please check your internet connection.");
      } else {
        setError(err.response?.data?.detail || "Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-8 bg-gray-800 rounded-lg shadow-xl">
      <h2 className="text-2xl font-bold mb-6 text-center">Register or Login</h2>
      <form onSubmit={handleRegister}>
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
            className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md focus:ring-cyan-500 focus:border-cyan-500"
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
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md font-semibold transition disabled:opacity-50"
        >
          {loading ? "Registering..." : "Enter"}
        </button>
      </form>
    </div>
  );
};

export default Home;
