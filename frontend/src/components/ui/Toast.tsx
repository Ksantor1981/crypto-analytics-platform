'use client';

import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ToastProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  onClose: () => void;
}

export interface ToastMessage extends Omit<ToastProps, 'onClose'> {
  id: string;
}

const toastStyles = {
  success: 'bg-green-100 border-green-500 text-green-900',
  error: 'bg-red-100 border-red-500 text-red-900',
  warning: 'bg-yellow-100 border-yellow-500 text-yellow-900',
  info: 'bg-blue-100 border-blue-500 text-blue-900',
};

export const Toast: React.FC<ToastProps> = ({
  type,
  title,
  message,
  onClose,
}) => {
  return (
    <div
      className={`${toastStyles[type]} p-4 rounded-lg border shadow-lg min-w-[300px] max-w-md flex items-start gap-2`}
      role="alert"
    >
      <div className="flex-1">
        <h3 className="font-semibold">{title}</h3>
        <p className="text-sm mt-1">{message}</p>
      </div>
      <button
        onClick={onClose}
        className="text-gray-500 hover:text-gray-700 focus:outline-none"
        aria-label="Close"
      >
        <XMarkIcon className="w-5 h-5" />
      </button>
    </div>
  );
};

interface ToastContainerProps {
  toasts: ToastMessage[];
  onRemove: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onRemove,
}) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-4">
      {toasts.map(toast => (
        <Toast key={toast.id} {...toast} onClose={() => onRemove(toast.id)} />
      ))}
    </div>
  );
};
