"""
Analysis & Testing Control Panel

Allows users to:
- Run code validation (syntax, dependencies)
- Execute tests (pytest, jest, mocha)
- Analyze code structure and quality
- Auto-fix issues
- Refactor code
- View analysis results and recommendations
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
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  FormGroup,
  FormControlLabel,
} from "@mui/material";
import {
  PlayArrowIcon,
  CheckCircleIcon,
  ErrorIcon,
  WarningIcon,
  RefreshIcon,
  DownloadIcon,
  BugReportIcon,
  SpeedIcon,
  CodeIcon,
  AutoFixHighIcon,
  AssignmentIcon,
} from "@mui/icons-material";
import { useProjectStore } from "../../stores/projectStore";
import { useUIStore } from "../../stores/uiStore";

interface ValidationResult {
  status: "success" | "error" | "warning" | "running";
  validation_results?: {
    syntax?: {
      valid: boolean;
      issues: Array<{ file: string; line: number; message: string }>;
    };
    dependencies?: {
      missing: string[];
      unused: string[];
    };
    tests?: {
      tests_passed: number;
      tests_failed: number;
      tests_skipped: number;
      duration_seconds: number;
      failures?: Array<{ test: string; message: string }>;
    };
  };
  recommendations?: string[];
  timestamp?: string;
}

interface AnalysisResult {
  status: "success" | "error" | "running";
  analysis_summary?: {
    maturity_score: number;
    phase: string;
    completeness: number;
    quality_score: number;
  };
  metrics?: {
    lines_of_code: number;
    cyclomatic_complexity: number;
    functions: number;
    classes: number;
  };
  warnings?: string[];
  timestamp?: string;
}

export const AnalysisPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject } = useProjectStore();
  const { showNotification } = useUIStore();

  const [activeTab, setActiveTab] = useState(0);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [refactorDialogOpen, setRefactorDialogOpen] = useState(false);
  const [refactorType, setRefactorType] = useState<string>("optimize");
  const [refactoringInProgress, setRefactoringInProgress] = useState(false);

  // Batch analysis state
  const [batchMode, setBatchMode] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [batchResults, setBatchResults] = useState<Record<string, ValidationResult>>({});
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });

  const handleValidate = async () => {
    try {
      setLoading(true);
      setValidationResult({ status: "running" });

      const response = await fetch(`/api/analysis/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          validate_syntax: true,
          validate_dependencies: true,
          run_tests: true,
        }),
      });

      if (!response.ok) throw new Error("Validation failed");

      const data = await response.json();
      setValidationResult(data);
      setActiveTab(0);

      const failureCount =
        (data.validation_results?.syntax?.issues?.length || 0) +
        (data.validation_results?.dependencies?.missing?.length || 0) +
        (data.validation_results?.tests?.tests_failed || 0);

      showNotification(
        failureCount === 0
          ? "✓ All validations passed!"
          : `⚠ Found ${failureCount} issues`,
        failureCount === 0 ? "success" : "warning"
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Validation failed";
      setValidationResult({ status: "error" });
      showNotification(message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleBatchAnalyze = async () => {
    if (selectedFiles.size === 0) {
      showNotification("Select at least one file to analyze", "warning");
      return;
    }

    try {
      setLoading(true);
      setBatchProgress({ current: 0, total: selectedFiles.size });
      const results: Record<string, ValidationResult> = {};
      const filesArray = Array.from(selectedFiles);

      for (let i = 0; i < filesArray.length; i++) {
        const file = filesArray[i];
        setBatchProgress({ current: i + 1, total: filesArray.length });

        try {
          const response = await fetch(`/api/analysis/validate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              project_id: projectId,
              file_path: file,
              validate_syntax: true,
              validate_dependencies: true,
            }),
          });

          if (response.ok) {
            results[file] = await response.json();
          } else {
            results[file] = { status: "error" };
          }
        } catch (err) {
          results[file] = { status: "error" };
        }
      }

      setBatchResults(results);
      setActiveTab(0);
      showNotification(`✓ Analyzed ${filesArray.length} files`, "success");
    } catch (err) {
      showNotification("Batch analysis failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setAnalysisResult({ status: "running" });

      const response = await fetch(`/api/analysis/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          include_structure: true,
          include_quality: true,
        }),
      });

      if (!response.ok) throw new Error("Analysis failed");

      const data = await response.json();
      setAnalysisResult(data);
      setActiveTab(1);
      showNotification("✓ Analysis complete", "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analysis failed";
      setAnalysisResult({ status: "error" });
      showNotification(message, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFix = async () => {
    try {
      setLoading(true);
      showNotification("🔧 Running auto-fix...", "info");

      const response = await fetch(`/api/analysis/fix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          fix_syntax: true,
          fix_imports: true,
        }),
      });

      if (!response.ok) throw new Error("Auto-fix failed");

      const data = await response.json();
      showNotification("✓ Auto-fix complete! Files updated.", "success");

      // Refresh validation to show improvements
      handleValidate();
    } catch (err) {
      showNotification("Failed to auto-fix issues", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleRefactor = async () => {
    try {
      setRefactoringInProgress(true);
      showNotification(`Refactoring code (${refactorType})...`, "info");

      const response = await fetch(
        `/api/projects/${projectId}/code/refactor`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            refactor_type: refactorType,
          }),
        }
      );

      if (!response.ok) throw new Error("Refactoring failed");

      const data = await response.json();
      showNotification("✓ Refactoring complete!", "success");
      setRefactorDialogOpen(false);

      // Re-analyze after refactoring
      handleAnalyze();
    } catch (err) {
      showNotification("Failed to refactor code", "error");
    } finally {
      setRefactoringInProgress(false);
    }
  };

  const getStatusChip = (status: string) => {
    const statusMap: Record<string, any> = {
      success: { color: "success", icon: <CheckCircleIcon /> },
      error: { color: "error", icon: <ErrorIcon /> },
      warning: { color: "warning", icon: <WarningIcon /> },
      running: { color: "info", icon: <RefreshIcon /> },
    };

    const config = statusMap[status] || statusMap.warning;
    return (
      <Chip
        icon={config.icon}
        label={status.charAt(0).toUpperCase() + status.slice(1)}
        color={config.color}
        variant="filled"
      />
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 2 }}>
          🔍 Code Analysis & Testing
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Validate, analyze, test, and improve your project code
        </Typography>
      </Box>

      {/* Batch Mode Toggle */}
      <Paper sx={{ p: 2, mb: 3, backgroundColor: "action.hover" }}>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", justifyContent: "space-between" }}>
          <Box>
            <Typography variant="subtitle2">📦 Batch Analysis Mode</Typography>
            <Typography variant="caption" color="textSecondary">
              Analyze multiple files at once
            </Typography>
          </Box>
          <Button
            variant={batchMode ? "contained" : "outlined"}
            color={batchMode ? "primary" : "inherit"}
            onClick={() => {
              setBatchMode(!batchMode);
              setSelectedFiles(new Set());
              setBatchResults({});
            }}
          >
            {batchMode ? "Exit Batch Mode" : "Enable Batch Mode"}
          </Button>
        </Box>
      </Paper>

      {/* Batch File Selection */}
      {batchMode && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Select Files to Analyze
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={<Checkbox />}
              label="Select all files"
              onChange={(e) => {
                if (e.target.checked) {
                  // In real implementation, fetch files from project
                  setSelectedFiles(new Set(["file1.py", "file2.js", "file3.ts"]));
                } else {
                  setSelectedFiles(new Set());
                }
              }}
            />
          </FormGroup>

          {batchProgress.total > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption">
                Progress: {batchProgress.current}/{batchProgress.total}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(batchProgress.current / batchProgress.total) * 100}
                sx={{ mt: 1 }}
              />
            </Box>
          )}

          <Button
            variant="contained"
            color="primary"
            onClick={handleBatchAnalyze}
            disabled={selectedFiles.size === 0 || loading}
            sx={{ mt: 2 }}
          >
            Analyze {selectedFiles.size} File(s)
          </Button>
        </Paper>
      )}

      {/* Control Panel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Analysis Tools
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              startIcon={<AssignmentIcon />}
              onClick={handleValidate}
              disabled={loading}
              sx={{ height: "56px" }}
            >
              Validate Code
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="contained"
              color="secondary"
              startIcon={<SpeedIcon />}
              onClick={handleAnalyze}
              disabled={loading}
              sx={{ height: "56px" }}
            >
              Analyze Quality
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              color="success"
              startIcon={<AutoFixHighIcon />}
              onClick={handleAutoFix}
              disabled={loading || !validationResult}
              sx={{ height: "56px" }}
            >
              Auto-Fix Issues
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              color="primary"
              startIcon={<CodeIcon />}
              onClick={() => setRefactorDialogOpen(true)}
              disabled={loading}
              sx={{ height: "56px" }}
            >
              Refactor Code
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Tabs for Results */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="📋 Validation Results" />
          <Tab label="📊 Analysis Results" />
          <Tab label="📈 Metrics" />
        </Tabs>
        <Divider />

        {/* Validation Tab */}
        {activeTab === 0 && (
          <Box sx={{ p: 3 }}>
            {validationResult ? (
              <>
                <Box sx={{ display: "flex", gap: 1, mb: 3, alignItems: "center" }}>
                  {getStatusChip(validationResult.status)}
                  <Typography variant="caption" color="textSecondary">
                    {validationResult.timestamp}
                  </Typography>
                </Box>

                {/* Syntax Validation */}
                {validationResult.validation_results?.syntax && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Syntax Validation
                    </Typography>
                    {validationResult.validation_results.syntax.valid ? (
                      <Alert severity="success">✓ All files have valid syntax</Alert>
                    ) : (
                      <>
                        <Alert severity="error" sx={{ mb: 2 }}>
                          ✗ Found{" "}
                          {
                            validationResult.validation_results.syntax.issues
                              .length
                          }{" "}
                          syntax issues
                        </Alert>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>File</TableCell>
                                <TableCell>Line</TableCell>
                                <TableCell>Issue</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {validationResult.validation_results.syntax.issues.map(
                                (issue, idx) => (
                                  <TableRow key={idx}>
                                    <TableCell>{issue.file}</TableCell>
                                    <TableCell>{issue.line}</TableCell>
                                    <TableCell>{issue.message}</TableCell>
                                  </TableRow>
                                )
                              )}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </>
                    )}
                  </Box>
                )}

                {/* Dependencies */}
                {validationResult.validation_results?.dependencies && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Dependencies
                    </Typography>
                    {validationResult.validation_results.dependencies.missing
                      .length > 0 && (
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        Missing:{" "}
                        {validationResult.validation_results.dependencies.missing.join(
                          ", "
                        )}
                      </Alert>
                    )}
                    {validationResult.validation_results.dependencies.unused
                      .length > 0 && (
                      <Alert severity="info">
                        Unused:{" "}
                        {validationResult.validation_results.dependencies.unused.join(
                          ", "
                        )}
                      </Alert>
                    )}
                  </Box>
                )}

                {/* Tests */}
                {validationResult.validation_results?.tests && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Test Results
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6} sm={3}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="small">
                              Passed
                            </Typography>
                            <Typography variant="h5" sx={{ color: "green" }}>
                              {validationResult.validation_results.tests
                                .tests_passed || 0}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="small">
                              Failed
                            </Typography>
                            <Typography variant="h5" sx={{ color: "red" }}>
                              {validationResult.validation_results.tests
                                .tests_failed || 0}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="small">
                              Skipped
                            </Typography>
                            <Typography variant="h5" sx={{ color: "orange" }}>
                              {validationResult.validation_results.tests
                                .tests_skipped || 0}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Card>
                          <CardContent>
                            <Typography color="textSecondary" variant="small">
                              Duration
                            </Typography>
                            <Typography variant="h5">
                              {validationResult.validation_results.tests
                                .duration_seconds || 0}
                              s
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>

                    {validationResult.validation_results.tests.failures &&
                      validationResult.validation_results.tests.failures.length >
                        0 && (
                        <>
                          <Typography variant="subtitle2" sx={{ mb: 1 }}>
                            Failed Tests:
                          </Typography>
                          <List>
                            {validationResult.validation_results.tests.failures.map(
                              (failure, idx) => (
                                <ListItem key={idx}>
                                  <ListItemIcon>
                                    <ErrorIcon color="error" />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={failure.test}
                                    secondary={failure.message}
                                  />
                                </ListItem>
                              )
                            )}
                          </List>
                        </>
                      )}
                  </Box>
                )}

                {/* Recommendations */}
                {validationResult.recommendations &&
                  validationResult.recommendations.length > 0 && (
                    <Box>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Recommendations
                      </Typography>
                      <List>
                        {validationResult.recommendations.map((rec, idx) => (
                          <ListItem key={idx}>
                            <ListItemIcon>
                              <CheckCircleIcon color="primary" />
                            </ListItemIcon>
                            <ListItemText primary={rec} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
              </>
            ) : (
              <Alert severity="info">
                Run validation to see results here
              </Alert>
            )}
          </Box>
        )}

        {/* Analysis Tab */}
        {activeTab === 1 && (
          <Box sx={{ p: 3 }}>
            {analysisResult ? (
              <>
                <Box sx={{ display: "flex", gap: 1, mb: 3, alignItems: "center" }}>
                  {getStatusChip(analysisResult.status)}
                </Box>

                {analysisResult.analysis_summary && (
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Maturity Score
                          </Typography>
                          <Typography variant="h5">
                            {Math.round(
                              analysisResult.analysis_summary.maturity_score * 100
                            )}
                            %
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Quality Score
                          </Typography>
                          <Typography variant="h5">
                            {Math.round(
                              analysisResult.analysis_summary.quality_score * 100
                            )}
                            %
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Completeness
                          </Typography>
                          <Typography variant="h5">
                            {Math.round(
                              analysisResult.analysis_summary.completeness * 100
                            )}
                            %
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card>
                        <CardContent>
                          <Typography color="textSecondary" gutterBottom>
                            Phase
                          </Typography>
                          <Typography variant="h5">
                            {analysisResult.analysis_summary.phase}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                )}

                {analysisResult.warnings &&
                  analysisResult.warnings.length > 0 && (
                    <Box>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Warnings
                      </Typography>
                      {analysisResult.warnings.map((warning, idx) => (
                        <Alert severity="warning" sx={{ mb: 1 }} key={idx}>
                          {warning}
                        </Alert>
                      ))}
                    </Box>
                  )}
              </>
            ) : (
              <Alert severity="info">
                Run analysis to see results here
              </Alert>
            )}
          </Box>
        )}

        {/* Metrics Tab */}
        {activeTab === 2 && (
          <Box sx={{ p: 3 }}>
            {analysisResult?.metrics ? (
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Lines of Code
                      </Typography>
                      <Typography variant="h5">
                        {analysisResult.metrics.lines_of_code}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Functions
                      </Typography>
                      <Typography variant="h5">
                        {analysisResult.metrics.functions}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Classes
                      </Typography>
                      <Typography variant="h5">
                        {analysisResult.metrics.classes}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Complexity
                      </Typography>
                      <Typography variant="h5">
                        {analysisResult.metrics.cyclomatic_complexity}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            ) : (
              <Alert severity="info">
                Run analysis to see metrics here
              </Alert>
            )}
          </Box>
        )}
      </Paper>

      {/* Refactor Dialog */}
      <Dialog
        open={refactorDialogOpen}
        onClose={() => setRefactorDialogOpen(false)}
      >
        <DialogTitle>Refactor Code</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Refactor Type</InputLabel>
            <Select
              value={refactorType}
              onChange={(e) => setRefactorType(e.target.value)}
              label="Refactor Type"
            >
              <MenuItem value="optimize">Optimize (improve performance)</MenuItem>
              <MenuItem value="simplify">Simplify (reduce complexity)</MenuItem>
              <MenuItem value="document">Document (add comments & docstrings)</MenuItem>
              <MenuItem value="modernize">Modernize (update to latest practices)</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRefactorDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleRefactor}
            variant="contained"
            disabled={refactoringInProgress}
          >
            {refactoringInProgress ? "Refactoring..." : "Refactor"}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AnalysisPage;
