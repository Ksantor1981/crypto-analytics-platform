import React from 'react';

export type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline';
export type BadgeSize = 'default' | 'sm' | 'lg';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  children: React.ReactNode;
}

const getVariantClasses = (variant: BadgeVariant) => {
  switch (variant) {
    case 'default':
      return 'bg-blue-500 text-white border-blue-500';
    case 'secondary':
      return 'bg-gray-100 text-gray-800 border-gray-200';
    case 'destructive':
      return 'bg-red-500 text-white border-red-500';
    case 'outline':
      return 'bg-transparent text-gray-600 border-gray-300';
    default:
      return 'bg-blue-500 text-white border-blue-500';
  }
};

const getSizeClasses = (size: BadgeSize) => {
  switch (size) {
    case 'sm':
      return 'px-2 py-0.5 text-xs';
    case 'lg':
      return 'px-3 py-1 text-sm';
    default:
      return 'px-2.5 py-0.5 text-xs';
  }
};

export const Badge: React.FC<BadgeProps> = ({ 
  variant = 'default', 
  size = 'default', 
  className = '', 
  children, 
  ...props 
}) => {
  const variantClasses = getVariantClasses(variant);
  const sizeClasses = getSizeClasses(size);
  
  return (
    <div
      className={`inline-flex items-center rounded-full border font-semibold ${variantClasses} ${sizeClasses} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Badge;