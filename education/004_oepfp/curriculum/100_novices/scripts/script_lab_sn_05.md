# Video Storyboard: Lab SN.05: S(n) Applications: Distributed Protocols & Linear Capabilities

AuthorityEffect: None.

**Target Duration:** `140s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | Dual channel communication diagram showing !T and ?T matching. | "In distributed systems, session types enforce algebraic duality between sender and receiver, preventing deadlocks statically." | `[Declared]` |
| **02** | `0:30 - 1:00` | Execution of verify_session_pair matching client orders with server receipts. | "When client sends order and waits for receipt, the server must receive order and send receipt. Mismatches trigger immediate deadlock detection." | `[Executed]` |
| **03** | `1:00 - 1:20` | Linear capability account: second transfer attempt blocked with ERR_DOUBLE_SPEND_REFUSED. | "Linear tokens cannot be copied or discarded silently. Once transferred, a capability is spent, preventing double-spending at compile time." | `[Tested]` |
| **04** | `1:20 - 2:20` | Commutative state-based convergence across two out-of-order message streams. | "Independent replicas processing commutative messages in reverse order arrive at identical final state sets without central consensus." | `[Tested]` |

---

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (140s target).
