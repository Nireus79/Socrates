# Frontend Integration Guide - Analytics Metrics Updates

## Quick Reference: API Response Changes

### Before vs After

#### Phase Maturity Scores

**BEFORE:**
```json
{
  "phase_maturity_scores": {
    "discovery": 21.25,
    "analysis": 0,
    "design": 0,
    "implementation": 0
  }
}
```

**AFTER:**
```json
{
  "phase_maturity": {
    "scores": {
      "discovery": 21.25,
      "analysis": 0,
      "design": 0,
      "implementation": 0
    },
    "unit": "percentage",
    "labels": {
      "discovery": "21.25%",
      "analysis": "0.0%",
      "design": "0.0%",
      "implementation": "0.0%"
    }
  }
}
```

**Migration:**
```typescript
// Old way (❌ no longer works)
const score = response.phase_maturity_scores.discovery;

// New way (✅ correct)
const score = response.phase_maturity.scores.discovery;
const label = response.phase_maturity.labels.discovery; // "21.25%"
```

---

#### Completion Percentage

**BEFORE:**
```json
{
  "completion_percentage": 100.0
}
// ⚠️ Wrong! Shows 100% when only discovery is at 21.25%
```

**AFTER:**
```json
{
  "maturity_metrics": {
    "overall_project_completion": 5.3,
    "current_phase_maturity": 21.25,
    "unit": "percentage"
  }
}
// ✓ Correct! Shows 5.3% (average of all phases)
// ✓ Clear distinction between overall and current phase
```

**Migration:**
```typescript
// Old way (❌ incorrect data)
const completion = response.completion_percentage; // Was wrong

// New way (✓ accurate)
const overallCompletion = response.maturity_metrics.overall_project_completion; // 5.3%
const phaseMaturity = response.maturity_metrics.current_phase_maturity; // 21.25%
```

---

### New Fields Added

#### 1. Phase Readiness Status

```json
{
  "phase_readiness": {
    "discovery": {
      "phase": "discovery",
      "maturity_percentage": 21.25,
      "is_ready_to_advance": true,
      "ready_threshold": 20.0,
      "complete_threshold": 100.0,
      "is_complete": false,
      "status": "ready"
    },
    "analysis": {
      "phase": "analysis",
      "maturity_percentage": 0.0,
      "is_ready_to_advance": false,
      "ready_threshold": 20.0,
      "complete_threshold": 100.0,
      "is_complete": false,
      "status": "not_started"
    },
    // ... other phases
  }
}
```

**Usage in Frontend:**

```typescript
// Check if ready to advance
if (response.phase_readiness.discovery.is_ready_to_advance) {
  // Show "Next Phase" button
}

// Display phase status with colors
const status = response.phase_readiness.discovery.status;
// "not_started" → gray
// "in_progress" → yellow
// "ready" → green
// "complete" → blue

// Show maturity with threshold context
const phase = response.phase_readiness.discovery;
const progress = (phase.maturity_percentage / phase.complete_threshold) * 100;
// Shows 21.25% towards 100% goal
```

---

#### 2. Advancement Guidance

```json
{
  "advancement_guidance": {
    "current_phase": "discovery",
    "ready_to_advance": true,
    "next_action": "You're ready to advance to the next phase. Review findings and proceed to the next phase."
  }
}
```

**Usage in Frontend:**

```typescript
// Show guidance message
if (response.advancement_guidance.ready_to_advance) {
  showNotification(response.advancement_guidance.next_action);
  // → "You're ready to advance to the next phase..."
} else {
  showNotification(response.advancement_guidance.next_action);
  // → "Continue answering questions to increase phase maturity. Target: 20% to unlock advancement."
}

// Dynamically enable/disable phase navigation
const canAdvance = response.advancement_guidance.ready_to_advance;
```

---

#### 3. Updated Dashboard Response

**New `phase_breakdown` structure:**

```json
{
  "phase_breakdown": {
    "scores": {
      "discovery": 21.25,
      "analysis": 0.0,
      "design": 0.0,
      "implementation": 0.0
    },
    "labels": {
      "discovery": "21.25%",
      "analysis": "0.0%",
      "design": "0.0%",
      "implementation": "0.0%"
    },
    "readiness": {
      "discovery": { ... },
      "analysis": { ... },
      // All phase readiness info
    }
  },
  "advancement_guidance": {
    "current_phase": "discovery",
    "ready_to_advance": true,
    "next_steps": ["discovery"],  // Phases ready to advance to
    "recommendation": "Ready to advance! Current maturity is sufficient..."
  }
}
```

**Usage in Frontend:**

```typescript
// Get all phase info in one place
const phases = Object.entries(response.phase_breakdown.readiness).map(([key, data]) => ({
  name: key,
  maturity: data.maturity_percentage,
  label: response.phase_breakdown.labels[key],
  status: data.status,
  isReady: data.is_ready_to_advance,
}));

// Show phases with their readiness
phases.forEach(phase => {
  console.log(`${phase.name}: ${phase.label} - ${phase.status}`);
});
// Output:
// discovery: 21.25% - ready
// analysis: 0.0% - not_started
// design: 0.0% - not_started
// implementation: 0.0% - not_started
```

