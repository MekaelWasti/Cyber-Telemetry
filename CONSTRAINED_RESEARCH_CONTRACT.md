# Constrained Research Contract

**Status:** Active project-governance document  
**Adopted:** 2026-07-14  
**Applies to:** the researcher, collaborators, and AI assistants working in this repository

## 1. Purpose

This contract exists to prevent a sound research project from becoming an indefinitely expanding research program.

The project will remain rigorous, evidence-based, and informed by theory and the literature. Those qualities are **constraints on how the agreed work is performed**. They are not permission to continually enlarge the work whenever a new method, diagnostic, control, or theoretical possibility is discovered.

The governing principle is:

> Work inside a deliberately small box. Use research and theory to make the best decisions available inside that box. Do not expand the box merely because expansion could produce a more complete or interesting study.

The target is a complete, defensible project—not the most exhaustive project imaginable.

## 2. Authority and precedence

This document governs scope admission and execution behavior. `MASTER_PLAN.md` Version 2 is the locked active execution plan. Earlier expansive versions of the master plan, literature notes, and other planning documents remain research maps and future-work inventories; they do not make every described extension a current requirement.

When documents or recommendations conflict:

1. Explicit instructions from the project owner take precedence.
2. This constrained research contract determines what enters the active scope.
3. `MASTER_PLAN.md` Version 2 determines the current sequence of work.
4. Earlier plans, literature notes, and new suggestions inform decisions within that scope.
5. Unselected ideas go to a backlog; they do not silently become prerequisites.

Only the project owner may expand the active scope.

## 3. The box

### Time constraint

- **Execution target:** three weeks.
- **Hard maximum:** six weeks.
- The three-week plan is the default planning horizon. The remaining time is contingency, not space to add features.
- A task that threatens the three-week target must be simplified, substituted, deferred, or removed unless it is essential to validity.

### Deliverable constraint

The active project delivers:

1. One canonical session table and evaluation contract.
2. One raw-feature baseline.
3. The already-built session-similarity filter-bank baseline, closed as an exploratory result.
4. One label-free, semantically declared telemetry graph with a basic reliability and coverage audit.
5. Three graph representations:
   - typed structural statistics;
   - Node2Vec;
   - relational GraphSAGE.
6. One shared session-pooling, scoring, and metric interface used by every representation.
7. Essential controls only:
   - random ranking;
   - raw-feature baseline;
   - one appropriate degree-preserving graph rewire;
   - trained-versus-random-initialized control for GraphSAGE.
8. One frozen holdout evaluation.
9. A written account of the method, results, limitations, and future work.

Anything beyond this list is outside the active scope unless the project owner explicitly trades it for an existing item.

### Method constraint

- Prefer the simplest method that tests the stated hypothesis.
- Reuse the common pipeline rather than building method-specific evaluation machinery.
- Use a small, declared configuration instead of searches over large hyperparameter spaces.
- A method is allowed to produce a negative result. A weak result does not authorize an automatic rescue phase.
- Once a method satisfies its interface and validity checks, evaluate it, record it, and move forward.

## 4. Rigor without expansion

Rigor means that the claims actually made are supported. It does not mean testing every adjacent claim that could be made.

The minimum rigor standard is:

- session definitions and evaluation units are consistent across methods;
- scores are label-free and labels enter only during declared evaluation or diagnostics;
- comparisons use the same pooling, scorer, and metrics;
- graph construction rules are semantically explained and selected without label-driven repair;
- basic graph coverage and reliability are reported before graph results are interpreted;
- stochastic methods use declared seeds;
- the essential controls listed in this contract are run;
- development choices are frozen before holdout evaluation;
- limitations and uncertainty are stated honestly;
- code and artifacts are reproducible enough to support the reported result.

Rigor does **not** require, within the active scope:

- every possible null model;
- every representation diagnostic;
- exhaustive hyperparameter tuning;
- a full spectral or graph-signal atlas;
- every relation, hop, metapath, or architecture ablation;
- conditional amplification experiments;
- deletion-faithfulness or causal-path analysis;
- a second dataset;
- rescuing every method that underperforms.

These may be valuable future work. Their value does not make them current requirements.

## 5. Admission test for new work

Every proposed task, including suggestions from literature or an AI assistant, must be classified before work begins.

### A. Required now

