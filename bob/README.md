# IBM Bob Workflow

This folder documents how IBM Bob is used as the engineering copilot for SafetySentinel.

## Bob modes
- **Plan mode:** ask Bob to inspect the P2 requirements and propose an implementation plan before editing.
- **Agent mode:** ask Bob to implement the plan and run the application/tests.
- **Ask mode:** ask questions about the codebase without requesting edits.
- **Review:** ask Bob to review the implementation against the P2 requirements and the submission checklist.

## Recommended first prompt
> You are the lead engineer for this IBM Bob hackathon project. Read the repository, especially submission.yaml, docs/problem-statement.md, docs/solution-overview.md and docs/setup-guide.md. Do not rewrite the problem statement. First create a concrete implementation plan for P2 with two modes: PRR-based safety signal detection and ICH M4-inspired CTD readiness checking. Identify risks, tests, and demo steps. Do not modify files until I approve the plan.

## After approval
> Implement the approved plan. Keep all source code under src/. Preserve the required top-level template structure. Use deterministic, inspectable calculations. Add tests where useful. Run the app or tests and report exactly what passed and what remains.

## Review prompt
> Review this repository against P2 and the hackathon submission guide. Check that both workflows actually work, that PRR inputs are transparent, that CTD gaps are explainable, that no credentials are committed, and that the setup guide works from a fresh terminal. Do not claim a feature exists unless you can verify it in source code.

## Important
The app does not call a fictional "Bob API." Bob is the engineering agent used to plan, implement, test and review the actual repository. This keeps the prototype reproducible and avoids inventing an unsupported IBM API integration.
