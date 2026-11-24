"""Generates a fictional Slack workspace export in Slack's export format (used from EP07).

data/acme/slack/
  users.json, channels.json (public), groups.json (private channels)
  <channel>/<YYYY-MM-DD>.json   one file per channel per day
data/acme/slack_update/          one extra day, to demo incremental sync

Realistic mess: <@U123> mentions, <#C123|name> channel links, <url|label> links, threads (thread_ts),
an edited message, channel_join noise, a CI bot, and a private #hr channel with restricted members.

    python tools/make_slack.py
"""
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "acme" / "slack"
UPDATE = ROOT / "data" / "acme" / "slack_update"
IST = timezone(timedelta(hours=5, minutes=30))

USERS = [("U01MAYA", "maya", "Maya Pillai", "Sales Ops Manager"), ("U02ARJUN", "arjun", "Arjun Mehta", "Account Executive"),
         ("U03SOFIA", "sofia", "Sofia Martins", "Firmware Lead"), ("U04RAHUL", "rahul", "Rahul Desai", "Support Engineer"),
         ("U05PRIYA", "priya", "Priya Nair", "Head of Sales Enablement"), ("U06NEHA", "neha", "Neha Kulkarni", "HR Business Partner"),
         ("U07ANANYA", "ananya", "Ananya Rao", "CFO"), ("U08VIKRAM", "vikram", "Vikram Shah", "QA Lead")]
U = {short: uid for uid, short, *_ in USERS}
U["ci-bot"] = "B01CI"  # bots post with a bot_id; real exports often still carry a user field
CHANNELS = {"general": ("C01GENERAL", False, [u for _, u, *_ in USERS]), "sales-ops": ("C02SALES", False, ["maya", "arjun", "priya", "ananya"]),
            "engineering": ("C03ENG", False, ["sofia", "rahul", "vikram", "arjun"]),
            "hr-private": ("G04HR", True, ["neha", "ananya", "priya"])}


def ts(dt):
    return f"{dt.timestamp():.6f}"


def m(who, text, at, **kw):
    msg = {"type": "message", "user": U[who], "text": text, "ts": ts(at)}
    msg.update(kw)
    return msg


def day(y, mo, d, h, mi):
    return datetime(y, mo, d, h, mi, tzinfo=IST)


def thread(parent_who, parent_text, at, replies):
    """replies: [(who, text, minutes_after)]"""
    p = m(parent_who, parent_text, at)
    p["thread_ts"] = p["ts"]
    out = [p]
    for who, text, mins in replies:
        out.append(m(who, text, at + timedelta(minutes=mins), thread_ts=p["ts"], parent_user_id=U[parent_who]))
    p["reply_count"] = len(replies)
    p["replies"] = [{"user": r["user"], "ts": r["ts"]} for r in out[1:]]
    return out


