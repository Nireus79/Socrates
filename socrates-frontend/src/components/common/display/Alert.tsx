/**
 * Alert Component - Display alert messages
 */

import React from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';

type AlertType = 'success' | 'error' | 'warning' | 'info';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  type?: AlertType;
  title?: string;
  closeable?: boolean;
  onClose?: () => void;
}

const icons: Record<AlertType, React.ReactNode> = {
  success: <CheckCircle size={20} />,
  error: <AlertCircle size={20} />,
  warning: <AlertTriangle size={20} />,
  info: <Info size={20} />,
};

const styles: Record<AlertType, { bg: string; border: string; text: string; icon: string }> = {
  success: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    text: 'text-green-800 dark:text-green-200',
    icon: 'text-green-600 dark:text-green-400',
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-800 dark:text-red-200',
    icon: 'text-red-600 dark:text-red-400',
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    text: 'text-yellow-800 dark:text-yellow-200',
    icon: 'text-yellow-600 dark:text-yellow-400',
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-800 dark:text-blue-200',
    icon: 'text-blue-600 dark:text-blue-400',
  },
};

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      type = 'info',
      title,
      closeable = false,
      onClose,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const [isVisible, setIsVisible] = React.useState(true);

    const handleClose = () => {
      setIsVisible(false);
      onClose?.();
    };

    if (!isVisible) return null;

    const style = styles[type];

    return (
      <div
        ref={ref}
        className={`${style.bg} ${style.border} border rounded-lg p-4 ${className}`.trim()}
        {...props}
      >
        <div className="flex gap-3">
          <div className={style.icon}>{icons[type]}</div>
          <div className="flex-1">
            {title && <p className={`font-semibold ${style.text}`}>{title}</p>}
            {typeof children === 'string' ? (
              <p className={style.text}>{children}</p>
            ) : (
              <div className={style.text}>{children}</div>
            )}
          </div>
          {closeable && (
            <button
              onClick={handleClose}
              className={`${style.text} hover:opacity-70 transition-opacity`}
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>
    );
  }
);

Alert.displayName = 'Alert';
