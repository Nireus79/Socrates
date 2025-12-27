/**
 * Skills Management Page - Phase 4 Integration
 *
 * Displays and manages project skills tracking
 * - Add new skills
 * - View skills with proficiency levels
 * - Track skill progression
 * - Filter and sort skills
 */

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useSkillsStore } from '../../stores/skillsStore';

export const SkillsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const {
    skills,
    statistics,
    isLoading,
    error,
    sortBy,
    setSortBy,
    setSkill,
    listSkills,
    clearError,
  } = useSkillsStore();

  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    skillName: '',
    proficiencyLevel: 'beginner',
    confidence: 0.5,
    notes: '',
  });

  // Load skills on component mount
  useEffect(() => {
    if (projectId) {
      listSkills(projectId);
    }
  }, [projectId, listSkills]);

  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !formData.skillName.trim()) return;

    try {
      await setSkill(
        projectId,
        formData.skillName,
        formData.proficiencyLevel,
        formData.confidence,
        formData.notes
      );

      // Reset form
      setFormData({
        skillName: '',
        proficiencyLevel: 'beginner',
        confidence: 0.5,
        notes: '',
      });
      setShowAddForm(false);
    } catch (err) {
      console.error('Failed to add skill:', err);
    }
  };

  const handleSortChange = (newSort: 'proficiency' | 'confidence' | 'name' | 'created_at') => {
    setSortBy(newSort);
  };

  const getProficiencyColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'bg-blue-100 text-blue-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-orange-100 text-orange-800';
      case 'expert':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceBar = (confidence: number) => {
    const percentage = confidence * 100;
    let color = 'bg-red-500';
    if (confidence >= 0.7) color = 'bg-green-500';
    else if (confidence >= 0.5) color = 'bg-yellow-500';

    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div className={`${color} h-2 rounded-full`} style={{ width: `${percentage}%` }}></div>
        </div>
        <span className="text-sm text-gray-600 w-8">{Math.round(percentage)}%</span>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Skills Management</h1>
            <p className="text-gray-600 mt-2">Track your acquired skills and proficiency levels</p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            {showAddForm ? 'Cancel' : '+ Add Skill'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
            <button onClick={clearError} className="ml-4 text-sm underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Add Skill Form */}
        {showAddForm && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Add New Skill</h2>
            <form onSubmit={handleAddSkill} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Skill Name *
                  </label>
                  <input
                    type="text"
                    value={formData.skillName}
                    onChange={(e) =>
                      setFormData({ ...formData, skillName: e.target.value })
                    }
                    placeholder="e.g., Python, React, Docker"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Proficiency Level
                  </label>
                  <select
                    value={formData.proficiencyLevel}
                    onChange={(e) =>
                      setFormData({ ...formData, proficiencyLevel: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confidence: {Math.round(formData.confidence * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.confidence}
                  onChange={(e) =>
                    setFormData({ ...formData, confidence: parseFloat(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Add any notes about this skill..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Adding...' : 'Add Skill'}
              </button>
            </form>
          </div>
        )}

        {/* Statistics */}
        {statistics && (
          <div className="grid grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Total Skills</div>
              <div className="text-3xl font-bold text-gray-900">
                {statistics.proficiency_levels.beginner +
                  statistics.proficiency_levels.intermediate +
                  statistics.proficiency_levels.advanced +
                  statistics.proficiency_levels.expert}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Avg Confidence</div>
              <div className="text-3xl font-bold text-gray-900">
                {Math.round(statistics.average_confidence * 100)}%
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Advanced+</div>
              <div className="text-3xl font-bold text-gray-900">
                {statistics.proficiency_levels.advanced + statistics.proficiency_levels.expert}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Expert Level</div>
              <div className="text-3xl font-bold text-gray-900">
                {statistics.proficiency_levels.expert}
              </div>
            </div>
          </div>
        )}

        {/* Sort Options */}
        <div className="mb-6 flex gap-2">
          {(['proficiency', 'confidence', 'name', 'created_at'] as const).map((sort) => (
            <button
              key={sort}
              onClick={() => handleSortChange(sort)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                sortBy === sort
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {sort.charAt(0).toUpperCase() + sort.slice(1)}
            </button>
          ))}
        </div>

        {/* Skills List */}
        {isLoading && !skills.length ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading skills...</p>
          </div>
        ) : skills.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-600">No skills yet. Add your first skill to get started!</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {skills.map((skill) => (
              <div key={skill.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">{skill.name}</h3>
                    {skill.notes && <p className="text-sm text-gray-600 mt-1">{skill.notes}</p>}
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getProficiencyColor(
                      skill.proficiency_level
                    )}`}
                  >
                    {skill.proficiency_level.charAt(0).toUpperCase() +
                      skill.proficiency_level.slice(1)}
                  </span>
                </div>

                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-600">Confidence Level</span>
                      <span className="text-sm font-medium text-gray-900">
                        {Math.round(skill.confidence * 100)}%
                      </span>
                    </div>
                    {getConfidenceBar(skill.confidence)}
                  </div>
                </div>

                <div className="mt-4 text-xs text-gray-500">
                  <span>Added {new Date(skill.created_at).toLocaleDateString()}</span>
                  {skill.update_count > 0 && (
                    <span> • Updated {skill.update_count} time{skill.update_count !== 1 ? 's' : ''}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
