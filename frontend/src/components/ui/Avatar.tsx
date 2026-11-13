import React, { useState } from 'react';
import { cn } from '../../utils/cn';

export interface AvatarProps {
  src?: string | null;
  name?: string | null;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  status?: 'online' | 'offline' | 'busy' | 'away';
  className?: string;
}

const sizeClasses = {
  xs: 'w-6 h-6 text-[10px]',
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
  xl: 'w-16 h-16 text-lg font-bold',
};

const statusClasses = {
  online: 'bg-emerald-500',
  offline: 'bg-slate-400',
  busy: 'bg-rose-500',
  away: 'bg-amber-500',
};

const statusSize = {
  xs: 'w-1.5 h-1.5 border',
  sm: 'w-2 h-2 border',
  md: 'w-2.5 h-2.5 border-2',
  lg: 'w-3 h-3 border-2',
  xl: 'w-3.5 h-3.5 border-2',
};

const getInitials = (name?: string | null): string => {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

export const Avatar: React.FC<AvatarProps> = ({
  src,
  name,
  size = 'md',
  status,
  className,
}) => {
  const [imageError, setImageError] = useState(false);
  const initials = getInitials(name);

  // Generate pleasant background hue based on name
  const getBackgroundColor = (str?: string | null) => {
    if (!str) return 'bg-brand-600 text-white';
    const hues = [
      'bg-indigo-600 text-white',
      'bg-sky-600 text-white',
      'bg-emerald-600 text-white',
      'bg-violet-600 text-white',
      'bg-rose-600 text-white',
      'bg-amber-600 text-white',
    ];
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return hues[Math.abs(hash) % hues.length];
  };

  return (
    <div className="relative inline-block shrink-0 select-none">
      <div
        className={cn(
          'flex items-center justify-center rounded-full font-semibold overflow-hidden shadow-inner',
          sizeClasses[size],
          !src || imageError ? getBackgroundColor(name) : 'bg-slate-100 dark:bg-slate-800',
          className
        )}
      >
        {src && !imageError ? (
          <img
            src={src}
            alt={name || 'Avatar'}
            onError={() => setImageError(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <span>{initials}</span>
        )}
      </div>

      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 rounded-full border-white dark:border-slate-900',
            statusClasses[status],
            statusSize[size]
          )}
        />
      )}
    </div>
  );
};

export default Avatar;
