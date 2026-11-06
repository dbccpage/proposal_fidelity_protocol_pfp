# pilot_0000000 — 22-Test Performance, Cost & Speed Comparison

**Model:** `deepseek/deepseek-v4.1-flash` (DeepSeek V4.1 Flash via OpenRouter)  
**Timestamp:** `2026-10-11T02:46:15.980445+00:00`  
**Expected Outcome:** `answer = 3` under `PFP-01-EXACT-LINALG`  

---

## 1. High-Level Comparative Summary

| Metric | Plain Inputs (11 tests) | Templated P* (11 tests) | Templated / Plain Ratio |
|---|---|---|---|
| **Average Payload Size (KB)** | 0.094 KB | 6.31 KB | **67.13x** |
| **Average Prompt Tokens** | 77.1 | 1764.6 | **22.9x** |
| **Average Completion Tokens** | 4545.3 | 5896.4 | **1.3x** |
| **Average Total Tokens** | 4622.4 | 7661.0 | **1.66x** |
| **Average Latency (s)** | 31.88s | 29.67s | **0.93x** |
| **Total Duration (s)** | 350.67s | 326.39s | **0.93x** |
| **Average Cost ($ USD)** | $0.002749 | $0.003556 | **1.29x** |
| **Total Cost ($ USD)** | $0.030241 | $0.039113 | **1.29x** |
| **Accuracy (Answer = 3)** | 3/11 (27.3%) | 5/11 (45.5%) | — |

---

## 2. Granular 22-Test Results Table

| # | Test ID | Kind | Case ID | Payload (KB) | Latency (s) | Prompt Tok | Compl Tok (Reasoning) | Total Tok | Cost ($) | Extracted Answer | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | `seed_plain` | plain_input | `seed` | 0.055 | 1.00s | 58 | 93 (86) | 151 | $0.000072 | `3` | `ACCEPTED` |
| 02 | `rewrite_01_plain` | plain_input | `rewrite_01` | 0.105 | 3.34s | 81 | 694 (514) | 775 | $0.000471 | `3` | `MALFORMED` |
| 03 | `rewrite_02_plain` | plain_input | `rewrite_02` | 0.122 | 2.14s | 87 | 296 (293) | 383 | $0.000202 | `None` | `MALFORMED` |
| 04 | `rewrite_03_plain` | plain_input | `rewrite_03` | 0.027 | 90.84s | 49 | 6881 (5213) | 6930 | $0.001243 | `None` | `MALFORMED` |
| 05 | `rewrite_04_plain` | plain_input | `rewrite_04` | 0.11 | 1.83s | 89 | 234 (232) | 323 | $0.000184 | `None` | `MALFORMED` |
| 06 | `rewrite_05_plain` | plain_input | `rewrite_05` | 0.262 | 25.61s | 148 | 830 (704) | 978 | $0.000299 | `3` | `MALFORMED` |
| 07 | `rewrite_06_plain` | plain_input | `rewrite_06` | 0.082 | 99.37s | 73 | 27147 (27142) | 27220 | $0.017929 | `None` | `MALFORMED` |
| 08 | `rewrite_07_plain` | plain_input | `rewrite_07` | 0.018 | 8.33s | 43 | 1352 (1223) | 1395 | $0.000896 | `None` | `MALFORMED` |
| 09 | `rewrite_08_plain` | plain_input | `rewrite_08` | 0.092 | 50.27s | 74 | 5691 (5364) | 5765 | $0.004276 | `None` | `MALFORMED` |
| 10 | `rewrite_09_plain` | plain_input | `rewrite_09` | 0.009 | 34.14s | 37 | 2364 (2219) | 2401 | $0.001777 | `None` | `MALFORMED` |
| 11 | `rewrite_10_plain` | plain_input | `rewrite_10` | 0.147 | 33.81s | 109 | 4416 (4413) | 4525 | $0.002892 | `None` | `MALFORMED` |
| 12 | `p_star_seed` | p_star_templated | `seed` | 6.271 | 2.05s | 1745 | 528 (372) | 2273 | $0.001157 | `3` | `ACCEPTED` |
| 13 | `p_star_rewrite_01` | p_star_templated | `rewrite_01` | 6.322 | 5.67s | 1768 | 1198 (1024) | 2966 | $0.000871 | `3` | `ACCEPTED` |
| 14 | `p_star_rewrite_02` | p_star_templated | `rewrite_02` | 6.339 | 9.54s | 1774 | 1347 (1149) | 3121 | $0.000969 | `3` | `ACCEPTED` |
| 15 | `p_star_rewrite_03` | p_star_templated | `rewrite_03` | 6.244 | 36.61s | 1737 | 7835 (7674) | 9572 | $0.009471 | `9` | `WRONG_ANSWER` |
| 16 | `p_star_rewrite_04` | p_star_templated | `rewrite_04` | 6.327 | 17.67s | 1777 | 1106 (876) | 2883 | $0.000359 | `3` | `ACCEPTED` |
| 17 | `p_star_rewrite_05` | p_star_templated | `rewrite_05` | 6.479 | 12.96s | 1836 | 2119 (1915) | 3955 | $0.001592 | `3` | `ACCEPTED` |
| 18 | `p_star_rewrite_06` | p_star_templated | `rewrite_06` | 6.299 | 90.41s | 1761 | 18383 (18228) | 20144 | $0.005550 | `1` | `WRONG_ANSWER` |
| 19 | `p_star_rewrite_07` | p_star_templated | `rewrite_07` | 6.234 | 18.42s | 1730 | 4825 (4671) | 6555 | $0.003226 | `4` | `WRONG_ANSWER` |
| 20 | `p_star_rewrite_08` | p_star_templated | `rewrite_08` | 6.309 | 37.32s | 1762 | 6464 (6303) | 8226 | $0.001961 | `7` | `WRONG_ANSWER` |
| 21 | `p_star_rewrite_09` | p_star_templated | `rewrite_09` | 6.226 | 41.68s | 1724 | 7543 (7315) | 9267 | $0.004987 | `7` | `WRONG_ANSWER` |
| 22 | `p_star_rewrite_10` | p_star_templated | `rewrite_10` | 6.364 | 54.07s | 1797 | 13512 (13316) | 15309 | $0.008970 | `1` | `WRONG_ANSWER` |