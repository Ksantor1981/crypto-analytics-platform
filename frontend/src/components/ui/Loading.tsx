'use client';

import React from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  text,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className="text-center">
        <div
          className={`
            animate-spin rounded-full border-2 border-gray-200 border-t-blue-600
            ${sizeClasses[size]}
          `}
        />
        {text && (
          <p className="mt-2 text-sm text-gray-600">{text}</p>
        )}
      </div>
    </div>
  );
};

interface SkeletonProps {
  className?: string;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = 'h-4 w-full',
  count = 1
}) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={`animate-pulse bg-gray-200 rounded ${className} ${
            index > 0 ? 'mt-2' : ''
          }`}
        />
      ))}
    </>
  );
};

// Экспортируем компоненты из LoadingStates
export {
  LoadingSpinner,
  PageLoading,
  SectionLoading,
  ButtonLoading,
  TableLoading,
  CardLoading,
  ListLoading,
  EmptyState,
  ErrorState
} from './LoadingStates'; 