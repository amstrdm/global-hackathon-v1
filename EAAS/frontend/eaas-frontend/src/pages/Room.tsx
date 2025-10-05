import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useUserStore, useRoomStore } from "../store/useStore";
import { connectWebSocket, disconnectWebSocket } from "../api/websocket";
import { getWallet } from "../api/api";
import StatusTracker from "../components/StatusTracker";
import ChatWindow from "../components/ChatWindow";
import ActionPanel from "../components/ActionPanel";
import EvidenceUploader from "../components/EvidenceUploader";
import ContractDetails from "../components/ContractDetails";
import AIVerdict from "../components/AIVerdict";
import WalletDisplay from "../components/WalletDisplay";
import LoadingSpinner from "../components/LoadingSpinner";

const Room = () => {
  const { room_phrase } = useParams<{ room_phrase: string }>();
  const navigate = useNavigate();
  const { user, setWallet } = useUserStore();
  const { room, setRoom } = useRoomStore();
  const [connectionError, setConnectionError] = useState("");

  useEffect(() => {
    if (!room_phrase || !user) {
      navigate("/");
      return;
    }

    setConnectionError("");
    
    // Fetch wallet data when entering room
    const fetchWalletData = async () => {
      try {
        const response = await getWallet(user.user_id);
        setWallet(response.data);
      } catch (error) {
        console.error("Failed to fetch wallet:", error);
        // Set a default wallet if fetch fails
        setWallet({
          user_id: user.user_id,
          balance: 1000, // Default balance for testing
          locked: 0,
          transactions: []
        });
      }
    };
    
    fetchWalletData();
    connectWebSocket(room_phrase, user.user_id);

    return () => {
      disconnectWebSocket();
      setRoom(null); // Clear room state on leaving
    };
  }, [room_phrase, user, navigate, setRoom, setWallet]);

  if (connectionError) {
    return (
      <div className="max-w-2xl mx-auto mt-20 p-8 bg-gray-800 rounded-lg shadow-xl text-center">
        <div className="text-red-400 text-6xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold mb-4">Connection Error</h2>
        <p className="text-gray-300 mb-6">{connectionError}</p>
        <div className="space-x-4">
          <button
            onClick={() => window.location.reload()}
            className="py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md font-semibold transition"
          >
            Retry
          </button>
          <button
            onClick={() => navigate("/dashboard")}
            className="py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md font-semibold transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!room) {
    return (
      <div className="max-w-2xl mx-auto mt-20 p-8 bg-gray-800 rounded-lg shadow-xl text-center">
        <LoadingSpinner size="lg" text="Connecting to room..." />
      </div>
    );
  }

  const showEvidenceUploader =
    room.status === "DISPUTE" &&
    room.dispute_status === "AWAITING_EVIDENCE" &&
    user?.role === "SELLER";


  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-3">
          <div className="bg-gray-800 p-6 rounded-lg shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">
                Transaction Room:{" "}
                <span className="text-cyan-400">{room.room_phrase}</span>
              </h2>
              <button
                onClick={() => navigate("/dashboard")}
                className="py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md font-semibold transition"
              >
                Back to Dashboard
              </button>
            </div>
            
            <StatusTracker
              status={room.status}
              disputeStatus={room.dispute_status}
            />
            
            <ActionPanel />
            
            {showEvidenceUploader && <EvidenceUploader />}
            
            
            {room.contract && <ContractDetails />}
            
            {room.ai_verdict && <AIVerdict />}
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <WalletDisplay />
          <div className="bg-gray-800 p-4 rounded-lg shadow-xl">
            <ChatWindow />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Room;
