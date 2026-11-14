"""Hand-made outcome labels for Appendix A tests (BASS-II, NASA/TM-20210011385).

Every entry is checked by build_test_points.py:
  * basis text must be a verbatim substring of the named Appendix A cell of that test,
  * the outcome quote must be a verbatim substring of the named cell (or of the page text),
  * a cm/s value is only accepted if that number is literally present in the basis text.
Nothing here is typed from memory of the PDF without that check.

P(test, outcome, flow_cm_s, cond, basis_col, basis_text, quote_col, quote, derivation, notes)
  basis_col / quote_col: "notes" (test notes), "air" (Air display), "fan" (Fan display),
                         or "page:<n>" (body text of that PDF page).
"""

DIRECT = "direct"
START = ("step test: sustained at start flow (flame was established at the start flow and the test "
         "went on to later steps / a stated end outcome)")
LISTED = ("step test: listed step; the notes affirm steady burning across the listed steps but do not "
          "name this step individually")
STEP = "step test: this step is individually reported in the notes"
END_Q = "step test: extinguished at the end flow after the flow was reduced (low-flow extinction)"
OFF = "flow turned off / pot set to 0: extinction at zero forced flow (low-flow extinction)"
END_B = "step test: extinguished after the flow was increased (high-flow extinction)"
SELFX = ("self-extinguished at a constant low flow (not a blowoff attempt); labelled as low-flow-side "
         "extinction - judgement call")
MILLER_Q = ("extinction at a finite flow during a Miller slab test; the report classes these as quenching: "
            "'Quenching extinction data was also obtained at finite flow rates for most of the tests.' (PDF p66)")
AMB_NO_OUTCOME = "ambiguous: the notes describe the flame/test but state no outcome"

SPEC = []
def P(test, outcome, flow, cond, bcol, btext, qcol, quote, deriv, notes=""):
    SPEC.append(dict(test=test, outcome=outcome, flow=flow, cond=cond, bcol=bcol, btext=btext,
                     qcol=qcol, quote=quote, deriv=deriv, notes=notes))

# ----------------------------------------------------------------------------- A.1 Bhattacharjee
P("B1", "sustained", "5", "", "air", "5", "notes", "turned flow off after spread halfway",
  "direct: single set flow (air display) at which the flame spread before the flow was turned off")
P("B1", "quenched", "", "flow off", "notes", "turned flow off", "notes",
  "turned flow off after spread halfway; flame extinguished very quickly", OFF)
for f in ("5", "4", "3", "2", "1"):
    P("B10", "sustained", f, "", "air", "5, 4, 3, 2, 1", "notes", "Multiple velocities for steady spread", LISTED)
P("B10", "quenched", "", "pot 0.35", "notes", "pot 0.35", "notes", "extinguished at pot 0.35", END_Q)
for f in ("5", "3", "1"):
    P("B11", "sustained", f, "", "air", "5, 3, 1, <1", "notes", "Multiple velocities for steady spread", LISTED,
      "air display also lists '<1' (not a number; no row emitted for it)")
P("B11", "quenched", "", "pot 0.35", "notes", "pot 0.35", "notes", "extinguished at pot 0.35", END_Q)
P("B12", "ambiguous", "2", "", "air", "2", "notes", "Mostly blue, soot only on bottom", AMB_NO_OUTCOME)
for f in ("10", "5", "4", "3", "2", "1"):
    P("B13", "sustained", f, "", "air", "10, 5, 4, 3, 2, 1", "notes", "Multiple velocities for steady spread", LISTED)
P("B13", "quenched", "", "pot 0.35", "notes", "pot 0.35", "notes", "extinguished at pot 0.35", END_Q)
P("B14", "ambiguous", "", "air display lists '5, 3, 2, extinction'", "air", "5, 3, 2, extinction", "notes",
  "only brief ignition, flame extinguished",
  "ambiguous: notes say only brief ignition, but the air display lists steps 5, 3, 2 then extinction; "
  "the flow at which the flame went out is unclear")
P("B15", "sustained", "10", "", "notes", "Spread at 10 cm/s", "notes", "Spread at 10 cm/s, did not blowoff", DIRECT)
P("B15", "sustained", "", "maximum flow, no flow restrictor (air display 'max'; fan pot 10.0)", "air", "10, max",
  "notes", "did not blowoff", "blowoff attempt at maximum flow; flame survived",
  "flow at 'max' is not given in cm/s for this test")
