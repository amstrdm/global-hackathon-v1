import axios, { AxiosError } from "axios";
import { API_BASE_URL } from "./config";
import { useErrorStore } from "../store/useStore";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor to handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const { addError } = useErrorStore.getState();
    
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;
      
      let errorMessage = data?.detail || `Server error (${status})`;
      
      // Provide specific error messages based on status codes
      switch (status) {
        case 400:
          errorMessage = data?.detail || "Invalid request. Please check your input.";
          break;
        case 401:
          errorMessage = "Authentication required. Please log in again.";
          break;
        case 403:
          errorMessage = "Access denied. You don't have permission to perform this action.";
          break;
        case 404:
          errorMessage = data?.detail || "Resource not found.";
          break;
        case 409:
          errorMessage = data?.detail || "Conflict. The resource already exists.";
          break;
        case 413:
          errorMessage = "File too large. Please choose a smaller file.";
          break;
        case 422:
          errorMessage = data?.detail || "Validation error. Please check your input.";
          break;
        case 500:
          errorMessage = "Internal server error. Please try again later.";
          break;
        case 502:
          errorMessage = "Service temporarily unavailable. Please try again later.";
          break;
        case 503:
          errorMessage = "Service temporarily unavailable. Please try again later.";
          break;
        default:
          errorMessage = data?.detail || `Server error (${status})`;
      }
      
      addError(errorMessage, "error");
    } else if (error.request) {
      // Request was made but no response received
      addError("Network error. Please check your connection.", "error");
    } else {
      // Something else happened
      addError("An unexpected error occurred.", "error");
    }
    
    return Promise.reject(error);
  }
);

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