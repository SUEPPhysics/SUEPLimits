import numpy as np
import re
import hepdata_lib as hlib
import uproot
import json
import csv

submission = hlib.Submission()

## Additional Files
#submission.add_additional_resource("ZH Signal Fragment", "ZHleptonic_template.py", copy_file=True)

def ConsolidateULScan(decay_mode, title, description, location, observed_data_file, expected_data_file, image):
    table_sigs = hlib.Table(title)
    table_sigs.description = description
    table_sigs.location = location

    # Load observed and expected data
    obs_data = np.loadtxt(observed_data_file, delimiter=':', comments='#')
    exp_data = np.loadtxt(expected_data_file, delimiter=':', comments='#')

    # Ensure both datasets have the same number of entries
    assert obs_data.shape[0] == exp_data.shape[0], "Observed and Expected data must have the same number of entries."

    # Extract mass and ratio
    mass = obs_data[:, 1]
    ratio = np.log2(obs_data[:, 2] / mass)

    # Create Variables
    dark_meson_mass = hlib.Variable(r"$m_{\phi}$", is_independent=True, is_binned=False, units="GeV")
    dark_meson_mass.values = mass
    table_sigs.add_variable(dark_meson_mass)

    log_T_m = hlib.Variable(r"$\log_2(T/m_{\phi})$", is_independent=True, is_binned=False)
    log_T_m.values = ratio
    table_sigs.add_variable(log_T_m)

    # Observed data
    observed = hlib.Variable("Observed", is_independent=False, is_binned=False, units="fb")
    observed.values = obs_data[:, 3] * 870 * 0.0336 * 3  # Adjust scaling as needed
    table_sigs.add_variable(observed)

    # Expected data
    expected = hlib.Variable("Expected", is_independent=False, is_binned=False, units="fb")
    expected.values = exp_data[:, 5] * 870 * 0.0336 * 3  # Adjust scaling as needed
    table_sigs.add_variable(expected)

    # Uncertainties for Expected
    oneSigma = hlib.Uncertainty(r"$1\sigma$", is_symmetric=False)
    one_sigma_lower = -exp_data[:, 3] * 870 * 0.0336 * 3
    one_sigma_upper = exp_data[:, 6] * 870 * 0.0336 * 3
    oneSigma.values = list(zip(one_sigma_lower, one_sigma_upper))
    expected.add_uncertainty(oneSigma)

    twoSigma = hlib.Uncertainty(r"$2\sigma$", is_symmetric=False)
    two_sigma_lower = -exp_data[:, 4] * 870 * 0.0336 * 3
    two_sigma_upper = exp_data[:, 7] * 870 * 0.0336 * 3
    twoSigma.values = list(zip(two_sigma_lower, two_sigma_upper))
    expected.add_uncertainty(twoSigma)

    # Add image if provided
    if image:
        table_sigs.add_image(image)

    # Add the table to submission
    submission.add_table(table_sigs)

decay_modes = {
    "Hadronic": {
        "observed": "hadronic_UL_SRCR.txt",
        "expected": "hadronic_UL_SRCR_Exp.txt",
        "image": "BR_XSec_1D.pdf",
        "description": r"Observed and Expected UL exclusions on the $\sigma\times BR(H\to S) \times BR(Z\to ll)$ of hadronic signals with $m_{A'} = 0.7\;GeV$ and $BR(A' \rightarrow ee) = BR(A' \rightarrow \mu\mu) = 0.15$ and $BR(A' \rightarrow \pi\pi) = 0.7$.",
        "location": "Figure 3 (Hadronic)"
    },
    "Leptonic": {
        "observed": "leptonic_UL_SRCR.txt",
        "expected": "leptonic_UL_SRCR_Exp.txt",
        "image": "BR_XSec_1D.pdf",
        "description": r"Observed and Expected UL exclusions on the $\sigma\times BR(H\to S) \times BR(Z\to ll)$ of leptonic signals with $m_{A'} = 0.5\;GeV$ and $BR(A' \rightarrow ee) = BR(A' \rightarrow \mu\mu) = 0.2$ and $BR(A' \rightarrow \pi\pi) = 0.6$.",
        "location": "Figure 3 (Leptonic)"
    },
    "Generic": {
        "observed": "generic_UL_SRCR.txt",
        "expected": "generic_UL_SRCR_Exp.txt",
        "image": "BR_XSec_1D.pdf",
        "description": r"Observed and Expected UL exclusions on the $\sigma\times BR(H\to S) \times BR(Z\to ll)$ of generic signals with $m_{A'} = 1.0\;GeV$ and $BR(A' \rightarrow \pi\pi) = 1.0$.",
        "location": "Figure 3 (Generic)"
    }
}

