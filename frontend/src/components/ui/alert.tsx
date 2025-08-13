import React from 'react';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive' | 'warning' | 'success';
  children: React.ReactNode;
}

export interface AlertDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
}

const getVariantClasses = (variant: AlertProps['variant']) => {
  switch (variant) {
    case 'destructive':
      return 'border-red-200 bg-red-50 text-red-800';
    case 'warning':
      return 'border-yellow-200 bg-yellow-50 text-yellow-800';
    case 'success':
      return 'border-green-200 bg-green-50 text-green-800';
    default:
      return 'border-blue-200 bg-blue-50 text-blue-800';
  }
};

export const Alert: React.FC<AlertProps> = ({ 
  variant = 'default', 
  className = '', 
  children, 
  ...props 
}) => {
  const variantClasses = getVariantClasses(variant);
  
  return (
    <div
      className={`relative w-full rounded-lg border p-4 ${variantClasses} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ 
  className = '', 
  children, 
  ...props 
}) => {
  return (
    <p
      className={`text-sm leading-relaxed ${className}`}
      {...props}
    >
      {children}
    </p>
  );
};

export default Alert;
