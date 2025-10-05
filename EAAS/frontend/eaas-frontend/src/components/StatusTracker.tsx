import { useRoomStore } from "../store/useStore";

const StatusTracker = ({
  status,
  disputeStatus,
}: {
  status: string;
  disputeStatus: string | null;
}) => {
  const { room } = useRoomStore();

  const getStatusColor = (status: string) => {
    switch (status) {
      case "WAITING_FOR_BUYER":
        return "text-yellow-400";
      case "AWAITING_DESCRIPTION":
        return "text-blue-400";
      case "AWAITING_SELLER_APPROVAL":
      case "AWAITING_BUYER_APPROVAL":
        return "text-orange-400";
      case "AWAITING_SELLER_READY":
        return "text-purple-400";
      case "AWAITING_PAYMENT":
        return "text-cyan-400";
      case "MONEY_SECURED":
        return "text-green-400";
      case "PRODUCT_DELIVERED":
        return "text-emerald-400";
      case "DISPUTE":
        return "text-red-400";
      case "COMPLETE":
      case "TRANSACTION SUCCESSFULL":
        return "text-green-500";
      default:
        return "text-gray-400";
    }
  };

  const getStatusDescription = (status: string) => {
    switch (status) {
      case "WAITING_FOR_BUYER":
        return "Waiting for a buyer to join this room";
      case "AWAITING_DESCRIPTION":
        return "Buyer needs to propose a description for the transaction";
      case "AWAITING_SELLER_APPROVAL":
        return "Seller needs to review and approve the description";
      case "AWAITING_BUYER_APPROVAL":
        return "Buyer needs to review the seller's changes";
      case "AWAITING_SELLER_READY":
        return "Seller needs to confirm they're ready to proceed";
      case "AWAITING_PAYMENT":
        return "Buyer needs to lock funds into escrow. Click 'Lock Funds' to proceed with payment.";
      case "MONEY_SECURED":
        return "Funds are locked. Seller can now deliver the product/service";
      case "PRODUCT_DELIVERED":
        return "Product delivered. Buyer can confirm or dispute";
      case "DISPUTE":
        return "Transaction is in dispute. AI arbitration in progress";
      case "COMPLETE":
      case "TRANSACTION SUCCESSFULL":
        return "Transaction completed successfully!";
      default:
        return "Unknown status";
    }
  };

  return (
    <div className="mb-6 p-4 bg-gray-900 rounded-md">
      <h3 className="text-lg font-semibold mb-3">Transaction Status</h3>

      <div className="space-y-3">
        <div>
          <p className={`text-2xl font-mono ${getStatusColor(status)}`}>
            {status.replace(/_/g, " ")}
          </p>
          <p className="text-sm text-gray-400 mt-1">
            {getStatusDescription(status)}
          </p>
        </div>

        {disputeStatus && (
          <div className="border-t border-gray-700 pt-3">
            <p className="text-lg font-mono text-red-400">
              Dispute: {disputeStatus.replace(/_/g, " ")}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              AI arbitration is in progress
            </p>
          </div>
        )}

        {room && (
          <div className="border-t border-gray-700 pt-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Amount:</span>
              <span className="text-white font-mono">
                ${room.amount?.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Escrow Address:</span>
              <span className="text-cyan-400 font-mono text-xs">
                {room.escrow_address?.slice(0, 10)}...
              </span>
            </div>
            {room.description && (
              <div className="text-sm">
                <span className="text-gray-400">Description:</span>
                <p className="text-gray-300 mt-1 p-2 bg-gray-800 rounded text-xs">
                  {room.description}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusTracker;