for mode, files in decay_modes.items():
    ConsolidateULScan(
        decay_mode=mode,
        title=f"Figure UL {mode} (Observed & Expected)",
        description=files["description"],
        location=files["location"],
        observed_data_file=files["observed"],
        expected_data_file=files["expected"],
        image=files["image"]
    )

def ConsolidateAgnosticLimits(title, description, location, input_file, image=None):
    """
    Creates a HepData table from an 'agnostic' limits file which contains:
      # cardName  observed  -2sigma  -1sigma  median  +1sigma  +2sigma
    for lines like:
      nT21  20840.2625  6825.4295  9008.6965  12305   16866.488  21924.0135

    Parameters
    ----------
    title : str
        Table title (e.g. "Agnostic Limits for ...")
    description : str
        Table description
    location : str
        Location in the paper, e.g. "Figure 3 (Agnostic)"
    input_file : str
        Path to the text file containing the limits data.
    image : str, optional
        Path to an image/PDF to attach to the table, e.g. a limit plot.
    """

    # Read the lines from the input file, skipping any '#' comments
    cardNames = []
    observedVals = []
    minus2sig = []
    minus1sig = []
    medianVals = []
    plus1sig = []
    plus2sig = []

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments or empty lines
            if not line or line.startswith('#'):
                continue
            cols = line.split()
            # Expect 7 columns total
            if len(cols) < 7:
                continue

            cardNames.append(cols[0])
            observedVals.append(float(cols[1]))
            minus2sig.append(-float(cols[2]))
            minus1sig.append(-float(cols[3]))
            medianVals.append(float(cols[4]))
            plus1sig.append(float(cols[5]))
            plus2sig.append(float(cols[6]))

    # Convert to numpy arrays (useful for vector arithmetic)
    observedVals = np.array(observedVals)
    minus2sig    = np.array(minus2sig)
    minus1sig    = np.array(minus1sig)
    medianVals   = np.array(medianVals)
    plus1sig     = np.array(plus1sig)
    plus2sig     = np.array(plus2sig)

    # Now build the table
    table_agn = hlib.Table(title)
    table_agn.description = description
    table_agn.location = location

    # 1) cardName as an independent variable
    cardNameVar = hlib.Variable(r"Lower $N_{Tracks}$ bound", is_independent=True, is_binned=False)
    cardNameVar.values = cardNames
    table_agn.add_variable(cardNameVar)

    # 2) Observed limit
    observedVar = hlib.Variable("Observed UL on Yields", is_independent=False, is_binned=False)
    observedVar.values = observedVals
    table_agn.add_variable(observedVar)

    # 3) Expected limit (median) with 1 sigma and 2 sigma uncertainties
    expectedVar = hlib.Variable("Expected UL on Yields", is_independent=False, is_binned=False)
    expectedVar.values = medianVals

    # Create the 1 sigma band as an asymmetric uncertainty
    # Lower side: median - (-1sigma value) = medianVals - minus1sig
    # Upper side: (+1sigma value) - medianVals = plus1sig - medianVals
    oneSigma = hlib.Uncertainty(r"$1\sigma$", is_symmetric=False)
    oneSigma.values = list(zip(medianVals - minus1sig, plus1sig - medianVals))
    expectedVar.add_uncertainty(oneSigma)

    # Create the 2 sigma band as an asymmetric uncertainty
    # Lower side: median - (-2sigma) = medianVals - minus2sig
    # Upper side: (+2sigma) - medianVals = plus2sig - medianVals
    twoSigma = hlib.Uncertainty(r"$2\sigma$", is_symmetric=False)
    twoSigma.values = list(zip(medianVals - minus2sig, plus2sig - medianVals))
    expectedVar.add_uncertainty(twoSigma)

    table_agn.add_variable(expectedVar)

    # Add the image if you have one
    if image:
        table_agn.add_image(image)

    # Finally, add the table to the global submission
    submission.add_table(table_agn)

ConsolidateAgnosticLimits(
    title="Model Agnostic Limits",
    description="Observed and Expected UL exclusions on the number of 'signal' yields in sideband A from the model agnostic fit, assuming no 'SUEP-like' signal contamination in the CRs.",
    location="Figure 3 (Agnostic)",
    input_file="AgnosticLimits.txt",
    image="scan_agnostic.pdf"
)

