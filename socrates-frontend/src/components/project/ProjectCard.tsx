/**
 * ProjectCard Component - Displays individual project summary
 */

import React from 'react';
import { MoreVertical, Users } from 'lucide-react';
import type { Project } from '../../types/models';
import { Card, Badge, Progress, Button, Dropdown } from '../common';

interface ProjectCardProps {
  project: Project;
  maturity?: number;
  teamCount?: number;
  onOpen?: (id: string) => void;
  onEdit?: (id: string) => void;
  onArchive?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  maturity = 0,
  teamCount = 0,
  onOpen,
  onEdit,
  onArchive,
  onDelete,
}) => {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const phaseNames: Record<string, string> = {
    'discovery': 'Discovery',
    'analysis': 'Analysis',
    'design': 'Design',
    'implementation': 'Implementation',
    'testing': 'Testing',
    'deployment': 'Deployment',
  };

  const phaseVariants: Record<string, string> = {
    'discovery': 'blue',
    'analysis': 'purple',
    'design': 'pink',
    'implementation': 'green',
    'testing': 'orange',
    'deployment': 'indigo',
  };

  return (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => onOpen?.(project.project_id)}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex justify-between items-start gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {project.name}
            </h3>
            <Badge
              variant={phaseVariants[project.phase] as any}
              size="sm"
              className="mt-1"
            >
              {phaseNames[project.phase]}
            </Badge>
          </div>

          <div className="flex-shrink-0">
            <Dropdown
              isOpen={isMenuOpen}
              onClose={() => setIsMenuOpen(false)}
              trigger={
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsMenuOpen(!isMenuOpen);
                  }}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <MoreVertical className="h-4 w-4" />
                </button>
              }
            >
              {onEdit && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(project.project_id);
                    setIsMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Edit
                </button>
              )}
              {onArchive && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onArchive(project.project_id);
                    setIsMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {project.is_archived ? 'Restore' : 'Archive'}
                </button>
              )}
              {onDelete && (
                <>
                  <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(project.project_id);
                      setIsMenuOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900"
                  >
                    Delete
                  </button>
                </>
              )}
            </Dropdown>
          </div>
        </div>

        {/* Phase and Progress */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Created {new Date(project.created_at).toLocaleDateString()}
            </span>
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
              {maturity}%
            </span>
          </div>
          <Progress value={maturity} size="sm" />
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
            <Users className="h-4 w-4" />
            <span>{teamCount} member{teamCount !== 1 ? 's' : ''}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onOpen?.(project.project_id);
            }}
          >
            Open
          </Button>
        </div>
      </div>
    </Card>
  );
};

ProjectCard.displayName = 'ProjectCard';
