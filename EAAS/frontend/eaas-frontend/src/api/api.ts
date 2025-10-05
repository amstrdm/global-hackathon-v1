import axios from "axios";
import { API_BASE_URL } from "./config";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const registerUser = (
  username: string,
  role: "BUYER" | "SELLER",
  public_key: string
) => {
  return apiClient.post("/register", { username, role, public_key });
};

export const createRoom = (user_id: string, amount: number) => {
  return apiClient.post(`/rooms/create/${user_id}`, { amount });
};

export const uploadEvidence = (
  room_phrase: string,
  user_id: string,
  file: File,
  evidence_type: string
) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("evidence_type", evidence_type);

  return apiClient.post(
    `/rooms/${room_phrase}/${user_id}/upload_evidence`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
};

export const getWallet = (user_id: string) => {
  return apiClient.get(`/wallet/${user_id}`);
};

export const getRooms = () => {
  return apiClient.get("/rooms");
};

export const getRoom = (room_phrase: string) => {
  return apiClient.get(`/rooms/${room_phrase}`);
};