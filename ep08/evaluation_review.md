# EP08 evaluation: manual review of the top-1 misses

Unified index (PDF + Word + email + Slack), 53 questions, evaluated as a normal employee
(private channels filtered out). Strict scoring: hit@1 70%, hit@4 92%.

Each question was written with ONE expected source. Once sources overlap, the top result is
sometimes a different source that answers the question correctly. Reviewed by hand:

| question | top result | verdict |
|---|---|---|
| Can a big corporate client get their money back…? | Slack #sales-ops (30 days firm, full refund) | correct alternative |
| Are the offices open between Christmas and New Year? | Slack #general (closed 24 Dec–1 Jan) | correct alternative |
| Who has to sign off on a 40% discount? | pricing_memo.docx (newer rules) | correct alternative, more current |
| What happens if a customer still hasn't paid after two months? | legal_terms.docx (read-only after 60 days) | correct alternative |
| How many more AX-200 arms does Brightline plan for 2027? | Slack #sales-ops (six arms) | correct alternative |
| I clicked a suspicious link… what should I do, and how fast? | IT security alert email | partial (no "within one hour") |
| When is payment due for invoice INV-2026-0418? | legal_terms.docx (generic net 45) | miss: exact identifier |
| What is the total amount billed to Brightline Packaging? | discount email | miss |
| When is the on-site installation at Brightline? | Slack #sales-ops | miss |
| What discount did the CFO approve for Brightline's 2027 framework? | Slack #sales-ops thresholds thread | miss |
| Who supported the Brightline discount but left the decision to the CFO? | Slack #sales-ops thresholds thread | miss |
| When will AX-200 firmware 4.0 be released? (email set) | Slack 10 Nov: "2 December" | miss: stale information |
| When will firmware 4.0 for the AX-200 be released? (Slack set) | Slack 10 Nov: "2 December" | miss: stale information |
| Why was the firmware 4.0 release delayed? | Slack 21 Nov confirmation | miss |
| What did Maya say about the Northwind refund? | Northwind thank-you email | miss |
| When do the new discount thresholds apply? | pricing memo header chunk | miss (partial) |

Counting correct alternatives: hit@1 = 42/53 = 79%.
Real misses cluster around stale information, exact identifiers and short messages: the motivation for EP09
(hybrid keyword + vector search, re-ranking, recency).
