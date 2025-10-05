import { useState } from "react";
import { useRoomStore, useUserStore } from "../store/useStore";
import { uploadEvidence } from "../api/api";
import { sendMessage } from "../api/websocket";

const EvidenceUploader = () => {
  const { room } = useRoomStore();
  const { user } = useUserStore();
  const [files, setFiles] = useState<{ [key: string]: File | null }>({});
  const [uploadStatus, setUploadStatus] = useState<{ [key: string]: string }>(
    {}
  );

  if (!room || !user) return null;

  const handleFileChange = (evidenceType: string, file: File | null) => {
    setFiles((prev) => ({ ...prev, [evidenceType]: file }));
  };

  const handleUpload = async (evidenceType: string) => {
    const file = files[evidenceType];
    if (!file || !room.room_phrase) return;

    setUploadStatus((prev) => ({ ...prev, [evidenceType]: "Uploading..." }));
    try {
      await uploadEvidence(room.room_phrase, user.user_id, file, evidenceType);
      setUploadStatus((prev) => ({ ...prev, [evidenceType]: "Success!" }));
    } catch (error) {
      setUploadStatus((prev) => ({ ...prev, [evidenceType]: "Failed." }));
    }
  };

  const allEvidenceSubmitted = room.required_evidence?.every(
    (type) => room.submitted_evidence && room.submitted_evidence[type]
  );

  const getEvidenceTypeDescription = (type: string) => {
    switch (type) {
      case "file_upload":
        return "Upload the completed work or deliverable";
      case "screenshot_of_deliverable":
        return "Screenshot showing the completed work";
      case "calendar_proof":
        return "Calendar or scheduling proof for timed services";
      case "both_parties_confirmation_messages":
        return "Chat messages confirming completion";
      case "completed_work_upload":
        return "Upload the completed work files";
      case "acceptance_communication":
        return "Communication showing buyer acceptance";
      case "public_link_to_post":
        return "Public link to social media post or content";
      case "screenshot_with_timestamp":
        return "Screenshot with visible timestamp";
      default:
        return "Upload evidence for this requirement";
    }
  };

  return (
    <div className="mt-6 p-4 bg-red-900/50 border border-red-700 rounded-md">
      <div className="flex items-center mb-4">
        <div className="w-3 h-3 bg-red-400 rounded-full mr-3 animate-pulse"></div>
        <h3 className="text-lg font-semibold text-red-300">
          Dispute: Submit Evidence
        </h3>
      </div>
      
      <p className="text-sm text-gray-300 mb-4">
        The AI arbiter requires the following evidence to make a decision. Please upload all requested materials.
      </p>

      <div className="space-y-4">
        {room.required_evidence?.map((type) => (
          <div key={type} className="bg-gray-800 p-3 rounded-md">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium capitalize text-gray-300">
                {type.replace(/_/g, " ")}
              </label>
              {room.submitted_evidence?.[type] && (
                <span className="text-green-400 text-sm flex items-center">
                  ✓ Submitted
                </span>
              )}
            </div>
            
            <p className="text-xs text-gray-400 mb-3">
              {getEvidenceTypeDescription(type)}
            </p>
            
            <div className="flex items-center space-x-2">
              <input
                type="file"
                accept="image/*,.pdf,.doc,.docx,.txt,.zip"
                onChange={(e) =>
                  handleFileChange(
                    type,
                    e.target.files ? e.target.files[0] : null
                  )
                }
                className="flex-1 text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-cyan-300 hover:file:bg-gray-600"
              />
              <button
                onClick={() => handleUpload(type)}
                disabled={!files[type] || uploadStatus[type] === "Uploading..."}
                className="py-2 px-3 bg-gray-600 hover:bg-gray-500 rounded-md text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploadStatus[type] === "Uploading..." ? "..." : "Upload"}
              </button>
            </div>
            
            {uploadStatus[type] && (
              <p className={`text-xs mt-2 ${
                uploadStatus[type] === "Success!" ? "text-green-400" : 
                uploadStatus[type] === "Failed." ? "text-red-400" : 
                "text-yellow-400"
              }`}>
                {uploadStatus[type]}
              </p>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 p-3 bg-gray-800 rounded-md">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-300">Evidence Progress:</span>
          <span className="text-sm text-gray-300">
            {room.required_evidence?.filter(type => 
              room.submitted_evidence?.[type]
            ).length || 0} / {room.required_evidence?.length || 0}
          </span>
        </div>
        
        <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
          <div 
            className="bg-cyan-400 h-2 rounded-full transition-all duration-300"
            style={{ 
              width: `${((room.required_evidence?.filter(type => 
                room.submitted_evidence?.[type]
              ).length || 0) / (room.required_evidence?.length || 1)) * 100}%` 
            }}
          ></div>
        </div>

        <button
          onClick={() => sendMessage({ type: "finalize_submission" })}
          disabled={!allEvidenceSubmitted}
          className="w-full py-2 px-4 bg-red-600 hover:bg-red-700 rounded-md font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {allEvidenceSubmitted ? "Finalize & Submit to AI" : "Complete All Evidence First"}
        </button>
      </div>
    </div>
  );
};

export default EvidenceUploader;
