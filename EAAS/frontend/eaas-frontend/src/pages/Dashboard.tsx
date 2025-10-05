import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "../store/useStore";
import { createRoom, getRooms, getWallet } from "../api/api";
import WalletDisplay from "../components/WalletDisplay";

const Dashboard = () => {
  const { user, logout, setWallet } = useUserStore();
  const navigate = useNavigate();

  // For Seller
  const [amount, setAmount] = useState("");

  // For Buyer
  const [roomPhrase, setRoomPhrase] = useState("");

  // Room listing
  const [availableRooms, setAvailableRooms] = useState<any[]>([]);
  const [roomsLoading, setRoomsLoading] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.role === "BUYER") {
      fetchAvailableRooms();
    }
    
    // Always fetch wallet data when dashboard loads
    if (user) {
      const fetchWallet = async () => {
        try {
          const response = await getWallet(user.user_id);
          setWallet(response.data);
        } catch (error) {
          console.error("Failed to fetch wallet:", error);
        }
      };
      fetchWallet();
    }
  }, [user]);

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || user.role !== "SELLER") return;

    const amountValue = parseFloat(amount);
    if (isNaN(amountValue) || amountValue <= 0) {
      setError("Please enter a valid amount greater than 0.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const response = await createRoom(user.user_id, amountValue);
      navigate(`/room/${response.data.room.room_phrase}`);
    } catch (err: any) {
      console.error("Create room error:", err);
      
      if (err.response?.status === 404) {
        setError("User not found. Please try logging in again.");
      } else if (err.response?.status === 403) {
        setError("Only sellers can create rooms.");
      } else if (err.code === 'NETWORK_ERROR' || !err.response) {
        setError("Unable to connect to server. Please check your internet connection.");
      } else {
        setError(err.response?.data?.detail || "Failed to create room. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableRooms = async () => {
    setRoomsLoading(true);
    try {
      const response = await getRooms();
      setAvailableRooms(response.data);
    } catch (err) {
      console.error("Failed to fetch rooms:", err);
    } finally {
      setRoomsLoading(false);
    }
  };

  const handleJoinRoom = (e: React.FormEvent) => {
    e.preventDefault();
    if (roomPhrase.trim()) {
      navigate(`/room/${roomPhrase.trim().toLowerCase()}`);
    }
  };

  const handleJoinRoomById = (roomPhrase: string) => {
    navigate(`/room/${roomPhrase}`);
  };

  return (
    <div className="max-w-6xl mx-auto mt-10 p-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-lg shadow-xl p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold">Welcome, {user?.username}</h2>
                <p className="text-gray-400">You are a {user?.role}</p>
              </div>
              <button
                onClick={logout}
                className="py-2 px-4 bg-red-600 hover:bg-red-700 rounded-md font-semibold transition"
              >
                Logout
              </button>
            </div>

            <div className="border-t border-gray-700 my-6"></div>

            {user?.role === "SELLER" ? (
              <div>
                <h3 className="text-xl font-semibold mb-4">Create New Escrow Room</h3>
                <form onSubmit={handleCreateRoom}>
                  <div className="mb-4">
                    <label
                      htmlFor="amount"
                      className="block text-sm font-medium text-gray-300 mb-2"
                    >
                      Transaction Amount
                    </label>
                    <input
                      id="amount"
                      type="number"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md"
                      placeholder="e.g., 500"
                      required
                    />
                  </div>
                  {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md font-semibold transition disabled:opacity-50"
                  >
                    {loading ? "Creating..." : "Create Room"}
                  </button>
                </form>
              </div>
            ) : (
              <div>
                <h3 className="text-xl font-semibold mb-4">Join an Escrow Room</h3>
                <form onSubmit={handleJoinRoom} className="mb-6">
                  <div className="mb-4">
                    <label
                      htmlFor="roomPhrase"
                      className="block text-sm font-medium text-gray-300 mb-2"
                    >
                      4-Word Room Phrase
                    </label>
                    <input
                      id="roomPhrase"
                      type="text"
                      value={roomPhrase}
                      onChange={(e) => setRoomPhrase(e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md"
                      placeholder="word-word-word-word"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md font-semibold transition"
                  >
                    Join Room
                  </button>
                </form>

                {/* Available Rooms */}
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="text-lg font-semibold">Available Rooms</h4>
                    <button
                      onClick={fetchAvailableRooms}
                      disabled={roomsLoading}
                      className="text-cyan-400 hover:text-cyan-300 text-sm disabled:opacity-50"
                    >
                      {roomsLoading ? "Loading..." : "Refresh"}
                    </button>
                  </div>
                  
                  {roomsLoading ? (
                    <p className="text-gray-400">Loading rooms...</p>
                  ) : availableRooms.length > 0 ? (
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {availableRooms.map((room) => (
                        <div
                          key={room.room_phrase}
                          className="bg-gray-700 p-3 rounded-md hover:bg-gray-600 transition cursor-pointer"
                          onClick={() => handleJoinRoomById(room.room_phrase)}
                        >
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="font-mono text-cyan-300">{room.room_phrase}</p>
                              <p className="text-sm text-gray-400">
                                Amount: ${room.amount?.toFixed(2)}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-gray-300">{room.status}</p>
                              <p className="text-xs text-gray-500">
                                {room.description ? "Has description" : "No description"}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-400">No available rooms found.</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <WalletDisplay />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
