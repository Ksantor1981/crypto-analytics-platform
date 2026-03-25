import React, {
  useState,
  useRef,
  useEffect,
  createContext,
  useContext,
} from 'react';

interface SelectContextType {
  value?: string;
  onValueChange?: (value: string) => void;
  open: boolean;
  setOpen: (open: boolean) => void;
}

const SelectContext = createContext<SelectContextType>({
  open: false,
  setOpen: () => {},
});

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
}

export const Select: React.FC<SelectProps> = ({
  value,
  onValueChange,
  children,
}) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
      <div className="relative" ref={ref}>
        {children}
      </div>
    </SelectContext.Provider>
  );
};

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

export const SelectTrigger: React.FC<SelectTriggerProps> = ({
  children,
  className = '',
}) => {
  const { open, setOpen } = useContext(SelectContext);
  return (
    <button
      type="button"
      onClick={() => setOpen(!open)}
      className={`flex items-center justify-between w-full border border-gray-300 rounded-md px-3 py-2 bg-white cursor-pointer text-left hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${className}`}
    >
      {children}
      <svg
        className={`ml-2 h-4 w-4 shrink-0 opacity-50 transition-transform ${open ? 'rotate-180' : ''}`}
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fillRule="evenodd"
          d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
          clipRule="evenodd"
        />
      </svg>
    </button>
  );
};

interface SelectContentProps {
  children: React.ReactNode;
}

export const SelectContent: React.FC<SelectContentProps> = ({ children }) => {
  const { open } = useContext(SelectContext);
  if (!open) return null;
  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-60 overflow-y-auto py-1">
      {children}
    </div>
  );
};

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

export const SelectItem: React.FC<SelectItemProps> = ({
  value: itemValue,
  children,
}) => {
  const { value, onValueChange, setOpen } = useContext(SelectContext);
  const isSelected = value === itemValue;

  return (
    <button
      type="button"
      className={`w-full text-left px-3 py-2 cursor-pointer text-sm transition-colors ${
        isSelected
          ? 'bg-blue-50 text-blue-700 font-medium'
          : 'hover:bg-gray-100 text-gray-900'
      }`}
      onClick={() => {
        onValueChange?.(itemValue);
        setOpen(false);
      }}
    >
      {children}
    </button>
  );
};

interface SelectValueProps {
  placeholder?: string;
}

export const SelectValue: React.FC<SelectValueProps> = ({ placeholder }) => {
  const { value } = useContext(SelectContext);
  return (
    <span className={value ? 'text-gray-900' : 'text-gray-500'}>
      {value || placeholder}
    </span>
  );
};