MESSAGES = {
    "sales-ops": [
        {"subtype": "channel_join", "type": "message", "user": U["priya"], "text": f"<@{U['priya']}> has joined the channel",
         "ts": ts(day(2026, 3, 2, 9, 0))},
        *thread("arjun", f"<@{U['maya']}> Northwind Foods wants to cancel their Enterprise subscription 25 days after the "
                         f"invoice. Can we still give a full refund?", day(2026, 3, 9, 16, 5),
                [("maya", "Yes. Legal says 30 days is firm for enterprise, and 25 < 30, so full refund. Loop in billing.", 12),
                 ("arjun", "Thanks! Forwarding to Kavya in billing.", 15)]),
        *thread("maya", "Heads up: from 1 October the new discount thresholds apply (VP above 15%, CFO above 30%). "
                        "Details in the pricing memo from Finance.", day(2026, 9, 15, 10, 30),
                [("arjun", f"Good timing, I have Brightline asking for 32% on a 2027 framework. <@{U['ananya']}> I'll send you the details.", 20)]),
        m("arjun", ":tada: Brightline Packaging signed the 2027 framework agreement today: six AX-200 arms at 28% off. "
                   "First delivery planned for March 2027.", day(2026, 10, 28, 17, 45)),
        *thread("priya", "Reminder: quote template v3 with the vision kit add-on is live. Please stop using v2.",
                day(2026, 11, 4, 11, 0), [("maya", "Updated the CRM link as well.", 30)]),
    ],
    "engineering": [
        *thread("sofia", "Firmware 4.0 for the AX-200: code freeze is on 18 November, release still planned for 2 December.",
                day(2026, 11, 10, 10, 0), [("vikram", "QA plan is ready, 3 days of safety regression tests after the freeze.", 25)]),
        m("ci-bot", "Build #1842 passed (ax200-firmware, branch release/4.0)", day(2026, 11, 17, 21, 3), bot_id="B01CI",
          subtype="bot_message", username="ci-bot"),
        *thread("vikram", "Safety regression found an issue in the new collision sensitivity setting at the highest level: "
                          "the protective stop takes 310 ms instead of the required 250 ms.", day(2026, 11, 19, 15, 20),
                [("sofia", "Confirmed. Fix is small but needs a full re-test. Firmware 4.0 release moves to 9 December.", 40),
                 ("rahul", f"<@{U['sofia']}> should I tell the customers who asked about 4.0?", 55),
                 ("sofia", "Yes please, 9 December, and no change for anyone not using the highest sensitivity level.", 70)]),
        m("rahul", "Rover-S firmware 2.3.2 is now rolled out to all customer fleets. Charging issue ticket count is back to zero.",
          day(2026, 7, 2, 12, 10)),
    ],
    "general": [
        m("neha", "Reminder: offices are closed from 24 December to 1 January. Support rota volunteers get those days back.",
          day(2026, 11, 16, 9, 30)),
        m("priya", f"All-hands on 5 December at 15:00 IST in the Pune cafeteria, with a stream for Munich and Austin. "
                   f"Questions for leadership go to <#C02SALES|sales-ops> or to me.", day(2026, 11, 18, 12, 0)),
        m("sofia", "Lunch & learn on Friday: how we test robot safety functions. Snacks provided :pizza:",
          day(2026, 11, 18, 14, 10)),
    ],
    "hr-private": [
        *thread("neha", "Salary review: letters go out on 15 January. The merit budget for 2027 is 6% of payroll, "
                        "with a separate 1.5% pool for promotions.", day(2026, 11, 12, 11, 0),
                [("ananya", "Confirmed from Finance. Please keep this channel only until the letters are out.", 18),
                 ("priya", "Noted, I'll prepare the sales team's promotion cases by 10 December.", 40)]),
    ],
}

# an edited message: the export only keeps the final text, plus an "edited" marker
for msg in MESSAGES["engineering"]:
    if "release still planned" in msg["text"]:
        msg["edited"] = {"user": U["sofia"], "ts": ts(day(2026, 11, 10, 10, 6))}

UPDATE_MESSAGES = {"engineering": [
    m("sofia", "Firmware 4.0 re-test passed. Release candidate 2 is tagged, release on 9 December confirmed.",
      day(2026, 11, 21, 18, 30))]}


def write_export(root, messages):
    for name, msgs in messages.items():
        by_day = {}
        for msg in msgs:
            d = datetime.fromtimestamp(float(msg["ts"]), IST).strftime("%Y-%m-%d")
            by_day.setdefault(d, []).append(msg)
        (root / name).mkdir(parents=True, exist_ok=True)
        for d, ms in by_day.items():
            (root / name / f"{d}.json").write_text(json.dumps(sorted(ms, key=lambda x: float(x["ts"])), indent=2))


if __name__ == "__main__":
    for d in (OUT, UPDATE):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    (OUT / "users.json").write_text(json.dumps([
        {"id": uid, "name": short, "real_name": real, "profile": {"display_name": real.split()[0], "title": title},
         "is_bot": False} for uid, short, real, title in USERS], indent=2))
    chans = [{"id": cid, "name": name, "is_private": priv, "members": [U[x] for x in mem if x != "ci-bot"],
              "created": int(datetime(2025, 1, 6, tzinfo=IST).timestamp())} for name, (cid, priv, mem) in CHANNELS.items()]
    (OUT / "channels.json").write_text(json.dumps([c for c in chans if not c["is_private"]], indent=2))
    (OUT / "groups.json").write_text(json.dumps([c for c in chans if c["is_private"]], indent=2))
    write_export(OUT, MESSAGES)
    write_export(UPDATE, UPDATE_MESSAGES)
    n = sum(len(v) for v in MESSAGES.values())
    print(f"wrote {n} messages in {len(MESSAGES)} channels to {OUT}, +1 message in {UPDATE}")