P("B16", "quenched", "", "0.4 pot", "notes", "0.4 pot", "notes", "flame quenched after prolonged burn at 0.4 pot",
  "direct (the notes use the word 'quenched')", "notes add: one-sided flame; spread to top side and quenched immediately")
for f in ("5", "3"):
    P("B17", "sustained", f, "", "air", "5, 3, pot 0.4", "notes", "Burned steadily at higher flows", LISTED)
P("B17", "quenched", "", "pot 0.4", "notes", "a pot of 0.4", "notes", "extinguished just as we reached a pot of 0.4", END_Q)
P("B18", "sustained", "10", "", "air", "10, blowoff", "air", "10, blowoff", START)
P("B18", "blowoff", "", "fan pot 7.0 (no flow restrictor)", "notes", "a fan pot of 7.0", "notes",
  "flame blew out at a fan pot of 7.0", END_B)
P("B19", "sustained", "10", "", "air", "10, blowoff", "air", "10, blowoff", START)
P("B19", "blowoff", "", "pot 6.0 (no flow restrictor)", "notes", "a pot of 6.0", "notes",
  "flame blew out at a pot of 6.0", END_B)
P("B2", "ambiguous", "5", "", "air", "5", "notes", "No stills taken, cable came loose", AMB_NO_OUTCOME)
for f in ("5", "3"):
    P("B20", "sustained", f, "", "air", "5, 3, pot 0.5", "notes", "flame burned entire sample", LISTED)
P("B20", "sustained", "", "pot 0.5", "air", "pot 0.5", "notes", "flame burned entire sample", LISTED)
P("B21", "sustained", "5", "", "notes", "Ignition at 5 cm/s", "notes",
  "Ignition at 5 cm/s then fan pot turned down slowly after flame; spreads halfway", START)
P("B21", "quenched", "", "0.355 pot setting", "notes", "0.355 pot setting", "notes",
  "flame goes out at 0.355 pot setting", END_Q)
P("B22", "sustained", "5", "", "notes", "Ignition at 5 cm/s", "notes", "Ignition at 5 cm/s then decreased flow in step", START)
P("B22", "quenched", "", "fan pot 0.36", "notes", "0.36 (flame out)", "notes",
  "fan pot 1.7, 0.5, 0.4, 0.36 (flame out)", END_Q)
P("B3", "ambiguous", "2", "", "air", "2", "notes", "lower flow flames much more blue overall; still some soot though",
  AMB_NO_OUTCOME, "notes also question the O2 value: 'Probably 20.6 O2 to start'")
P("B4", "ambiguous", "5", "", "air", "5", "notes", "Bubble layer thickness increases with sample thickness", AMB_NO_OUTCOME)
P("B5", "ambiguous", "5", "", "air", "5", "notes", "Repeat of B2 test conditions, to get top view images",
  AMB_NO_OUTCOME, "notes also question the O2 value: 'question the 20.9 reading; all others were 20.6 this day'")
for f in ("3", "5"):
    P("B6", "sustained", f, "", "notes", "Steady burning at 3 and 5 cm/s", "notes", "Steady burning at 3 and 5 cm/s", DIRECT)
P("B7", "ambiguous", "2", "", "air", "2", "notes", "Very long bubble layer", AMB_NO_OUTCOME)
P("B8", "sustained", "10", "", "notes", "Spread at 10 cm/s", "notes", "Spread at 10 cm/s, did not blowoff", DIRECT)
P("B8", "sustained", "", "maximum flow, no flow restrictor (air display 'maximum'; fan pot 10.0)", "air",
  "10, maximum", "notes", "did not blowoff", "blowoff attempt at maximum flow; flame survived",
  "flow at 'maximum' is not given in cm/s for this test")
P("B9", "sustained", "2", "", "notes", "Steady burning at 2 cm/s", "notes", "Steady burning at 2 cm/s", DIRECT)
P("B9", "quenched", "", "0.35 (potentiometer setting; fan display '0.6, 0.35')", "notes", "extinguished at 0.35",
  "notes", "extinguished at 0.35", END_Q)

# ----------------------------------------------------------------------------- A.2 Ferkul
P("F1", "no_ignition", "9.5", "", "air", "9.5", "notes",
  "Ignited briefly but did not spread at all and extinguished while the igniter was still on", DIRECT)
P("F2", "no_ignition", "15", "", "air", "15", "notes", "Tried to ignite, flame would not sustain", DIRECT)
P("F3", "no_ignition", "8", "", "air", "8", "notes", "Brief ignition flash, no sustained flame", DIRECT)
P("F4", "sustained", "3", "", "notes", "blue flame established at 3 cm/s", "notes",
  "Long ignition, but blue flame established at 3 cm/s", DIRECT,
  "Figure 3.1 caption (PDF p54) pairs this with pot 0.6: 'Postignition at 3 cm/s (potentiometer or pot 0.6)'")
