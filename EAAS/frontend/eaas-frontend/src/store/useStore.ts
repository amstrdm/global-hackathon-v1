import { create } from "zustand";
import { persist } from "zustand/middleware";

// Define types based on backend documentation
interface User {
  user_id: string;
  username: string;
  role: "BUYER" | "SELLER";
  public_key: string; // Hex format for localStorage
  private_key_obj?: any; // Raw key object for signing (not persisted)
}

interface Wallet {
  user_id: string;
  balance: number;
  locked: number;
  transactions: any[];
}

interface RoomState {
  room_phrase: string;
  seller_id: string;
  buyer_id: string | null;
  amount: number;
  description: string | null;
  status: string;
  contract: any | null;
  dispute_status: string | null;
  escrow_address: string;
  required_evidence: string[] | null;
  submitted_evidence: any | null;
  ai_verdict: any | null;
  messages: any[];
}

interface UserState {
  user: User | null;
  wallet: Wallet | null;
  setUser: (user: User | null) => void;
  setWallet: (wallet: Wallet | null) => void;
  logout: () => void;
}

interface RoomStore {
  room: RoomState | null;
  setRoom: (room: RoomState | null) => void;
  addMessage: (message: any) => void;
  updateState: (updates: Partial<RoomState>) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      wallet: null,
      setUser: (user) => set({ user }),
      setWallet: (wallet) => set({ wallet }),
      logout: () => set({ user: null, wallet: null }),
    }),
    {
      name: "eaas-user-storage", // key in localStorage
    }
  )
);

export const useRoomStore = create<RoomStore>((set) => ({
  room: null,
  setRoom: (room) => set({ room }),
  addMessage: (message) =>
    set((state) => ({
      room: state.room
        ? { ...state.room, messages: [...state.room.messages, message] }
        : null,
    })),
  updateState: (updates) =>
    set((state) => ({
      room: state.room ? { ...state.room, ...updates } : null,
    })),
}));
