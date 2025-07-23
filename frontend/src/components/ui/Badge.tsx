import React from 'react';

type BadgeVariant = 'success' | 'danger' | 'warning' | 'info' | 'secondary';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const Badge = ({
  children,
  variant = 'secondary',
  className = '',
}: BadgeProps) => {
  const baseClasses =
    'badge inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium';

  const variantClasses = {
    success: 'badge-success',
    danger: 'badge-danger',
    warning: 'badge-warning',
    info: 'badge-info',
    secondary: 'badge-secondary',
  };

  const classes = `${baseClasses} ${variantClasses[variant]} ${className}`;

  return <span className={classes}>{children}</span>;
};

export { Badge };
export type { BadgeProps, BadgeVariant };
