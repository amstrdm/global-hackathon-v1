import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUserStore } from "../store/useStore";
import { createRoom, getRooms, getWallet } from "../api/api";
import WalletDisplay from "../components/WalletDisplay";
import AnimatedBackground from "../components/AnimatedBackground";
import GlassSurface from "../components/GlassSurface";

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
    <div className="relative min-h-screen overflow-hidden">
      <AnimatedBackground status="room" />
      
      <div className="relative z-10 max-w-6xl mx-auto p-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-3xl text-white font-light" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
                    Welcome, <span className="text-cyan-400">{user?.username}</span>
                  </h2>
                  <p className="text-gray-300 text-xl font-light" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
                    You are a {user?.role}
                  </p>
                </div>
                <GlassSurface
                  width={120}
                  height={50}
                  borderRadius={25}
                  brightness={50}
                  opacity={0.8}
                  className="cursor-pointer hover:brightness-70 transition-all duration-300"
                  onClick={logout}
                >
                  <div className="flex items-center justify-center h-full">
                    <span 
                      className="text-white text-lg font-light"
                      style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                    >
                      Logout
                    </span>
                  </div>
                </GlassSurface>
              </div>

              <div className="border-t border-white/20 my-6"></div>

            {user?.role === "SELLER" ? (
              <div>
                <h3 className="text-2xl text-white mb-6 font-light" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
                  Create New Escrow Room
                </h3>
                <form onSubmit={handleCreateRoom}>
                  <div className="mb-6">
                    <label
                      htmlFor="amount"
                      className="block text-xl text-gray-300 mb-4 font-light"
                      style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                    >
                      Transaction Amount
                    </label>
                    <input
                      id="amount"
                      type="number"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="w-full max-w-md p-4 text-xl text-center bg-white/5 backdrop-blur-sm border border-white/20 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:border-white/60 focus:bg-white/10 focus:ring-4 focus:ring-white/10 transition-all duration-300"
                      style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif', fontWeight: '300' }}
                      placeholder="e.g., 500"
                      required
                    />
                  </div>
                  {error && <p className="text-red-400 text-xl mb-4 font-light" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>{error}</p>}
                  <GlassSurface
                    width={200}
                    height={60}
                    borderRadius={30}
                    brightness={loading ? 30 : 60}
                    opacity={loading ? 0.6 : 0.9}
                    className={`cursor-pointer transition-all duration-300 ${
                      loading 
                        ? 'cursor-not-allowed' 
                        : 'hover:brightness-80 hover:scale-105'
                    }`}
                    onClick={loading ? undefined : () => handleCreateRoom({ preventDefault: () => {} } as any)}
                  >
                    <div className="flex items-center justify-center h-full">
                      <span 
                        className="text-white text-xl font-light"
                        style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                      >
                        {loading ? "Creating..." : "Create Room"}
                      </span>
                    </div>
                  </GlassSurface>
                </form>
              </div>
            ) : (
              <div>
                <h3 className="text-2xl text-white mb-6 font-light" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
                  Join an Escrow Room
                </h3>
                <form onSubmit={handleJoinRoom} className="mb-6">
                  <div className="mb-6">
                    <label
                      htmlFor="roomPhrase"
                      className="block text-xl text-gray-300 mb-4 font-light"
                      style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                    >
                      4-Word Room Phrase
                    </label>
                    <input
                      id="roomPhrase"
                      type="text"
                      value={roomPhrase}
                      onChange={(e) => setRoomPhrase(e.target.value)}
                      className="w-full max-w-md p-4 text-xl text-center bg-white/5 backdrop-blur-sm border border-white/20 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:border-white/60 focus:bg-white/10 focus:ring-4 focus:ring-white/10 transition-all duration-300"
                      style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif', fontWeight: '300' }}
                      placeholder="word-word-word-word"
                      required
                    />
                  </div>
                  <GlassSurface
                    width={180}
                    height={60}
                    borderRadius={30}
                    brightness={60}
                    opacity={0.9}
                    className="cursor-pointer hover:brightness-80 hover:scale-105 transition-all duration-300"
                    onClick={() => handleJoinRoom({ preventDefault: () => {} } as any)}
                  >
                    <div className="flex items-center justify-center h-full">
                      <span 
                        className="text-white text-xl font-light"
                        style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}
                      >
                        Join Room
                      </span>
                    </div>
                  </GlassSurface>
                </form>

                {/* Available Rooms */}
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="text-xl text-white" style={{ fontFamily: 'Times New Roman, serif' }}>
                      Available Rooms
                    </h4>
                    <GlassSurface
                      width={100}
                      height={40}
                      borderRadius={20}
                      brightness={roomsLoading ? 30 : 50}
                      opacity={roomsLoading ? 0.6 : 0.8}
                      className={`cursor-pointer transition-all duration-300 ${
                        roomsLoading ? 'cursor-not-allowed' : 'hover:brightness-70'
                      }`}
                      onClick={roomsLoading ? undefined : fetchAvailableRooms}
                    >
                      <div className="flex items-center justify-center h-full">
                        <span 
                          className="text-white text-sm"
                          style={{ fontFamily: 'Brush Script MT, cursive, serif' }}
                        >
                          {roomsLoading ? "Loading..." : "Refresh"}
                        </span>
                      </div>
                    </GlassSurface>
                  </div>
                  
                  {roomsLoading ? (
                    <p className="text-gray-300 text-xl" style={{ fontFamily: 'Times New Roman, serif' }}>
                      Loading rooms...
                    </p>
                  ) : availableRooms.length > 0 ? (
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {availableRooms.map((room) => (
                        <div
                          key={room.room_phrase}
                          className="cursor-pointer p-4 border border-white/30 hover:border-white hover:bg-white/10 transition-all duration-300"
                          onClick={() => handleJoinRoomById(room.room_phrase)}
                        >
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="font-mono text-cyan-300 text-lg">{room.room_phrase}</p>
                              <p className="text-gray-300 text-lg" style={{ fontFamily: 'Times New Roman, serif' }}>
                                Amount: ${room.amount?.toFixed(2)}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-white text-lg" style={{ fontFamily: 'Times New Roman, serif' }}>
                                {room.status}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-300 text-xl" style={{ fontFamily: 'Times New Roman, serif' }}>
                      No available rooms found.
                    </p>
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
    </div>
  );
};

export default Dashboard;
