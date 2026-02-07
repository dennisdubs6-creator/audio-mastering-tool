import React from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  onClick?: () => void;
  disabled?: boolean;
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<string, string> = {
  primary:
    'bg-blue-600 hover:bg-blue-500 text-white disabled:bg-blue-800 disabled:text-blue-400',
  secondary:
    'bg-slate-700 hover:bg-slate-600 text-slate-200 disabled:bg-slate-800 disabled:text-slate-500',
  danger:
    'bg-red-600 hover:bg-red-500 text-white disabled:bg-red-800 disabled:text-red-400',
};

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  onClick,
  disabled = false,
  children,
  className = '',
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded-md font-medium text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:cursor-not-allowed ${variantClasses[variant]} ${className}`}
    >
      {children}
    </button>
  );
};

export default Button;
