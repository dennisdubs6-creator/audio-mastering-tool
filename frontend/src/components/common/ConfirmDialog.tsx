import React, { useRef, useEffect } from 'react';
import Modal from './Modal';
import Button from './Button';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
}) => {
  const cancelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      cancelRef.current?.querySelector('button')?.focus();
    }
  }, [open]);

  return (
    <Modal open={open} onClose={onCancel}>
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold text-slate-200">{title}</h2>
        <p className="text-sm text-slate-400">{message}</p>
        <div className="flex justify-end gap-3 mt-2">
          <div ref={cancelRef}>
            <Button variant="secondary" onClick={onCancel}>
              {cancelLabel}
            </Button>
          </div>
          <Button variant="danger" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;