for pot in ("0.4", "0.35", "0.32", "0.31"):
    P("F4", "sustained", "", "pot " + pot, "notes", "potentiometers 0.6, 0.4, 0.35, 0.32, 0.31, 0.305", "page:54",
      "burned at five different flow velocities corresponding to the test matrix potentiometer settings",
      "step test: body text (PDF p54) says the candle burned at five flow velocities; Figure 3.1 caption lists them as "
      "pot 0.6 (3 cm/s), 0.4, 0.35, 0.32 and 0.31")
P("F4", "quenched", "", "pot 0.305", "notes", "0.305 flame extinguished", "notes",
  "reduced flow in increments: potentiometers 0.6, 0.4, 0.35, 0.32, 0.31, 0.305 flame extinguished", END_Q)

# ----------------------------------------------------------------------------- A.3 Fernandez-Pello
P("P1", "sustained", "5", "", "air", "5, 2, slow decrease to extinction", "notes", "nice flame", START)
P("P1", "quenched", "", "pot 0.315", "notes", "extinction at pot 0.315 (finite low flow)", "notes",
  "got down to extinction at pot 0.315 (finite low flow)", END_Q)
P("P10", "sustained", "5", "", "air", "5, pots 0.4, 0.36, 0.32, 0.31, 0.30 extinguished", "notes",
  "steady burn at multiple velocities", START)
P("P10", "quenched", "", "pot 0.3", "notes", "finite quench at pot 0.3", "notes", "finite quench at pot 0.3", END_Q)
for f in ("5", "3", "2", "1", "0.5"):
    P("P12", "sustained", f, "", "air", "5, 3, 2, 1, 0.5, lower", "notes", "multiple steady spread flows", LISTED)
P("P12", "quenched", "", "pot 0.34", "notes", "out immediately at 0.34", "notes",
  "oscillating at 0.36, out immediately at 0.34", END_Q, "notes add: 'Loss of signal before extinguished'")
P("P13a", "sustained", "5", "", "notes", "Fan pot 1.1 (5 cm/s)", "notes", "Fan pot 1.1 (5 cm/s), 0.4, 0.36, 0.32, 0.3, 0.28, 0.26", START)
P("P13a", "quenched", "", "pot 0 (flow off)", "notes", "flame out when pot turned to 0", "notes",
  "flame out when pot turned to 0", OFF)
P("P13b", "sustained", "5", "", "notes", "Fan pot 1.3 (5 cm/s)", "notes", "Fan pot 1.3 (5 cm/s), 0.4, 0.36, 0.32", START,
  "second burn of sample 203m (same sample number as P13a)")
P("P13b", "quenched", "", "pot 0.32", "notes", "flame out when pot turned to 0.32", "notes",
  "flame out when pot turned to 0.32", END_Q, "second burn of sample 203m (same sample number as P13a)")
P("P14", "sustained", "5", "", "air", "5, low (0.85, 0.4, 0.32)", "air", "5, low (0.85, 0.4, 0.32)", START)
P("P14", "quenched", "", "0.31 (potentiometer setting; the note does not write the unit)", "notes",
  "extinguished at 0.31", "notes", "All blue, extinguished at 0.31", END_Q)
P("P15", "sustained", "5", "", "air", "5, (0.36)", "notes", "Nice stable burn",
  "listed step; the notes report a stable burn but do not name the step; no end state is stated")
P("P16", "sustained", "5", "", "air", "5, 8, 2, low", "air", "5, 8, 2, low", START)
P("P16", "quenched", "", "pot 0.32", "notes", "Extinguished at pot 0.32", "notes", "Extinguished at pot 0.32", END_Q)
P("P17", "sustained", "5", "", "air", "5, 3, 2, 22, 2, low", "notes", "A few finite flows", START)
P("P17", "sustained", "22", "air display 22 (fan display 233; pot 10)", "air", "5, 3, 2, 22, 2, low", "notes",
  "tried blowoff without success",
  "blowoff attempt at the highest listed air-display step; flame survived ('did not blowoff')")
P("P17", "quenched", "", "pot 0.34", "notes", "oscillated and out at 0.34", "notes",
  "then 0.36, 0.34 pots, oscillated and out at 0.34", END_Q)
