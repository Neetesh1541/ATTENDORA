import React from 'react';
import { cn } from '../../utils/cn';

export type BadgeColor = 'green' | 'red' | 'yellow' | 'blue' | 'gray' | 'purple' | 'indigo';
export type BadgeVariant = 'soft' | 'solid' | 'outline' | 'dot';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  color?: BadgeColor;
  variant?: BadgeVariant;
  size?: BadgeSize;
  children: React.ReactNode;
}

const colorStyles: Record<BadgeColor, { soft: string; solid: string; outline: string; dot: string }> = {
  green: {
    soft: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400 border border-emerald-200/50 dark:border-emerald-800/40',
    solid: 'bg-emerald-600 text-white',
    outline: 'border border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400',
    dot: 'bg-emerald-500',
  },
  red: {
    soft: 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400 border border-rose-200/50 dark:border-rose-800/40',
    solid: 'bg-rose-600 text-white',
    outline: 'border border-rose-600 text-rose-600 dark:border-rose-400 dark:text-rose-400',
    dot: 'bg-rose-500',
  },
  yellow: {
    soft: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400 border border-amber-200/50 dark:border-amber-800/40',
    solid: 'bg-amber-600 text-white',
    outline: 'border border-amber-600 text-amber-600 dark:border-amber-400 dark:text-amber-400',
    dot: 'bg-amber-500',
  },
  blue: {
    soft: 'bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-400 border border-sky-200/50 dark:border-sky-800/40',
    solid: 'bg-sky-600 text-white',
    outline: 'border border-sky-600 text-sky-600 dark:border-sky-400 dark:text-sky-400',
    dot: 'bg-sky-500',
  },
  gray: {
    soft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700',
    solid: 'bg-slate-700 text-white dark:bg-slate-300 dark:text-slate-900',
    outline: 'border border-slate-400 text-slate-700 dark:border-slate-600 dark:text-slate-300',
    dot: 'bg-slate-400 dark:bg-slate-500',
  },
  purple: {
    soft: 'bg-purple-50 text-purple-700 dark:bg-purple-950/50 dark:text-purple-400 border border-purple-200/50 dark:border-purple-800/40',
    solid: 'bg-purple-600 text-white',
    outline: 'border border-purple-600 text-purple-600 dark:border-purple-400 dark:text-purple-400',
    dot: 'bg-purple-500',
  },
  indigo: {
    soft: 'bg-brand-50 text-brand-700 dark:bg-brand-950/50 dark:text-brand-300 border border-brand-200/50 dark:border-brand-800/40',
    solid: 'bg-brand-600 text-white',
    outline: 'border border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400',
    dot: 'bg-brand-500',
  },
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-[11px]',
  md: 'px-2.5 py-1 text-xs',
};

export const Badge: React.FC<BadgeProps> = ({
  color = 'gray',
  variant = 'soft',
  size = 'md',
  children,
  className,
  ...props
}) => {
  const currentStyle = colorStyles[color];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium rounded-full shrink-0 select-none tracking-tight',
        sizeClasses[size],
        variant === 'dot'
          ? 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
          : currentStyle[variant],
        className
      )}
      {...props}
    >
      {variant === 'dot' && (
        <span className={cn('h-1.5 w-1.5 rounded-full shrink-0', currentStyle.dot)} />
      )}
      {children}
    </span>
  );
};

export default Badge;
