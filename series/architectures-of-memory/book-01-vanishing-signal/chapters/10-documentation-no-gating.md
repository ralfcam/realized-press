# Chapter 10 — Documentation Without Gating: Knowledge Loss in Runaway Information Systems

*Sources: research note `research/notes/ch10-documentation-no-gating`; M. J. Eppler and J. Mengis (2004); L. J. Holtzblatt, L. E. Damianos, and D. Weiss (2010); W. S. Tan, M. Wagner, and C. Treude (2022, arXiv:2212.01479; 2023, *Empirical Software Engineering* 29(1)); Episteca (2025); J. Lave and E. Wenger (1991); E. Wenger (1998); E. Wenger, R. McDermott, and W. M. Snyder (2002); fact-checks ARC-30 and ARC-49.*

---

## The tragedy of the documentation commons

When organizations attempt to safeguard institutional memory by mandating comprehensive wiki updates, documentation without gating triggers the very knowledge loss it was designed to prevent. **Martin J. Eppler** and **Jeanne Mengis**, in an *Information Society* review that has become a standard reference, catalogue **causes of information overload** that cross disciplines—characteristics of the person, of the information itself, of tasks, of organizational process, and of **information technology** that *lower the cost of production* without a matching tax on *consumption*. The architectural point for institutions is (5): email, wikis, and intranets that make writing cheap can make *finding* *true* and *useful* **expensive**. Each author’s rational add becomes the commons’ irrational noise. In this environment, documentation without gating guarantees organizational knowledge loss because stale and active policies become indistinguishable.[^eppler2004]

A firm’s **knowledge base** is not “failed” the day it launches. It is failed the day nobody has **permission to forget**—or to govern what stays *valid*. The contrast with the last chapter is instructive. A reorg is a *sudden* substrate **loss**; a runaway wiki is a *slow* dilution of *relevance*—a recurrent state in which *everything* the firm ever said remains in the **corpus** unless someone **removes** it, while nothing in the system *automatically* downweights the stale.

---

## Technical lens — A recurrent state without a forget gate

A plain recurrent network *without* a gating path keeps one hidden **trajectory** through time: old activations and new input add in fixed roles; stale **context** and current **signal** can fight in the same **vector**. The LSTM family, which *Book* *2* takes up as *engineering* (*The* *Forget* *Gate*), was built to **choose** what to carry and what to **discard** (forget gate, input gate) because unbounded **accumulation** in time is not *neutral* for learning—it is a **structural** hazard.[^bridge]

An “open” enterprise wiki that **treats** every new page as *equally* authoritative in retrieval is, in the analogy, a state in which the text base only *grows*; the reader is left to guess what still **matters**. The mechanism the LSTM line discovered—a **trainable** choice about *how* much of the past to attenuate in each **dimension**—is what a curation-poor **knowledge management** platform does **not** implement in software, governance, or roles.

Gating is not a decoration. It is how you **bound** a memory when **inflow** is unpriced.

---

## Organizational lens — Decay, vendor numbers, and the tax on experts

What reads as “helpful” on launch can rot on a faster clock than most governance cycles touch. A 2025 industry blog (Episteca) attributes dramatic figures to Readme- and Zoomin-sourced data—**API**-**class** technical documentation *materially* stale on the order of **tens of days**, and large fractions of enterprise technical content not updated for half-year or year scales. As of 2026 the **original** vendor **reports** for those exact numbers are not independently **archived** in **forms** this book can **verify** (see research/fact-checks/ch10-residual). Treat the Episteca figures as *vendor-routed* **order of magnitude**, not a peer-reviewed experiment. A **citable** peer-reviewed result in the same **direction** is **Wen Siang Tan**, **Markus Wagner**, and **Christoph Treude** (2022/2023), who found outdated code-element references in **28.9%** of studied Google repositories and **5.4%** of the top-1,000 most popular GitHub projects currently (**82.3%** and **29.7%** historically).[^episteca2025][^tan2023]

**Lester J. Holtzblatt**, **Laurie E. Damianos**, and **Daniel Weiss** (MITRE) used **Contextual Inquiry** with 26 **participants** in an **extended** **abstract** at **CHI 2010** to map impediments to **internal** wiki use—a **qualitative** portrait of one large not-for-profit R&D **employer**, not a **statistical** law of all firms. The tension is as much **social** as **technical**: **reluctance** to **share** unfinished or **sensitive** work on open pages; **reliance** on familiar **non-wiki** channels—**governance** **deficits** (ownership, curation) more than a universal “people hate wikis” mood.[^holtzblatt2010]