P("P18", "quenched", "", "fan pot 0.32", "notes", "extinction at fan pot 0.32", "notes",
  "finally turned pot down slowly, extinction at fan pot 0.32", END_Q,
  "before the final ramp the fan pot was alternated between 1 and 2 at 1-min intervals")
P("P19", "sustained", "5", "", "air", "5, 8, 2, maximum, 0", "air", "5, 8, 2, maximum, 0", START)
P("P19", "sustained", "", "pot 10 with 2 restrictors (air display 'maximum')", "notes",
  "did not blowoff at pot 10 2 restrictors", "notes", "Tried blowoff, did not blowoff at pot 10 2 restrictors",
  "blowoff attempt at maximum flow; flame survived", "flow at 'maximum' is not given in cm/s for this test")
P("P19", "quenched", "", "0.32 (pot)", "notes", "flame out at 0.32", "notes", "flame out at 0.32", END_Q)
P("P2", "sustained", "5", "", "air", "5, 2.5, 2 (pot 0.9, 0.5, 0.35, 0.33)", "notes", "Nice stable burn at low velocity", START)
P("P2", "sustained", "", "pot 0.33", "notes", "stable flame at pot 0.33", "notes", "stable flame at pot 0.33", DIRECT)
P("P2", "quenched", "", "fan off", "notes", "was just fan off, not slow ramp", "notes",
  "did not get extinction on stills, but was just fan off, not slow ramp", OFF)
P("P20", "quenched", "", "fan pot 0.335", "notes", "extinction at fan pot 0.335", "notes",
  "finally turned pot down slowly, extinction at fan pot 0.335", END_Q,
  "before the final ramp the fan pot was alternated between 1 and 2 at 1-min intervals")
P("P21a", "quenched", "5", "", "notes", "Flame self-extinguished at 5 cm/s", "notes",
  "Flame self-extinguished at 5 cm/s after sample end became flat, dim flame", SELFX)
P("P21b", "ambiguous", "5", "", "air", "5", "notes", "Igniter broke after third attempt to ignite flattened end of sample",
  "ambiguous: ignition attempts ended because the igniter broke; not a clean no-ignition result",
  "second burn attempt on sample 196M (same sample number as P21a)")
P("P22a", "sustained", "5", "", "air", "5 down to extinction", "air", "5 down to extinction", START)
P("P22a", "quenched", "", "pot 0.32", "fan", "0.32 extinction after some time", "fan",
  "5, 0.36, 0.32 extinction after some time", END_Q)
P("P22b", "sustained", "5", "", "air", "5 down to extinction", "air", "5 down to extinction", START,
  "second burn of sample 200m (same sample number as P22a)")
P("P22b", "quenched", "", "pot 0.31", "fan", "0.31, extinction", "fan", "0.31, extinction", END_Q,
  "second burn of sample 200m (same sample number as P22a)")
P("P23", "quenched", "", "fan pot 0.38", "notes", "extinction at fan pot 0.38", "notes",
  "finally turned pot down slowly, extinction at fan pot 0.38", END_Q,
  "before the final ramp the fan pot was alternated between 1 and 2")
P("P24", "quenched", "", "fan pot 0.30", "notes", "extinction at fan pot 0.30", "notes",
  "finally turned pot down slowly, extinction at fan pot 0.30", END_Q,
  "before the final ramp the fan pot was alternated between 1 and 2 at 1-min intervals")
P("P25", "sustained", "5", "", "air", "5 down to extinction", "air", "5 down to extinction", START,
  "notes: 'Reburn of 217m in opposed geometry'")
P("P25", "quenched", "", "0.31 pot", "notes", "extinguished at same 0.31 pot", "notes",
  "repeat of P22b, extinguished at same 0.31 pot", END_Q, "notes: 'Reburn of 217m in opposed geometry'")
P("P3a", "sustained", "5", "", "air", "5, 2.5 (1.15, 0.5, 0.35, 0.33. 0.32, 0.315, 0.31, 0.3)", "notes", "but steady spread", START)
P("P3a", "quenched", "", "0.3 pot", "notes", "extinguished at 0.3 pot", "notes",
  "extinguished at 0.3 pot very small flame, but steady spread", END_Q)
P("P3b", "sustained", "5", "", "air", "5, very low (0.85, 0.32, 0.31, 0.305, 0.30, 0.295)", "notes",
  "pot 0.32 spread, 0.31 spread, etc.", START, "second burn of sample 215M; no end state stated (camera power failed)")
