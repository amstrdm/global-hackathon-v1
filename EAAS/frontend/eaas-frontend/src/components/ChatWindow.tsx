import React, { useState, useRef, useEffect } from "react";
import { useRoomStore, useUserStore } from "../store/useStore";
import { sendMessage } from "../api/websocket";

const ChatWindow = () => {
  const { room } = useRoomStore();
  const { user } = useUserStore();
  const [message, setMessage] = useState("");
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [room?.messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      sendMessage({ type: "chat_message", message });
      setMessage("");
    }
  };

  return (
    <div className="flex flex-col h-[70vh]">
      <h3 className="text-lg font-semibold mb-2 text-center border-b border-gray-700 pb-2">
        Chat
      </h3>
      <div className="flex-grow overflow-y-auto p-2">
        {room?.messages.map((msg, index) => (
          <div
            key={index}
            className={`mb-3 p-2 rounded-lg max-w-xs ${
              msg.type === "admin_message"
                ? "bg-blue-900 text-center mx-auto text-sm"
                : msg.sender_id === user?.user_id
                ? "bg-cyan-800 ml-auto"
                : "bg-gray-700 mr-auto"
            }`}
          >
            {msg.type === "chat_message" && (
              <p className="font-bold text-sm text-cyan-300">
                {msg.sender_username}
              </p>
            )}
            <p className="text-md">{msg.message}</p>
            <p className="text-xs text-gray-400 text-right mt-1">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSendMessage} className="mt-4 flex">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-grow p-2 bg-gray-700 border border-gray-600 rounded-l-md"
          placeholder="Type a message..."
        />
        <button
          type="submit"
          className="py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-r-md font-semibold"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatWindow;
