# USER INTERFACE DESIGN
## Complete UI/UX Specifications and Mockups

---

## DESIGN SYSTEM OVERVIEW

### Color Palette

```
Primary Blue:        #2563eb (rgb(37, 99, 235))
Secondary Blue:      #1e40af (rgb(30, 64, 175))
Success Green:       #059669 (rgb(5, 150, 105))
Warning Amber:       #f59e0b (rgb(245, 158, 11))
Error Red:           #dc2626 (rgb(220, 38, 38))
Gray 50:             #f9fafb (rgb(249, 250, 251))
Gray 100:            #f3f4f6 (rgb(243, 244, 246))
Gray 200:            #e5e7eb (rgb(229, 231, 235))
Gray 500:            #6b7280 (rgb(107, 114, 128))
Gray 700:            #374151 (rgb(55, 65, 81))
Gray 900:            #111827 (rgb(17, 24, 39))
```

### Typography

```
Font Family:         Inter, -apple-system, BlinkMacSystemFont, "Segoe UI"
Heading 1:           32px, bold (2rem)
Heading 2:           24px, bold (1.5rem)
Heading 3:           20px, semibold (1.25rem)
Body:                16px, regular (1rem)
Small:               14px, regular (0.875rem)
Line Height:         1.5 (150%)
```

### Spacing Scale

```
0:    0
1:    0.25rem (4px)
2:    0.5rem (8px)
3:    0.75rem (12px)
4:    1rem (16px)
6:    1.5rem (24px)
8:    2rem (32px)
12:   3rem (48px)
16:   4rem (64px)
```

---

## PAGE LAYOUTS

### 1. Dashboard Page

**Purpose:** Overview of all projects, recent sessions, and system metrics

**Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    HEADER (with user menu)                      │
├────────────────────────────────────────────────────────────────┤
│  SIDEBAR │                                                      │
│          │  Dashboard                                           │
│          ├───────────────────────────────────────────────────┤
│          │  Welcome Message (if first time)                  │
│          │  ┌─────────────────────────────────────────────┐  │
│          │  │ Quick Stats (Metrics Cards)                 │  │
│          │  │ ┌──────────┬──────────┬──────────────────┐  │  │
│          │  │ │ Projects │ Sessions │ Messages (Total) │  │  │
│          │  │ │    5     │    12    │      247         │  │  │
│          │  │ └──────────┴──────────┴──────────────────┘  │  │
│          │  └─────────────────────────────────────────────┘  │
│          │                                                    │
│          │  ┌──────────────────┬──────────────────────────┐  │
│          │  │ Recent Projects  │ Recent Sessions        │  │
│          │  │ • Project 1      │ • Session A (2h ago)   │  │
│          │  │ • Project 2      │ • Session B (4h ago)   │  │
│          │  │ • Project 3      │ • Session C (1d ago)   │  │
│          │  └──────────────────┴──────────────────────────┘  │
│          │                                                    │
│          │  ┌──────────────────────────────────────────────┐  │
│          │  │ System Health                                │  │
│          │  │ • API: ✓ Healthy                            │  │
│          │  │ • Database: ✓ Healthy                       │  │
│          │  │ • Agents: 9/9 Ready                         │  │
│          │  └──────────────────────────────────────────────┘  │
│          │                                                    │
└────────────────────────────────────────────────────────────────┘
```

**Components:**

- Welcome card (shown on first visit)
- 3 metric cards (projects, sessions, messages)
- Recent projects list (5 items)
- Recent sessions list (5 items)
- System health status

**Key Features:**

- Live metric updates via WebSocket
- Quick action buttons (New Project, New Session)
- Filter/sort controls

---

### 2. Projects Page

**Purpose:** Browse, create, and manage all projects

**Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         PROJECTS                                │
├─────────────────────────────────────────────────────────────────┤
│  Filter: [All ▼] Sort: [Newest ▼] Search: [_______]             │
│  [+ New Project]                                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Project Card                                               │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │ Project Name                         Owner: John          │ │
│  │ Description: This is a project...                         │ │
│  │                                                            │ │
│  │ Phase: Design    Status: Active   Tech: React, Node      │ │
│  │ Created: 2025-10-18                                       │ │
│  │                                                            │ │
│  │ [View Sessions] [Edit] [Archive] [Delete]               │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ (More project cards...)                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Pagination: [< 1 2 3 ... >]  Showing 1-10 of 23 projects    │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**

- Filter/sort controls
- Search bar
- New project button
- Project cards (grid layout)
- Pagination controls

**Project Card Fields:**

- Project name and description
- Owner name
- Phase badge (with color coding)
- Status badge
- Tech stack tags
- Created date
- Action buttons (View, Edit, Archive, Delete)

---

### 3. Sessions Page

**Purpose:** Manage sessions within a project and conduct interactions

**Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Project: My API Project      Phase: Development     [Back]     │
├─────────────────────────┬───────────────────────────────────────┤
│  Sessions (5)           │  Session Chat                         │
│  ┌───────────────────┐  │  ┌─────────────────────────────────┐ │
│  │ Session 1         │  │  │  Socratic: Design Patterns      │ │
│  │ Type: Socratic    │◄─│─ │  (Selected)                      │ │
│  │ 2 days ago       │  │  │                                   │ │
│  └───────────────────┘  │  │  Messages:                       │ │
│  ┌───────────────────┐  │  │  ┌─────────────────────────────┐ │
│  │ Session 2         │  │  │  │ User: What patterns should │ │
│  │ Type: Chat        │  │  │  │ I use?                      │ │
│  │ 1 day ago       │  │  │  │                               │ │
│  └───────────────────┘  │  │  Socratic: Good question!     │ │
│  ┌───────────────────┐  │  │  Consider...                  │ │
│  │ Session 3         │  │  │                               │ │
│  │ Type: Code Review │  │  │  [Messages scroll...]         │ │
│  │ 5 hours ago      │  │  │                               │ │
│  └───────────────────┘  │  │ Message Input:                │ │
│  [+ New Session]        │  │ ┌─────────────────────────────┐ │
│  [Archive Selected]     │  │ │ Type your message...        │ │
│  [Delete Selected]      │  │ └─────────────────────────────┘ │
│                         │  │ [Send] [Save] [Export]          │ │
│                         │  └─────────────────────────────────┘ │
└─────────────────────────┴───────────────────────────────────────┘
```

**Components:**

- Sessions list (left sidebar)
  - Session type badge
  - Created date
  - Selection/focus state
- Chat interface (main area)
  - Message history (scrollable)
  - Message bubbles (user vs agent)
  - Message input field
  - Send button
  - Session controls (Save, Export, etc.)

**Session Types:**

- Socratic (blue): Question-based learning
- Chat (green): Conversational
- Code Review (orange): Code analysis

---

### 4. Code Editor Page

**Purpose:** Edit, refactor, and debug code with AI assistance

**Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Code Editor                                    [← Back]         │
├─────────────────────────────────────────────────────────────────┤
│  File: app.py              [Open File] [Save] [Export]          │
├────────────────────────────────────┬────────────────────────────┤
│  Code Editor                       │  AI Assistant              │
│  1   import flask                  │  ┌──────────────────────┐  │
│  2   from flask import render_t... │  │ Suggestions:         │  │
│  3                                 │  │ • Add error handling  │  │
│  4   app = Flask(__name__)         │  │ • Use logging module  │  │
│  5   app.config['DEBUG'] = True    │  │ • Type hints          │  │
│  6                                 │  │                      │  │
│  7   @app.route('/api')            │  │ [Refactor] [Fix] [D] │  │
│  8   def api():                    │  │                      │  │
│  9       return {'status': 'ok'}   │  │ Quality Score: 7/10  │  │
│  10                                │  │ Confidence: 85%      │  │
│  11  if __name__ == '__main__':    │  │                      │  │
│  12      app.run()                 │  │ Apply Suggestion ▼   │  │
│                                    │  └──────────────────────┘  │
│  [Line 1]                          │                            │
│  Find:     [________] Replace: [_] │  Instructions Panel        │
│  [Next] [Previous] [Replace] [All] │  ┌──────────────────────┐  │
│                                    │  │ Active Rules:        │  │
│                                    │  │ ✓ Include tests      │  │
│                                    │  │ ✓ No hardcoded vals  │  │
│                                    │  │ ✓ Document changes   │  │
│                                    │  └──────────────────────┘  │
└────────────────────────────────────┴────────────────────────────┘
```

**Components:**

- Code editor (left side)
  - Line numbers
  - Syntax highlighting
  - Find/replace
- AI Assistant panel (right side)
  - Suggestions list
  - Quality score
  - Action buttons
- Instructions panel
  - Active rules display
  - Compliance indicators

**Features:**

- Syntax highlighting (multiple languages)
- Real-time code quality feedback
- AI suggestions for improvements
- Diff view before applying changes
- Undo/Redo support

---

### 5. Settings Page

**Purpose:** Manage user preferences, IDE integration, and AI instructions

**Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings                                        [Search: ____] │
├───────────────────────────┬───────────────────────────────────┤
│  Settings Menu            │  Settings Content                 │
│  ┌──────────────────────┐ │  ┌─────────────────────────────┐ │
│  │ Profile              │ │  │ Profile Settings            │ │
│  │ IDE Configuration    │ │  │ ┌──────────────────────────┐ │ │
│  │ System Configuration │ │  │ First Name: [John ___]      │ │ │
│  │ AI Instructions      │◄┼──│ Last Name:  [Doe  ___]      │ │ │
│  │ Notifications        │ │  │ Email: john@example.com      │ │ │
│  │ About                │ │  │                              │ │ │
│  └──────────────────────┘ │  │ [Save] [Cancel] [Reset]     │ │ │
│                           │  └──────────────────────────────┘ │ │
│                           │                                    │ │
│                           │  IDE Integration                   │ │
│                           │  ┌──────────────────────────────┐ │ │
│                           │  │ IDE Type: [VSCode ▼]         │ │ │
│                           │  │ Path: [C:\Users\...\Code]    │ │ │
│                           │  │ ☑ Auto-sync enabled          │ │ │
│                           │  │ ☑ Real-time updates          │ │ │
│                           │  │                              │ │ │
│                           │  │ [Test Connection]            │ │ │
│                           │  └──────────────────────────────┘ │ │
│                           │                                    │ │
│                           │  [Save Changes]                    │ │
│                           └─────────────────────────────────┘ │
└───────────────────────────┴───────────────────────────────────┘
```

**Tabs:**

1. **Profile** - User information
2. **IDE Configuration** - IDE path, auto-sync options
3. **System Configuration** - Theme, language, logging level
4. **AI Instructions** - User-defined behavior rules (CRITICAL)
5. **Notifications** - Email/push preferences
6. **About** - Version info, documentation links

**AI Instructions Tab Details:**

```
┌────────────────────────────────────────┐
│ Your AI Instructions                   │
│                                        │
│ These rules guide all AI operations    │
│ within Socrates.                       │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Instructions Text Area             │ │
│ │ (Enter one rule per line, start    │ │
│ │  with -)                           │ │
│ │                                    │ │
│ │ - Always include tests             │ │
│ │ - Use TypeScript for frontend      │ │
│ │ - Document breaking changes        │ │
│ │ - Prioritize security              │ │
│ │ - Maintain backward compatibility  │ │
│ │                                    │ │
│ │ [Clear] [Load Template]            │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Recent Instructions:                   │
│ ┌────────────────────────────────────┐ │
│ │ • Version: 2025-10-18 (Current)    │ │
│ │ • Version: 2025-10-17 (Restore)    │ │
│ │ • Version: 2025-10-16 (Restore)    │ │
│ └────────────────────────────────────┘ │
│                                        │
│ [Save Instructions] [Cancel]           │
└────────────────────────────────────────┘
```

---

## COMMON COMPONENTS

### 1. Button Component

**Types:**