def postFit(title, description, location, image, isCR, root_file1_path, root_file2_path, root_file3_path, root_file4_path):
    def zero_small_values(values, uncertainties, threshold=1e-6):
        for i in range(len(values)):
            if values[i] < threshold:
                values[i] = 0.0
                uncertainties[i] = 0.0

    # --- Open ROOT files ---
    with uproot.open(root_file1_path) as file1, \
         uproot.open(root_file2_path) as file2, \
         uproot.open(root_file3_path) as file3, \
         uproot.open(root_file4_path) as file4:

        # --- Read Data ---
        data_hist = file1["data_prefit;1"]
        data = data_hist.values()
        data_unc = data_hist.errors()  # GetBinError

        # --- Read b_SRCR and b_SRCR_Unc ---
        b_SRCR_hist = file1["total_background_fitb;1"]
        b_SRCR = b_SRCR_hist.values()

        b_SRCR_up = file1["total_background_fitbUp;1"].values()
        b_SRCR_dn = file1["total_background_fitbDn;1"].values()
        b_SRCR_unc = np.maximum(np.abs(b_SRCR_up - b_SRCR), np.abs(b_SRCR_dn - b_SRCR))

        # --- Read b_CR and b_CR_Unc ---
        b_CR_hist = file2["total_background_fitb;1"]
        b_CR = b_CR_hist.values()

        b_CR_up = file2["total_background_fitbUp;1"].values()
        b_CR_dn = file2["total_background_fitbDn;1"].values()
        b_CR_unc = np.maximum(np.abs(b_CR_up - b_CR), np.abs(b_CR_dn - b_CR))

        # --- Read Signal 1 and Signal 2 ---
        signal_hist = file3["SUEP_generic_mS125_mD2.0_T2.00_prefit;1"]
        signal = signal_hist.values()
        signal_up = file3["SUEP_generic_mS125_mD2.0_T2.00_prefitUp;1"].values()
        signal_dn = file3["SUEP_generic_mS125_mD2.0_T2.00_prefitDn;1"].values()
        signal_unc = np.maximum(np.abs(signal_up - signal), np.abs(signal_dn - signal))

        signal_hist_2 = file4["SUEP_generic_mS125_mD6.0_T3.00_prefit;1"]
        signal_2 = signal_hist_2.values()
        signal_up_2 = file4["SUEP_generic_mS125_mD6.0_T3.00_prefitUp;1"].values()
        signal_dn_2 = file4["SUEP_generic_mS125_mD6.0_T3.00_prefitDn;1"].values()
        signal_unc_2 = np.maximum(np.abs(signal_up_2 - signal_2), np.abs(signal_dn_2 - signal_2))

    # --- Condition 1: If "PR " is in the title, zero out all signal entries ---
    if "PR " in title:
        signal[:] = 0.0
        signal_unc[:] = 0.0
        signal_2[:] = 0.0
        signal_unc_2[:] = 0.0

    # --- Condition 2: If any entry < 1e-6, set it to 0 along with its uncertainty ---
    # (Do this for background, data, and signal unless the signals are already zeroed out above.)
    zero_small_values(b_SRCR, b_SRCR_unc)
    zero_small_values(b_CR, b_CR_unc)
    zero_small_values(data, data_unc)
    # Only apply if not already forced to zero for PR
    if "PR " not in title:
        zero_small_values(signal, signal_unc)
        zero_small_values(signal_2, signal_unc_2)

    # --- Now build the table ---
    table_postfit = hlib.Table(title)
    table_postfit.description = description
    table_postfit.location = location

    # Region Variable
    sideband = hlib.Variable(r"Region", is_independent=True, is_binned=False)
    if isCR:
        sideband.values = [
            'E2', 'E1', 'B2_1', 'B2_2', 'B2_3', 'B2_4', 'B2_5', 'D2', 'D1',
            'B1_1', 'B1_2', 'B1_3', 'B1_4', 'B1_5', 'C2', 'C1',
            'A_1', 'A_2', 'A_3', 'A_4', 'A_5'
        ] 
    else:
        sideband.values = [
            'E2', 'E1', 'B2_1', 'B2_2', 'B2_3', 'B2_4', 'B2_5', 'B2_6',
            'B2_7', 'B2_8', 'D2', 'D1', 'B1_1', 'B1_2', 'B1_3',
            'B1_4', 'B1_5', 'B1_6', 'B1_7', 'B1_8', 'C2', 'C1',
            'A_1', 'A_2', 'A_3', 'A_4', 'A_5', 'A_6', 'A_7', 'A_8'
        ]
    table_postfit.add_variable(sideband)

    # N_tracks Variable
    ntracks = hlib.Variable(r"$N_{tracks}$", is_independent=True, is_binned=True)
    if isCR:
        ntracks.values = [(0, 14), (14, 21), (21, 26), (26, 31), (31, 36),
                          (36, 41), (41, float('inf'))] * 3
    else:
        ntracks.values = [(0, 14), (14, 21), (21, 26), (26, 31), (31, 36),
                          (36, 41), (41, 46), (46, 51), (51, 56), (56, float('inf'))] * 3
    table_postfit.add_variable(ntracks)

    # Jet1 pT Variable
    jet1pt = hlib.Variable(r"$p_T^{jet1}$", is_independent=False, is_binned=False, units="GeV")
    if isCR:
        jet1pt.values = ["< 135"] * 7 + ["135 - 220"] * 7 + ["220 <="] * 7
    else:
        jet1pt.values = ["< 135"] * 10 + ["135 - 220"] * 10 + ["220 <="] * 10
    table_postfit.add_variable(jet1pt)

    # --- Add Background (SR+CR) ---
    b_SRCR_var = hlib.Variable(r"Post-fit Background (SR+CR)", is_independent=False, is_binned=False)
    b_SRCR_var.values = b_SRCR
    b_SRCR_var_unc = hlib.Uncertainty("Stat. + Syst.", is_symmetric=True)
    b_SRCR_var_unc.values = b_SRCR_unc
    b_SRCR_var.add_uncertainty(b_SRCR_var_unc)
    table_postfit.add_variable(b_SRCR_var)

    # --- Add Background (CR) ---
    b_CR_var = hlib.Variable(r"Post-fit Background (CR)", is_independent=False, is_binned=False)
    b_CR_var.values = b_CR
    b_CR_var_unc = hlib.Uncertainty("Stat. + Syst.", is_symmetric=True)
    b_CR_var_unc.values = b_CR_unc
    b_CR_var.add_uncertainty(b_CR_var_unc)
    table_postfit.add_variable(b_CR_var)

    # --- Add Data ---
    data_var = hlib.Variable(r"Data", is_independent=False, is_binned=False)
    data_var.values = data
    data_var_unc = hlib.Uncertainty("Poissonian Unc.", is_symmetric=True)
    data_var_unc.values = data_unc
    data_var.add_uncertainty(data_var_unc)
    table_postfit.add_variable(data_var)

    # --- Add Signal 1 ---
    signal_var = hlib.Variable(r"Pre-fit Signal $m_{A'} = 1.0\;GeV$ $BR(A' \rightarrow \pi\pi) = 1.0$ $m_{D} = T = 2\;GeV$", 
                               is_independent=False, is_binned=False)
    signal_var.values = signal
    signal_var_unc = hlib.Uncertainty("Stat.", is_symmetric=True)
    signal_var_unc.values = signal_unc
    signal_var.add_uncertainty(signal_var_unc)
    table_postfit.add_variable(signal_var)

    # --- Add Signal 2 ---
    signal_var_2 = hlib.Variable(r"Pre-fit Signal $m_{A'} = 1.0\;GeV$ $BR(A' \rightarrow \pi\pi) = 1.0$ $m_{D} = 6$ $T = 3\;GeV$", 
                                 is_independent=False, is_binned=False)
    signal_var_2.values = signal_2
    signal_var_unc_2 = hlib.Uncertainty("Stat.", is_symmetric=True)
    signal_var_unc_2.values = signal_unc_2
    signal_var_2.add_uncertainty(signal_var_unc_2)
    table_postfit.add_variable(signal_var_2)

    # Add Image
    table_postfit.add_image(image)

    # Submit the table
    submission.add_table(table_postfit)

