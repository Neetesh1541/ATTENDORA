import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number; // e.g. 5.4 (%)
    direction?: 'up' | 'down' | 'neutral';
    label?: string; // e.g. "vs last month"
  };
  description?: string;
  className?: string;
  isLoading?: boolean;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  label,
  value,
  icon,
  trend,
  description,
  className,
  isLoading = false,
}) => {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ duration: 0.15 }}
      className={cn(
        'relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all dark:border-slate-800 dark:bg-slate-900',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {label}
          </p>
          {isLoading ? (
            <div className="mt-2 h-8 w-24 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800" />
          ) : (
            <h4 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              {value}
            </h4>
          )}
        </div>

        {icon && (
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400">
            {icon}
          </div>
        )}
      </div>

      {(trend || description) && (
        <div className="mt-3 flex items-center gap-2 text-xs">
          {trend && (
            <span
              className={cn(
                'inline-flex items-center gap-0.5 font-semibold rounded-md px-1.5 py-0.5',
                trend.direction === 'up'
                  ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400'
                  : trend.direction === 'down'
                  ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
              )}
            >
              {trend.direction === 'up' ? (
                <TrendingUp className="h-3.5 w-3.5" />
              ) : trend.direction === 'down' ? (
                <TrendingDown className="h-3.5 w-3.5" />
              ) : (
                <Minus className="h-3.5 w-3.5" />
              )}
              {trend.value > 0 ? `+${trend.value}%` : `${trend.value}%`}
            </span>
          )}

          <span className="text-slate-500 dark:text-slate-400">
            {trend?.label || description}
          </span>
        </div>
      )}
    </motion.div>
  );
};

export default StatsCard;