P("P3b", "sustained", "", "pot 0.32", "notes", "pot 0.32 spread", "notes", "pot 0.32 spread, 0.31 spread, etc.", STEP,
  "second burn of sample 215M; no end state stated (camera power failed)")
P("P3b", "sustained", "", "pot 0.31", "notes", "0.31 spread", "notes", "pot 0.32 spread, 0.31 spread, etc.", STEP,
  "second burn of sample 215M; no end state stated (camera power failed)")
P("P4", "sustained", "5", "", "air", "5, pots 0.4, 0.36, 0.32, 0.308, .3, off", "notes",
  "long slow burn, steady at multiple pots until turned off flow", START)
P("P4", "quenched", "", "flow off", "notes", "until turned off flow", "notes",
  "steady at multiple pots until turned off flow", OFF)
_p5q = "Fan pot 1.5 (5 cm/s), 0.9, 0.4, 0.36, 0.32, 0.308, 0.3, 0.29, 0.28 (flame persisted for all)"
P("P5", "sustained", "5", "fan pot 1.5 (5 cm/s)", "notes", "Fan pot 1.5 (5 cm/s)", "notes", _p5q, STEP)
for pot in ("0.9", "0.4", "0.36", "0.32", "0.308", "0.3", "0.29", "0.28"):
    P("P5", "sustained", "", "fan pot " + pot, "notes", _p5q, "notes", _p5q, STEP)
P("P5", "quenched", "", "flow 0 (fan pot 0)", "notes", "finally turned down flow to 0 to extinguish", "notes",
  "finally turned down flow to 0 to extinguish", OFF)
P("P6", "sustained", "5", "", "air", "5, pots 0.4, 0.36, 0.32, 0.31, off", "notes",
  "steady burning until turned flow off, multiple pot settings", START)
P("P6", "quenched", "", "flow off", "notes", "until turned flow off", "notes", "steady burning until turned flow off", OFF)
for f in ("5", "10", "15"):
    P("P8", "no_ignition", f, "", "air", "5, would not stay lit, 10, 15 ibid", "air",
      "5, would not stay lit, 10, 15 ibid", DIRECT, "notes: 'would not stay lit, tip of sample was flat'; sample 197m was burned before in P4")
P("P9", "sustained", "5", "", "notes", "Fan pot 1.5 (5 cm/s)", "notes", "Fan pot 1.5 (5 cm/s), 0.9, 0.4, 0.36, 0.32, 0.3, 0.28", START,
  "second burn of sample 202m (same sample number as P5)")
P("P9", "quenched", "", "pot 0.28", "notes", "flame out at 0.28", "notes", "0.28 flame out at 0.28", END_Q,
  "second burn of sample 202m (same sample number as P5)")

# ----------------------------------------------------------------------------- A.4 Miller
# Sustained points for M1-M20 come from Table 5.1; Table A.4 adds the extinction points below.
P("M1", "quenched", "", "flow off", "notes", "put flame out by turning off flow", "notes",
  "put flame out by turning off flow", OFF, "extinction was forced by the crew when the camera card ran out")
P("M10", "quenched", "8", "", "notes", "flame self-extinguished at 8 cm/s after almost 10 min", "notes",
  "flame self-extinguished at 8 cm/s after almost 10 min", MILLER_Q)
P("M11", "quenched", "12", "", "notes", "extinguished at 12 cm/s", "notes", "extinguished at 12 cm/s", MILLER_Q)
P("M13", "quenched", "", "pot 0.3", "notes", "finally extinguished by turning pot down to 0.3", "notes",
  "finally extinguished by turning pot down to 0.3", END_Q)
P("M14", "quenched", "9", "", "notes", "flame self-extinguished at an air reading of 9 cm/s", "notes",
  "flame self-extinguished at an air reading of 9 cm/s", MILLER_Q)
P("M15", "quenched", "15", "", "notes", "turned down flow to 15 and got spreading and slow extinction there", "notes",
  "turned down flow to 15 and got spreading and slow extinction there", MILLER_Q,
  "the note writes '15' without a unit; the same sentence says 'turned flow up to 20 cm/s' and the air display ends '18, 16, 15'")
P("M16", "sustained", "1", "", "notes", "Burned at decreasing flow down to 1 cm/s or so, still fine", "notes",
  "Burned at decreasing flow down to 1 cm/s or so, still fine", DIRECT, "approximate in source: '1 cm/s or so'")
P("M17", "quenched", "", "fan pot 0 (flow off)", "notes", "finally turned fan pot to 0 to extinguish", "notes",
  "finally turned fan pot to 0 to extinguish", OFF)
