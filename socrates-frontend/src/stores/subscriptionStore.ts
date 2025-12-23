/**
 * Subscription Store - Subscription tier and feature gating
 */

import { create } from 'zustand';
import type { SubscriptionTier } from '../types/models';

interface SubscriptionState {
  // State
  tier: 'free' | 'pro' | 'enterprise';
  status: 'active' | 'inactive' | 'suspended';
  features: SubscriptionTier['features'];

  // Actions
  setTier: (tier: 'free' | 'pro' | 'enterprise', status: 'active' | 'inactive' | 'suspended') => void;
  hasFeature: (feature: keyof SubscriptionTier['features']) => boolean;
  canPerformAction: (feature: string) => boolean;
  getAvailableProjects: () => number | null;
  getAvailableTeamMembers: () => number | null;
  getAvailableQuestions: () => number | null;
}

// Default feature sets for each tier
const TIER_FEATURES: Record<string, SubscriptionTier['features']> = {
  free: {
    max_projects: 1,
    max_team_members: 1,
    max_questions_per_month: 50,
    code_generation: false,
    collaboration: false,
    api_access: false,
    advanced_analytics: false,
  },
  pro: {
    max_projects: 10,
    max_team_members: 5,
    max_questions_per_month: 500,
    code_generation: true,
    collaboration: true,
    api_access: false,
    advanced_analytics: true,
  },
  enterprise: {
    max_projects: null,
    max_team_members: null,
    max_questions_per_month: null,
    code_generation: true,
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

  // Set tier
  setTier: (tier: 'free' | 'pro' | 'enterprise', status: 'active' | 'inactive' | 'suspended') => {
    set({
      tier,
      status,
      features: TIER_FEATURES[tier],
    });
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
