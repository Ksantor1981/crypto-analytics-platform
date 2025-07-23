import React from 'react';

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

interface SelectValueProps {
  placeholder?: string;
}

export const Select: React.FC<SelectProps> = ({ value, onValueChange, children }) => {
  return (
    <div className="relative">
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { value, onValueChange } as any);
        }
        return child;
      })}
    </div>
  );
};

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ children, className = '' }) => {
  return (
    <div className={`border border-gray-300 rounded-md px-3 py-2 bg-white cursor-pointer ${className}`}>
      {children}
    </div>
  );
};

export const SelectContent: React.FC<SelectContentProps> = ({ children }) => {
  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10">
      {children}
    </div>
  );
};

export const SelectItem: React.FC<SelectItemProps> = ({ value, children }) => {
  return (
    <div 
      className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
      onClick={() => {
        // This would need proper event handling in a real implementation
      }}
    >
      {children}
    </div>
  );
};

export const SelectValue: React.FC<SelectValueProps> = ({ placeholder }) => {
  return <span className="text-gray-500">{placeholder}</span>;
};