P("M18", "quenched", "8", "", "notes", "extinguished 8 cm/s", "notes", "extinguished 8 cm/s", MILLER_Q)
P("M19", "quenched", "5", "", "notes", "went out on its own at 5 cm/s", "notes",
  "Burned with decreasing flows until it went out on its own at 5 cm/s", MILLER_Q)
P("M2", "quenched", "14", "", "notes", "increased flow to 14 cm/s, but it self-extinguished", "notes",
  "flame got very dim, so increased flow to 14 cm/s, but it self-extinguished", MILLER_Q)
P("M20", "quenched", "8", "", "notes", "then flow down to 8 cm/s (flame out after 3 more minutes)", "notes",
  "then flow down to 8 cm/s (flame out after 3 more minutes)", MILLER_Q)
P("M3", "quenched", "18", "", "notes", "Extinguished at 18 cm/s", "notes", "Extinguished at 18 cm/s", MILLER_Q)
P("M4", "quenched", "", "pot 0.3", "notes", "finally extinguished by turning pot down to 0.3", "notes",
  "finally extinguished by turning pot down to 0.3", END_Q)
P("M5", "quenched", "5", "", "notes", "extinguished at 5 cm/s after prolonged flashing", "notes",
  "extinguished at 5 cm/s after prolonged flashing", MILLER_Q)
for pot in ("0.4", "0.36"):
    P("M6", "sustained", "", "pot " + pot, "notes", "two flow plateaus (pot 0.4 and 0.36)", "notes",
      "had two flow plateaus (pot 0.4 and 0.36); when flame reached end of sample it started backing up and spreading along the edges",
      "step test: flow plateau named in the notes; the flame went on to reach the end of the sample")
P("M8", "quenched", "", "pot 0.4", "notes", "went out at pot 0.4", "notes",
  "turned down flow to extinguish, went out at pot 0.4", END_Q)
P("M9", "quenched", "14", "", "notes", "died after 15 min at 14 cm/s", "notes", "died after 15 min at 14 cm/s", MILLER_Q,
  "same test and velocity as the Table 5.1 'sustained' point (spread rate 0.025 mm/s at 14 cm/s): the flame spread for 15 min and then died")

# ----------------------------------------------------------------------------- A.5 Olson
P("O1", "ambiguous", "", "air display lists '20, 10, 5, 2, 1'", "air", "20, 10, 5, 2, 1", "notes",
  "Bracket test with decreasing flows; very sooty long flame at high flows",
  "ambiguous: no outcome stated (the rod broke off its holder); the flow-direction cell is '?'")
P("O10", "sustained", "5", "", "air", "5, 2, 0, maximum", "air", "5, 2, 0, maximum", START)
P("O10", "blowoff", "", "maximum flow, 2 restrictors (leading edge blew out at fan 81)", "notes",
  "blowoff at maximum flow", "notes",
  "Leading edge (LE) blew out at fan 81, 25 s for rest of flame to blowoff at maximum flow", END_B,
  "flow at blowoff is not given in cm/s for this test")
P("O11", "sustained", "5", "", "air", "5, down then blowoff", "air", "5, down then blowoff", START)
P("O11", "blowoff", "", "pot 6.0", "notes", "blowoff at pot of 6.0", "notes", "blowoff at pot of 6.0", END_B)
for pot in ("1.4", "3", "0.9", "0.7"):
    P("O12", "no_ignition", "", "pot " + pot, "fan", "pots 1.4, 3, 0.9, 0.7", "notes",
      "No sustained flame at any flow, flame with igniter but died immediately upon igniter removal", DIRECT,
      "sample 217m was burned again later as P25")
_o13 = "Ignited and burned at 5 pot settings, flame self-extinguished after 3+ min at pot 0.31"
P("O13a", "sustained", "5", "first pot setting 1.3; air display '(5, 2, 0)'", "air", "49, 44, 42, 41, 41, 40.5 (5, 2, 0)",
  "notes", "Ignited and burned at 5 pot settings", START,
  "in this row the fan-display cell holds pot settings and the air-display cell holds fan readings with air readings in brackets")
for pot in ("0.7", "0.45", "0.36", "0.32"):
    P("O13a", "sustained", "", "pot " + pot, "fan", "1.3, 0.7, 0.45, 0.36, 0.32, 0.31", "notes", _o13,
      "step test: notes say the rod burned at 5 pot settings; six are listed and the sixth (0.31) is the extinction")
