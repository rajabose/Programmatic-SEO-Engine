# SpecKit Project Documentation

This directory contains the formal specifications for the Vanchai Programmatic SEO Engine using the SpecKit methodology.

## Quick Start

### Available Slash Commands

After running `specify init`, you can use these slash commands in your AI coding agent:

#### Core Commands
- `/speckit.constitution` - View or update project constitution
- `/speckit.specify` - Create or edit feature specifications
- `/speckit.plan` - Create implementation plans
- `/speckit.tasks` - Generate task breakdowns
- `/speckit.taskstoissues` - Convert tasks to GitHub issues
- `/speckit.implement` - Start implementation with AI assistance

#### Optional Commands
- `/speckit.clarify` - Clarify requirements
- `/speckit.analyze` - Analyze implementation
- `/speckit.checklist` - Review checklists

## Directory Structure

```
.specify/
├── README.md                    # This file
├── constitution/                # Project-level principles
│   └── project-constitution.md
├── specs/                       # Feature specifications
│   ├── content-generation-spec.md
│   ├── demand-validation-spec.md    # TODO: create
│   └── merchant-center-feed-spec.md # TODO: create
├── plans/                       # Implementation plans
│   └── content-generation-plan.md
├── tasks/                       # Specific tasks
│   └── TASK-CG-001-setup-project.md
└── templates/                   # Templates for new specs
    ├── constitution.md
    ├── spec.md
    ├── plan.md
    └── task.md
```

## Hierarchy Explained

### 1. Constitution (Project Level)
**Purpose**: Define the project's core vision, principles, and architecture

**File**: `constitution/project-constitution.md`

**Contains**:
- Project vision and goals
- Core principles and values
- High-level architecture
- Technical standards
- Success metrics
- Governance model

**When to update**: Rarely - only for major architectural changes

### 2. Spec (Feature Level)
**Purpose**: Define what features need to be built and why

**Files**: `specs/*.md`

**Naming Convention**: `{feature-name}-spec.md`

**Contains**:
- Feature overview and purpose
- User stories with acceptance criteria
- Technical specifications
- API definitions
- Data models
- Business logic workflows

**When to update**: As features evolve

### 3. Plan (Implementation Level)
**Purpose**: Define how to implement the feature

**Files**: `plans/*.md`

**Naming Convention**: `{feature-name}-plan.md`

**Contains**:
- Implementation phases
- Detailed task breakdown
- Technical architecture
- Dependencies and libraries
- Risk management
- Timeline and effort estimates

**When to update**: During sprint planning

### 4. Task (Action Level)
**Purpose**: Define specific, actionable work items

**Files**: `tasks/TASK-{FEATURE}-{XXX}-{description}.md`

**Naming Convention**: `TASK-{FEATURE}-{XXX}-{description}.md`

Where `{FEATURE}` is a short uppercase abbreviation of the feature name (e.g., `CG` for content-generation, `LP` for landing-page-generation). This prevents task ID collisions when multiple features generate tasks independently.

**Examples**:
- `TASK-CG-001-setup-project.md` (content-generation, task 1)
- `TASK-LP-001-setup-python-project.md` (landing-page-generation, task 1)

**Contains**:
- Specific task description
- Acceptance criteria
- Implementation details
- Testing steps
- Definition of done

**When to update**: Daily/As needed

## Workflow

### Starting a New Feature

1. **Create Spec**
   ```bash
   # Use the specify command or create manually
   # Copy template: cp .specify/templates/spec.md .specify/specs/my-feature-spec.md
   ```

2. **Create Plan**
   ```bash
   # Copy template: cp .specify/templates/plan.md .specify/plans/my-feature-plan.md
   ```

3. **Create Tasks**
   ```bash
   # Copy template: cp .specify/templates/task.md .specify/tasks/TASK-{FEATURE}-XXX-my-task.md
   ```

### Working on Tasks

1. **Before Starting**
   - Read the Task document
   - Check dependencies
   - Update task status to "In Progress"

2. **During Development**
   - Follow implementation steps
   - Write tests
   - Update task with notes

3. **After Completion**
   - Mark task as complete
   - Update plan progress
   - Create PR for review

## Branch Strategy

Each feature should have its own branch:

```
main
├── feature/content-generation
├── feature/seo-optimization
└── feature/template-management
```

## Best Practices

1. **Link Everything**
   - Tasks should reference Plans
   - Plans should reference Specs
   - Specs should reference Constitution

2. **Keep Updated**
   - Update specs when requirements change
   - Don't let specs become outdated

3. **Use Templates**
   - Follow the structure in existing files
   - Don't skip sections unless not applicable

4. **Document Decisions**
   - Why choices were made
   - Alternative approaches considered
   - Lessons learned

## Git Integration

### Commit Messages
Reference tasks in commit messages:
```
TASK-CG-001: Implement health check endpoint

- Add express server setup
- Configure middleware
- Create health check route
```

### Pull Requests
Link to relevant specs/plans/tasks:
```
## Related Documentation
- Spec: .specify/specs/content-generation-spec.md
- Plan: .specify/plans/content-generation-plan.md
- Task: .specify/tasks/TASK-CG-001-setup-project.md
```

## Getting Started

1. **Read the Constitution** first
2. **Study the Specs** for your feature
3. **Follow the Plans** for implementation
4. **Pick up Tasks** and start working

## Questions?

- **Architecture decisions** → Check Constitution
- **Feature requirements** → Check Spec
- **Implementation approach** → Check Plan
- **Specific work item** → Check Task

## Maintenance

**Owner**: Tech Lead  
**Review Cycle**: Monthly  
**Version**: 1.0.0