postFit("SR B-Only Post-Fit",
       "Postfit values for SR in the B-Only CR+SR and CR-Only fits with the prefit signal overlayed for reference",
       "Data from Figure 2 (SR)",
       "SR_Postfit_forPaper.pdf",
       False,
       "output_4_8.root",
       "output_CRfit_4_8.root",
       "SR_2_2_prefit.root",
       "SR_6_3_prefit.root")

postFit("PR B-Only Post-Fit",
       "Postfit values for PR in the B-Only CR+SR and CR-Only fits with the prefit signal overlayed for reference",
       "Data from Figure 4 (PR)",
       "PR_Postfit_forPaper.pdf",
       False,
       "PRCRfit.root",
       "PRCR_fitCR_CR.root",
       "SR_2_2_prefit.root",
       "SR_6_3_prefit.root")

postFit("CRDY B-Only Post-Fit",
       "Postfit values for CRDY in the B-Only CR+SR and CR-Only fits with the prefit signal overlayed for reference",
       "Data from Figure 4 (CRDY)",
       "CRDY_Postfit_forPaper.pdf",
       True,
       "output_CRDY_4_8.root",
       "output_CRDY_4_8_CRfit.root",
       "CRDY_2_2_prefit.root",
       "CRDY_6_3_prefit.root")

