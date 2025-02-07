#Implementation of the SUEP decay in CMSSW - https://github.com/cms-sw/cmssw/blob/79a21738b3213206b3e20f8588ef3f3d455b4f62/GeneratorInterface/Pythia8Interface/plugins/SuepDecay.cc#L4
#Implementation of the SUEP shower in CMSSW - https://github.com/cms-sw/cmssw/blob/7f549d8b8d96f56e754980fc106d5fef9a04f1c4/GeneratorInterface/Pythia8Interface/src/SuepShower.cc#L18

processParameters = (
  'Check:event = off',
  'HiggsSM:all = off', 
  'HiggsSM:ffbar2HZ = on', # ZH production
  'HiggsSM:ffbar2HW = off', # WH production
  '25:m0 = {[MHIGGS]}', # Mediator is SM Higgs
  '23:onMode = off',
  '23:onIfAny = 11 13 15', #Leptonic decays
  '23:mMin = 0.1',
  '999999:all = GeneralResonance void 0 0 0 {[MDARK]} 0.001 0.0 0.0 0.0', # The dark meson definition: name, antiname, spin=2s+1 (0=undef), charge*3, color (0=single, 1=triplet, 2=octet), m0, width, mMin, mMax, tau
  '999998:all = GeneralResonance void 1 0 0 {[MPHO]} 0.001 0.0 0.0 0.0', # A dark boson which is a color triplet
  '999999:addChannel = 1 1.0 101 999998 999998 ', # First dark particle decays to a pair of the second
  {[DECAYS]}
),

UserCustomization = (
  pluginName = cms.string("SuepDecay"),
  idDark = cms.int32(999999), # pdgId of the dark meson
  idMediator = cms.int32(25), # pdgId of the mediator
  temperature = cms.double({[TEMPERATURE]}) # Temperature of the thermal distribution
)

