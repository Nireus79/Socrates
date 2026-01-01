/**
 * Hook to show "taking longer than usual" message for slow requests
 */

import { useEffect, useState } from 'react';

export const useRequestTimeout = (isLoading: boolean, warningDelay: number = 15000) => {
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      setShowTimeoutWarning(false);
      return;
    }

    const timer = setTimeout(() => {
      setShowTimeoutWarning(true);
    }, warningDelay);

    return () => {
      clearTimeout(timer);
    };
  }, [isLoading, warningDelay]);

  return showTimeoutWarning;
};