postFit("CRTT B-Only Post-Fit",
       "Postfit values for CRTT in the B-Only CR+SR and CR-Only fits with the prefit signal overlayed for reference",
       "Data from Figure 4 (CRTT)",
       "CRTT_Postfit_forPaper.pdf",
       True,
       "output_CRTT_4_8.root",
       "output_CRTT_4_8_CRfit.root",
       "CRTT_2_2_prefit.root",
       "CRTT_6_3_prefit.root")

def signalCutflows():
    ###############################################
    # 1) Parse the three initial size files
    ###############################################
    # They each look like "Generic_1.0_0.25 - 600000"
    # We'll parse out: (mass, temp) -> initial count, keyed by decayMode in a dict.

    def parseInitialSizes(filename, decayMode):
        dataDict = {}
        # Example pattern for "Generic_1.0_0.25 - 600000"
        pattern = re.compile(rf"{decayMode}_(\d+\.\d+)_(\d+\.\d+)\s*-\s*(\d+)")

        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                match = pattern.search(line)
                if match:
                    massStr = match.group(1)
                    tempStr = match.group(2)
                    countStr = match.group(3)
                    massVal = float(massStr)
                    tempVal = float(tempStr)
                    initEvents = float(countStr)
                    dataDict[(massVal, tempVal)] = initEvents
        return dataDict

    # Gather all initial data in one dictionary
    initialData = {
        "generic":  parseInitialSizes("Generic_Sizes.txt",  "Generic"),
        "hadronic": parseInitialSizes("Hadronic_Sizes.txt", "Hadronic"),
        "leptonic": parseInitialSizes("Leptonic_Sizes.txt", "Leptonic")
    }

    ###############################################
    # 2) Parse the selection files
    ###############################################
    # Each selection file is named something like "0_generic.txt", "1_generic.txt", etc.
    # Lines look like:
    #   Signal Variant: SUEP_generic_mS125_mD1.0_T0.25, Total Histogram Size: 198197.419921875
    #
    # We'll parse out (decayMode, mass, temp, histSize).

    def parseSelectionFile(filename):
        pattern = re.compile(
            r"Signal Variant:\s+SUEP_(\w+)_mS125_mD(\d+\.\d+)_T(\d+\.\d+),\s+Total Histogram Size:\s+(\d+\.\d+)"
        )
        output = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                match = pattern.search(line)
                if match:
                    modeStr = match.group(1)
                    massStr = match.group(2)
                    tempStr = match.group(3)
                    sizeStr = match.group(4)

                    modeVal = modeStr.lower()   # "generic", "hadronic", or "leptonic"
                    massVal = float(massStr)
                    tempVal = float(tempStr)
                    histSize = float(sizeStr)
                    output.append((modeVal, massVal, tempVal, histSize))
        return output

    # We have 7 selections; rename them for clarity:
    selectionNames = [
        "twoLepton",
        "oneCluster",
        "ZM",
        "ZpT",
        "BTag",
        "SUEPpT",
        "dR"
    ]

    # Store the histogram sizes in a dict keyed by selection name and decay mode:
    # selectionData["twoLepton"]["generic"][(mass, temp)] = histSize, etc.
    selectionData = {}
    for selName in selectionNames:
        selectionData[selName] = {"generic": {}, "hadronic": {}, "leptonic": {}}

    # The actual files are named 0_generic.txt, 1_generic.txt, etc.
    for i, selName in enumerate(selectionNames):
        for decayMode in ["generic", "hadronic", "leptonic"]:
            filename = f"{i}_{decayMode}.txt"
            parsedLines = parseSelectionFile(filename)
            for (mode, mass, temp, size) in parsedLines:
                selectionData[selName][mode][(mass, temp)] = size

    ###############################################
    # 3) Compute the ratio (efficiency) for each selection
    ###############################################
    # For each row (mass, temp, mode), we compute:
    #   twoLeptonEff     = selectionData[twoLepton] / initialData
    #   oneClusterEff    = selectionData[oneCluster] / selectionData[twoLepton]
    #   ...
    #   dREff            = selectionData[dR] / selectionData[SUEPpT]
    #
    # Additionally, we add a "totalCumulativeEff" = selectionData[dR] / initialData.

    allModes  = ["generic", "hadronic", "leptonic"]
    finalRows = []  # Will hold rows of [decayMode, mass, temp, eff0, eff1, ..., eff6, totalCumulativeEff]

    # Helper for ratio, returns None if either old or new is missing
    def safeRatio(numerDict, denomDict, key):
        if key not in numerDict or key not in denomDict:
            return None
        denomVal = denomDict[key]
        if denomVal == 0:
            return None
        return numerDict[key] / denomVal

    for mode in allModes:
        for (mass, temp) in sorted(initialData[mode].keys()):
            row = [mode, mass, temp]

            # twoLepton: ratio of selectionData[twoLepton]/initialData
            effTwoLepton = safeRatio(selectionData["twoLepton"][mode], initialData[mode], (mass, temp))
            if effTwoLepton is None:
                # skip if missing
                continue
            row.append(effTwoLepton)

            # oneCluster: ratio of selectionData[oneCluster]/selectionData[twoLepton]
            effOneCluster = safeRatio(selectionData["oneCluster"][mode],
                                      selectionData["twoLepton"][mode],
                                      (mass, temp))
            row.append(effOneCluster)

            # ZM: ratio of selectionData[ZM]/selectionData[oneCluster]
            effZM = safeRatio(selectionData["ZM"][mode],
                              selectionData["oneCluster"][mode],
                              (mass, temp))
            row.append(effZM)

            # ZpT: ratio of selectionData[ZpT]/selectionData[ZM]
            effZpT = safeRatio(selectionData["ZpT"][mode],
                               selectionData["ZM"][mode],
                               (mass, temp))
            row.append(effZpT)

            # BTag: ratio of selectionData[BTag]/selectionData[ZpT]
            effBTag = safeRatio(selectionData["BTag"][mode],
                                selectionData["ZpT"][mode],
                                (mass, temp))
            row.append(effBTag)

            # SUEPpT: ratio of selectionData[SUEPpT]/selectionData[BTag]
            effSUEPpT = safeRatio(selectionData["SUEPpT"][mode],
                                  selectionData["BTag"][mode],
                                  (mass, temp))
            row.append(effSUEPpT)

            # dR: ratio of selectionData[dR]/selectionData[SUEPpT]
            effDR = safeRatio(selectionData["dR"][mode],
                              selectionData["SUEPpT"][mode],
                              (mass, temp))
            row.append(effDR)

            # Finally, the total cumulative efficiency: selectionData[dR] / initial
            totalCumulativeEff = safeRatio(selectionData["dR"][mode],
                                           initialData[mode],
                                           (mass, temp))
            row.append(totalCumulativeEff)

            finalRows.append(row)

    ###############################################
    # 4) Create a hepdata_lib table
    ###############################################
    tableEfficiency = hlib.Table("Signal Efficiency Table")
    tableEfficiency.description = (
        r"Per-selection efficiencies on Generic - $m_{A'} = 1.0\;GeV$ $BR(A' \rightarrow \pi\pi) = 1.0$"
        "\n"
        r"Hadronic - $m_{A'} = 0.7\;GeV$ and $BR(A' \rightarrow ee) = BR(A' \rightarrow \mu\mu) = 0.15$ $BR(A' \rightarrow \pi\pi) = 0.7$"
        "\n"
        r"Leptonic - $m_{A'} = 0.5\;GeV$ and $BR(A' \rightarrow ee) = BR(A' \rightarrow \mu\mu) = 0.2$ and $BR(A' \rightarrow \pi\pi) = 0.6$ samples."
        "\n"
        r"Selections: 2 OSSF leptons, one SUEP cluster, $60\leq Z_{m}\leq 120$ GeV, $p_{T}^Z\geq 25$ GeV, veto events with b-tagged jets, $p_{T}^{SUEP} > 60\;GeV$, and $dR^{Ak4}_{Ak15} < 1.5$."
        "\n"
        "Efficiencies are the ratio of the histogram size at the selection step to the previous step (except twoLepton vs. initial). The final column is the total cumulative efficiency (dR vs. initial).\n"
        "Note that these selection numbers were all calculated using samples generated with 600,000 events for each signal point considered."
    )
    tableEfficiency.location = "Signal efficiencies from internal selection studies."

    # The finalRows structure is:
    #  [
    #    [decayMode, mass, temp, effTwoLepton, effOneCluster, effZM, effZpT, effBTag, effSUEPpT, effDR, totalCumulative]
    #    ...
    #  ]

    decayModeVar = hlib.Variable("Decay Mode", is_independent=False, is_binned=False)
    mDVar        = hlib.Variable(r"$m_{D}$",   is_independent=True,  is_binned=False)
    TDVar        = hlib.Variable(r"$T$",   is_independent=True,  is_binned=False)

    # The 7 step-by-step columns:
    twoLeptonVar    = hlib.Variable("Two OSSF Lepton Efficiency",    is_independent=False, is_binned=False)
    oneClusterVar   = hlib.Variable("One Cluster Efficiency",   is_independent=False, is_binned=False)
    zMVar           = hlib.Variable("Z Mass Efficiency",           is_independent=False, is_binned=False)
    zPtVar          = hlib.Variable("Z pT Efficiency",          is_independent=False, is_binned=False)
    bTagVar         = hlib.Variable("BTag Veto Efficiency",         is_independent=False, is_binned=False)
    sUEPpTVar       = hlib.Variable("SUEP pT Efficiency",       is_independent=False, is_binned=False)
    dRVar           = hlib.Variable("dR Efficiency",           is_independent=False, is_binned=False)
    totalCumulVar   = hlib.Variable("Total Cumulative Efficiency", is_independent=False, is_binned=False)

    # Prepare lists for column values
    decayModeValues  = []
    mDValues         = []
    TDValues         = []
    twoLeptonValues  = []
    oneClusterValues = []
    zMValues         = []
    zPtValues        = []
    bTagValues       = []
    sUEPpTValues     = []
    dRValues         = []
    totalCumulValues = []

    for row in finalRows:
        # row = [mode, mass, temp, effTwoLepton, effOneCluster, effZM, effZpT, effBTag, effSUEPpT, effDR, totalCumulativeEff]
        decayMode, mass, temp = row[:3]
        effTwoLepton, effOneCluster, effZM, effZpT, effBTag, effSUEPpT, effDR, totalEff = row[3:]

        decayModeValues.append(decayMode)
        mDValues.append(mass)
        TDValues.append(temp)

        twoLeptonValues.append(effTwoLepton)
        oneClusterValues.append(effOneCluster)
        zMValues.append(effZM)
        zPtValues.append(effZpT)
        bTagValues.append(effBTag)
        sUEPpTValues.append(effSUEPpT)
        dRValues.append(effDR)
        totalCumulValues.append(totalEff)

    # Assign to hepdata_lib Variables
    decayModeVar.values = decayModeValues
    mDVar.values        = mDValues
    TDVar.values        = TDValues

    twoLeptonVar.values    = twoLeptonValues
    oneClusterVar.values   = oneClusterValues
    zMVar.values           = zMValues
    zPtVar.values          = zPtValues
    bTagVar.values         = bTagValues
    sUEPpTVar.values       = sUEPpTValues
    dRVar.values           = dRValues
    totalCumulVar.values   = totalCumulValues

    # Add them all to the table
    tableEfficiency.add_variable(decayModeVar)
    tableEfficiency.add_variable(mDVar)
    tableEfficiency.add_variable(TDVar)

    tableEfficiency.add_variable(twoLeptonVar)
    tableEfficiency.add_variable(oneClusterVar)
    tableEfficiency.add_variable(zMVar)
    tableEfficiency.add_variable(zPtVar)
    tableEfficiency.add_variable(bTagVar)
    tableEfficiency.add_variable(sUEPpTVar)
    tableEfficiency.add_variable(dRVar)
    tableEfficiency.add_variable(totalCumulVar)

    ###############################################
    # 5) Write out a Submission
    ###############################################
    submission.add_table(tableEfficiency)