A task is required now only if at least one of these is true:

1. Without it, a claim already planned would be invalid or materially misleading.
2. Without it, the shared pipeline cannot run or methods cannot be compared fairly.
3. It is explicitly part of the locked deliverables above.
4. It is necessary to produce the frozen holdout result or final write-up.

The reason must be stated concretely. “More rigorous,” “interesting,” “publishable,” or “could strengthen the result” is not sufficient.

### B. Substitution candidate

A new task may enter if it replaces an existing task of comparable or greater cost and better serves the same deliverable. The displaced task must be named explicitly.

### C. Deferred extension

Everything else goes into future work. It may be recorded in one sentence, but it must not interrupt active implementation.

If classification is uncertain, the default is **deferred extension**.

## 6. Satisficing and stop rules

The project uses declared “good enough” conditions instead of searching for an undefined best solution.

A pipeline component is done when:

1. Its input and output contract is explicit.
2. It runs on the canonical development data.
3. It returns exactly one aligned representation or score per canonical session, as applicable.
4. It passes the relevant label-isolation and alignment checks.
5. Its configuration and seed are recorded.
6. Its result and known limitation are recorded.

A method experiment stops when those conditions are met, even if:

- its score is disappointing;
- another diagnostic might explain the result more deeply;
- another parameter might improve it;
- another paper suggests a more sophisticated variant.

A failed validity check permits the smallest repair needed to restore validity. It does not authorize redesigning the whole method.

## 7. Change-control rule

No new active task is added without answering:

1. Which admission-test category does it meet?
2. What concrete claim or deliverable requires it?
3. How much time will it cost?
4. What will be removed or deferred to preserve the deadline?

Scope expansion without a corresponding deletion is prohibited by default.

Discovering new theory does not reopen completed design decisions unless it reveals a genuine validity defect. A preference for a more sophisticated approach is not a validity defect.

## 8. Rules for AI assistants and research feedback

When reviewing work in this repository, an AI assistant must:

- lead with whether the current result is usable for its declared purpose;
- distinguish errors from optional improvements;
- label every recommendation **required now**, **substitution**, or **future work**;
- recommend no more than the smallest set of required next actions;
- avoid turning an observed result into a new mandatory research branch;
- avoid adding a control merely because that control exists in the literature;
- preserve completed modules unless a concrete validity failure is identified;
- keep the user moving horizontally through the planned pipeline;
- treat the deadline and cognitive load as real methodological constraints.

An assistant must not use phrases such as “before you can move on” or “the next step should be” for optional work. Optional ideas belong in the backlog and require explicit project-owner approval before implementation.

When the user asks “is this done?”, the answer must be evaluated against this contract, not against the maximum possible rigor of an unlimited research program.

## 9. Constraint-first decision pattern

For each stage:

```text
state the fixed deliverable
→ state the time and interface constraints
→ consult theory and evidence relevant to that decision
→ consider at most three viable choices when a choice is genuinely needed
→ select the simplest defensible choice
→ record it
→ implement and validate it
→ stop and move horizontally
```

Research is used to choose well among bounded alternatives. It is not used to generate an unlimited menu.

## 10. Current execution sequence

The current sequence is locked as:

```text
close the existing filter-bank result
→ confirm canonical session alignment
→ build one telemetry graph
→ run the basic graph audit
→ typed structural statistics
→ Node2Vec
→ relational GraphSAGE
→ essential controls
→ freeze
→ holdout
→ write up
```

The session-similarity filter bank is closed once its existing implementation and results are recorded cleanly. Additional spectral diagnostics, blocked null families, and amplification experiments are deferred unless the project owner explicitly substitutes them for an active deliverable.

Node2Vec and GraphSAGE are not invitations to conduct architecture searches. Each receives one primary declared configuration plus only the control necessary for the intended claim.

## 11. Definition of project completion

The project is complete when the locked deliverables have run through the common evaluation pipeline, the method choices are frozen, holdout has been evaluated once, and the results and limitations are written clearly.

Completion does not require every method to win. A coherent negative result is a completed result.

## 12. Standing reminder

> Constraints are part of the research design. Finishing a smaller, coherent, reproducible study is more valuable than indefinitely approaching an exhaustive one.

When a new idea appears, preserve it without obeying it: place it in future work, return to the locked sequence, and finish the box.
