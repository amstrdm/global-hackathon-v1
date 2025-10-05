import React from "react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  text?: string;
}

const LoadingSpinner = ({ size = "md", text }: LoadingSpinnerProps) => {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12"
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      <div className={`${sizeClasses[size]} border-2 border-gray-300 border-t-cyan-400 rounded-full animate-spin`}></div>
      {text && (
        <p className="text-sm text-gray-400">{text}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;
