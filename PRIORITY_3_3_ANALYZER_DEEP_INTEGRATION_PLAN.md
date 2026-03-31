# Priority 3.3: Analyzer Deep Integration

**Status**: Ready for Implementation
**Estimated Effort**: 2 hours
**Expected Result**: Enhanced code analysis endpoints with metrics, health scoring, and recommendations

---

## Overview

Deepen integration of socratic-analyzer library by adding comprehensive analysis endpoints that provide:
- Code complexity metrics
- Project health scoring
- Maintainability analysis
- Security issue categorization
- Performance improvement recommendations
- Architecture insights

---

## Current State

### Available in AnalyzerIntegration
- CodeAnalyzer - for quality analysis
- MetricsCalculator - for metrics
- InsightGenerator - for insights
- SecurityAnalyzer - for security issues
- PerformanceAnalyzer - for performance problems

### Current Endpoints
- POST /analysis/code - Code analysis (already using AnalyzerIntegration)
- Others delegate to orchestrator

### Missing Endpoints
- Code metrics and complexity analysis
- Project health scoring
- Security deep-dive
- Performance analysis with recommendations
- Architecture analysis

---

## Implementation Plan

### Phase 3.3.1: Enhance AnalyzerIntegration (30 min)

**File**: `backend/src/socrates_api/models_local.py`

**Add methods to AnalyzerIntegration**:

```python
def analyze_metrics(self, code: str, language: str = "python") -> Dict[str, Any]:
    """Calculate detailed code metrics"""
    if not self.available or not self.metrics:
        return {}

    try:
        metrics = self.metrics.calculate(code)
        return {
            "cyclomatic_complexity": metrics.get("cyclomatic_complexity", 0),
            "cognitive_complexity": metrics.get("cognitive_complexity", 0),
            "maintainability_index": metrics.get("maintainability_index", 0),
            "test_coverage": metrics.get("test_coverage", 0),
            "code_duplication": metrics.get("code_duplication", 0),
            "lines_of_code": metrics.get("lines_of_code", 0),
            "documentation_coverage": metrics.get("documentation_coverage", 0),
        }
    except Exception as e:
        logger.error(f"Failed to calculate metrics: {e}")
        return {}

def analyze_security(self, code: str, language: str = "python") -> Dict[str, Any]:
    """Deep security analysis"""
    if not self.available or not self.security:
        return {"issues": []}

    try:
        issues = self.security.find_issues(code)
        return {
            "critical_count": len([i for i in issues if i.get("severity") == "critical"]),
            "high_count": len([i for i in issues if i.get("severity") == "high"]),
            "medium_count": len([i for i in issues if i.get("severity") == "medium"]),
            "low_count": len([i for i in issues if i.get("severity") == "low"]),
            "issues": issues,
        }
    except Exception as e:
        logger.error(f"Failed to analyze security: {e}")
        return {"issues": []}

def analyze_performance(self, code: str, language: str = "python") -> Dict[str, Any]:
    """Analyze performance issues"""
    if not self.available or not self.performance:
        return {"issues": []}

    try:
        issues = self.performance.find_issues(code)
        recommendations = self.performance.get_recommendations(code)
        return {
            "issue_count": len(issues),
            "issues": issues,
            "recommendations": recommendations,
        }
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}")
        return {"issues": []}

def calculate_health_score(self, code: str, language: str = "python") -> Dict[str, Any]:
    """Calculate overall project health score"""
    if not self.available:
        return {"score": 0, "grade": "N/A"}

    try:
        metrics = self.analyze_metrics(code, language)
        security = self.analyze_security(code, language)
        performance = self.analyze_performance(code, language)

        # Calculate health score (0-100)
        score = 100
        score -= metrics.get("cyclomatic_complexity", 0) * 2  # Max -20
        score -= (100 - metrics.get("maintainability_index", 100)) * 0.3  # Max -30
        score -= security.get("critical_count", 0) * 10  # Max -50
        score -= security.get("high_count", 0) * 5  # Max -25
        score -= performance.get("issue_count", 0) * 2  # Max -20

        # Ensure score is 0-100
        score = max(0, min(100, score))

        # Grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": round(score, 1),
            "grade": grade,
            "metrics": metrics,
            "security_issues": security.get("critical_count", 0) + security.get("high_count", 0),
            "performance_issues": performance.get("issue_count", 0),
        }
    except Exception as e:
        logger.error(f"Failed to calculate health score: {e}")
        return {"score": 0, "grade": "N/A"}

def get_improvement_suggestions(self, code: str, language: str = "python") -> List[Dict[str, Any]]:
    """Get code improvement suggestions"""
    if not self.available or not self.insights:
        return []

    try:
        suggestions = self.insights.generate(code, language)
        return suggestions if suggestions else []
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}")
        return []
```

---

### Phase 3.3.2: Create Enhanced Analysis Endpoints (1.5 hours)

**File**: `backend/src/socrates_api/routers/analysis.py`

**Add 3 new endpoints**:

1. **POST /analysis/metrics** - Calculate code metrics
   - Parameters: code, language
   - Response: Complexity, maintainability, coverage, duplication

2. **POST /analysis/health** - Calculate project health score
   - Parameters: code, language
   - Response: Overall score (0-100), grade (A-F), breakdown

3. **POST /analysis/improvements** - Get improvement suggestions
   - Parameters: code, language
   - Response: Actionable improvement recommendations

**Implementation Examples**:

