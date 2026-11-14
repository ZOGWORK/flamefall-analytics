# Questions for Sushil

Things that need a human decision or a human at a keyboard. The build continued on the stated
assumption for each one.

## Needs an answer before submitting

**Q1. Team size and global judging.** The research notes quote the official Participant FAQs:
Universal Event teams need at least two participants to be eligible for global judging. The team
is registered as a solo team. Is that still the rule on the 2026 FAQ page, and if so do you want to
add a second participant before submitting?
*Assumption while building:* none needed; this does not change anything built here.

**Q3. Two hard rules in the brief were overturned by primary sources. Keep the corrections?**

- *Rule:* "LUCI has NO published quantitative results. Do not present LUCI spread rates."
  *Found:* NTRS 20250010653 (ASGSR, Dec 2025) gives spread rates for both LUCI samples. I read the
  slides directly.
- *Rule:* "There is NO Saffire VI-vs-IV spread-rate comparison in the literature. Do not present one."
  *Found:* ICES-2026-577 (NTRS 20260001992) Table 1 tabulates IV-1, V-2 and VI-2 spread rates side
  by side. I read the table directly.

*What I did:* presented both, each labelled with exactly what it is (LUCI: preliminary slides, one
flight, simulated gravity, not a PSI dataset, no oxygen limit claimed; Saffire: the three numbers
with their pressures, no ratio derived). The brief told me to correct numbers that primary sources
contradict, so I treated these as corrections (DECISIONS.md C6, C7).
*If you would rather hold to the brief's wording:* say so and I will remove both. The change is six entries in
`data/evidence.json` (`luci-sibal`, `luci-pmma`, `luci-method`, `saffire-2026-spread`,
`saffire-2026-alarm`, `saffire-2026-hrr-differs`), the LUCI catalogue row, and anything the front end
shows from those entries.

**Q4. The "85% O2" correction is itself corrected.** The brief says the 85% figure is Flame
Design's, "never CFI-G". PSI's own CFI-G inverse-flame table and the challenge page both put 85%
burner-feed oxygen in CFI-G as well. The data keeps the point that matters (a burner feed,
never an ambient) and attributes it to the inverse flames of both investigations. No action needed
unless you disagree.

## Could not verify (source blocked to automated access)

**Q2. ICES-2019-101** (Olson, Ferkul et al., BASS-II flammability limits). The Texas Tech
repository returns HTTP 403 to non-browser clients, so this paper was not re-read during the build.
Link: https://ttu-ir.tdl.org/server/api/core/bitstreams/2024efac-4733-4352-826e-8eaaa6954038/content

*What a human can do:* open the link in a browser and save the PDF; I can then check the four
statements that rest on it alone (thin-film blowoff speeds, CO yield, "flames went out when the
flow was turned off", buoyant velocities 24 / 10 / 15 cm/s).
*Assumption while building:* those four statements carry the level `unverified`. Wherever the
BASS-II summary memo states the same quantity, the memo is cited instead.

**Q5. Sources that only an abstract could be read for** (publisher blocks automated access): the
Flame Design journal paper (burn times 28 to 336 s) and the FLEX limiting-oxygen abstract (0.12
methanol, 0.15 n-heptane). Both are shown with an "index-level" badge. The FLARE conference paper
was unreachable, so FLARE has no numbers in the catalogue.
