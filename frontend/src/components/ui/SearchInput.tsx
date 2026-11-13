import React, { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface SearchInputProps {
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  className?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value: initialValue = '',
  onChange,
  placeholder = 'Search...',
  debounceMs = 300,
  className,
}) => {
  const [innerValue, setInnerValue] = useState(initialValue);

  useEffect(() => {
    setInnerValue(initialValue);
  }, [initialValue]);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (innerValue !== initialValue) {
        onChange(innerValue);
      }
    }, debounceMs);

    return () => clearTimeout(handler);
  }, [innerValue, debounceMs, onChange, initialValue]);

  const handleClear = () => {
    setInnerValue('');
    onChange('');
  };

  return (
    <div className={cn('relative flex items-center w-full max-w-md', className)}>
      <Search className="pointer-events-none absolute left-3.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
      <input
        type="text"
        value={innerValue}
        onChange={(e) => setInnerValue(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-10 pr-9 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-brand-500"
      />
      {innerValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 rounded-md p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300 transition-colors"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
};

export default SearchInput;
