/**
 * NoteForm - Create or edit a note
 */

import React, { useState } from 'react';
import { Plus, X } from 'lucide-react';
import { Button, Input, TextArea } from '../common';

interface NoteFormProps {
  onSubmit: (title: string, content: string, tags: string[]) => Promise<void>;
  isSubmitting?: boolean;
  error?: string;
}

export const NoteForm: React.FC<NoteFormProps> = ({ onSubmit, isSubmitting = false, error }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  const handleAddTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      return;
    }

    try {
      await onSubmit(title, content, tags);
      // Reset form
      setTitle('');
      setContent('');
      setTags([]);
      setTagInput('');
    } catch (err) {
      // Error is handled by parent component
    }
  };

  const isValid = title.trim().length > 0 && content.trim().length > 0;

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Title Input */}
      <div className="mb-4">
        <label htmlFor="note-title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Title
        </label>
        <Input
          id="note-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Note title..."
          disabled={isSubmitting}
        />
      </div>

      {/* Content Input */}
      <div className="mb-4">
        <label htmlFor="note-content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Content
        </label>
        <TextArea
          id="note-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Write your note here..."
          rows={6}
          disabled={isSubmitting}
        />
      </div>

      {/* Tags Input */}
      <div className="mb-4">
        <label htmlFor="note-tag" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Tags
        </label>
        <div className="flex gap-2 mb-2">
          <Input
            id="note-tag"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value.toLowerCase())}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddTag();
              }
            }}
            placeholder="Add tags and press Enter..."
            disabled={isSubmitting}
          />
          <Button
            type="button"
            variant="secondary"
            icon={<Plus className="h-4 w-4" />}
            onClick={handleAddTag}
            disabled={isSubmitting || !tagInput.trim()}
          >
            Add
          </Button>
        </div>

        {/* Tag List */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm rounded"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  disabled={isSubmitting}
                  className="hover:text-blue-900 dark:hover:text-blue-200"
                >
                  <X className="h-4 w-4" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        disabled={isSubmitting || !isValid}
        className="w-full"
      >
        {isSubmitting ? 'Creating...' : 'Create Note'}
      </Button>
    </form>
  );
};
