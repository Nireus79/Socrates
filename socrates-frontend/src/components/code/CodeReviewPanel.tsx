"""
Code Review Panel - Display code with inline comments and annotations

Features:
- Line-by-line code display
- Inline comments on specific lines
- Issue highlighting and annotation
- Reviewer marks and status badges
- Discussion threads per annotation
"""

import React, { useState } from "react";
import {
  Box,
  Paper,
  TextField,
  Button,
  Avatar,
  Typography,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
} from "@mui/material";
import {
  DeleteIcon,
  ReplyIcon,
  MoreVertIcon,
  CheckCircleIcon,
  WarningIcon,
  ErrorIcon,
} from "@mui/icons-material";

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
    if (annotation.severity === "error") return <ErrorIcon fontSize="small" />;
    if (annotation.severity === "warning") return <WarningIcon fontSize="small" />;
    return <CheckCircleIcon fontSize="small" />;
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
    <Box sx={{ display: "flex", height: "100%", gap: 2 }}>
      {/* Code Panel */}
      <Paper
        sx={{
          flex: 1,
          overflow: "auto",
          fontFamily: "monospace",
          fontSize: "0.875rem",
          backgroundColor: "#f5f5f5",
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: "bold" }}>
            📄 {fileName}
          </Typography>

          <Box sx={{ display: "flex", flexDirection: "column" }}>
            {lines.map((line, index) => {
              const lineNumber = index + 1;
              const lineAnnotations = getAnnotationsForLine(lineNumber);

              return (
                <div key={lineNumber}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "flex-start",
                      backgroundColor:
                        selectedLine === lineNumber ? "rgba(66, 165, 245, 0.1)" : "transparent",
                      transition: "background-color 0.2s",
                      cursor: "pointer",
                      "&:hover": {
                        backgroundColor: "rgba(0, 0, 0, 0.02)",
                      },
                    }}
                    onClick={() => setSelectedLine(lineNumber)}
                  >
                    {/* Line Number */}
                    <Box
                      sx={{
                        width: "50px",
                        padding: "4px 12px",
                        backgroundColor: "#f0f0f0",
                        color: "#999",
                        textAlign: "right",
                        userSelect: "none",
                        borderRight: "1px solid #ddd",
                        fontSize: "0.8rem",
                      }}
                    >
                      {lineNumber}
                    </Box>

                    {/* Code Content */}
                    <Box
                      sx={{
                        flex: 1,
                        padding: "4px 12px",
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-all",
                        color: "#333",
                      }}
                    >
                      {line || " "}
                    </Box>

                    {/* Annotation Indicators */}
                    {lineAnnotations.length > 0 && (
                      <Box sx={{ display: "flex", gap: 0.5, px: 1, alignItems: "center" }}>
                        {lineAnnotations.map((ann) => (
                          <Tooltip key={ann.id} title={ann.content}>
                            <Box
                              sx={{
                                width: "8px",
                                height: "8px",
                                borderRadius: "50%",
                                backgroundColor: getAnnotationColor(ann),
                              }}
                            />
                          </Tooltip>
                        ))}
                      </Box>
                    )}

                    {/* Add Comment Button */}
                    {!readOnly && selectedLine === lineNumber && (
                      <Button
                        size="small"
                        sx={{ ml: 1 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setCommentDialogOpen(true);
                        }}
                      >
                        💬 Comment
                      </Button>
                    )}
                  </Box>

                  {/* Inline Annotations */}
                  {lineAnnotations.map((annotation) => (
                    <Box
                      key={annotation.id}
                      sx={{
                        ml: "50px",
                        pl: 2,
                        py: 1,
                        borderLeft: `3px solid ${getAnnotationColor(annotation)}`,
                        backgroundColor: "rgba(0,0,0,0.02)",
                      }}
                    >
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                        {getAnnotationIcon(annotation)}
                        <Typography variant="caption" sx={{ fontWeight: "bold" }}>
                          {annotation.type.charAt(0).toUpperCase() + annotation.type.slice(1)}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          by {annotation.author}
                        </Typography>
                        {annotation.resolved && (
                          <Chip label="Resolved" size="small" variant="outlined" />
                        )}
                      </Box>

                      <Typography variant="body2" sx={{ mb: 1 }}>
                        {annotation.content}
                      </Typography>

                      {annotation.replies.length > 0 && (
                        <Box sx={{ mt: 1, ml: 2, borderLeft: "1px solid #ddd", pl: 1 }}>
                          {annotation.replies.map((reply) => (
                            <Box key={reply.id} sx={{ mb: 1 }}>
                              <Typography variant="caption" sx={{ fontWeight: "bold" }}>
                                {reply.author}:
                              </Typography>
                              <Typography variant="caption"> {reply.content}</Typography>
                            </Box>
                          ))}
                        </Box>
                      )}

                      {!readOnly && (
                        <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                          <Button
                            size="small"
                            startIcon={<ReplyIcon />}
                            onClick={() => setSelectedAnnotation(annotation)}
                          >
                            Reply
                          </Button>
                          {!annotation.resolved && (
                            <Button
                              size="small"
                              onClick={() => onResolveAnnotation?.(annotation.id)}
                            >
                              Resolve
                            </Button>
                          )}
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              setAnnotationMenuAnchor(e.currentTarget);
                              setSelectedAnnotation(annotation);
                            }}
                          >
                            <MoreVertIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      )}
                    </Box>
                  ))}
                </div>
              );
            })}
          </Box>
        </Box>
      </Paper>

      {/* Add Comment Dialog */}
      <Dialog
        open={commentDialogOpen}
        onClose={() => {
          setCommentDialogOpen(false);
          setCommentText("");
          setCommentType("comment");
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Comment to Line {selectedLine}</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            select
            fullWidth
            label="Comment Type"
            value={commentType}
            onChange={(e) => setCommentType(e.target.value as any)}
            sx={{ mb: 2 }}
          >
            <MenuItem value="comment">💬 Comment</MenuItem>
            <MenuItem value="issue">⚠️ Issue</MenuItem>
            <MenuItem value="suggestion">💡 Suggestion</MenuItem>
          </TextField>

          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="Write your comment..."
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAddComment} disabled={!commentText.trim()}>
            Add Comment
          </Button>
        </DialogActions>
      </Dialog>

      {/* Annotation Menu */}
      <Menu
        anchorEl={annotationMenuAnchor}
        open={Boolean(annotationMenuAnchor)}
        onClose={() => setAnnotationMenuAnchor(null)}
      >
        <MenuItem onClick={() => setAnnotationMenuAnchor(null)}>Edit</MenuItem>
        <MenuItem onClick={() => setAnnotationMenuAnchor(null)}>Delete</MenuItem>
      </Menu>
    </Box>
  );
};

export default CodeReviewPanel;
