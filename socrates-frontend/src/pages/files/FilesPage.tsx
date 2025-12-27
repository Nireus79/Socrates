"""
Files Page - Browse generated, imported, and saved project files

Displays:
- Directory structure of generated files
- File explorer with syntax highlighting preview
- File statistics and metadata
- Import/export operations
"""

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  Divider,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  Tooltip,
  IconButton,
} from "@mui/material";
import {
  ExpandLess,
  ExpandMore,
  FolderIcon,
  FileIcon,
  DescriptionIcon,
  CodeIcon,
  DownloadIcon,
  RefreshIcon,
  SearchIcon,
  DeleteIcon,
  CopyIcon,
  VisibilityIcon,
  CloudUploadIcon,
} from "@mui/icons-material";
import { useProjectStore } from "../../stores/projectStore";
import { useUIStore } from "../../stores/uiStore";

interface FileNode {
  name: string;
  path: string;
  type: "file" | "folder";
  language?: string;
  size?: number;
  children?: FileNode[];
  content?: string;
  createdAt?: string;
  updatedAt?: string;
}

export const FilesPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject } = useProjectStore();
  const { showNotification } = useUIStore();

  const [files, setFiles] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set()
  );
  const [viewMode, setViewMode] = useState<"tree" | "list">("tree");
  const [filePreviewOpen, setFilePreviewOpen] = useState(false);
  const [fileStats, setFileStats] = useState({
    totalFiles: 0,
    totalSize: 0,
    byType: {} as Record<string, number>,
  });
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Load files on mount or when projectId changes
  useEffect(() => {
    if (projectId) {
      loadProjectFiles();
    }
  }, [projectId]);

  const loadProjectFiles = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/projects/${projectId}/files`);
      if (!response.ok) throw new Error("Failed to load files");

      const data = await response.json();
      const fileTree = buildFileTree(data.files);
      setFiles(fileTree);
      calculateStats(data.files);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      showNotification(message, "error");
    } finally {
      setLoading(false);
    }
  };

  const buildFileTree = (fileList: any[]): FileNode[] => {
    const map: Record<string, FileNode> = {};
    const roots: FileNode[] = [];

    // First pass: create all nodes
    fileList.forEach((file) => {
      map[file.path] = {
        name: getFileName(file.path),
        path: file.path,
        type: "file",
        language: detectLanguage(file.path),
        size: file.size,
        content: file.content,
        createdAt: file.createdAt,
        updatedAt: file.updatedAt,
      };
    });

    // Second pass: build tree structure
    fileList.forEach((file) => {
      const parts = file.path.split("/");
      let current = roots;
      let currentPath = "";

      for (let i = 0; i < parts.length - 1; i++) {
        currentPath += (currentPath ? "/" : "") + parts[i];
        let folder = (current as any).find(
          (n: any) => n.path === currentPath && n.type === "folder"
        );

        if (!folder) {
          folder = {
            name: parts[i],
            path: currentPath,
            type: "folder",
            children: [],
          };
          current.push(folder);
        }

        current = folder.children!;
      }

      current.push(map[file.path]);
    });

    return roots;
  };

  const calculateStats = (fileList: any[]) => {
    const stats = {
      totalFiles: fileList.length,
      totalSize: fileList.reduce((sum, f) => sum + (f.size || 0), 0),
      byType: {} as Record<string, number>,
    };

    fileList.forEach((file) => {
      const ext = file.path.split(".").pop() || "unknown";
      stats.byType[ext] = (stats.byType[ext] || 0) + 1;
    });

    setFileStats(stats);
  };

  const detectLanguage = (path: string): string => {
    const ext = path.split(".").pop()?.toLowerCase() || "";
    const langMap: Record<string, string> = {
      py: "python",
      js: "javascript",
      ts: "typescript",
      jsx: "jsx",
      tsx: "tsx",
      java: "java",
      cpp: "cpp",
      cs: "csharp",
      go: "go",
      rs: "rust",
      md: "markdown",
      json: "json",
      yaml: "yaml",
      yml: "yaml",
      xml: "xml",
      html: "html",
      css: "css",
      sql: "sql",
    };
    return langMap[ext] || ext;
  };

  const getFileName = (path: string): string => {
    return path.split("/").pop() || path;
  };

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const filteredFiles = filterFiles(files, searchTerm);

  const handleDownloadFile = async (file: FileNode) => {
    try {
      const response = await fetch(
        `/api/projects/${projectId}/files/${encodeURIComponent(file.path)}`
      );
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = file.name;
      link.click();
      showNotification(`Downloaded ${file.name}`, "success");
    } catch (err) {
      showNotification("Failed to download file", "error");
    }
  };

  const handleDeleteFile = async (file: FileNode) => {
    if (!window.confirm(`Delete ${file.name}?`)) return;

    try {
      const response = await fetch(
        `/api/projects/${projectId}/files/${encodeURIComponent(file.path)}`,
        { method: "DELETE" }
      );

      if (!response.ok) throw new Error("Failed to delete file");

      showNotification(`Deleted ${file.name}`, "success");
      loadProjectFiles();
    } catch (err) {
      showNotification("Failed to delete file", "error");
    }
  };

  const handleUploadFiles = async (filesToUpload: FileList) => {
    if (!projectId) {
      showNotification("No project selected", "error");
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();

      for (let i = 0; i < filesToUpload.length; i++) {
        formData.append("files", filesToUpload[i]);
      }

      const response = await fetch(
        `/api/projects/${projectId}/files/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) throw new Error("Upload failed");

      showNotification(
        `✓ Uploaded ${filesToUpload.length} file(s)`,
        "success"
      );
      setUploadDialogOpen(false);
      loadProjectFiles();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      showNotification(message, "error");
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUploadFiles(e.dataTransfer.files);
    }
  };

  const renderFileTree = (nodes: FileNode[], depth = 0) => {
    return nodes.map((node) => (
      <div key={node.path}>
        <ListItem
          sx={{ pl: 2 + depth * 2 }}
          button
          onClick={() => {
            if (node.type === "folder") {
              toggleFolder(node.path);
            } else {
              setSelectedFile(node);
              setFilePreviewOpen(true);
            }
          }}
        >
          <ListItemIcon>
            {node.type === "folder" ? (
              expandedFolders.has(node.path) ? (
                <ExpandLess />
              ) : (
                <ExpandMore />
              )
            ) : (
              <FileIcon />
            )}
          </ListItemIcon>
          <ListItemText
            primary={node.name}
            secondary={
              node.type === "file"
                ? `${node.language} • ${formatFileSize(node.size || 0)}`
                : undefined
            }
          />
          {node.type === "file" && (
            <Box sx={{ display: "flex", gap: 1 }}>
              <Tooltip title="View">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(node);
                    setFilePreviewOpen(true);
                  }}
                >
                  <VisibilityIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Download">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownloadFile(node);
                  }}
                >
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteFile(node);
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </ListItem>

        {node.type === "folder" && expandedFolders.has(node.path) && (
          <div>
            {renderFileTree(node.children || [], depth + 1)}
          </div>
        )}
      </div>
    ));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const filterFiles = (nodes: FileNode[], term: string): FileNode[] => {
    if (!term) return nodes;
    return nodes
      .map((node) => ({
        ...node,
        children:
          node.type === "folder" ? filterFiles(node.children || [], term) : [],
      }))
      .filter(
        (node) =>
          node.name.toLowerCase().includes(term.toLowerCase()) ||
          (node.type === "folder" && node.children && node.children.length > 0)
      );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 2 }}>
          📁 Project Files
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Browse and manage generated, imported, and saved project files
        </Typography>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Files
              </Typography>
              <Typography variant="h5">{fileStats.totalFiles}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Size
              </Typography>
              <Typography variant="h5">
                {formatFileSize(fileStats.totalSize)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={6}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                File Types
              </Typography>
              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1 }}>
                {Object.entries(fileStats.byType).map(([ext, count]) => (
                  <Chip
                    key={ext}
                    label={`${ext}: ${count}`}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search and Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
          <TextField
            fullWidth
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <Button
            startIcon={<CloudUploadIcon />}
            variant="contained"
            color="success"
            onClick={() => setUploadDialogOpen(true)}
            disabled={loading || uploading}
          >
            Upload Files
          </Button>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadProjectFiles}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* File Browser */}
      {loading ? (
        <LinearProgress />
      ) : (
        <Paper>
          <List>
            {filteredFiles.length > 0 ? (
              renderFileTree(filteredFiles)
            ) : (
              <Box sx={{ p: 3, textAlign: "center" }}>
                <Typography color="textSecondary">
                  No files found {searchTerm && "matching your search"}
                </Typography>
              </Box>
            )}
          </List>
        </Paper>
      )}

      {/* File Preview Dialog */}
      <Dialog
        open={filePreviewOpen}
        onClose={() => setFilePreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedFile?.name}
          <Chip
            label={selectedFile?.language}
            size="small"
            sx={{ ml: 1 }}
          />
        </DialogTitle>
        <DialogContent>
          <Box
            sx={{
              fontFamily: "monospace",
              fontSize: "0.85rem",
              whiteSpace: "pre-wrap",
              wordWrap: "break-word",
              backgroundColor: "#f5f5f5",
              p: 2,
              mt: 2,
              maxHeight: "400px",
              overflowY: "auto",
            }}
          >
            {selectedFile?.content}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFilePreviewOpen(false)}>Close</Button>
          {selectedFile && (
            <>
              <Button
                startIcon={<CopyIcon />}
                onClick={() => {
                  if (selectedFile.content) {
                    navigator.clipboard.writeText(selectedFile.content);
                    showNotification("Copied to clipboard", "success");
                  }
                }}
              >
                Copy
              </Button>
              <Button
                startIcon={<DownloadIcon />}
                onClick={() => {
                  if (selectedFile) handleDownloadFile(selectedFile);
                }}
              >
                Download
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload Files to Project</DialogTitle>
        <DialogContent>
          <Box
            sx={{
              border: "2px dashed",
              borderColor: dragActive ? "primary.main" : "divider",
              borderRadius: 2,
              p: 3,
              textAlign: "center",
              backgroundColor: dragActive ? "action.hover" : "transparent",
              transition: "all 0.3s ease",
              cursor: "pointer",
              mt: 2,
            }}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <CloudUploadIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
            <Typography variant="h6" sx={{ mb: 1 }}>
              Drag and drop files here
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              or click to select files from your computer
            </Typography>
            <Button
              variant="contained"
              component="label"
              disabled={uploading}
            >
              Select Files
              <input
                ref={fileInputRef}
                hidden
                multiple
                type="file"
                onChange={(e) => {
                  if (e.target.files) {
                    handleUploadFiles(e.target.files);
                  }
                }}
              />
            </Button>

            {uploading && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="caption" sx={{ mt: 1, display: "block" }}>
                  Uploading...
                </Typography>
              </Box>
            )}
          </Box>

          <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: "block" }}>
            Supported formats: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Markdown, JSON, YAML, XML, HTML, CSS, SQL
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)} disabled={uploading}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default FilesPage;