```
Primary:   [Primary Action]    (Blue background)
Secondary: [Secondary Action]  (Gray background)
Success:   [Success Action]    (Green background)
Danger:    [Delete Action]     (Red background)
Ghost:     [Ghost Action]      (Transparent)
Disabled:  [Disabled Action]   (Grayed out)
Loading:   [Saving...] ⟳       (With spinner)
```

**Sizes:**

```
Small:    12px font, 6px padding
Medium:   14px font, 8px padding (default)
Large:    16px font, 12px padding
```

### 2. Input Fields

```
Text Input:
┌─────────────────────────────┐
│ Label (optional)            │
│ ┌──────────────────────────┐│
│ │ Placeholder text...      ││
│ └──────────────────────────┘│
│ Helper text (optional)      │
└─────────────────────────────┘

Select Dropdown:
┌─────────────────────────────┐
│ Label (optional)            │
│ ┌──────────────────────────┐│
│ │ Option 1           [▼]   ││
│ └──────────────────────────┘│
│ ┌──────────────────────────┐│ (when open)
│ │ Option 1               ✓ ││
│ │ Option 2                 ││
│ │ Option 3                 ││
│ └──────────────────────────┘│
└─────────────────────────────┘

Textarea:
┌─────────────────────────────┐
│ Label (optional)            │
│ ┌──────────────────────────┐│
│ │ Multiple lines of text  ││
│ │ can go here...          ││
│ │                         ││
│ │ (Character count: 45)   ││
│ └──────────────────────────┘│
└─────────────────────────────┘
```

### 3. Cards

```
Standard Card:
┌──────────────────────────────┐
│ Card Title                   │
├──────────────────────────────┤
│ Card content goes here       │
│                              │
│ More content                 │
│                              │
│ [Action Button] [Secondary]  │
└──────────────────────────────┘

Metric Card:
┌──────────────────┐
│ Total Projects   │
│      23          │ (Large number)
│ ↑ 2 this week    │ (Trend indicator)
└──────────────────┘
```

### 4. Modals

```
┌────────────────────────────────────┐
│  Confirm Action              [✕]   │
├────────────────────────────────────┤
│ Are you sure you want to delete    │
│ this project? This action cannot   │
│ be undone.                         │
│                                    │
│ [Cancel]  [Delete] (danger color) │
└────────────────────────────────────┘
```

### 5. Message Bubbles

```
User Message:
                                  ┌──────────────┐
                                  │ User message │
                                  │ goes here    │
                                  └──────────────┘

Agent Message:
┌──────────────────────────────┐
│ Agent Response Name          │
│ Agent message goes here      │
│ with optional formatting     │
└──────────────────────────────┘
```

### 6. Badges

```
Status Badges:
[Active]     [Inactive]    [Archived]
(Green)      (Gray)        (Red)

Phase Badges:
[Planning] [Design] [Development] [Testing] [Deployment]

Type Badges:
[Socratic] [Chat] [Code Review]
```

---

## RESPONSIVE DESIGN

### Breakpoints

```
Mobile:     < 640px   (sm)
Tablet:     640-1024px (md)
Desktop:    1024px+   (lg)
```

### Mobile Adaptations

- Sidebar collapses to hamburger menu
- Code editor single pane (tab between code/AI)
- Cards stack vertically
- Reduce padding/spacing
- Larger touch targets (min 44px)

---

## ACCESSIBILITY (WCAG 2.1)

### Key Principles

- Sufficient color contrast (4.5:1 for body text)
- Keyboard navigation support
- Screen reader friendly
- Focus indicators visible
- Alt text for images
- Form labels associated with inputs

### Implementation

```typescript
// Example accessible button
<button
  aria-label="Create new project"
  aria-pressed={isActive}
  className="focus:outline-none focus:ring-2 focus:ring-blue-500"
>
  + New Project
</button>
```

---

## NEXT STEPS

1. Create all page layouts in Figma
2. Design component library
3. Implement in React with Tailwind
4. User testing and feedback
5. Iterate on design

**Proceed to 08_STATE_MANAGEMENT.md** for Redux setup details
