import React from 'react';
import { cn } from '../../utils/cn';
import Button, { ButtonProps } from './Button';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
    variant?: ButtonProps['variant'];
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30',
        className
      )}
    >
      {icon && (
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-slate-900/5 dark:bg-slate-800 dark:ring-white/10 text-brand-600 dark:text-brand-400">
          {icon}
        </div>
      )}

      <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
        {title}
      </h3>

      {description && (
        <p className="mt-1.5 max-w-sm text-sm text-slate-500 dark:text-slate-400">
          {description}
        </p>
      )}

      {action && (
        <div className="mt-6">
          <Button
            variant={action.variant || 'primary'}
            size="sm"
            onClick={action.onClick}
            leftIcon={action.icon}
          >
            {action.label}
          </Button>
        </div>
      )}
    </div>
  );
};

export default EmptyState;
