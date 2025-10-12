import React, { useState, useEffect } from "react";
import { useRoomStore, useUserStore } from "../store/useStore";
import { sendMessage } from "../api/websocket";
import { createContractSignature } from "../lib/crypto";

const ActionButton = ({
  onClick,
  disabled,
  children,
  variant = "primary",
}: {
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
  variant?: "primary" | "secondary";
}) => {
  const baseClasses =
    "w-full py-2 px-4 rounded-md font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed";
  const variantClasses =
    variant === "primary"
      ? "bg-cyan-600 hover:bg-cyan-700"
      : "bg-gray-600 hover:bg-gray-500";

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses}`}
    >
      {children}
    </button>
  );
};

// A new component for the negotiation UI to keep the main panel clean
const DescriptionNegotiation = ({ isMyTurn }: { isMyTurn: boolean }) => {
  const { room } = useRoomStore();
  const [editedDescription, setEditedDescription] = useState(
    room?.description || ""
  );

  // Keep local state in sync with global state from WebSocket
  useEffect(() => {
    setEditedDescription(room?.description || "");
  }, [room?.description]);

  const handleApprove = () => {
    sendMessage({ type: "approve_description" });
  };

  const handleEdit = () => {
    if (editedDescription.trim() !== room?.description) {
      sendMessage({
        type: "edit_description",
        description: editedDescription.trim(),
      });
    }
  };

  if (isMyTurn) {
    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Proposed Description (you can edit below):
          </label>
          <textarea
            value={editedDescription}
            onChange={(e) => setEditedDescription(e.target.value)}
            className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md"
          />
        </div>
        <div className="flex gap-4">
          <ActionButton onClick={handleApprove} variant="primary">
            Approve
          </ActionButton>
          <ActionButton
            onClick={handleEdit}
            variant="secondary"
            disabled={
              editedDescription.trim() === room?.description ||
              !editedDescription.trim()
            }
          >
            Update & Propose
          </ActionButton>
        </div>
      </div>
    );
  }

  return (
    <div>
      <p className="text-gray-400 mb-2">Current Proposal:</p>
      <p className="p-3 bg-gray-900 rounded whitespace-pre-wrap">
        "{room?.description}"
      </p>
      <p className="text-center mt-4 text-yellow-400 animate-pulse">
        Waiting for the other party to respond...
      </p>
    </div>
  );
};

const ActionPanel = () => {
  const { room } = useRoomStore();
  const { user } = useUserStore();
  const [description, setDescription] = useState("");

  if (!room || !user) return null;

  const isBuyer = user.user_id === room.buyer_id;
  const isSeller = user.user_id === room.seller_id;

  const handleSign = (decision: "RELEASE_TO_SELLER" | "REFUND_TO_BUYER") => {
    // HOTFIX: Bypass signature creation for now
    console.log("HOTFIX: Bypassing signature creation");
    
    try {
      if (decision === "RELEASE_TO_SELLER") {
        if (isBuyer) {
          sendMessage({
            type: "transaction_successfull",
            signed_message: "hotfix_signature_buyer",
          });
        }
        if (isSeller) {
          sendMessage({ 
            type: "product_delivered", 
            signed_message: "hotfix_signature_seller" 
          });
        }
      }
    } catch (error) {
      console.error("Error in handleSign:", error);
      alert(`Failed to send message: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const renderActions = () => {
    switch (room.status) {
      case "AWAITING_DESCRIPTION":
        if (isBuyer) {
          return (
            <div>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md mb-2"
                placeholder="Describe the product or service..."
              ></textarea>
              <ActionButton
                onClick={() =>
                  sendMessage({ type: "propose_description", description })
                }
                disabled={!description.trim()}
              >
                Propose Description
              </ActionButton>
            </div>
          );
        }
        return <p>Waiting for buyer to propose a description.</p>;

      case "AWAITING_SELLER_APPROVAL":
        return <DescriptionNegotiation isMyTurn={isSeller} />;

      case "AWAITING_BUYER_APPROVAL":
        return <DescriptionNegotiation isMyTurn={isBuyer} />;

      case "AWAITING_SELLER_READY":
        if (isSeller) {
          return (
            <ActionButton
              onClick={() => sendMessage({ type: "confirm_seller_ready" })}
            >
              I am Ready to Proceed
            </ActionButton>
          );
        }
        return (
          <p>
            Description approved. Waiting for seller to confirm they are ready.
          </p>
        );

      case "AWAITING_PAYMENT":
        if (isBuyer) {
          return (
            <ActionButton
              onClick={() => sendMessage({ type: "buyer_lock_funds" })}
            >
              Lock Funds (${room.amount})
            </ActionButton>
          );
        }
        return <p>Waiting for buyer to lock funds into escrow.</p>;

      case "MONEY_SECURED":
        if (isSeller) {
          return (
            <ActionButton onClick={() => handleSign("RELEASE_TO_SELLER")}>
              Confirm Product Delivered
            </ActionButton>
          );
        }
        return (
          <p>
            Funds are secured. Waiting for seller to deliver the
            product/service.
          </p>
        );

      case "PRODUCT_DELIVERED":
        if (isBuyer) {
          return (
            <div className="space-y-2">
              <ActionButton onClick={() => handleSign("RELEASE_TO_SELLER")}>
                Confirm & Release Funds
              </ActionButton>
              <button
                onClick={() => sendMessage({ type: "init_dispute" })}
                className="w-full py-2 px-4 bg-red-600 hover:bg-red-700 rounded-md font-semibold transition"
              >
                Initiate Dispute
              </button>
            </div>
          );
        }
        return (
          <p>
            Product marked as delivered. Waiting for buyer's confirmation or
            dispute.
          </p>
        );

      case "DISPUTE":
        return (
          <p className="text-red-400">
            Transaction is in dispute. Follow instructions.
          </p>
        );

      case "COMPLETE":
      case "TRANSACTION SUCCESSFULL":
        return <p className="text-green-400">Transaction Complete!</p>;

      default:
        return <p>Waiting for participants...</p>;
    }
  };

  return (
    <div className="mt-6 p-4 bg-gray-900 rounded-md">
      <h3 className="text-lg font-semibold mb-4">Actions</h3>
      {renderActions()}
    </div>
  );
};

export default ActionPanel;
