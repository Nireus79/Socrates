/**
 * Two Factor Setup - Setup and manage 2FA
 */

import React from 'react';
import {
  Shield,
  Copy,
  CheckCircle,
  AlertCircle,
  X,
  Download,
} from 'lucide-react';
import { Card } from '../common';
import { Button } from '../common';
import { Input } from '../common';
import { Alert } from '../common';

interface TwoFactorSetupProps {
  isOpen: boolean;
  onClose: () => void;
  onSetup?: () => Promise<void>;
  onVerify?: (code: string) => Promise<void>;
  isLoading?: boolean;
}

interface SetupData {
  secret: string;
  qr_code_url: string;
  backup_codes: string[];
  manual_entry_key: string;
}

export const TwoFactorSetup: React.FC<TwoFactorSetupProps> = ({
  isOpen,
  onClose,
  onSetup,
  onVerify,
  isLoading = false,
}) => {
  const [step, setStep] = React.useState<'init' | 'setup' | 'verify' | 'success'>(
    'init'
  );
  const [setupData, setSetupData] = React.useState<SetupData | null>(null);
  const [verificationCode, setVerificationCode] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);
  const [copiedCode, setCopiedCode] = React.useState<string | null>(null);

  const handleStartSetup = async () => {
    setError(null);
    try {
      await onSetup?.();
      // In a real app, this would come from the API response
      setSetupData({
        secret: 'JBSWY3DPEBLW64TMMQ======',
        qr_code_url: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        backup_codes: [
          'BACKUP-0001',
          'BACKUP-0002',
          'BACKUP-0003',
          'BACKUP-0004',
          'BACKUP-0005',
        ],
        manual_entry_key: 'JBSWY3DPEBLW64TMMQ======',
      });
      setStep('setup');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to setup 2FA');
    }
  };

  const handleVerify = async () => {
    setError(null);

    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    try {
      await onVerify?.(verificationCode);
      setStep('success');
      setTimeout(() => {
        resetForm();
        onClose();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid 2FA code');
    }
  };

  const resetForm = () => {
    setStep('init');
    setSetupData(null);
    setVerificationCode('');
    setError(null);
  };

  const copyToClipboard = (text: string, code: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-md">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Two-Factor Authentication
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {error && (
            <Alert type="error" closeable onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Init Step */}
          {step === 'init' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Add an extra layer of security to your account with two-factor
                authentication.
              </p>
              <Button
                variant="primary"
                fullWidth
                onClick={handleStartSetup}
                disabled={isLoading}
                isLoading={isLoading}
              >
                Start Setup
              </Button>
            </div>
          )}

          {/* Setup Step */}
          {step === 'setup' && setupData && (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Step 1: Scan QR Code
                </p>
                <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                  <img
                    src={setupData.qr_code_url}
                    alt="2FA QR Code"
                    className="h-40 w-40"
                  />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  Scan this QR code with Google Authenticator, Microsoft Authenticator, or Authy
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Or enter this key manually:
                </p>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    value={setupData.manual_entry_key}
                    readOnly
                    className="font-mono text-xs"
                  />
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Copy className="h-4 w-4" />}
                    onClick={() =>
                      copyToClipboard(setupData.manual_entry_key, 'manual')
                    }
                  >
                    {copiedCode === 'manual' ? '✓' : 'Copy'}
                  </Button>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Save Backup Codes
                </p>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md space-y-1 mb-2">
                  {setupData.backup_codes.map((code) => (
                    <div
                      key={code}
                      className="flex justify-between items-center text-xs font-mono text-gray-700 dark:text-gray-300"
                    >
                      <span>{code}</span>
                      <button
                        onClick={() => copyToClipboard(code, code)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        {copiedCode === code ? <CheckCircle className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                      </button>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Store these codes in a safe place. You can use them to recover your account if you lose access to your authenticator.
                </p>
              </div>

              <Button
                variant="primary"
                fullWidth
                onClick={() => setStep('verify')}
              >
                Continue to Verification
              </Button>
            </div>
          )}

          {/* Verify Step */}
          {step === 'verify' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Enter the 6-digit code from your authenticator app to verify:
              </p>
              <Input
                type="text"
                placeholder="000000"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.slice(0, 6))}
                maxLength={6}
                inputMode="numeric"
                className="text-center text-2xl font-bold tracking-widest"
                disabled={isLoading}
              />
              <Button
                variant="primary"
                fullWidth
                onClick={handleVerify}
                disabled={isLoading || verificationCode.length !== 6}
                isLoading={isLoading}
              >
                Verify & Enable 2FA
              </Button>
            </div>
          )}

          {/* Success Step */}
          {step === 'success' && (
            <div className="text-center py-4">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                2FA Enabled
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Your account is now protected with two-factor authentication
              </p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
