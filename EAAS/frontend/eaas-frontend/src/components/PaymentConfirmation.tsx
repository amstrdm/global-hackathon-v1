
interface PaymentConfirmationProps {
  amount: number;
  currentBalance: number;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

const PaymentConfirmation = ({ 
  amount, 
  currentBalance, 
  onConfirm, 
  onCancel, 
  loading = false 
}: PaymentConfirmationProps) => {
  const newBalance = currentBalance - amount;
  const hasInsufficientFunds = currentBalance < amount;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <h3 className="text-xl font-bold mb-4 text-center">Confirm Payment</h3>
          
          <div className="space-y-4">
            <div className="bg-gray-700 p-4 rounded-lg">
              <h4 className="text-lg font-semibold mb-3 text-cyan-300">Payment Details</h4>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Amount to Lock:</span>
                  <span className="text-white font-mono">${amount.toFixed(2)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-400">Current Balance:</span>
                  <span className="text-green-400 font-mono">${currentBalance.toFixed(2)}</span>
                </div>
                
                <div className="border-t border-gray-600 pt-2">
                  <div className="flex justify-between font-semibold">
                    <span className="text-gray-300">After Payment:</span>
                    <span className={`font-mono ${
                      hasInsufficientFunds ? "text-red-400" : "text-white"
                    }`}>
                      ${newBalance.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {hasInsufficientFunds && (
              <div className="bg-red-900/50 border border-red-700 rounded-lg p-3">
                <p className="text-red-300 text-sm text-center">
                  Insufficient funds. You need ${(amount - currentBalance).toFixed(2)} more.
                </p>
              </div>
            )}

            <div className="bg-blue-900/50 border border-blue-700 rounded-lg p-3">
              <p className="text-blue-300 text-sm">
                <strong>Note:</strong> This payment will be locked in escrow until the transaction is completed or disputed.
              </p>
            </div>
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              onClick={onCancel}
              disabled={loading}
              className="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-500 rounded-md font-semibold transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              disabled={hasInsufficientFunds || loading}
              className="flex-1 py-2 px-4 bg-cyan-600 hover:bg-cyan-700 rounded-md font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Processing..." : "Confirm Payment"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentConfirmation;
