"""EP05: do dates help when two documents disagree?

The handbook (March 2026) says discounts above 35% need the CFO.
The pricing memo (September 2026) lowers that to above 30%.
For a 32% discount, the correct current answer needs the CFO.

In our index the memo already outranks the handbook, but you can't rely on that,
so we test the worst case: both versions in the context, the outdated one first.
We run the same question N times with:
  A) EP04-style context: no dates, no conflict rule
  B) EP05 context: modified dates + "follow the most recent source"
in two scenarios: the memo says it replaces the handbook rule, and the memo is "silent".

    python ep05/conflict_check.py [runs]
"""
import json
import re
import sys

from ask import PROMPT, cite, retrieve
from llm import generate
from qdrant_client import models

from store import COLLECTION, check_meta, open_db

QUESTION = "Who has to approve a 32% discount for a customer?"
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
PROMPT_A = ("You are Acme Robotics' internal assistant. Answer ONLY from the context below.\n"
            "If the answer is not in the context, say \"I don't know\". Cite sources like [handbook.pdf p3].\n\n"
            "Context:\n{context}\n\nQuestion: {question}")

check_meta()
db = open_db()
print("normal retrieval:", ", ".join(f"{cite(p)} [{p['modified']}]" for p, _ in retrieve(db, QUESTION)))


def chunk(source, page=None, contains=""):
    must = [models.FieldCondition(key="source", match=models.MatchValue(value=source))]
    points, _ = db.scroll(COLLECTION, scroll_filter=models.Filter(must=must), limit=100)
    return next(p.payload for p in points if (page is None or p.payload["page"] == page) and contains in p.payload["text"])


# Worst case: BOTH versions reach the model, and the outdated one comes first.
hits = [(chunk("handbook.pdf", 11, "VP of Sales"), 0), (chunk("pricing_memo.docx", contains="above 30%"), 0)]
db.close()
print("conflict test context:", ", ".join(f"{cite(p)} [{p['modified']}]" for p, _ in hits))
memo = hits[1][0]
silent = dict(memo, text=re.sub(r"Effective 1 October 2026.*?v7\.2\.\s*", "", memo["text"], flags=re.S))
assert silent["text"] != memo["text"]

out = {"question": QUESTION, "runs": RUNS}
scenarios = {
    "1_memo_says_it_replaces": [hits[0], (memo, 0)],
    "2_memo_silent": [hits[0], (silent, 0)],     # same rules, but no "this replaces section 4.1" sentence
}
for scen, ctx_hits in scenarios.items():
    ctx_a = "\n\n".join(f"(source: {cite(p)})\n{p['text']}" for p, _ in ctx_hits)
    ctx_b = "\n\n".join(f"(source: {cite(p)} · modified {p['modified']} · author {p['author']})\n{p['text']}"
                         for p, _ in ctx_hits)
    out[scen] = {"memo_text": ctx_hits[1][0]["text"]}
    for name, prompt, ctx in [("A_no_dates", PROMPT_A, ctx_a), ("B_dates_and_rule", PROMPT, ctx_b)]:
        answers = [generate(prompt.format(context=ctx, question=QUESTION)) for _ in range(RUNS)]
        out[scen][name] = answers
        # "mentions the CFO" is only a first filter (the old rule mentions the CFO too): read the answers!
        print(f"{scen:<26}{name:<18} answers that mention the CFO: {sum('CFO' in a for a in answers)}/{RUNS}",
              flush=True)
json.dump(out, open("ep05/conflict_check.json", "w"), indent=1)
