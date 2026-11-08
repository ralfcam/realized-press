# Chapter 3: Federated Learning — Decentralized Training and the Geometry of Aggregation

In millions of pockets across the globe, mobile phones rest on nightstands. They charge on home wireless networks during the quiet hours before dawn. Inside each phone, a local client wakes up.

It reviews words typed and voice notes recorded over the previous day. Yet it does not upload a single private message to a cloud server. Instead, it computes a small mathematical update directly on the device. It discards the raw text right away. Then it sends only an encrypted numerical update back to the main server.

This shift marks a major change in computer architecture. For years, machine learning followed a simple rule: collect all data into a central lake. Companies gathered billions of photos, emails, and search queries onto central storage drives. But centralized data lakes became prime targets for hackers and state surveillance. Gathering all personal memory in one place created an unacceptable liability. To protect privacy, engineering had to invert the flow: move the computation to the data, rather than moving the data to the machine.

## I. The Midnight Network of Pockets

The mobile fleet acts as a vast distributed computer. Each phone trains a local copy of a next-word model on its owner's habits.

This local training respects physical boundaries. A hospital system can train diagnostic tools across five clinical sites without sharing patient files. A bank can improve fraud detection across international branches without violating cross-border data transfer laws. The raw records stay where they were born.

## II. The Architecture of Local Intelligence

Centralizing raw data creates severe security and regulatory risks. Under modern privacy laws, storing user communications on central servers requires explicit consent and costly protection.

Decentralized training swaps raw data hoarding for clean math. Instead of acting as a dragnet vault, the central server sends a base model out to thousands of phones. Each phone trains on its own local text for a few steps, then ships back only the weight shifts so the server can merge them into a sharper global model.

## III. Federated Averaging and Secure Aggregation

Coordinating updates from millions of unreliable devices required a new mathematical framework.

Empirical work by Brendan McMahan and his team shows that federated averaging trains deep nets across remote devices in far fewer sync rounds.[^mcmahan2017] Merging weight updates locally shields user privacy because raw text never leaves the phone. Even when devices drop offline or run on slow links, the shared model still converges.

## IV. The Geometry of Decentralized Memory

Decentralized training introduces unique systems challenges. First, user data is non-identical. One person writes business emails, while another writes teenage slang. The global model must synthesize these diverse streams without erasing minority patterns.

Second, raw weight updates can still leak secrets when attackers invert gradients. If a snoop inspects a single phone's weight shift, math tricks can rebuild the private text that caused it. To block that leak, engineers pair federated runs with secure sums and noise so the server sees only the crowd total, never one person's step.

<aside class="chapter-takeaway">
<header>Chapter Takeaway: Decentralized Memory</header>
Centralizing sensitive user data creates an unacceptable privacy and security liability. Federated learning inverts the architecture: computation moves to edge devices, while raw data never leaves the user. Decentralized memory learns global patterns while leaving personal records isolated at the perimeter.
</aside>

Dawn breaks over the coast. Phone screens light up as morning alarms sound. In a remote datacenter, the global model updates its weights from the combined signals of ten million phones. Not a single private message was saved to corporate disk. The central system learned the common language. Meanwhile, the personal secrets of every private life remained safe on the devices where they belong.

## Notes

[^mcmahan2017]: H. Brendan McMahan, Eider Moore, Daniel Ramage, Seth Hampson, and Blaise Agüera y Arcas, "Communication-Efficient Learning of Deep Networks from Decentralized Data," in *Proceedings of the 20th International Conference on Artificial Intelligence and Statistics (AISTATS 2017)*, Proceedings of Machine Learning Research 54 (PMLR, 2017), 1273–1282, https://doi.org/10.48550/arXiv.1602.05629.
