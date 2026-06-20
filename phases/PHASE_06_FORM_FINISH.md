# Phase 06 — Form & Finish

## Objective

Take the validated-but-boxy body from massing fidelity to a screen-accurate, cohesive Johnny 5 form, then give the fully assembled robot a holistic finish review. Form only — no functional, electrical, or firmware changes. All work stays inside the envelopes the earlier phases froze.

---

## Gate Condition

**Whole-robot form & finish review complete and signed off.**

Every subassembly's cosmetic geometry is finalized in the parametric FreeCAD source, re-exported, and reprinted where changed; the assembled robot reads as Number 5 from the canonical front, side, and back views. Approved means Andrew has reviewed the assembled robot against reference and accepted it.

---

## Context

Phases 00–05 deliberately decentralize *functional* geometry refinement: each subassembly firms up as its real hardware lands, with Phase 05 the final fit and hardening pass. That keeps the structure honest but leaves the body at "validated massing" fidelity — correct sizes, mounts, and clearances, with boxy surfaces standing in for screen-accurate form.

The governing principle is **detail follows fit**: the parametric scaffold makes structural resizing cheap, but screen-accurate surfacing is the expensive-to-redo work, so it is held until the boxes stop moving — which is the end of Phase 05. Individual subassemblies may pick up some cosmetic attention earlier; this phase completes that work and, critically, unifies it. A part that looks right in isolation still has to cohere with its neighbors on the assembled robot, and that whole-robot read is the reason this exists as its own final phase rather than a footnote to hardening.

The working surface is unchanged: `params.csv` → `build_*.py` → STL. Form changes are made by adding detail to the build scripts and tuning parameters, re-running, and re-exporting — the same loop used to baseline the body, now aimed at appearance rather than fit.

---

## Tasks

### 1. Reference lock & gap analysis

Put the canonical front, side, and back reference set beside the current renders and catalog the specific divergences between massing and film form, per subassembly — surface paneling, proportions, and signature features (boombox torso face, neck bellows and twin shocks, track-pod shaping, head greebles, antenna). Prioritize by visual impact.

### 2. Per-subassembly form detailing

Working up the stack, take each subassembly from massing to screen-accurate form within its frozen functional envelope: chassis and track pods, torso (control-panel face, shoulder bar), neck (bellows, cosmetic shocks), head (lens housings, brow blades, bridge), arms. Add surface detail, fillets and chamfers, panel lines, and cosmetic greebles. Track cosmetic mass against the 1.6 kg ceiling.

### 3. Whole-robot cohesion review

Assemble all finalized parts — digitally and physically — and review the complete robot against reference from every canonical angle. Resolve cross-subassembly mismatches that only surface when assembled: seam alignment, finish breaks, proportion reads. This is the holistic pass.

### 4. Surface finish & color

Define and apply the finish scheme: print orientation for surface quality, post-processing (sanding, filler, primer on show surfaces), and the Johnny 5 color convention. Promote cosmetic show-parts to the appropriate material or finish.

### 5. Final documentation

Update the parametric source and STL set to the finalized geometry, tag the release (`v6.0`), and capture the final render set and a build/finish guide so the form is reproducible.

---

## Dependencies & Sequencing

Starts after Phase 05. Functional geometry must be frozen first — cosmetic work on a moving envelope is wasted effort. Cosmetic mass is the one new budget pressure; keep it inside the weight ceiling. No electrical or firmware change originates in this phase.

---

## Open Questions for This Phase

- Fidelity target: clean stylized homage, or screen-replica greeble density? This sets the scope.
- Finish: bare printed PLA/PETG, painted, or hybrid? This influences material choices made as early as Phase 00 reprints.
- Are any cosmetic features worth promoting to functional later — the neck bellows as a real compliant element, or the waist lean from the V2 lever?

---

## Recommended Session Start

Begin with Task 1: put the current renders next to the reference set and build the prioritized divergence list before touching any geometry.
