import { useRoomStore, useErrorStore } from "../store/useStore";
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
    const { addError } = useErrorStore.getState();

    switch (data.type) {
      case "connected":
        console.log("WebSocket connected, setting room:", data.room);
        setRoom(data.room);
        addError("Connected to room successfully!", "success");
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
          addError("Payment successful! Funds locked in escrow.", "success");
        }
        // Show success message for product delivery
        if (data.status === "PRODUCT_DELIVERED") {
          const successMessage = {
            type: "admin_message",
            message: "✅ Product marked as delivered! Waiting for buyer confirmation.",
            timestamp: new Date().toISOString(),
          };
          addMessage(successMessage);
          addError("Product marked as delivered!", "info");
        }
        // Show success message for transaction completion
        if (data.status === "TRANSACTION SUCCESSFULL" || data.status === "COMPLETE") {
          const successMessage = {
            type: "admin_message",
            message: "🎉 Transaction completed successfully! Funds have been released.",
            timestamp: new Date().toISOString(),
          };
          addMessage(successMessage);
          addError("Transaction completed successfully!", "success");
        }
        break;
      case "error":
        console.error("WebSocket error received:", data.message);
        addError(data.message, "error");
        break;
      case "admin_message":
      case "chat_message":
        addMessage(data);
        break;
      default:
        console.warn("Received unknown message type:", data.type, data);
        addError(`Unknown message type received: ${data.type}`, "warning");
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    const { addError } = useErrorStore.getState();
    addError("WebSocket connection error occurred", "error");
  };

  socket.onclose = (event) => {
    console.log("WebSocket connection closed:", event.reason);
    const { setRoom } = useRoomStore.getState();
    const { addError } = useErrorStore.getState();
    
    setRoom(null);
    socket = null;
    
    // If it was an unexpected close, show an error
    if (event.code !== 1000 && event.code !== 1001) {
      console.error("Unexpected WebSocket close:", event.code, event.reason);
      let errorMessage = "Connection closed unexpectedly";
      
      // Provide specific error messages based on close codes
      switch (event.code) {
        case 1008:
          errorMessage = event.reason || "Policy violation - you may not have permission to access this room";
          break;
        case 1011:
          errorMessage = "Server error occurred";
          break;
        case 1002:
          errorMessage = "Protocol error";
          break;
        case 1003:
          errorMessage = "Unsupported data type";
          break;
        default:
          errorMessage = event.reason || "Connection closed unexpectedly";
      }
      
      addError(errorMessage, "error");
    }
  };
};

export const sendMessage = (message: object) => {
  console.log("Attempting to send WebSocket message:", message);
  const { addError } = useErrorStore.getState();
  
  if (socket && socket.readyState === WebSocket.OPEN) {
    try {
      const messageString = JSON.stringify(message);
      console.log("Sending WebSocket message:", messageString);
      socket.send(messageString);
      console.log("WebSocket message sent successfully");
    } catch (error) {
      console.error("Error sending WebSocket message:", error);
      addError("Failed to send message", "error");
    }
  } else {
    console.error("WebSocket is not connected. Socket state:", socket?.readyState);
    addError("Not connected to room. Please refresh and try again.", "error");
  }
};

export const disconnectWebSocket = () => {
  if (socket) {
    socket.close();
  }
};