signalCutflows()

#####################################################################################################################################
# WH
#####################################################################################################################################

def postFitW(title, description, location, image, input):
    
    def zero_small_values(values, uncertainties, threshold=1e-6):
        for i in range(len(values)):
            if values[i] < threshold:
                values[i] = 0.0
                uncertainties[i] = 0.0

    # open input json file
    with open(input, 'r') as f:
        infile = json.load(f)

    # --- Read Data ---
    data = infile['data']
    data_unc = infile['data_err']

    # --- Read b_SRCR and b_SRCR_Unc ---
    b_SR = infile['fit_b']
    b_SR_unc = infile['fit_b_err']

    # --- Now build the table ---
    table_postfit = hlib.Table(title)
    table_postfit.description = description
    table_postfit.location = location

    # Region Variable
    sideband = hlib.Variable(r"Region", is_independent=True, is_binned=False)
    sideband.values = infile['bins']
    table_postfit.add_variable(sideband)

    # N_tracks Variable
    ntracks = hlib.Variable(r"$n^{\mathrm{SUEP}}_{\mathrm{constituent}}$", is_independent=True, is_binned=True)
    ntracks.values = infile['bin_edges']
    table_postfit.add_variable(ntracks)

    # Sphericity Variable
    sphericity = hlib.Variable(r"$S^{\mathrm{SUEP}}_{\mathrm{boosted}}$", is_independent=False, is_binned=False)
    sphericity.values = ["0.3 - 0.4"] * 3 + ["0.4 - 0.5"] * 7 + ["0.5 - 1.0"] * 7
    table_postfit.add_variable(sphericity)

    # --- Add Background (SR+CR) ---
    b_SR_var = hlib.Variable(r"Post-fit Background", is_independent=False, is_binned=False)
    b_SR_var.values = b_SR
    b_SR_var_unc = hlib.Uncertainty("Stat. + Syst.", is_symmetric=True)
    b_SR_var_unc.values = b_SR_unc
    b_SR_var.add_uncertainty(b_SR_var_unc)
    table_postfit.add_variable(b_SR_var)

    # --- Add Data ---
    data_var = hlib.Variable(r"Data", is_independent=False, is_binned=False)
    data_var.values = data
    data_var_unc = hlib.Uncertainty("Poissonian Unc.", is_symmetric=False)
    data_var_unc.values = data_unc
    data_var.add_uncertainty(data_var_unc)
    table_postfit.add_variable(data_var)

    # Add Image
    #table_postfit.add_image(image)

    # Submit the table
    submission.add_table(table_postfit)

