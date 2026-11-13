import React from 'react';
import Modal from './Modal';
import Button from './Button';
import { AlertTriangle } from 'lucide-react';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title?: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'primary';
  isLoading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'Are you sure?',
  description = 'This action cannot be undone. Please confirm to proceed.',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm" showCloseButton={!isLoading}>
      <div className="flex flex-col items-center text-center">
        <div
          className={`mb-4 flex h-12 w-12 items-center justify-center rounded-2xl ${
            variant === 'danger'
              ? 'bg-rose-100 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400'
              : 'bg-brand-100 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400'
          }`}
        >
          <AlertTriangle className="h-6 w-6" />
        </div>

        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          {title}
        </h3>

        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {description}
        </p>

        <div className="mt-6 flex w-full gap-3">
          <Button
            variant="outline"
            fullWidth
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelText}
          </Button>

          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            fullWidth
            onClick={onConfirm}
            isLoading={isLoading}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;
