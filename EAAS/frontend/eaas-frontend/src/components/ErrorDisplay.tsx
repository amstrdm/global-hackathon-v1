import React, { useEffect } from "react";
import { useErrorStore } from "../store/useStore";

const ErrorDisplay: React.FC = () => {
  const { errors, removeError } = useErrorStore();

  useEffect(() => {
    // Auto-remove errors after 5 seconds
    const timers = errors.map((error) =>
      setTimeout(() => {
        removeError(error.id);
      }, 5000)
    );

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [errors, removeError]);

  if (errors.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
      {errors.map((error) => (
        <div
          key={error.id}
          className={`p-4 rounded-lg shadow-lg border-l-4 ${
            error.type === "error"
              ? "bg-red-900 border-red-500 text-red-100"
              : error.type === "warning"
              ? "bg-yellow-900 border-yellow-500 text-yellow-100"
              : error.type === "success"
              ? "bg-green-900 border-green-500 text-green-100"
              : "bg-blue-900 border-blue-500 text-blue-100"
          }`}
        >
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <p className="font-semibold capitalize">{error.type}</p>
              <p className="text-sm mt-1">{error.message}</p>
            </div>
            <button
              onClick={() => removeError(error.id)}
              className="ml-2 text-gray-400 hover:text-white transition-colors"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ErrorDisplay;