---

## Displaying Metrics in UI

### Phase Progress Cards

```typescript
function PhaseCard({ phase, readiness, label, maturity }) {
  const getStatusColor = (status) => {
    switch(status) {
      case 'complete': return 'blue';
      case 'ready': return 'green';
      case 'in_progress': return 'yellow';
      case 'not_started': return 'gray';
    }
  };

  return (
    <Card style={{ borderColor: getStatusColor(readiness.status) }}>
      <Title>{phase}</Title>
      <MetricRow>
        <Label>Maturity: {label}</Label>
        <ProgressBar value={readiness.maturity_percentage} max={100} />
      </MetricRow>
      <StatusBadge status={readiness.status} />
      {readiness.is_ready_to_advance && (
        <Button>Advance to Next Phase</Button>
      )}
      <ThresholdInfo>
        Threshold to advance: {readiness.ready_threshold}%
      </ThresholdInfo>
    </Card>
  );
}
```

### Overall Project Progress

```typescript
function ProjectProgress({ metrics }) {
  const { overall_project_completion, current_phase_maturity } = metrics.maturity_metrics;

  return (
    <ProgressSection>
      <Row>
        <Metric>
          <Label>Overall Project Completion</Label>
          <Value>{overall_project_completion}%</Value>
          <ProgressBar value={overall_project_completion} max={100} />
        </Metric>
      </Row>
      <Row>
        <Metric>
          <Label>Current Phase Maturity</Label>
          <Value>{current_phase_maturity}%</Value>
          <ProgressBar value={current_phase_maturity} max={100} />
        </Metric>
      </Row>
      <Unit>All values in {metrics.maturity_metrics.unit}</Unit>
    </ProgressSection>
  );
}
```

### Advancement Guidance Banner

```typescript
function AdvancementBanner({ guidance }) {
  return (
    <Banner variant={guidance.ready_to_advance ? "success" : "info"}>
      <Message>{guidance.next_action}</Message>
      {guidance.ready_to_advance && (
        <Button>
          Proceed to {getNextPhaseName(guidance.current_phase)}
        </Button>
      )}
    </Banner>
  );
}
```

---

## TypeScript Types

```typescript
interface PhaseMaturity {
  scores: Record<string, number>;
  unit: "percentage";
  labels: Record<string, string>;
}

interface MaturityMetrics {
  overall_project_completion: number;
  current_phase_maturity: number;
  unit: "percentage";
}

interface PhaseReadiness {
  phase: string;
  maturity_percentage: number;
  is_ready_to_advance: boolean;
  ready_threshold: number;
  complete_threshold: number;
  is_complete: boolean;
  status: "not_started" | "in_progress" | "ready" | "complete";
}

interface AdvancementGuidance {
  current_phase: string;
  ready_to_advance: boolean;
  next_action: string;
  next_steps?: string[]; // In dashboard response
  recommendation?: string; // In dashboard response
}

interface ProjectAnalyticsResponse {
  project_id: string;
  total_questions: number;
  average_response_time: number;
  phase_maturity: PhaseMaturity;
  maturity_metrics: MaturityMetrics;
  phase_readiness: Record<string, PhaseReadiness>;
  advancement_guidance: AdvancementGuidance;
  confidence_metrics: {
    average_confidence: number;
    strong_categories: string[];
    weak_categories: string[];
  };
  velocity: {
    value: number;
    unit: string;
    total_qa_sessions: number;
  };
}
```

---

## Testing the Changes

### Test Endpoints

```bash
# Get project analytics with new metrics
curl http://localhost:8000/analytics/projects/PROJECT_ID

# Get dashboard with readiness info
curl http://localhost:8000/analytics/dashboard/PROJECT_ID
```

### Expected Response Structure

```json
{
  "success": true,
  "status": "success",
  "message": "Analytics retrieved for project ...",
  "data": {
    "project_id": "...",
    "phase_maturity": {
      "scores": { ... },
      "unit": "percentage",
      "labels": { ... }
    },
    "maturity_metrics": {
      "overall_project_completion": 5.3,
      "current_phase_maturity": 21.25,
      "unit": "percentage"
    },
    "phase_readiness": { ... },
    "advancement_guidance": { ... }
  }
}
```

---

## Migration Checklist

- [ ] Update phase maturity score access: `phase_maturity.scores` instead of `phase_maturity_scores`
- [ ] Update completion display: use `overall_project_completion` instead of `completion_percentage`
- [ ] Add phase readiness status display using `phase_readiness`
- [ ] Add advancement guidance banner using `advancement_guidance`
- [ ] Update TypeScript types/interfaces
- [ ] Update unit tests for analytics components
- [ ] Test all phase states (not_started, in_progress, ready, complete)
- [ ] Verify percentage labels display with % symbol
- [ ] Test advancement button enable/disable logic
