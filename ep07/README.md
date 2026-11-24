# EP07: Slack

| File | What it does |
|---|---|
| [`slack_parser.py`](slack_parser.py) | Reads a Slack workspace export (`users.json`, `channels.json`, `groups.json`, one JSON per channel per day). Resolves `<@U…>` mentions, `<#C…>` channel links and `<url|text>` links, drops joins and bot messages, turns each **thread** into one chunk and groups other messages into **60-minute windows**. Every chunk knows its channel, visibility and members |
| [`sync_slack.py`](sync_slack.py) | Incremental sync: remembers every message `ts` in `index/slack_store.json`, re-embeds only the conversations that got new messages; stable IDs (`uuid5("slack:" + key)`) overwrite old vectors |
| [`index.py`](index.py) | Index PDFs, Word, email and Slack; non-Slack chunks get `visibility: public` |
| [`ask.py`](ask.py) | `--as "Name"`: permission filter **inside Qdrant** (public OR the user is a member); `--type slack` |
| [`compare_slack.py`](compare_slack.py) | One chunk per raw message vs conversation chunks: retrieval |
| [`answer_check.py`](answer_check.py) | Answer quality for both, 3 runs per question |

```bash
python tools/make_slack.py                          # regenerate the sample export (optional)
python ep07/index.py data/acme/pdfs data/acme/docs data/acme/emails data/acme/slack
python ep07/ask.py --as "Arjun Mehta" "What is the merit budget for 2027?"   # I don't know
python ep07/ask.py --as "Priya Nair"  "What is the merit budget for 2027?"   # member of #hr-private
python ep07/sync_slack.py data/acme/slack data/acme/slack_update             # 1 new message → 1 conversation
```

In a real app the user comes from authentication, never from a command-line flag. EP12 attacks this filter.

## Results on our sample data (llama3.2 3B, mxbai-embed-large)

Retrieval, 10 questions, public channels (`slack_comparison.json`):

| variant | chunks | hit@1 | hit@4 |
|---|---|---|---|
| one per message | 18 | 90% | 100% |
| conversations | 10 | 90% | 100% |

Both miss *"When will firmware 4.0 be released?"*: the 10 Nov message (2 December) outranks the 19 Nov thread (9 December). Stale information, for EP09.

Answers, 3 runs each (`answer_check.json`, read by hand):

| question | one per message | conversations |
|---|---|---|
| Who asked whether to tell customers about the delay? | 0/3 (`<@U03SOFIA>`) | 3/3 (Rahul Desai) |
| What did Maya say about the Northwind refund? | 3/3 | 3/3 |
| When will firmware 4.0 be released? | 3/3 | 3/3 |

Permissions: as Arjun, *"I don't know"* with no `#hr-private` source; as Priya, *6% of payroll* (but she credits the 1.5% promotion pool to the wrong message). Sync: re-run → 0 new messages; new export → 1 conversation re-embedded in 0.4 s.
