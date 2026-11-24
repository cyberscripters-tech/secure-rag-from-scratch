"""EP07: do conversation chunks change the ANSWERS?

Same retrieval (top 4), same model, naive per-message chunks vs conversation chunks.
  who_asked : "Who asked whether to tell customers about the firmware 4.0 delay?"  correct = Rahul Desai
  maya      : "What did Maya say about the Northwind refund?"                     correct = full refund (30 days firm)
  release   : "When will firmware 4.0 for the AX-200 be released?"                correct = 9 December

    python ep07/answer_check.py [runs]
"""
import json
import sys

import numpy as np

from compare_slack import ROOT, conv_of, embed
from llm import generate
from slack_parser import conversation_chunks, load_messages, load_workspace

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
PROMPT = ("You are Acme Robotics' internal assistant. Answer ONLY from the context below.\n"
          "If the answer is not in the context, say \"I don't know\".\n\nContext:\n{context}\n\nQuestion: {question}")
QUESTIONS = {"who_asked": "Who asked whether to tell customers about the firmware 4.0 delay?",
             "maya": "What did Maya say about the Northwind refund?",
             "release": "When will firmware 4.0 for the AX-200 be released?"}

if __name__ == "__main__":
    users, channels = load_workspace(ROOT)
    msgs = [m for m in load_messages(ROOT) if not channels[m["channel"]]["private"]]
    variants = {"naive": [m["text"] for m in msgs],
                "clean": [c["text"] for c in conversation_chunks(msgs, users, channels)]}
    out = {}
    for name, texts in variants.items():
        docs = embed(texts)
        out[name] = {}
        for key, q in QUESTIONS.items():
            top = [texts[i] for i in np.argsort(docs @ embed([q])[0])[::-1][:4]]
            out[name][key] = {"context": top, "answers": [generate(PROMPT.format(context="\n\n".join(top), question=q))
                                                          for _ in range(RUNS)]}
            print(f"{name:<6}{key:<10} done", flush=True)
    json.dump(out, open("ep07/answer_check.json", "w"), indent=1)