P("O13a", "quenched", "", "pot 0.31", "notes", "flame self-extinguished after 3+ min at pot 0.31", "notes", _o13, END_Q)
P("O13b", "quenched", "", "pot 0.9", "notes", "Only stayed lit at 0.9 for less than a minute", "notes",
  "Only stayed lit at 0.9 for less than a minute",
  "self-extinguished shortly after the flow was set to pot 0.9 (low-flow side); judgement call",
  "second burn of sample 221m; air display '7, 4? (49, ?)' is itself marked uncertain in the source")
P("O14", "sustained", "5", "", "notes", "Ignition at 5 cm/s", "notes", "Ignition at 5 cm/s then slow pot decreases", START)
P("O14", "quenched", "", "pot 0.28", "notes", "quenching pot 0.28", "notes", "slow pot decreases to quenching pot 0.28", DIRECT)
P("O15a", "sustained", "5", "", "notes", "1.5 min at 5 cm/s", "notes", "1.5 min at 5 cm/s", STEP)
for pot, q in (("1.0", "2.5 min pot 1.0"), ("0.5", "3.5 min at 0.5"), ("0.35", "3.5 min 0.35")):
    P("O15a", "sustained", "", "pot " + pot, "notes", q, "notes", q, STEP)
P("O15a", "quenched", "", "0.32 pot", "notes", "slow turn down to 0.32, flame out fairly quickly", "notes",
  "Decrease flow to extinction at 0.32 pot, from 0.35 pot", END_Q)
_o15b = "notes: 'Reburn of same rod as previous ... much lower than previous; rod heatup effect?'"
P("O15b", "sustained", "5", "", "notes", "1 min 5 cm/s", "notes", "1 min 5 cm/s", STEP, _o15b)
for pot, q in (("0.5", "3.5 min pot 0.5"), ("0.35", "5 min 0.35"), ("0.34", "4 min 0.34"), ("0.33", "4 min 0.33"),
               ("0.32", "3 min 0.32"), ("0.31", "1 min 0.31"), ("0.3", "1 min 0.3;"), ("0.29", "1 min 0.29"),
               ("0.28", "1.5 min 0.28")):
    P("O15b", "sustained", "", "pot " + pot, "notes", q, "notes", q, STEP, _o15b)
P("O15b", "quenched", "", "0.27 pot", "notes", "0.27 out", "notes", "decreased flow to extinction at 0.27 pot", END_Q, _o15b)
P("O16", "no_ignition", "5", "", "air", "5", "notes", "Brief flame at end of first ignition, but no joy on sustained flame", DIRECT)
P("O17", "sustained", "3", "", "air", "3, 0, 11", "notes", "Stable burns at slightly higher flows", START)
P("O17", "blowoff", "11", "fan 72 (pot 4.0); last air-display value 11", "air", "3, 0, 11", "notes",
  "LE blowoff at fan 72 and turned down flow but flame did not recover and extinguished even after flow was down to 43-44",
  "leading-edge blowoff at the high-flow step and the flame did not recover; cm/s is the last air-display value "
  "(fan 72 = pot 4.0; in O18 fan 72 pairs with air display 11)")
P("O18", "sustained", "5", "", "air", "5, 2, 0, 11, 2, 11, 2, 0", "notes", "Got rod hot, blue flame", START)
P("O18", "blowoff", "11", "pot 4.0 (fan 72); air display 11", "air", "5, 2, 0, 11, 2, 11, 2, 0", "notes",
  "turned flow up to pot 4.0, stag region blew out",
  "stagnation-region blowout at pot 4.0 (air display 11, paired by list position: 8 fan values / 8 air values)",
  "first blowout was recovered by quickly turning the flow down; on the repeat the flame 'would not restabilize second "
  "time and flame extinguished after multiple oscillations at pot 1.0'")
P("O19", "sustained", "5", "", "notes", "Ignition at 5 cm/s", "notes", "Ignition at 5 cm/s then slow pot decreases", START)
P("O19", "quenched", "", "pot 0.288", "notes", "quenching pot 0.288", "notes", "slow pot decreases to quenching pot 0.288", DIRECT)
P("O2", "ambiguous", "2", "", "notes", "Ignited at 2 cm/s", "notes",
  "Ignited at 2 cm/s, and got dim flame that got sooty with lots of vapor jetting",
  "ambiguous: a flame is described but no outcome / end state is stated; the flow-direction cell is '?'")
P("O3a", "sustained", "5", "", "notes", "flame sooty at 5 cm/s", "notes", "flame sooty at 5 cm/s",
  "direct: flame reported at 5 cm/s before the flow was turned down")
