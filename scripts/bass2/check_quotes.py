"""Check that every sentence quoted in README.md about flow / labels is verbatim on the stated PDF page."""
import sys, io, re, pymupdf
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
doc = pymupdf.open(sys.argv[1])
Q = [
 (12, "The flow was blown through the duct using a variable speed fan. Two additional flow restrictors could be used at the fan inlet to increase the pressure drop and thus reduce the flow through the duct to the desired value for the test point. With no restrictors, the maximum flow velocity was ~55 cm/s, and with two restrictors this was reduced to ~35 cm/s."),
 (12, "An omnidirectional spherical airspeed transducer (TSI Incorporated 8475) was positioned between the honeycomb and the screen and was used to measure the steady-state flow through the duct. The air velocity transducer probe had a response time of approximately 1 minute."),
 (13, "camera had an overlay that displayed the N2 flow rate (cm3/min), fan voltage (10× V), air velocity transducer reading (cm/s), and the radiometer signal. The fan voltage was calibrated with the airspeed transducer at the end of every operations day."),
 (13, "The external control box had controls for the fan voltage, N2 flow rate, enable switches for the igniter and N2 flow, and a radiometer gain level setting."),
 (74, "The air velocity transducer probe had a response time of approximately 1 min and its digital display only read out to the units place (no decimals) yielding an effective resolution of ±0.5 cm/s. A fan calibration was performed at the end of each operational day to associate the fan voltage with the flow velocity for each flow restrictor, after the fan had adequate time for warmup."),
 (74, "The voltage to the fan was displayed and could be set."),
 (21, "The fan voltage at that time indicates a flow velocity of about 1.1 cm/s."),
 (21, "there are significant uncertainties in these values as the calibration at such low velocity has high error bars"),
 (29, "A hot wire anemometer is used to calibrate the flow velocity with fan voltage, which is used to determine the flow velocity."),
 (54, "(a) Postignition at 3 cm/s (potentiometer or pot 0.6); (b) Pot 0.4"),
 (111, "cPotentiometer (pot)."), (112, "cPotentiometer (pot)."), (114, "bPotentiometer (pot). Extinction (ext)."),
 (115, "bPotentiometer (pot)."), (116, "cPotentiometer (pot)."), (117, "cPotentiometer (pot)."),
 (119, "cPotentiometer (pot). Maximum (max)."), (120, "cPotentiometer (pot)."), (121, "cPotentiometer (pot)."),
 (66, "Quenching extinction data was also obtained at finite flow rates for most of the tests."),
 (64, "The airflow was always opposed."),
 (103, "For those cases with flow velocity variations, the starting and the final velocities are indicated in the velocity column."),
 (103, "A total of 27 tests were carried out for the fabric samples in BASS–II, including six quenching tests, three nonignited tests, and one blowoff test."),
 (103, "These reused samples in general had a short unburned length and provided less quantitative data, thus will not be discussed in this report."),
 (13, "cast polymethylmethacrylate (PMMA) samples were shaped as rods of various diameters (6.35 to 12.7 mm), thin to thick slabs (0.125 to 5 mm), or a section of a 4-cm-diameter sphere. In addition, flat cotton-fiberglass blended fabric samples were also burned."),
 (55, "The tests for the present task were conducted with rods of cast PMMA"),
 (75, "The samples were ignited manually by the astronaut at the initially hemispherical stagnation tip with a hot-wire igniter, typically at a flow speed of 5 cm/s."),
 (135, "Sample 19 (1-cm PMMA sphere) was completely consumed in four tests (various high- and low-flow speeds) with the burn durations in Table D.2."),
 (63, "The experiment took place in opposed flow with a varying O2 concentration (uncontrolled) and varying flow velocities (controlled)."),
 (113, "Fan display"),
 (21, "the extinction velocities are found to be about 1 cm/s for 100, 200, and 300 μm and about 1.5 cm/s for 400 μm"),
 (54, "The wax candle test successfully ignited in an opposed flow (akin to holding a candle upside down)"),
 (104, "bO2 reading in these two tests might be inaccurate."),
 (119, "bPolymethylmethacrylate (PMMA)."),
 (120, "bSIBAL is Solid Inflammability Boundary at Low Speeds."),
]
print("quotes checked:", len(Q))
bad = 0
for p, q in Q:
    t = re.sub(r"\s+", " ", doc[p-1].get_text())
    ok = re.sub(r"\s+", " ", q) in t
    bad += (not ok)
    print("OK " if ok else "MISSING", p, q[:90])
print("missing:", bad)
