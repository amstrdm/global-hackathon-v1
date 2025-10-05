import { useRoomStore } from "../store/useStore";

const AIVerdict = () => {
  const { room } = useRoomStore();

  if (!room || !room.ai_verdict) return null;

  const verdict = room.ai_verdict;

  return (
    <div className="mt-6 p-4 bg-gray-900 rounded-md border border-gray-700">
      <h3 className="text-lg font-semibold mb-3 text-cyan-400">AI Arbitration Result</h3>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Decision:</span>
          <span className={`text-xl font-bold ${
            verdict.decision === "APPROVE" ? "text-green-400" : "text-red-400"
          }`}>
            {verdict.decision === "APPROVE" ? "✓ APPROVED" : "✗ REJECTED"}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-400">Confidence:</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  verdict.final_confidence > 0.75 ? "bg-green-400" : "bg-red-400"
                }`}
                style={{ width: `${(verdict.final_confidence || 0) * 100}%` }}
              ></div>
            </div>
            <span className="text-sm text-gray-300">
              {Math.round((verdict.final_confidence || 0) * 100)}%
            </span>
          </div>
        </div>

        {verdict.reasoning && (
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Reasoning:</h4>
            <p className="text-sm text-gray-300 bg-gray-800 p-3 rounded">
              {verdict.reasoning}
            </p>
          </div>
        )}

        {verdict.summary_of_evidence && (
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Evidence Summary:</h4>
            <p className="text-sm text-gray-300 bg-gray-800 p-3 rounded">
              {verdict.summary_of_evidence}
            </p>
          </div>
        )}

        <div className="border-t border-gray-700 pt-3">
          <p className="text-xs text-gray-500">
            This decision is final and binding. Funds will be released according to the AI's verdict.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIVerdict;
