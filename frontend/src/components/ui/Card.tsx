import React from 'react';
import { cn } from '../../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated' | 'glass';
  children: React.ReactNode;
}

export const Card: React.FC<CardProps> & {
  Header: React.FC<React.HTMLAttributes<HTMLDivElement>>;
  Title: React.FC<React.HTMLAttributes<HTMLHeadingElement>>;
  Description: React.FC<React.HTMLAttributes<HTMLParagraphElement>>;
  Content: React.FC<React.HTMLAttributes<HTMLDivElement>>;
  Footer: React.FC<React.HTMLAttributes<HTMLDivElement>>;
} = ({ variant = 'default', className, children, ...props }) => {
  const variantStyles = {
    default:
      'bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm',
    bordered:
      'bg-white dark:bg-slate-900 border-2 border-slate-200 dark:border-slate-700/80 shadow-none',
    elevated:
      'bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-slate-950/50',
    glass:
      'glass-panel border border-white/20 dark:border-slate-800/80 shadow-lg',
  };

  return (
    <div
      className={cn(
        'rounded-2xl transition-all duration-200',
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn('flex flex-col space-y-1.5 p-6 border-b border-slate-100 dark:border-slate-800/60', className)}
    {...props}
  >
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className,
  children,
  ...props
}) => (
  <h3
    className={cn('text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100', className)}
    {...props}
  >
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  className,
  children,
  ...props
}) => (
  <p
    className={cn('text-xs text-slate-500 dark:text-slate-400', className)}
    {...props}
  >
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn('p-6', className)} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn('flex items-center p-6 pt-0 border-t border-slate-100 dark:border-slate-800/60 mt-4', className)}
    {...props}
  >
    {children}
  </div>
);

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Description = CardDescription;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;
