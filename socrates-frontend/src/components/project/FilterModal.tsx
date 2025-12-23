/**
 * FilterModal Component - Advanced filtering for projects
 */

import React from 'react';
import { Modal, Select, Button, Checkbox } from '../common';

interface FilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (filters: FilterOptions) => void;
  onReset: () => void;
}

export interface FilterOptions {
  archived: boolean | null;
}

export const FilterModal: React.FC<FilterModalProps> = ({
  isOpen,
  onClose,
  onApply,
  onReset,
}) => {
  const [filters, setFilters] = React.useState<FilterOptions>({
    archived: null,
  });

  const handleReset = () => {
    setFilters({ archived: null });
    onReset();
    onClose();
  };

  const handleApply = () => {
    onApply(filters);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Filter Projects"
      size="sm"
    >
      <div className="space-y-6">
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900 dark:text-white">Status</h4>
          <div className="space-y-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <Checkbox
                checked={filters.archived === false}
                onChange={() => setFilters({ ...filters, archived: filters.archived === false ? null : false })}
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Active Projects</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <Checkbox
                checked={filters.archived === true}
                onChange={() => setFilters({ ...filters, archived: filters.archived === true ? null : true })}
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Archived Projects</span>
            </label>
          </div>
        </div>

        <div className="flex gap-3">
          <Button
            variant="secondary"
            fullWidth
            onClick={handleReset}
          >
            Reset Filters
          </Button>
          <Button
            variant="primary"
            fullWidth
            onClick={handleApply}
          >
            Apply Filters
          </Button>
        </div>
      </div>
    </Modal>
  );
};

FilterModal.displayName = 'FilterModal';