```python
@router.post(
    "/metrics",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate code metrics",
)
async def calculate_metrics(
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Calculate detailed code metrics.

    Analyzes code for complexity, maintainability, coverage, and duplication.

    Args:
        code: Source code to analyze
        language: Programming language

    Returns:
        APIResponse with detailed metrics
    """
    try:
        analyzer = AnalyzerIntegration()
        if not analyzer.available:
            raise HTTPException(status_code=503, detail="Analyzer not available")

        metrics = analyzer.analyze_metrics(code, language)

        return APIResponse(
            success=True,
            status="success",
            message="Code metrics calculated",
            data=metrics,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")

@router.post(
    "/health",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate project health score",
)
async def calculate_health_score(
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Calculate overall project health score.

    Combines metrics, security, and performance analysis into a health grade.

    Args:
        code: Project code to analyze
        language: Primary language

    Returns:
        APIResponse with health score (0-100) and grade (A-F)
    """
    try:
        analyzer = AnalyzerIntegration()
        if not analyzer.available:
            raise HTTPException(status_code=503, detail="Analyzer not available")

        health = analyzer.calculate_health_score(code, language)

        return APIResponse(
            success=True,
            status="success",
            message=f"Project health: {health.get('grade')} ({health.get('score')}/100)",
            data=health,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating health: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")

@router.post(
    "/improvements",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get improvement suggestions",
)
async def get_improvements(
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Get actionable code improvement suggestions.

    Analyzes code and provides specific recommendations for improvement.

    Args:
        code: Code to analyze
        language: Programming language

    Returns:
        APIResponse with improvement suggestions
    """
    try:
        analyzer = AnalyzerIntegration()
        if not analyzer.available:
            raise HTTPException(status_code=503, detail="Analyzer not available")

        suggestions = analyzer.get_improvement_suggestions(code, language)

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(suggestions)} improvement opportunities",
            data={"suggestions": suggestions, "count": len(suggestions)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting improvements: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")
```

---

## New Endpoints Summary

### Enhanced Analysis Endpoints (3 new)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /analysis/metrics | Code metrics (complexity, maintainability) |
| POST | /analysis/health | Project health score (A-F grade) |
| POST | /analysis/improvements | Improvement suggestions |

---

## Metrics Provided

### Complexity Metrics
- Cyclomatic Complexity - Branch complexity
- Cognitive Complexity - Mental complexity
- Lines of Code - Project size

### Quality Metrics
- Maintainability Index - 0-100
- Test Coverage - Percentage
- Code Duplication - Percentage

### Health Score
- Overall Score - 0-100
- Grade - A, B, C, D, F
- Breakdown by category

### Security Analysis
- Critical Issues - Count
- High Severity - Count
- Medium Severity - Count
- Low Severity - Count

### Performance Analysis
- Performance Issues - Count
- Recommendations - List
- Optimization opportunities

---

## Usage Examples

### Calculate Code Metrics
```bash
curl -X POST "http://localhost:8000/analysis/metrics" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def calculate(x, y):\n  return x + y",
    "language": "python"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "cyclomatic_complexity": 1,
    "cognitive_complexity": 0,
    "maintainability_index": 95,
    "test_coverage": 0,
    "code_duplication": 0,
    "lines_of_code": 2,
    "documentation_coverage": 50
  }
}
```

### Calculate Project Health
```bash
curl -X POST "http://localhost:8000/analysis/health" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "...", "language": "python"}'
```

Response:
```json
{
  "success": true,
  "message": "Project health: A (89.5/100)",
  "data": {
    "score": 89.5,
    "grade": "A",
    "metrics": {...},
    "security_issues": 1,
    "performance_issues": 0
  }
}
```

### Get Improvement Suggestions
```bash
curl -X POST "http://localhost:8000/analysis/improvements" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "...", "language": "python"}'
```

Response:
```json
{
  "success": true,
  "data": {
    "count": 3,
    "suggestions": [
      {
        "type": "refactoring",
        "title": "Extract method",
        "description": "Function is too long",
        "priority": "medium"
      },
      ...
    ]
  }
}
```

---

## Testing Strategy

### Unit Tests
```python
test_analyzer_integration_methods()
test_analyze_metrics()
test_analyze_security()
test_analyze_performance()
test_calculate_health_score()
test_get_improvement_suggestions()
```

### Integration Tests
```python
test_metrics_endpoint()
test_health_endpoint()
test_improvements_endpoint()
test_analyzer_with_different_languages()
```

### E2E Tests
```
1. Analyze code for metrics
2. Calculate health score
3. Get improvements
4. Verify scores are reasonable
5. Verify improvements are actionable
```

---

## Success Criteria

- [ ] AnalyzerIntegration enhanced with new methods
- [ ] 3 new endpoints created
- [ ] Health score calculation working
- [ ] Improvement suggestions generating
- [ ] Metrics calculations accurate
- [ ] All endpoints tested
- [ ] Graceful fallback if library unavailable

---

## Files to Modify

1. **backend/src/socrates_api/models_local.py** (modify)
   - Add methods to AnalyzerIntegration (~60 lines)

2. **backend/src/socrates_api/routers/analysis.py** (modify)
   - Add 3 new endpoints (~150 lines)

---

## Estimated Breakdown

| Task | Time |
|------|------|
| AnalyzerIntegration enhancements | 30 min |
| New endpoint implementation | 90 min |
| **Total** | **2 hours** |

---

**Ready to implement Priority 3.3: Analyzer Deep Integration**

This completes Phase 4 Library Integration!
