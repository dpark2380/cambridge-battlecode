# What Battlecode postmortems say about testing and improvement

Read 2026-10-25 with `pdftotext` (`brew install poppler`) from battlecode.org/assets/files/:
postmortem-2026-lorem-ipsum, -2025-just-woke-up, -2025-the-kragle, -2022-5-musketeers, -2019-oak.

- **Test targeted maps first, then all maps against old versions.** Lorem Ipsum (2026, §10.1): "test it locally
  against older bots on a select variety of maps (usually one to three)... where I would see the new feature/fix
  reflect the most", then the full pool; a ~30% result means a bug, and "even if the bot appears to perform
  roughly slightly above 50% we accept it". A constant tuner "is too slow on my system and doesn't do well".
  This matches our `gate.py --mode map` followed by `--mode nonreg`.
- **Scrim the top teams automatically and study every loss.** Just Woke Up (2025, "Automatic Scrimmaging"): a
  script that "would automatically log in... and request to scrimmage with as many enemy teams as I chose... around
  the top 20 teams", then "go through the replays where I lost". Our equivalent would be `cambc match-groups create`
  against chosen teams. It spends shared quota (50, unused) and plays only the submitted bot, so it needs Daniel's
  go-ahead.
- **Copy what works.** The Kragle (2025): "Other teams beat your bot for a reason, and the easiest way to improve is
  to copy what they do better than you." Oak (2019): the biggest mistake was scrimming too little and missing "the
  meta shift that was happening right in front of our eyes". Our scout, meta and openings tools do this
  (`docs/research/top-team-meta.md`, `top-team-play.md`).
- **Watch replays for stuck behaviour.** 5 Musketeers (2022): a healing queue that never cleared left "soldiers just
  sitting at home waiting to be healed for over 1000 rounds". It's the same class of bug as our the_farm freeze
  (v9 B1) and the big_world fuel freeze (B19). The `frozen` and `fuel` loss signatures catch it.
- **A/B test every change on every map.** Just Woke Up (2025, "AB Testing"): before, they tested "on a few
  different maps (usually my favorites)... going off of vibes"; the script "would show me on which maps my new bot
  won, lost, or tied".
