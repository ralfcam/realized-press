# Chapter 12 — Change Orders, Versioning, and the Architecture of Accountability

---

## I. The Serialized Change Order

In industrial work, physical systems do not evolve through silent replacement.

When an aircraft firm changes the metal in a turbine blade, the drawing is not just erased and redrawn. The change needs an Engineering Change Order, or ECO. This is a formal paper stating who authorized the change, what physical risks were weighed, which parts must be scrapped, and how serial numbers map to the new standard.

The change order keeps changes separate from erasing the past. It ensures that every present state of the machine carries an unbroken line of verified choices.

---

## II. Cryptographic Lineage and Lehman's Laws

Software teams learned this lesson through hard failures. Early tools treated code as mutable text files edited on shared disks. When two engineers saved the same file, the earlier work vanished without a trace.

Modern version control changed that model. In Git, history is never overwritten in place. Every commit is a fixed snapshot identified by a cryptographic hash. Modifying software means adding a new node to the graph.

Yet this append-only rule brings its own tension, mirroring state saturation in memory cells. If every small test, failed debugging probe, and accidental draft remains visible forever, navigation breaks down.

Lehman's laws of software evolution show that as a system evolves, its complexity grows steadily unless teams work to reduce it.[^lehman1980] A messy history full of dead tangents becomes hard for new hires to read.

---

## III. Gating Operations: The Squash and Rebase Discipline

Here again, the forget gate provides the design rule. The answer is not to destroy history, but to gate how it projects forward.[^git-gating]

In version control, this gating happens through squash and rebase steps before code merges to the main trunk. During local work, the engineer keeps high-detail logs: dozens of small commits tracking syntax fixes and experiments.

When merging into shared memory, the team squashes these small steps into one clear commit with an explicit message. The noise of scratch work is pruned, while the verified result enters the shared branch.

Accountability survives not by burying the team under every raw keystroke, but by preserving the clear link between intended design and verified outcome.

---

## IV. The Amorphous Overwrite Versus the Forensic Deluge

In regulatory compliance, failing to build gating rules creates two symmetric failures:

First is the amorphous overwrite. Teams edit live databases without version control, wiping out the historical record. When a failure happens, reconstructing past states becomes impossible.

Second is the forensic deluge. Companies dump every raw keystroke, chat message, and draft into an unindexed lake. When an audit occurs, critical choices are buried under mountains of digital noise. True accountability becomes too expensive to achieve.

Under FDA rules for clinical trials, regulators do not ask researchers to keep every scratch calculation.[^fda21cfr11] What the law requires is traceability: formal change amendments that state the rationale, timing, and statistical impact of every shift.

---

## V. Ricoeur and Ethical Selfhood in Systems

Philosophically, accountability connects to Paul Ricoeur's distinction between two kinds of identity: *idem* (physical sameness over time) and *ipse* (ethical selfhood kept through promises).[^ricoeur2004]

An institution does not stay itself by remaining physically identical. Staff rotate, software gets rewritten, and offices move.

Institutional identity lives in the ethical dimension: in the narrative integrity of its promises and the clarity of its change orders.

When an organization issues a change order, it makes an explicit promise to the future. It states why it shifted course, weighs the risks, and takes ownership of the results. The forget gate in an accountable system does not erase responsibility. It clears away noise so that responsibility remains legible.

<aside class="chapter-takeaway">
### Chapter 12 Takeaways: Architecture, Signal, and Retained Memory

- **The Technical Signal:** Append-only history creates state saturation; squashing and rebasing apply forget gates to prune scratch noise while preserving verified commits.
- **The Organizational Fallacy:** Believing that saving every keystroke creates accountability leads to a forensic deluge; true traceability requires structured change orders.
- **The Core Rule:** Accountability is not raw recording: it is the legible narrative of why a system altered its commitments over time.
</aside>

## Notes

[^lehman1980]: **Grade: High** for Lehman's laws of software evolution documenting monotonic complexity growth in continually modified software systems (Lehman 1980). M. M. Lehman, "Programs, Life Cycles, and Laws of Software Evolution," *Proceedings of the IEEE* 68, no. 9 (1980): 1060–1076, DOI: 10.1109/PROC.1980.11805.

[^fda21cfr11]: U.S. Food and Drug Administration, *Title 21, Code of Federal Regulations, Part 11: Electronic Records; Electronic Signatures*, Federal Register 62, no. 54 (1997): 13429–13466.

[^ricoeur2004]: **Historical Locus:** Paul Ricoeur, *Memory, History, Forgetting*, trans. K. Blamey and D. Pellauer (Chicago: University of Chicago Press, 2004).

[^git-gating]: **Squash and Rebase Operations as Gating:** In trunk-based development, intermediate exploratory commits are squashed via $\mathbf{C}_{\text{trunk}} = \mathbf{f}_{\text{squash}} \odot \mathbf{C}_{\text{scratch}} + \mathbf{i}_{\text{merge}} \odot \tilde{\mathbf{C}}_{\text{feature}}$, ensuring linear git history while preserving atomic auditability.
