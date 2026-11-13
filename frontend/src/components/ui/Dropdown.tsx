import React, { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { cn } from '../../utils/cn';

export interface DropdownItem {
  label: string;
  onClick: () => void;
  icon?: React.ReactNode;
  variant?: 'default' | 'danger';
  disabled?: boolean;
}

export interface DropdownProps {
  trigger: React.ReactNode;
  items: (DropdownItem | 'divider')[];
  align?: 'left' | 'right';
  className?: string;
}

export const Dropdown: React.FC<DropdownProps> = ({
  trigger,
  items,
  align = 'right',
  className,
}) => {
  return (
    <Menu as="div" className={cn('relative inline-block text-left', className)}>
      <Menu.Button as="div" className="cursor-pointer">
        {trigger}
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items
          className={cn(
            'absolute z-50 mt-2 w-56 origin-top-right rounded-2xl bg-white p-1.5 shadow-xl ring-1 ring-slate-900/5 focus:outline-none dark:bg-slate-900 dark:ring-slate-800 border border-slate-100 dark:border-slate-800',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {items.map((item, index) => {
            if (item === 'divider') {
              return (
                <div
                  key={`div-${index}`}
                  className="my-1 h-px bg-slate-100 dark:bg-slate-800"
                />
              );
            }

            return (
              <Menu.Item key={item.label} disabled={item.disabled}>
                {({ active, disabled }) => (
                  <button
                    type="button"
                    onClick={item.onClick}
                    disabled={disabled}
                    className={cn(
                      'group flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium transition-colors text-left',
                      active && !disabled
                        ? item.variant === 'danger'
                          ? 'bg-rose-50 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400'
                          : 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100'
                        : item.variant === 'danger'
                        ? 'text-rose-600 dark:text-rose-400'
                        : 'text-slate-700 dark:text-slate-300',
                      disabled && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {item.icon && (
                      <span className="h-4 w-4 shrink-0">{item.icon}</span>
                    )}
                    <span>{item.label}</span>
                  </button>
                )}
              </Menu.Item>
            );
          })}
        </Menu.Items>
      </Transition>
    </Menu>
  );
};

export default Dropdown;
