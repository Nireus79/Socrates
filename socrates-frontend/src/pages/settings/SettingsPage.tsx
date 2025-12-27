/**
 * SettingsPage - User settings, preferences, and account management
 */

import React from 'react';
import { LogOut, Moon, Sun, Lock, CreditCard, Zap, Shield, Github } from 'lucide-react';
import { useAuthStore, useThemeStore, useSubscriptionStore, showSuccess, showError } from '../../stores';
import { MainLayout, PageHeader } from '../../components/layout';
import { authAPI, apiClient } from '../../api';
import {
  Card,
  Button,
  Input,
  Select,
  Checkbox,
  FormField,
  Tab,
  Alert,
  Badge,
  Dialog,
} from '../../components/common';
import { LLMSettingsPage } from '../../components/llm';
import { ChangePasswordModal, TwoFactorSetup, SessionManager } from '../../components/settings';

export const SettingsPage: React.FC = () => {
  const { user, logout, deleteAccount, setTestingMode, isLoading } = useAuthStore();
  const { theme, toggleTheme, setTheme } = useThemeStore();
  const { tier, status, features, hasFeature, refreshSubscription } = useSubscriptionStore();

  const [activeTab, setActiveTab] = React.useState('account');
  const [isSaving, setIsSaving] = React.useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const [showFinalConfirmDialog, setShowFinalConfirmDialog] = React.useState(false);
  const [confirmationText, setConfirmationText] = React.useState('');
  const [deleteConfirmation, setDeleteConfirmation] = React.useState('');
  const [showChangePassword, setShowChangePassword] = React.useState(false);
  const [show2FA, setShow2FA] = React.useState(false);
  const [showDeveloper, setShowDeveloper] = React.useState(false);
  const [showUpgradeDialog, setShowUpgradeDialog] = React.useState(false);
  const [showDowngradeDialog, setShowDowngradeDialog] = React.useState(false);
  const [upgradeInProgress, setUpgradeInProgress] = React.useState(false);
  const [downgradeInProgress, setDowngradeInProgress] = React.useState(false);
  const [upgradeTier, setUpgradeTier] = React.useState<'pro' | 'enterprise'>('pro');
  const [sessions, setSessions] = React.useState<any[]>([
    {
      id: 'session_1',
      device: 'Chrome on Windows',
      ip_address: '192.168.1.1',
      last_activity: new Date().toISOString(),
      created_at: new Date(Date.now() - 24*60*60*1000).toISOString(),
      is_current: true,
    },
  ]);

  // Check for developer mode via URL parameter
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('dev') === 'true') {
      setShowDeveloper(true);
    }
  }, []);

  const tabs = [
    { label: 'Account', value: 'account', icon: Lock },
    { label: 'Preferences', value: 'preferences', icon: Moon },
    { label: 'LLM Providers', value: 'llm', icon: Zap },
    { label: 'Security', value: 'security', icon: Shield },
    { label: 'Subscription', value: 'subscription', icon: CreditCard },
    { label: 'API Keys', value: 'api', icon: Github },
    ...(showDeveloper ? [{ label: 'Developer', value: 'developer' }] : []),
  ];

  const handleSaveSettings = async () => {
    setIsSaving(true);
    try {
      // Update user profile with current settings
      if (user) {
        await authAPI.updateProfile({
          username: user.username,
          email: user.email,
          subscription_tier: user.subscription_tier as any,
          subscription_status: user.subscription_status,
          testing_mode: user.testing_mode,
          // Preferences would be saved here once full state management is implemented
        });
        showSuccess('Success', 'Settings saved successfully');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save settings';
      showError('Settings Error', message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    window.location.href = '/auth/login';
  };

  const handleUpgrade = async (newTier: 'pro' | 'enterprise') => {
    setUpgradeInProgress(true);
    try {
      const response = await apiClient.post(`/subscription/upgrade?new_tier=${newTier}`, {}) as any;

      if (response?.success) {
        showSuccess('Success', `Successfully upgraded to ${newTier} plan!`);
        await refreshSubscription();
        setShowUpgradeDialog(false);
      } else {
        showError('Upgrade Failed', response?.detail || 'Failed to upgrade subscription');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to upgrade subscription';
      showError('Upgrade Error', message);
    } finally {
      setUpgradeInProgress(false);
    }
  };

  const handleDowngrade = async () => {
    setDowngradeInProgress(true);
    try {
      const response = await apiClient.post('/subscription/downgrade?new_tier=free', {}) as any;

      if (response?.success) {
        showSuccess('Success', 'Successfully downgraded to free plan');
        await refreshSubscription();
        setShowDowngradeDialog(false);
      } else {
        showError('Downgrade Failed', response?.detail || 'Failed to downgrade subscription');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to downgrade subscription';
      showError('Downgrade Error', message);
    } finally {
      setDowngradeInProgress(false);
    }
  };

  const handleDeleteAccount = () => {
    setShowDeleteDialog(true);
  };

  const handleFirstConfirmation = () => {
    setShowDeleteDialog(false);
    setShowFinalConfirmDialog(true);
  };

  const handleFinalDeleteAccount = async () => {
    if (confirmationText !== 'I UNDERSTAND' || deleteConfirmation !== 'DELETE') {
      alert('Please complete the confirmation steps');
      return;
    }

    try {
      await deleteAccount();
      alert('Account deleted successfully. Goodbye!');
      window.location.href = '/auth/login';
    } catch (error) {
      console.error('Failed to delete account:', error);
      alert('Failed to delete account');
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <PageHeader
          title="Settings"
          description="Manage your account, preferences, and subscriptions"
          breadcrumbs={[
            { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
            { label: 'Settings' },
          ]}
        />

        {/* Tabs */}
        <Card>
          <Tab
            tabs={tabs}
            activeTab={activeTab}
            onChange={setActiveTab}
            variant="default"
          />
        </Card>

        {/* Account Tab */}
        {activeTab === 'account' && (
          <div className="space-y-6">
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Account Information
              </h3>

              <div className="space-y-4">
                <FormField label="Username">
                  <Input
                    value={user?.username || ''}
                    disabled
                    readOnly
                  />
                </FormField>

                <FormField label="Email Address">
                  <Input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    readOnly
                  />
                </FormField>

                <FormField label="Account Created">
                  <Input
                    value={new Date().toLocaleDateString()}
                    disabled
                    readOnly
                  />
                </FormField>

                <FormField label="Subscription Tier">
                  <div className="flex items-center gap-2">
                    <Badge variant="primary">
                      {user?.subscription_tier || 'Free'}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.location.href = '/settings?tab=subscription'}
                    >
                      Manage Plan
                    </Button>
                  </div>
                </FormField>
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Security
              </h3>

              <div className="space-y-3">
                <Button
                  variant="secondary"
                  fullWidth
                  icon={<Lock className="h-4 w-4" />}
                  onClick={() => setShowChangePassword(true)}
                >
                  Change Password
                </Button>

                <Button
                  variant="secondary"
                  fullWidth
                  onClick={() => setShow2FA(true)}
                >
                  Two-Factor Authentication
                </Button>
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Danger Zone
              </h3>

              <Button
                variant="danger"
                fullWidth
                onClick={handleDeleteAccount}
              >
                Delete Account
              </Button>
            </Card>
          </div>
        )}

        {/* Preferences Tab */}
        {activeTab === 'preferences' && (
          <div className="space-y-6">
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Display
              </h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-3">
                    {theme === 'dark' ? (
                      <Moon className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                    ) : (
                      <Sun className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                    )}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        Dark Mode
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {theme === 'dark'
                          ? 'Dark mode is enabled'
                          : 'Light mode is enabled'}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  >
                    {theme === 'dark' ? 'Light' : 'Dark'}
                  </Button>
                </div>
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Defaults
              </h3>

              <div className="space-y-4">
                <FormField label="Default Project Type">
                  <Select
                    options={[
                      { value: 'software', label: 'Software Development' },
                      { value: 'business', label: 'Business Strategy' },
                      { value: 'creative', label: 'Creative Project' },
                      { value: 'research', label: 'Research' },
                    ]}
                    defaultValue="software"
                  />
                </FormField>

                <FormField label="Default Code Language">
                  <Select
                    options={[
                      { value: 'python', label: 'Python' },
                      { value: 'javascript', label: 'JavaScript' },
                      { value: 'typescript', label: 'TypeScript' },
                      { value: 'java', label: 'Java' },
                    ]}
                    defaultValue="python"
                  />
                </FormField>

                <FormField label="Dialogue Mode">
                  <Select
                    options={[
                      { value: 'socratic', label: 'Socratic (Guided Questions)' },
                      { value: 'direct', label: 'Direct (Answers & Explanations)' },
                    ]}
                    defaultValue="socratic"
                  />
                </FormField>
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Notifications
              </h3>

              <div className="space-y-3">
                <Checkbox
                  label="Email notifications for collaborator activity"
                  checked={true}
                />
                <Checkbox
                  label="Email notifications for phase completion"
                  checked={true}
                />
                <Checkbox
                  label="Weekly summary email"
                  checked={false}
                />
                <Checkbox
                  label="Tips and educational content"
                  checked={true}
                />
              </div>
            </Card>

            <Button
              variant="primary"
              fullWidth
              onClick={handleSaveSettings}
              isLoading={isSaving}
            >
              Save Preferences
            </Button>
          </div>
        )}

        {/* Subscription Tab */}
        {activeTab === 'subscription' && (
          <Card>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Current Plan
                </h3>
                <Badge variant="primary" className="mb-4">
                  {tier.charAt(0).toUpperCase() + tier.slice(1)} Plan
                </Badge>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Status: <span className="capitalize font-medium">{status}</span>
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                  {tier === 'free'
                    ? 'You have a free account with limited features.'
                    : tier === 'pro'
                    ? 'Your pro plan includes advanced features and team collaboration.'
                    : 'Your enterprise plan includes unlimited features and premium support.'}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className={`p-4 rounded-lg border-2 ${tier === 'free' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900' : 'border-gray-200 dark:border-gray-700'}`}>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Free
                  </h4>
                  <ul className="text-sm space-y-2 text-gray-600 dark:text-gray-400">
                    <li>{features.max_projects ? `✓ Up to ${features.max_projects} projects` : '✗ Limited projects'}</li>
                    <li>✓ Basic dialogue</li>
                    <li>{features.code_generation ? '✓ Limited code generation' : '✗ No code generation'}</li>
                    <li>{features.collaboration ? '✓ Collaboration' : '✗ No collaboration'}</li>
                  </ul>
                </div>

                <div className={`p-4 rounded-lg border-2 ${tier === 'pro' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900' : 'border-gray-200 dark:border-gray-700'}`}>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Pro
                  </h4>
                  <ul className="text-sm space-y-2 text-gray-600 dark:text-gray-400">
                    <li>{features.max_projects ? `✓ Up to ${features.max_projects} projects` : '✗ Limited projects'}</li>
                    <li>✓ Advanced dialogue</li>
                    <li>{features.code_generation ? '✓ Unlimited code generation' : '✗ No code generation'}</li>
                    <li>{features.collaboration ? `✓ Up to ${features.max_team_members} team members` : '✗ No collaboration'}</li>
                  </ul>
                  {tier !== 'pro' && (
                    <Button
                      variant="primary"
                      fullWidth
                      className="mt-4"
                      icon={<CreditCard className="h-4 w-4" />}
                      onClick={() => {
                        setUpgradeTier('pro');
                        setShowUpgradeDialog(true);
                      }}
                      disabled={upgradeInProgress}
                    >
                      Upgrade to Pro
                    </Button>
                  )}
                </div>

                <div className={`p-4 rounded-lg border-2 ${tier === 'enterprise' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900' : 'border-gray-200 dark:border-gray-700'}`}>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Enterprise
                  </h4>
                  <ul className="text-sm space-y-2 text-gray-600 dark:text-gray-400">
                    <li>✓ Unlimited projects</li>
                    <li>✓ Advanced dialogue</li>
                    <li>✓ Unlimited code generation</li>
                    <li>✓ Unlimited team members</li>
                  </ul>
                  {tier !== 'enterprise' && (
                    <Button
                      variant="secondary"
                      fullWidth
                      className="mt-4"
                      onClick={() => {
                        setUpgradeTier('enterprise');
                        setShowUpgradeDialog(true);
                      }}
                      disabled={upgradeInProgress}
                    >
                      Upgrade to Enterprise
                    </Button>
                  )}
                </div>
              </div>

              {/* Downgrade Option */}
              {tier !== 'free' && (
                <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                    Want to downgrade?
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    You can downgrade to the free plan at any time. You'll lose access to premium features.
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => setShowDowngradeDialog(true)}
                    disabled={downgradeInProgress}
                  >
                    Downgrade to Free
                  </Button>
                </div>
              )}

              <Alert type="info" title="Billing">
                Your subscription status is {status}. Changes to your plan take effect at the start of your next billing cycle.
              </Alert>
            </div>
          </Card>
        )}

        {/* LLM Providers Tab */}
        {activeTab === 'llm' && (
          <LLMSettingsPage />
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Password Management
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Change your account password regularly to keep your account secure.
              </p>
              <Button
                variant="secondary"
                fullWidth
                icon={<Lock className="h-4 w-4" />}
                onClick={() => setShowChangePassword(true)}
              >
                Change Password
              </Button>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Two-Factor Authentication
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Add an extra layer of security to your account with two-factor authentication.
              </p>
              <Button
                variant="secondary"
                fullWidth
                onClick={() => setShow2FA(true)}
              >
                Set Up 2FA
              </Button>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Active Sessions
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Manage your active sessions and sign out from other devices.
              </p>
              <SessionManager sessions={sessions} onRevokeSession={async (sessionId) => {
                setSessions(sessions.filter(s => s.id !== sessionId));
              }} />
            </Card>
          </div>
        )}

        {/* API Keys Tab */}
        {activeTab === 'api' && (
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              API Keys
            </h3>

            <Alert type="warning" title="Be Careful">
              API keys are sensitive. Never share them or commit them to version control.
            </Alert>

            <div className="mt-4 space-y-3">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    sk_live_1234567890
                  </span>
                  <Badge variant="success" size="sm">Active</Badge>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                  Created on Jan 1, 2025 • Last used 5 minutes ago
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-600 dark:text-red-400"
                  onClick={() => {
                    if (confirm('Are you sure you want to revoke this API key?')) {
                      // Revoke API key logic would go here
                      alert('API key revoked');
                    }
                  }}
                >
                  Revoke
                </Button>
              </div>

              <Button
                variant="secondary"
                fullWidth
                onClick={() => {
                  // Generate new API key logic would go here
                  alert('New API key generated: sk_' + Math.random().toString(36).substr(2, 18));
                }}
              >
                Generate New Key
              </Button>
            </div>
          </Card>
        )}

        {/* Developer Tab */}
        {activeTab === 'developer' && (
          <Card className="border-yellow-500 border-2">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Developer Settings
            </h3>

            <Alert type="warning" title="Testing Mode">
              When enabled, all subscription checks are bypassed. Use for development only.
            </Alert>

            <div className="mt-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      Testing Mode
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {user?.testing_mode ? 'Enabled - All features unlocked' : 'Disabled - Normal restrictions apply'}
                    </p>
                  </div>
                  <Button
                    variant={user?.testing_mode ? 'danger' : 'secondary'}
                    onClick={() => setTestingMode(!user?.testing_mode)}
                    isLoading={isLoading}
                  >
                    {user?.testing_mode ? 'Disable' : 'Enable'}
                  </Button>
                </div>

                {user?.testing_mode && (
                  <div className="mt-3 p-2 bg-green-50 dark:bg-green-900 rounded border border-green-200 dark:border-green-800">
                    <p className="text-sm text-green-800 dark:text-green-200">
                      ✓ Testing mode active: Unlimited projects, team members, and questions.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </Card>
        )}

        {/* Logout Button - Always visible */}
        <Card className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-red-900 dark:text-red-100">
                Log Out
              </h3>
              <p className="text-sm text-red-800 dark:text-red-200">
                Sign out of your Socratic account
              </p>
            </div>
            <Button
              variant="danger"
              icon={<LogOut className="h-4 w-4" />}
              onClick={handleLogout}
            >
              Logout
            </Button>
          </div>
        </Card>

        {/* Password Change Modal */}
        <ChangePasswordModal
          isOpen={showChangePassword}
          onClose={() => setShowChangePassword(false)}
          onConfirm={async () => {
            setShowChangePassword(false);
            // Show success message
          }}
        />

        {/* 2FA Setup Modal */}
        <TwoFactorSetup
          isOpen={show2FA}
          onClose={() => setShow2FA(false)}
          onSetup={async () => {
            setShow2FA(false);
            // Show success message
          }}
        />

        {/* Subscription Upgrade Dialog */}
        <Dialog
          isOpen={showUpgradeDialog}
          onClose={() => setShowUpgradeDialog(false)}
          title={`Upgrade to ${upgradeTier === 'pro' ? 'Pro' : 'Enterprise'} Plan?`}
          description={upgradeTier === 'pro'
            ? 'Upgrade to Pro to unlock advanced features, unlimited code generation, and team collaboration.'
            : 'Upgrade to Enterprise for unlimited everything and premium support.'}
          confirmLabel={`Upgrade to ${upgradeTier === 'pro' ? 'Pro' : 'Enterprise'}`}
          cancelLabel="Cancel"
          onConfirm={() => handleUpgrade(upgradeTier)}
          isLoading={upgradeInProgress}
          variant="info"
        />

        {/* Subscription Downgrade Dialog */}
        <Dialog
          isOpen={showDowngradeDialog}
          onClose={() => setShowDowngradeDialog(false)}
          title="Downgrade to Free Plan?"
          description="Downgrading will remove access to all premium features. Your projects and data will remain intact, but some features will be unavailable."
          confirmLabel="Confirm Downgrade"
          cancelLabel="Keep Current Plan"
          onConfirm={handleDowngrade}
          isLoading={downgradeInProgress}
          variant="warning"
        />

        {/* Delete Account Confirmation Dialogs */}
        <Dialog
          isOpen={showDeleteDialog}
          onClose={() => setShowDeleteDialog(false)}
          title="Delete Account?"
          description="This will permanently delete your account and all associated data. This action cannot be undone."
          confirmLabel="I Understand, Continue"
          cancelLabel="Cancel"
          onConfirm={handleFirstConfirmation}
          variant="danger"
        />

        <Dialog
          isOpen={showFinalConfirmDialog}
          onClose={() => {
            setShowFinalConfirmDialog(false);
            setConfirmationText('');
            setDeleteConfirmation('');
          }}
          title="Final Confirmation"
          description="To confirm deletion, type 'I UNDERSTAND' and 'DELETE' in the prompts that follow."
          confirmLabel="Delete My Account Forever"
          cancelLabel="Cancel"
          onConfirm={handleFinalDeleteAccount}
          variant="danger"
          isLoading={isLoading}
        />
      </div>
    </MainLayout>
  );
};
