import { useRoomStore } from "../store/useStore";
import { WS_BASE_URL } from "./config";

let socket: WebSocket | null = null;

export const connectWebSocket = (room_phrase: string, user_id: string) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    return; // Already connected
  }
  socket = new WebSocket(`${WS_BASE_URL}/${room_phrase}/${user_id}`);

  socket.onopen = () => {
    console.log("WebSocket connection established");
  };

  socket.onmessage = (event) => {
    console.log("Received WebSocket message:", event.data);
    const data = JSON.parse(event.data);
    console.log("Parsed WebSocket data:", data);
    const { setRoom, addMessage, updateState } = useRoomStore.getState();

    switch (data.type) {
      case "connected":
        console.log("WebSocket connected, setting room:", data.room);
        setRoom(data.room);
        break;
      case "state_update":
        console.log("State update received:", data);
        updateState(data);
        // Show success message for payment completion
        if (data.status === "MONEY_SECURED") {
          const successMessage = {
            type: "admin_message",
            message: "✅ Payment successful! Funds have been locked in escrow.",
            timestamp: new Date().toISOString(),
          };
          addMessage(successMessage);
        }
        // Show success message for product delivery
        if (data.status === "PRODUCT_DELIVERED") {
          const successMessage = {
            type: "admin_message",
            message: "✅ Product marked as delivered! Waiting for buyer confirmation.",
            timestamp: new Date().toISOString(),
          };
          addMessage(successMessage);
        }
        // Show success message for transaction completion
        if (data.status === "TRANSACTION SUCCESSFULL" || data.status === "COMPLETE") {
          const successMessage = {
            type: "admin_message",
            message: "🎉 Transaction completed successfully! Funds have been released.",
            timestamp: new Date().toISOString(),
          };
          addMessage(successMessage);
        }
        break;
      case "admin_message":
      case "chat_message":
        addMessage(data);
        break;
      default:
        console.warn("Received unknown message type:", data.type, data);
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    // Could emit error to a global error handler here
  };

  socket.onclose = (event) => {
    console.log("WebSocket connection closed:", event.reason);
    useRoomStore.getState().setRoom(null);
    socket = null;
    
    // If it was an unexpected close, we might want to show an error
    if (event.code !== 1000 && event.code !== 1001) {
      console.error("Unexpected WebSocket close:", event.code, event.reason);
    }
  };
};

export const sendMessage = (message: object) => {
  console.log("Attempting to send WebSocket message:", message);
  
  if (socket && socket.readyState === WebSocket.OPEN) {
    const messageString = JSON.stringify(message);
    console.log("Sending WebSocket message:", messageString);
    socket.send(messageString);
    console.log("WebSocket message sent successfully");
  } else {
    console.error("WebSocket is not connected. Socket state:", socket?.readyState);
  }
};

export const disconnectWebSocket = () => {
  if (socket) {
    socket.close();
  }
};
