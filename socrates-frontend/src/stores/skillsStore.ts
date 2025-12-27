/**
 * Skills Store - Zustand state management
 *
 * Manages Phase 4 skills tracking endpoints:
 * - Set/update project skills
 * - List skills with proficiency levels
 * - Track skill progression
 */

import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { SuccessResponse } from '../api/types';

interface Skill {
  id: string;
  name: string;
  proficiency_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  confidence: number;
  notes?: string;
  created_at: string;
  created_by: string;
  update_count: number;
  progress_history: Array<{
    level: string;
    confidence: number;
    timestamp: string;
  }>;
}

interface SkillStatistics {
  level_distribution: Record<string, number>;
  average_confidence: number;
  proficiency_levels: {
    beginner: number;
    intermediate: number;
    advanced: number;
    expert: number;
  };
}

interface SkillsState {
  // State
  skills: Skill[];
  statistics: SkillStatistics | null;
  isLoading: boolean;
  error: string | null;
  currentProjectId: string | null;
  sortBy: 'proficiency' | 'confidence' | 'name' | 'created_at';

  // Actions
  setSkill: (
    projectId: string,
    skillName: string,
    proficiencyLevel?: string,
    confidence?: number,
    notes?: string
  ) => Promise<void>;
  listSkills: (
    projectId: string,
    proficiencyLevel?: string,
    minConfidence?: number,
    sortBy?: string
  ) => Promise<void>;
  setSortBy: (sortBy: 'proficiency' | 'confidence' | 'name' | 'created_at') => Promise<void>;
  clearError: () => void;
}

export const useSkillsStore = create<SkillsState>((set, get) => ({
  // Initial state
  skills: [],
  statistics: null,
  isLoading: false,
  error: null,
  currentProjectId: null,
  sortBy: 'proficiency',

  // Set/update skill
  setSkill: async (
    projectId: string,
    skillName: string,
    proficiencyLevel = 'beginner',
    confidence = 0.5,
    notes = ''
  ) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<SuccessResponse>(
        `/projects/${projectId}/skills`,
        {
          skill_name: skillName,
          proficiency_level: proficiencyLevel,
          confidence,
          notes,
        }
      );

      if (response.success) {
        // Refresh skills list
        await get().listSkills(projectId, undefined, undefined, get().sortBy);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to set skill';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // List skills
  listSkills: async (
    projectId: string,
    proficiencyLevel?: string,
    minConfidence?: number,
    sortBy?: string
  ) => {
    set({ isLoading: true, error: null, currentProjectId: projectId });
    try {
      let url = `/projects/${projectId}/skills`;
      const params = new URLSearchParams();

      if (proficiencyLevel) params.append('proficiency_level', proficiencyLevel);
      if (minConfidence !== undefined) params.append('min_confidence', minConfidence.toString());
      if (sortBy) params.append('sort_by', sortBy);

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await apiClient.get<SuccessResponse>(url);

      if (response.success && response.data) {
        set({
          skills: response.data.skills || [],
          statistics: response.data.statistics || null,
          isLoading: false,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to list skills';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  // Set sort by
  setSortBy: async (sortBy: 'proficiency' | 'confidence' | 'name' | 'created_at') => {
    set({ sortBy });

    // Refresh if project is loaded
    const { currentProjectId } = get();
    if (currentProjectId) {
      await get().listSkills(currentProjectId, undefined, undefined, sortBy);
    }
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },
}));
