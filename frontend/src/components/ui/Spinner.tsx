import React from 'react';
import { cn } from '../../utils/cn';

export interface SpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'primary' | 'white' | 'muted' | 'emerald';
  className?: string;
}

const sizeClasses = {
  xs: 'w-3 h-3 border-[2px]',
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
  xl: 'w-12 h-12 border-4',
};

const variantClasses = {
  primary: 'border-brand-600 border-t-transparent dark:border-brand-400 dark:border-t-transparent',
  white: 'border-white border-t-transparent',
  muted: 'border-slate-400 border-t-transparent dark:border-slate-600 dark:border-t-transparent',
  emerald: 'border-emerald-500 border-t-transparent',
};

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  className,
}) => {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        'inline-block animate-spin rounded-full shrink-0',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export default Spinner;
