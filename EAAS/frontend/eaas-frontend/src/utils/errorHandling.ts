import { useErrorStore } from "../store/useStore";

export interface ApiError {
  status: number;
  message: string;
  details?: any;
}

export const handleApiError = (error: any): ApiError => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data;
    
    return {
      status,
      message: data?.detail || `Server error (${status})`,
      details: data
    };
  } else if (error.request) {
    // Request was made but no response received
    return {
      status: 0,
      message: "Network error. Please check your connection."
    };
  } else {
    // Something else happened
    return {
      status: -1,
      message: "An unexpected error occurred."
    };
  }
};

export const showApiError = (error: any, customMessage?: string) => {
  const { addError } = useErrorStore.getState();
  const apiError = handleApiError(error);
  
  const message = customMessage || apiError.message;
  addError(message, "error");
  
  return apiError;
};

export const showSuccess = (message: string) => {
  const { addError } = useErrorStore.getState();
  addError(message, "success");
};

export const showWarning = (message: string) => {
  const { addError } = useErrorStore.getState();
  addError(message, "warning");
};

export const showInfo = (message: string) => {
  const { addError } = useErrorStore.getState();
  addError(message, "info");
};
