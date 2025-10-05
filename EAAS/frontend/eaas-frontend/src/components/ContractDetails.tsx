import { useRoomStore } from "../store/useStore";

const ContractDetails = () => {
  const { room } = useRoomStore();

  if (!room || !room.contract) return null;

  const contract = room.contract;

  return (
    <div className="mt-6 p-4 bg-gray-900 rounded-md">
      <h3 className="text-lg font-semibold mb-3">Contract Details</h3>
      
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Contract ID:</span>
          <span className="text-cyan-400 font-mono text-xs">
            {contract.contract_id?.slice(0, 16)}...
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Status:</span>
          <span className={`font-mono ${
            contract.status === "COMPLETED" ? "text-green-400" : "text-yellow-400"
          }`}>
            {contract.status}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Funds Locked:</span>
          <span className={contract.funds_locked ? "text-green-400" : "text-red-400"}>
            {contract.funds_locked ? "Yes" : "No"}
          </span>
        </div>

        {contract.released_to && (
          <div className="flex justify-between">
            <span className="text-gray-400">Released To:</span>
            <span className="text-green-400 font-mono text-xs">
              {contract.released_to}
            </span>
          </div>
        )}

        {contract.released_at && (
          <div className="flex justify-between">
            <span className="text-gray-400">Released At:</span>
            <span className="text-gray-300 text-xs">
              {new Date(contract.released_at).toLocaleString()}
            </span>
          </div>
        )}

        {/* Signatures */}
        <div className="border-t border-gray-700 pt-3">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Signatures</h4>
          <div className="space-y-2">
            {Object.entries(contract.signatures || {}).map(([party, sig]: [string, any]) => (
              <div key={party} className="flex justify-between items-center">
                <span className="text-gray-400 capitalize">{party.replace(/_/g, " ")}:</span>
                <div className="text-right">
                  <span className={`text-xs ${
                    sig.verified ? "text-green-400" : "text-gray-500"
                  }`}>
                    {sig.verified ? "✓ Verified" : "✗ Not signed"}
                  </span>
                  {sig.decision && (
                    <p className="text-xs text-gray-400">
                      {sig.decision.replace(/_/g, " ")}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContractDetails;
