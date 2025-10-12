import React, { useEffect, useState } from "react";
import { useUserStore } from "../store/useStore";
import { getWallet } from "../api/api";

const WalletDisplay = () => {
  const { user, wallet, setWallet } = useUserStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      fetchWallet();
    }
  }, [user]);

  const fetchWallet = async () => {
    if (!user) return;
    
    setLoading(true);
    setError("");
    try {
      const response = await getWallet(user.user_id);
      setWallet(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to fetch wallet");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  if (loading) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg shadow-xl">
        <h3 className="text-lg font-semibold mb-2">Wallet</h3>
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg shadow-xl">
        <h3 className="text-lg font-semibold mb-2">Wallet</h3>
        <p className="text-red-400 text-sm">{error}</p>
        <button
          onClick={fetchWallet}
          className="mt-2 text-cyan-400 hover:text-cyan-300 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-xl">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Wallet</h3>
        <button
          onClick={fetchWallet}
          className="text-cyan-400 hover:text-cyan-300 text-sm"
        >
          Refresh
        </button>
      </div>
      
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-400">Available Balance:</span>
          <span className="text-green-400 font-mono">
            ${wallet?.balance?.toFixed(2) || "0.00"}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Locked in Escrow:</span>
          <span className={`font-mono ${
            (wallet?.locked || 0) > 0 ? "text-yellow-400" : "text-gray-500"
          }`}>
            ${wallet?.locked?.toFixed(2) || "0.00"}
          </span>
        </div>
        
        <div className="flex justify-between border-t border-gray-700 pt-2">
          <span className="text-gray-300 font-semibold">Total:</span>
          <span className="text-white font-mono font-semibold">
            ${((wallet?.balance || 0) + (wallet?.locked || 0)).toFixed(2)}
          </span>
        </div>
      </div>

      {wallet?.transactions && wallet.transactions.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">
            Recent Transactions
          </h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {wallet.transactions.slice(0, 5).map((tx, index) => (
              <div key={index} className="text-xs text-gray-400 flex justify-between">
                <span>{tx.type || "Transaction"}</span>
                <span className={tx.amount > 0 ? "text-green-400" : "text-red-400"}>
                  {tx.amount > 0 ? "+" : ""}${tx.amount?.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WalletDisplay;
