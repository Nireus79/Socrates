/**
 * Subscription Store - Subscription tier and feature gating
 */

import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { SubscriptionTier } from '../types/models';

interface SubscriptionState {
  // State
  tier: 'free' | 'pro' | 'enterprise';
  status: 'active' | 'inactive' | 'suspended';
  features: SubscriptionTier['features'];
  testingMode: boolean;

  // Actions
  setTier: (tier: 'free' | 'pro' | 'enterprise', status: 'active' | 'inactive' | 'suspended') => void;
  setTestingMode: (enabled: boolean) => void;
  hasFeature: (feature: keyof SubscriptionTier['features']) => boolean;
  canPerformAction: (feature: string) => boolean;
  getAvailableProjects: () => number | null;
  getAvailableTeamMembers: () => number | null;
  getAvailableQuestions: () => number | null;
  refreshSubscription: () => Promise<void>;
}

// FREEMIUM MODEL: All tiers have FULL FEATURE ACCESS, differentiated only by quotas
const TIER_FEATURES: Record<string, SubscriptionTier['features']> = {
  free: {
    max_projects: 1,  // Quota limit: solo work
    max_team_members: 1,  // Quota limit: solo only
    max_questions_per_month: null,  // Unlimited
    code_generation: true,  // All features in free tier
    collaboration: false,  // Blocked by max_team_members=1 quota, not feature flag
    api_access: true,
    advanced_analytics: true,
  },
  pro: {
    max_projects: 10,  // Quota limit: up to 10 projects
    max_team_members: 5,  // Quota limit: up to 5 team members
    max_questions_per_month: null,  // Unlimited
    code_generation: true,  // All features in pro tier
    collaboration: true,  // Enabled with team member quota
    api_access: true,
    advanced_analytics: true,
  },
  enterprise: {
    max_projects: null,  // Unlimited
    max_team_members: null,  // Unlimited
    max_questions_per_month: null,  // Unlimited
    code_generation: true,  // All features in enterprise
    collaboration: true,
    api_access: true,
    advanced_analytics: true,
  },
};

export const useSubscriptionStore = create<SubscriptionState>((set, get) => ({
  // Initial state
  tier: 'free',
  status: 'active',
  features: TIER_FEATURES['free'],
  testingMode: false,

  // Set tier
  setTier: (tier: 'free' | 'pro' | 'enterprise', status: 'active' | 'inactive' | 'suspended') => {
        set({
          tier,
          status,
          features: TIER_FEATURES[tier],
        });
      },

      // Set testing mode
      setTestingMode: (enabled: boolean) => {
        set({ testingMode: enabled });
      },

  // Check if has feature
  hasFeature: (feature: keyof SubscriptionTier['features']): boolean => {
    const state = get();

    if (state.status !== 'active') return false;

    const featureValue = state.features[feature];
    if (typeof featureValue === 'boolean') {
      return featureValue;
    }
    return featureValue !== null && featureValue > 0;
  },

  // Check if can perform action
  canPerformAction: (feature: string): boolean => {
    const mapping: Record<string, keyof SubscriptionTier['features']> = {
      'code-generation': 'code_generation',
      'collaboration': 'collaboration',
      'api-access': 'api_access',
      'advanced-analytics': 'advanced_analytics',
    };

    const featureKey = mapping[feature];
    if (!featureKey) return false;

    return get().hasFeature(featureKey);
  },

  // Get available projects
  getAvailableProjects: (): number | null => {
    return get().features.max_projects;
  },

  // Get available team members
  getAvailableTeamMembers: (): number | null => {
    return get().features.max_team_members;
  },

  // Get available questions
  getAvailableQuestions: (): number | null => {
    return get().features.max_questions_per_month;
  },

  // Refresh subscription status from API
  refreshSubscription: async (): Promise<void> => {
    try {
      const response = await apiClient.get('/subscription/status') as any;
      if (response?.data?.current_tier) {
        const newTier = response.data.current_tier as 'free' | 'pro' | 'enterprise';
        const newStatus = response.data.status || 'active' as 'active' | 'inactive' | 'suspended';
        const testingModeEnabled = response.data.testing_mode || false;
        get().setTier(newTier, newStatus);
        get().setTestingMode(testingModeEnabled);
      }
    } catch (error) {
      console.error('Failed to refresh subscription status:', error);
      // Don't throw - gracefully degrade if API fails
    }
  },
}));

/**
 * Hook to check if feature is available
 */
export const useFeatureGate = (feature: string): boolean => {
  return useSubscriptionStore((state) => {
    const mapping: Record<string, keyof SubscriptionTier['features']> = {
      'code-generation': 'code_generation',
      'collaboration': 'collaboration',
      'api-access': 'api_access',
      'advanced-analytics': 'advanced_analytics',
    };

    const featureKey = mapping[feature];
    if (!featureKey) return false;

    if (state.status !== 'active') return false;

    const featureValue = state.features[featureKey];
    if (typeof featureValue === 'boolean') {
      return featureValue;
    }
    return featureValue !== null && featureValue > 0;
  });
};
