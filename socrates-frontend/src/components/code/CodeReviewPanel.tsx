/**
 * Code Review Panel - Display code with inline comments and annotations
 *
 * Features:
 * - Line-by-line code display
 * - Inline comments on specific lines
 * - Issue highlighting and annotation
 * - Reviewer marks and status badges
 * - Discussion threads per annotation
 */

import React, { useState } from "react";
import { MessageCircle, MoreVertical, CheckCircle, AlertTriangle, AlertCircle } from "lucide-react";
import { Button } from "../common";

interface CodeAnnotation {
  id: string;
  lineNumber: number;
  type: "comment" | "issue" | "suggestion";
  severity?: "error" | "warning" | "info";
  author: string;
  content: string;
  timestamp: string;
  replies: CodeReply[];
  resolved: boolean;
}

interface CodeReply {
  id: string;
  author: string;
  content: string;
  timestamp: string;
}

interface CodeReviewPanelProps {
  code: string;
  fileName: string;
  language: string;
  annotations?: CodeAnnotation[];
  onAddAnnotation?: (lineNumber: number, annotation: CodeAnnotation) => void;
  onResolveAnnotation?: (annotationId: string) => void;
  readOnly?: boolean;
}

export const CodeReviewPanel: React.FC<CodeReviewPanelProps> = ({
  code,
  fileName,
  language,
  annotations = [],
  onAddAnnotation,
  onResolveAnnotation,
  readOnly = false,
}) => {
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [commentType, setCommentType] = useState<"comment" | "issue" | "suggestion">("comment");
  const [selectedAnnotation, setSelectedAnnotation] = useState<CodeAnnotation | null>(null);
  const [replyText, setReplyText] = useState("");
  const [annotationMenuAnchor, setAnnotationMenuAnchor] = useState<null | HTMLElement>(null);

  const lines = code.split("\n");

  const getAnnotationsForLine = (lineNumber: number): CodeAnnotation[] => {
    return annotations.filter((a) => a.lineNumber === lineNumber);
  };

  const getAnnotationColor = (annotation: CodeAnnotation) => {
    if (annotation.severity === "error") return "#ff6b6b";
    if (annotation.severity === "warning") return "#ffd43b";
    return "#74c0fc";
  };

  const getAnnotationIcon = (annotation: CodeAnnotation) => {
    if (annotation.severity === "error") return <AlertCircle className="w-4 h-4" />;
    if (annotation.severity === "warning") return <AlertTriangle className="w-4 h-4" />;
    return <CheckCircle className="w-4 h-4" />;
  };

  const handleAddComment = () => {
    if (!selectedLine || !commentText.trim()) return;

    const newAnnotation: CodeAnnotation = {
      id: `ann_${Date.now()}`,
      lineNumber: selectedLine,
      type: commentType,
      severity: commentType === "issue" ? "warning" : undefined,
      author: "Current User",
      content: commentText,
      timestamp: new Date().toISOString(),
      replies: [],
      resolved: false,
    };

    onAddAnnotation?.(selectedLine, newAnnotation);

    setCommentText("");
    setCommentType("comment");
    setCommentDialogOpen(false);
    setSelectedLine(null);
  };

  const handleAddReply = (annotationId: string) => {
    if (!replyText.trim()) return;

    // In a real implementation, this would update the annotation with a new reply
    setReplyText("");
  };

  return (
    <div className="flex h-full gap-2">
      {/* Code Panel */}
      <div className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
        <div className="p-4">
          <div className="mb-4 font-bold text-sm">📄 {fileName}</div>

          <div className="font-mono text-sm space-y-0">
            {lines.map((line, index) => {
              const lineNumber = index + 1;
              const lineAnnotations = getAnnotationsForLine(lineNumber);

              return (
                <div key={lineNumber}>
                  <div
                    className={`flex items-start cursor-pointer transition-colors ${
                      selectedLine === lineNumber
                        ? "bg-blue-50 dark:bg-blue-900/20"
                        : "hover:bg-gray-100 dark:hover:bg-gray-800"
                    }`}
                    onClick={() => setSelectedLine(lineNumber)}
                  >
                    {/* Line Number */}
                    <div className="w-12 px-3 py-1 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 text-right border-r border-gray-200 dark:border-gray-700 text-xs flex-shrink-0">
                      {lineNumber}
                    </div>

                    {/* Code Content */}
                    <div className="flex-1 px-3 py-1 whitespace-pre-wrap break-all text-gray-700 dark:text-gray-300">
                      {line || " "}
                    </div>

                    {/* Annotation Indicators */}
                    {lineAnnotations.length > 0 && (
                      <div className="flex gap-1 px-2 items-center">
                        {lineAnnotations.map((ann) => (
                          <div
                            key={ann.id}
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: getAnnotationColor(ann) }}
                            title={ann.content}
                          />
                        ))}
                      </div>
                    )}

                    {/* Add Comment Button */}
                    {!readOnly && selectedLine === lineNumber && (
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<MessageCircle className="w-4 h-4" />}
                        onClick={(e) => {
                          e.stopPropagation();
                          setCommentDialogOpen(true);
                        }}
                        className="ml-2"
                      >
                        Comment
                      </Button>
                    )}
                  </div>

                  {/* Inline Annotations */}
                  {lineAnnotations.map((annotation) => (
                    <div
                      key={annotation.id}
                      className="ml-12 pl-4 py-2 border-l-4 bg-gray-50 dark:bg-gray-800/50"
                      style={{ borderLeftColor: getAnnotationColor(annotation) }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {getAnnotationIcon(annotation)}
                        <span className="text-xs font-bold text-gray-900 dark:text-white">
                          {annotation.type.charAt(0).toUpperCase() + annotation.type.slice(1)}
                        </span>
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          by {annotation.author}
                        </span>
                        {annotation.resolved && (
                          <span className="text-xs px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300">
                            Resolved
                          </span>
                        )}
                      </div>

                      <div className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                        {annotation.content}
                      </div>

                      {annotation.replies.length > 0 && (
                        <div className="mt-2 ml-4 border-l border-gray-300 dark:border-gray-600 pl-2 space-y-1">
                          {annotation.replies.map((reply) => (
                            <div key={reply.id} className="text-xs">
                              <span className="font-bold text-gray-700 dark:text-gray-300">
                                {reply.author}:
                              </span>
                              <span className="text-gray-600 dark:text-gray-400 ml-1">
                                {reply.content}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {!readOnly && (
                        <div className="flex gap-2 mt-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<MessageCircle className="w-4 h-4" />}
                            onClick={() => setSelectedAnnotation(annotation)}
                          >
                            Reply
                          </Button>
                          {!annotation.resolved && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onResolveAnnotation?.(annotation.id)}
                            >
                              Resolve
                            </Button>
                          )}
                          <button
                            onClick={(e) => {
                              setAnnotationMenuAnchor(e.currentTarget as HTMLElement);
                              setSelectedAnnotation(annotation);
                            }}
                            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Add Comment Dialog */}
      {commentDialogOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
              <h2 className="font-semibold text-gray-900 dark:text-white">
                Add Comment to Line {selectedLine}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <select
                value={commentType}
                onChange={(e) => setCommentType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="comment">💬 Comment</option>
                <option value="issue">⚠️ Issue</option>
                <option value="suggestion">💡 Suggestion</option>
              </select>

              <textarea
                rows={4}
                placeholder="Write your comment..."
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800 flex justify-end gap-3">
              <Button
                variant="secondary"
                onClick={() => {
                  setCommentDialogOpen(false);
                  setCommentText("");
                  setCommentType("comment");
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleAddComment}
                disabled={!commentText.trim()}
              >
                Add Comment
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CodeReviewPanel;