P("O3a", "quenched", "", "flow turned down from 5 cm/s (air display '5, 3'; notes: 'probably overshot')", "notes",
  "Flame extinguished as soon as he turned flow down, probably overshot", "notes",
  "Flame extinguished as soon as he turned flow down, probably overshot", END_Q,
  "the flow at extinction is not known (overshoot)")
P("O3b", "ambiguous", "", "air display lists '5, 3, 2, 1, low'", "air", "5, 3, 2, 1, low", "notes",
  "Flame sooty even at lower flows, didn't get blue until air reading was zero",
  "ambiguous: a flame is described at several flows but no outcome / end state is stated",
  "second burn of sample 205M (same sample number as O3a)")
P("O4", "sustained", "5", "", "air", "5 down to extinction", "air", "5 down to extinction", START)
P("O4", "quenched", "", "0.36 (potentiometer setting; fan display '0.36 extinction')", "notes", "extinguished at 0.36",
  "notes", "decreased flow, extinguished at 0.36", END_Q)
P("O5a", "sustained", "5", "", "air", "5, 10, 5, 2, 0 (49, 62, 49, 44, 42)", "notes", "burned for 9 min", START)
P("O5a", "blowoff", "", "pot of 4.0", "notes", "blew out with pot of 4.0", "notes",
  "burned for 9 min then blew out with pot of 4.0, tried to stay lit but blew off after multiple oscillations", END_B)
P("O5b", "no_ignition", "5", "", "air", "49, 5 cm/s", "notes", "Would not sustain a flame without igniter on", DIRECT,
  "second burn attempt on sample 220m (same sample number as O5a)")
P("O6", "quenched", "", "0.275 (fan-display cell; potentiometer setting)", "fan", "out 0.275", "fan",
  "5, 0.36, 0.32, 0.31, 0.305, out 0.275", END_Q, "the test-notes cell is dashes; the label rests on the fan-display cell")
P("O7", "blowoff", "", "fan 97 (fan display: 'blowoff fan max 10')", "notes", "Blowoff fan 97", "notes", "Blowoff fan 97", END_B)
P("O8a", "quenched", "", "pot 0.31", "notes", "Quench at pot 0.31", "notes", "Quench at pot 0.31", DIRECT)
P("O8b", "blowoff", "", "fan 78 (fan display: 'blowoff fan pot 6.0')", "notes", "Blowoff fan 78", "notes", "Blowoff fan 78", END_B,
  "second burn of sample 208m (same sample number as O8a)")
P("O9", "blowoff", "", "fan 68 (fan display: 'blowoff pot 4.0')", "notes", "Blowoff fan 68", "notes", "Blowoff fan 68", END_B)

# ----------------------------------------------------------------------------- A.6 T'ien (tests not in Table 7.1)
P("T3", "no_ignition", "10", "", "air", "10", "notes", "Multiple ignition attempts on card 3, brief flames go out", DIRECT)
P("T7", "sustained", "10", "", "air", "10, 5, 3, 1, decrease", "notes", "took a while to ignite, turned pot down in series", START,
  "sample 182m was also used in T3")
P("T7", "quenched", "", "pot 0.28", "notes", "0.28 extinction finally", "notes", "0.285, 0.28 extinction finally", END_Q,
  "sample 182m was also used in T3")

# Tests whose O2 value is not a clean sensor reading: every point of the test is forced to "ambiguous".
O2_FLAGGED = {
    "P22b": "calibrated initial O2 '20.0' is printed in red in the source and the raw 'Initial O2' cell is '----' "
            "(no sensor reading was taken before this test)",
}

# Table 7.1 rows whose comment is dashes: outcome taken from the Table A.6 notes of the same test.
# key = A.6 test number; value = {position: (outcome, verbatim A.6 quote)}; position in start / end / single
CROSS_7_1 = {
    "T6": {"start": ("sustained", "still did not extinguish"), "end": ("sustained", "still did not extinguish")},
    "T16": {"start": ("sustained", "flame spread whole sample at 3 cm/s"), "end": ("sustained", "flame spread whole sample at 3 cm/s")},
    "T11": {"single": ("sustained", "Burned completely, steady")},
    "T19": {"single": ("sustained", "Steady burn")},
}
# Extra reasons for Table 7.1 rows that stay ambiguous (verbatim A.6 quote that explains why)
AMBIG_7_1_EXTRA = {
    "T5": "seemed to burn full sample length as a flamelet",
}
