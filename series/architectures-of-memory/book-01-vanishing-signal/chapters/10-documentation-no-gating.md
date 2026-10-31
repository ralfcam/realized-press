# Chapter 10 — Documentation Without Gating: Knowledge Loss in Runaway Information Systems

---

## I. The Tragedy of the Documentation Commons

When companies try to save team memory by mandating endless wiki pages, documentation without gating triggers the exact memory loss it tried to prevent. Martin J. Eppler and Jeanne Mengis surveyed the causes of information overload across modern business.[^eppler2004] They pointed out a basic paradox: tools like email, wikis, and chats make writing cheap, but they create no balance on how people read.

When writing is cheap, finding what is true becomes costly. Each author makes a fair choice to add one more page to the wiki. Yet the joint result is overwhelming noise. Documentation without gating guarantees that teams lose track of real knowledge, because old drafts and active rules blur together.

A company wiki does not fail on day one. It fails on the day nobody has permission to delete old text, or to prune what is stale. A reorg causes sudden loss; a runaway wiki causes slow dilution. The wiki acts like a network that keeps every past word in its state vector, with no way to forget.

---

## II. A Recurrent State Without a Forget Gate

A basic recurrent net without gates keeps one hidden path through time. Old states and new inputs add together in fixed ways. Stale facts and fresh signals fight for space in the same vector.

The Long Short-Term Memory (LSTM) model, studied in Book 2 (*The Forget Gate*), was built to stop this pile-up.[^bridge] It added input and forget gates. These gave the network a trained way to pick what to keep and what to drop. Packing the past without bounds is not neutral; it is a structural trap.

An open wiki that treats every page as equally true acts like an ungated net. The text pile only grows, leaving the reader to guess what still holds weight. The core insight behind the LSTM—a learned choice about how much of the past to drop—is what open wikis fail to build.

Gating is not an extra perk. It is the only way a system can keep a clear signal when new text is free.

---

## III. Documentation Decay and the Tax on Experts

What looks helpful at launch rots fast. Software research shows how quickly code guides decay. Wen Siang Tan, Markus Wagner, and Christoph Treude studied code references across large projects.[^tan2023] They found broken documentation links in 28.9% of studied Google codebases and 5.4% of top GitHub projects, with historical rates reaching 82.3% and 29.7%.

In a study of wiki use at MITRE, Lester J. Holtzblatt, Laurie E. Damianos, and Daniel Weiss mapped the social walls to internal writing.[^holtzblatt2010] Engineers feared sharing half-done work, worried about leaks, and returned to old habits. The breakdown came from weak curation and poor ownership, not from simple laziness.

When junior staff find they cannot trust the wiki, they stop reading it. Instead, they book time with senior staff to ask basic questions. This turns high-value engineering time into repetitive tour-guide time. The firm skips its costly wiki tools and falls back on asking around.

---

## IV. Communities of Practice as Social Forget Gates

The fix that leaders try to buy as software must grow inside real peer groups. Jean Lave and Etienne Wenger laid the groundwork for situated learning.[^lavewenger1991] Wenger later showed how communities of practice hold shared craft, daily ties, and common habits.[^wenger1998] Along with Richard McDermott and William M. Snyder, he outlined ways to build these peer groups inside firms.[^wenger2002]

A strong community acts as a social forget gate. Staff in daily contact with the work easily spot and fix bad rules. Daily trust and shared pride create real pressure to update or delete old pages. This living review does what static wikis cannot: it keeps written notes in step with real work.

---

## V. Memory as Active Selection

What gated nets did in code, tool makers rarely built into corporate wikis. A static wiki is just a drawer. An LSTM is an active theory of what matters under a real loss score.

In the next chapter, we look at the legal extreme: what happens when compliance rules force a firm to save every log and email forever, creating paper trails without true memory.

<aside class="chapter-takeaway">
### Chapter 10 Takeaways: Architecture, Signal, and Retained Memory

- **The Technical Signal:** Simple recurrent networks accumulate past inputs without an attenuation mechanism, allowing stale context to interfere with current processing. The LSTM solved this by introducing an explicit forget gate: a trainable sigmoid layer that selectively discards irrelevant historical state.
- **The Organizational Fallacy:** Organizations treat internal wikis as infinite storage bins, believing that more written documentation equals better institutional memory. When writing is cheap but curation is unrewarded, the knowledge base becomes an unsearchable swamp of stale facts.
- **The Core Rule:** Memory requires active forgetting. A documentation system without a forget gate forces junior engineers to bypass search and rely on senior colleagues, converting expert time into tour-guide time.
</aside>

## Notes

[^eppler2004]: M. J. Eppler and J. Mengis, “The Concept of Information Overload: A Review of Literature from Organization Science, Accounting, Marketing, MIS, and Related Disciplines,” *The Information Society* 20, no. 5 (2004): 325–344.

[^bridge]: S. Hochreiter and J. Schmidhuber, “Long Short-Term Memory,” *Neural Computation* 9, no. 8 (1997): 1735–1780.

[^tan2023]: W. S. Tan, M. Wagner, and C. Treude, “Detecting Outdated Code Element References in Software Repository Documentation,” *Empirical Software Engineering* 29, no. 1 (2024): article 10397.

[^holtzblatt2010]: L. J. Holtzblatt, L. E. Damianos, and D. Weiss, “Factors Impeding Wiki Use in the Enterprise: A Case Study,” in *CHI 2010 Extended Abstracts* (ACM, 2010): 4661–4676.

[^lavewenger1991]: J. Lave and E. Wenger, *Situated Learning: Legitimate Peripheral Participation* (Cambridge University Press, 1991).

[^wenger1998]: E. Wenger, *Communities of Practice: Learning, Meaning, and Identity* (Cambridge University Press, 1998).

[^wenger2002]: E. Wenger, R. McDermott, and W. M. Snyder, *Cultivating Communities of Practice* (Harvard Business School Press, 2002).