Practitioner research in the DORA/Accelerate tradition—cited, in the Episteca-mediated chain this chapter uses for the documentation–onboarding link—gives a plausible **mechanism** for cost: if juniors cannot **trust** the **knowledge** **base**, they **revert** to **shadowing** seniors, **converting** expert time into **tour-guide** time and **bypassing** the transactive-memory routing **efficiency** Chapter 9 **described** (ask a sage **instead** of a search **box**).

---

## Philosophical lens — Communities of practice as *social* forget gates

The cure managers want to *buy* from a vendor may need to *grow* in **communities of practice (CoP)**. **Jean Lave** and **Etienne** **Wenger** (1991) are the **primary** source for the ethnographic **origin** of **situated** **learning** and “legitimate peripheral **participation**.” **E.** **Wenger**’s 1998 monograph is the primary for the *sociology-level* **framework** of communities of practice—mutual **engagement**, joint **enterprise**, shared **repertoire**; **E.** Wenger, **R.** **McDermott**, and **W.** **M.** **Snyder** (2002) is the primary for *cultivating* **communities** as an **organizational** **knowledge** **intervention**.[^lavewenger1991][^wenger1998][^wenger2002]

The three texts answer different questions; do not collapse them. A mature **CoP** **governs** its knowledge a little like a well-trained **forget** **gate**: people in daily **contact** with the **work** may **falsify** a **stale** page; **reputation** and **repeated** **use** supply **pressure** to **revise** or **remove**—a **selective** **editing** of the **corpus** that a read-only **repository** **cannot** do by metadata **alone**.

---

## The architectural gap to Book 2

What the **gated** RNN **family** did in **code** (*Book* *2*), vendors of “wiki as filing **cabinet**” **rarely** did in **product** **design** for **human** **curation** **incentives** and **roles**. A **knowledge** **base** is not a **theory** of **relevance**; an LSTM is a **theory** of **relevance** **under** a **loss** **function**. The **compliance** **extreme**—**“remember** **everything** in **the** **log**” without **assimilation**—waits in the **next** **chapter**: a **pathology** of a **different** **sign** than **vanishing** **gradients** **alone**.

---

## Notes

[^eppler2004]: M. J. Eppler and J. Mengis, “The Concept of Information Overload: A Review of Literature from Organization Science, Accounting, Marketing, MIS, and Related Disciplines,” *The Information Society* 20, no. 5 (2004): 325–344, https://doi.org/10.1080/01972240490507974. research/fact-checks/ch10.md (ARC-30).

[^bridge]: Long short-term memory: *Book 2 — The Forget Gate* (series bible); S. Hochreiter and J. Schmidhuber, “Long Short-Term Memory,” *Neural Computation* 9, no. 8 (1997): 1735–1780.

[^episteca2025]: Episteca, *The Documentation Decay Problem: Why Your Technical Docs Are Outdated*, Episteca.ai, 19 January 2025, https://episteca.ai/blog/documentation-decay/ — **vendor-secondary**; attributes numeric claims to Readme- and Zoomin-sourced data without publicly archived primary reports (research/fact-checks/ch10-residual.md, ARC-49).

[^tan2023]: W. S. Tan, M. Wagner, and C. Treude, “Detecting Outdated Code Element References in Software Repository Documentation,” *Empirical Software Engineering* 29, no. 1 (2023/2024), https://doi.org/10.1007/s10664-023-10397-6 (preprint arXiv:2212.01479, 2022; reports 28.9% of studied Google projects and 5.4% of top-1,000 GitHub projects with current outdated code-element references, and 82.3% / 29.7% historically—see research/fact-checks/ch10-residual.md, ARC-49).

[^holtzblatt2010]: L. J. Holtzblatt, L. E. Damianos, and D. Weiss, “Factors Impeding Wiki Use in the Enterprise: A Case Study,” in *CHI 2010 Extended Abstracts* (New York: ACM, 2010), 4661–4676, https://doi.org/10.1145/1753846.1754208 (n=26; qualitative, MITRE; non-generalizing claim). research/fact-checks/ch10.md (ARC-30).

[^lavewenger1991]: J. Lave and E. Wenger, *Situated Learning: Legitimate Peripheral Participation* (Cambridge: Cambridge University Press, 1991) — origin of the situated-learning/CoP line per fact-check mapping. research/fact-checks/ch10.md (ARC-30).

[^wenger1998]: E. Wenger, *Communities of Practice: Learning, Meaning, and Identity* (Cambridge: Cambridge University Press, 1998) — three-dimension model; theoretical elaboration. research/fact-checks/ch10.md (ARC-30).

[^wenger2002]: E. Wenger, R. McDermott, and W. M. Snyder, *Cultivating Communities of Practice* (Boston: Harvard Business School Press, 2002) — applied organizational cultivation of CoPs. research/fact-checks/ch10.md (ARC-30).