postFitW(
    "SR (W channel)",
    "Lorem ipsum",
    "Data from Figure N",
    '',
    "hepdata_fit_wh.json"
)

def theoryAgnosticW(title, description, location, image, input):
    
    def zero_small_values(values, uncertainties, threshold=1e-6):
        for i in range(len(values)):
            if values[i] < threshold:
                values[i] = 0.0
                uncertainties[i] = 0.0

    # open input json file
    with open(input, 'r') as f:
        infile = json.load(f)

    # --- Read Data ---
    data = infile['data']
    data_unc = infile['data_err']

    # --- Read b_SRCR and b_SRCR_Unc ---
    b_SR = infile['fit_b']
    b_SR_unc = infile['fit_b_err']

    # --- Now build the table ---
    table_postfit = hlib.Table(title)
    table_postfit.description = description
    table_postfit.location = location

    # N_tracks Variable
    ntracks = hlib.Variable(r"$n^{\mathrm{SUEP}}_{\mathrm{constituent}}$", is_independent=True, is_binned=False)
    ntracks.values = infile['bin_edges']
    table_postfit.add_variable(ntracks)

    # --- Add Background (SR+CR) ---
    b_SR_var = hlib.Variable(r"Post-fit Background", is_independent=False, is_binned=False)
    b_SR_var.values = b_SR
    b_SR_var_unc = hlib.Uncertainty("Stat. + Syst.", is_symmetric=True)
    b_SR_var_unc.values = b_SR_unc
    b_SR_var.add_uncertainty(b_SR_var_unc)
    table_postfit.add_variable(b_SR_var)

    # --- Add Data ---
    data_var = hlib.Variable(r"Data", is_independent=False, is_binned=False)
    data_var.values = data
    data_var_unc = hlib.Uncertainty("Poissonian Unc.", is_symmetric=False)
    data_var_unc.values = data_unc
    data_var.add_uncertainty(data_var_unc)
    table_postfit.add_variable(data_var)

    # Add Image
    #table_postfit.add_image(image)

    # Submit the table
    submission.add_table(table_postfit)

theoryAgnosticW(
    "Theory Agnostic Limits (W channel)",
    "Lorem ipsum",
    "Data from Figure N",
    '',
    "hepdata_agnostic_wh.json"
)

def signalCutflowsW(table_name, description, data_file_path):

    data = []
    with open('hepdata_cutflow_wh.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)

    header = data[0]
    data_values = data[1:]

    table = hlib.Table(table_name)
    table.description = description
    table.location = "Supplementary"
    table.keywords["observables"] = ["cutflow"]
    
    for i in range(len(header)):
        variable = hlib.Variable(header[i], is_independent=any([x in header[i] for x in ['$m_S$','$m_{\phi}$','$T_D$', "$m_{A'}$"]]), is_binned=False, units="")
        variable.values = [row[i] for row in data_values]
        table.add_variable(variable)

    submission.add_table(table)

signalCutflowsW(
    "Signal Cutflows (W channel)",
    "Cutflow tables for the signal selection in the W channel",
    "/home/submit/lavezzo/SUEP/CMSSW_14_1_0_pre4/src/SUEPLimits/notebook_tools/hepdata_cutflow_wh.csv"
)

## Ending
submission.create_files()
