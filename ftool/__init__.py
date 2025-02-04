from __future__ import division

import numpy as np
import uproot
import json
import os
import re
from . import methods
import hist
import boost_histogram as bh
import logging
import numbers
from sympy import symbols, diff, sqrt

__all__ = ['datacard', 'datagroup', "plot", "methods"]

def rebin_piecewise(h_in, bins, histtype='hist'):
     """
     Inputs:
          h : histogram
          bins: list of bins as real numbers
          histtype: one of allowed_histtypes to return

     Returns:
          h_out: a histogram of type 'histtype', rebinned according to desired bins
     """

     # only 1D hists supported for now
     if len(h_in.shape) != 1:
          raise Exception("Only 1D hists supported for now")

     # only hist and bh supported
     allowed_histtypes = ['hist', 'bh']
     if histtype not in allowed_histtypes:
          raise Exception("histtype in not in allowed_histtypes")

     # check that the bins are real numbers
     if any([x.imag != 0 for x in bins]):
          raise Exception("Only pass real-valued bins")

     # split the histogram by the bins
     # and for each bin, calculate total amount of events and variance
     z_vals, z_vars = [], []
     for iBin in range(len(bins)-1): 
          
          if histtype == 'hist':
               bin_lo = bins[iBin]*1.0j
               bin_hi = bins[iBin+1]*1.0j            
          elif histtype == 'bh':
               bin_lo = bh.loc(bins[iBin])
               bin_hi = bh.loc(bins[iBin+1])
          h_fragment = h_in[bin_lo:bin_hi]    
          z_vals.append(h_fragment.sum().value)
          z_vars.append(h_fragment.sum().variance)

     # fill the histograms
     if histtype == 'hist':
          h_out = hist.Hist(hist.axis.Variable(bins), storage=hist.storage.Weight())
          h_out[:] = np.stack([z_vals, z_vars], axis=-1)

     elif histtype == 'bh':
          h_out = bh.Histogram(bh.axis.Variable(bins), storage=bh.storage.Weight())
          h_out[:] = np.stack([z_vals, z_vars], axis=-1)

     return h_out

class datagroup:

     def __init__(self, files, observable, era, name, channel, ptype,
                  kfactor=1.0, luminosity= 1.0, rebin=1, bins=[], normalise=True, xsections=1.0):
          self._files  = files
          self.observable = observable
          self.era     = era
          self.name    = name
          self.ptype   = ptype
          self.lumi    = luminosity
          self.xsec    = xsections
          self.kfactor = kfactor
          self.outfile = None
          self.channel = channel
          self.nominal = {}
          self.systvar = set()
          self.rebin   = rebin
          self.bins = np.array(bins).astype(np.float64)
          self.normalise = normalise
          self.histograms = self.get_histograms()

     def get_histograms(self):
          pass
     
     def check_shape(self, histogram):
          for ibin in range(histogram.numbins+1):
               if histogram[ibin] < 0:
                    histogram[ibin] = 0
          return histogram

     def get(self, systvar):
          if systvar == 'nom':
               return self.histograms['nom']
          else:
               shapeUp = self.histograms[systvar + "_Up"]
               shapeDown = self.histograms[systvar + "_Down"]
               return (shapeUp, shapeDown)

     def add(self, other):
          """
          Adds a datagroup to this one. The result is stored in this object.
          """
          if not isinstance(other, datagroup):
               raise ValueError("Can only add datagroup objects")
          for key, hist in other.histograms.items():
               if key in self.histograms:
                    self.histograms[key] += hist
               else:
                    self.histograms[key] = hist
     
class ggf_datagroup(datagroup):

     def __init__(self, files, observable, era, name, channel, ptype, kfactor=1, luminosity=1, rebin=1, bins=[], normalise=True, xsections=1):
          super().__init__(files, observable, era, name, channel, ptype, kfactor, luminosity, rebin, bins, normalise, xsections)

     def get_histograms(self):

          _histograms = {}

          for fn in self._files:

               _file = uproot.open(fn)
               if not _file:
                    raise ValueError("%s is not a valid rootfile" % fn)

               _scale = 1
               if self.normalise:
                    _scale = self.lumi * self.xsec * self.kfactor

               if self.name == "expected" and "I_" in self.observable:
                    sum_var = 'x' #Change this to a y to look at the sphericity instead of nconst
                    systs = [] 
                    F = {}
                    H = {}
                    for name in _file.keys():
                        name = name.replace(";1","")
                        ABCD_obs = self.observable.split("I_")[1]
                        if "2D" in name: continue
                        if ABCD_obs not in name: continue
                        if "Inverted" in name: continue
                        if "up" in name:
                            if "Cluster70_" in name:
                                sys = name.split("Cluster70_")[1]
                            else:
                                sys = name.split("Cluster_")[1]
                            systs.append(sys)
                        elif "down" in name:
                            if "Cluster70_" in name:
                                sys = name.split("Cluster70_")[1]
                            else:
                                sys = name.split("Cluster_")[1]
                            systs.append(sys)
                        else:
                            sys = ""
                            if "I_" in name: systs.append("nom")

                        if sum_var == 'x':
                            if "F_"+ABCD_obs == name: F["nom"] = _file["F_"+ABCD_obs].to_boost()
                            if "F_"+ABCD_obs+"_"+sys == name: F[sys] = _file["F_"+ABCD_obs+"_"+sys].to_boost()

                        elif sum_var == 'y': 
                            if "H_"+ABCD_obs == name: H["nom"] = _file["H_"+ABCD_obs].to_boost()
                            if "H_"+ABCD_obs+"_"+sys == name: H[sys] = _file["H_"+ABCD_obs+"_"+sys].to_boost()
                        else:
                            raise ValueError('ERROR: Appropriate variable not chosen!')
                            
                    for syst in systs:
                        name = ABCD_obs+"_"+syst
                        if sum_var == 'x':
                            newhist=F[syst].copy()
                        elif sum_var == 'y':
                            newhist=H[syst].copy()
                        else:
                            raise ValueError('ERROR: Systematic plots not found for expected!')

                        #### merge bins
                        if self.rebin >= 1 and newhist.values().ndim == 1:#written only for 1D right now
                            newhist = newhist[::bh.rebin(self.rebin)]
                        
                        ####merge bins to specified array
                        if len(self.bins)!=0 and newhist.values().ndim == 1:#written only for 1D right now
                            newhist = rebin_piecewise(newhist, self.bins, 'bh')
                        
                        name = self.channel + "_" + name
                        newhist.name = name
                        if name in _histograms.keys():
                             _histograms[name] += newhist# * 0.0 + 1.0
                        else:
                             _histograms[name] = newhist#  * 0.0 + 1.0

                        try:
                             self.systvar.add(re.search("sys_[\w.]+", name).group())
                        except:
                             pass

               else:
                    for name in _file.keys():
                        name = name.replace(";1", "")
                        if self.observable not in name: continue
                        roothist = _file[name]
                        newhist = roothist.to_boost() * _scale
                    
                        #### merge bins
                        if self.rebin >= 1 and newhist.values().ndim == 1:#written only for 1D right now
                            newhist = newhist[::bh.rebin(self.rebin)]
                        
                        ####merge bins to specified array
                        if len(self.bins)!=0 and newhist.values().ndim == 1:#written only for 1D right now
                            newhist = rebin_piecewise(newhist, self.bins, 'bh')
                        
                        name = self.channel + "_" + name
                        newhist.name = name
                        if name in _histograms.keys():
                             _histograms[name] += newhist
                        else:
                             _histograms[name] = newhist

                        try:
                             self.systvar.add(re.search("sys_[\w.]+", name).group())
                        except:
                             pass
                        
          return _histograms
     

class wh_datagroup(datagroup):

     def __init__(self, files, observable, era, name, channel, ptype, kfactor=1, luminosity=1, rebin=1, bins=[], normalise=True, xsections=1, variations={}):
          self.variations = variations
          super().__init__(files, observable, era, name, channel, ptype, kfactor, luminosity, rebin, bins, normalise, xsections)

     def store_hist(self, _file, in_name: str, _histograms: dict, _out_name: str, _scale: float = 1) -> None:

          if self.normalise:
               _scale *= self.lumi * self.xsec * self.kfactor

          try:
               roothist = _file[in_name]
               newhist = roothist.to_boost() * _scale
          except uproot.exceptions.KeyInFileError:
               print("I am a silly little histogram: {in_name} in channel {channel}".format(in_name=in_name, channel=self.channel))
               newhist = hist.Hist.new.Reg(100,0,100).Weight()

          #### merge bins
          if self.rebin >= 1 and newhist.values().ndim == 1:#written only for 1D right now
               newhist = newhist[::bh.rebin(self.rebin)]

          ####merge bins to specified array
          if len(self.bins)!=0 and newhist.values().ndim == 1:#written only for 1D right now
               newhist = rebin_piecewise(newhist, self.bins, 'bh')

          newhist.name = _out_name
          if _out_name in _histograms.keys():
               _histograms[_out_name] += newhist
          else:
               _histograms[_out_name] = newhist

     def get_histograms(self):

          _histograms = {}

          for fn in self._files:

               _file = uproot.open(fn)
               if not _file:
                    raise ValueError("%s is not a valid rootfile" % fn)

               self.store_hist(_file, self.observable, _histograms, 'nom')

               for var_name, var in self.variations.items():

                    if type(var) is list and len(var) == 2:

                         self.store_hist(_file, self.observable + "_" + var[0], _histograms, var_name + "_Up")
                         self.store_hist(_file, self.observable + "_" + var[1], _histograms, var_name + "_Down")

                    if isinstance(var, numbers.Number):

                         self.store_hist(_file, self.observable, _histograms, var_name + "_Up", var)
                         self.store_hist(_file, self.observable, _histograms, var_name + "_Down", 1/var)
                        
          return _histograms
     

class datacard:
     def __init__(self, name, channel="ch1", tag=".", analysis="CMS", dcname=''):
          self.dc_file = []
          self.name = []
          self.nsignal = 1
          self.channel = channel
          self.tag = tag
          self.analysis = analysis
          self.dc_file.append("imax * number of categories")
          self.dc_file.append("jmax * number of samples minus one")
          self.dc_file.append("kmax * number of nuisance parameters")
          self.dc_file.append("-" * 30)

          self.shapes = []
          self.observation = []
          self.rates = []
          self.nuisances = {}
          self.extras = set()
          base_dc_name = dcname if dcname != '' else "{}/cards-{}/shapes-{}".format(self.tag, name, channel)
          self.dc_name = base_dc_name + ".dat"
          if not os.path.isdir(os.path.dirname(self.dc_name)):
               os.makedirs(os.path.dirname(self.dc_name), exist_ok=True)
          self.shape_file = uproot.recreate(
               bsae_dc_name + ".root"
          )
          self.do_manualMCstats = []

     def shapes_headers(self):
          filename = self.dc_name.replace("dat", "root")
          lines = "shapes * * {file:<20} $PROCESS $PROCESS_$SYSTEMATIC"
          lines = lines.format(file = os.path.basename(filename))
          self.dc_file.append(lines)

     def add_observation(self, shape):
          value = shape.sum()
          self.dc_file.append("bin          {0:>10}".format(self.channel))
          self.dc_file.append("observation  {0:>10}".format(value["value"]))
          self.shape_file["data_obs"] = shape

     def add_nuisance(self, process, name, value):
          if name not in self.nuisances:
               self.nuisances[name] = {}
          self.nuisances[name][process] = value

     def add_nominal(self, process, channel,  shape):
          if 'bkg' in process: 
               shape = shape * 0.0 + 1.0#values will come from rate_params
               shape.view().variance = shape.variances() * 0.0
          value = shape.values(flow=False).sum()
          self.rates.append((process, value))
          self.shape_file[process] = shape
          self.nominal_hist = shape

     def add_shape_nuisance(self, process, cardname, shape, symmetric=False):
          nuisance = "{:<20} shape".format(cardname)          

          if shape[0] is not None:
               
               if symmetric: # apply a symmetric variation to up using nominal and down
                
                    h_down = shape[1] #Taking down variation
                    h_nom = self.nominal_hist
                    
                    h_up = bh.Histogram(bh.axis.Variable(h_nom.to_numpy()[1]), storage=bh.storage.Weight())
                    h_up_vals = 2*h_nom.values() - h_down.values() # Calculate a symmetric variation
                    h_up_vals = np.where(h_up_vals<=0.0, 0.0, h_up_vals) # Set potentially negative counts (if h_down>2*h_up) to 0
                    h_up_vars = h_down.variances() 
                    h_up[:] = np.stack([h_up_vals, h_up_vars], axis=-1) 
                    
                    shape = (h_up, h_down)

          if shape[1].values().sum() != 0 and shape[0].values().sum() != 0:
                    
               self.add_nuisance(process, nuisance, 1.0)
               self.shape_file[process + "_" + cardname + "Up"  ] = shape[0]
               self.shape_file[process + "_" + cardname + "Down"] = shape[1]

     def add_rate_param(self, name, channel, process, rate=1.0, vmin=0.1, vmax=10):
          # name rateParam bin process initial_value [min,max]
          template = "{name} rateParam {channel} {process} {rate} [{vmin},{vmax}]" # take large interval s.t. rateparam is essentially floating
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               rate = rate,
               vmin = vmin, 
               vmax = vmax
          )
          self.extras.add(template)
     
     def add_ABCD_rate_param(self, name, channel, process, era, F):
          # name rateParam bin process initial_value [min,max]
          rera = "r" + era
          template = "{name} rateParam {channel} {process} @5*(@8+@9+@10+@11+@12)*@7*@7*@3*@3*@1*@1/(@6*@2*@0*@4*@4*@4*@4) {rera}_cat_crA,{rera}_cat_crB,{rera}_cat_crC,{rera}_cat_crD,{rera}_cat_crE,{rera}_{F},{rera}_cat_crG,{rera}_cat_crH,{rera}_Bin1crF,{rera}_Bin2crF,{rera}_Bin3crF,{rera}_Bin4crF,{rera}_Bin0crF"
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               rera = rera,
               F = F
          )
          self.extras.add(template)

     def add_9ABCD_rate_param(self, name, channel, process, bin_cr, region="SR", era=""):
          # name rateParam bin process initial_value [min,max]
          F_bins = ["F_Fbin0", "F_Fbin1", "F_Fbin2", "F_Fbin3", "F_Fbin4"]
          for bin in F_bins:
               if bin in bin_cr:
                    F_bins.remove(bin)
          template = "{name} rateParam {channel} {process} (@7*(@7+@8+@9+@10+@11)*@6*@6*@3*@3*@1*@1/(@5*@2*@0*@4*@4*@4*@4)) {analysis}_{region}_A{era},{analysis}_{region}_B{era},{analysis}_{region}_C{era},{analysis}_{region}_D{era},{analysis}_{region}_E{era},{analysis}_{region}_G{era},{analysis}_{region}_H{era},{analysis}_{bin_cr}{era},{analysis}_{region}_{other_bin_cr}{era},{analysis}_{region}_{other1_bin_cr}{era},{analysis}_{region}_{other2_bin_cr}{era},{analysis}_{region}_{other3_bin_cr}{era}"
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               era = era,
               bin_cr = bin_cr,
               other_bin_cr = F_bins[0],
               other1_bin_cr = F_bins[1],
               other2_bin_cr = F_bins[2],
               other3_bin_cr = F_bins[3],
               region=region,
               analysis=self.analysis
          )
          self.extras.add(template)

     def add_9ABCD_rate_param_eras_combined(self, name, channel, process, eras, bin_cr, region=""):
          # name rateParam bin process initial_value [min,max]
          F_bins = ["F0", "F1", "F2", "F3", "F4"]
          for bin in F_bins:
               if bin in bin_cr:
                    F_bins.remove(bin)
          template = "{name} rateParam {channel} {process} ((@7+@19+@31)*((@7+@19+@31)+(@8+@20+@32)+(@9+@21+@33)+(@10+@22+@34)+(@11+@23+@35))*(@6+@18+@30)*(@6+@18+@30)*(@3+@15+@27)*(@3+@15+@27)*(@1+@13+@25)*(@1+@13+@25)/((@5+@17+@29)*(@2+@14+@26)*(@0+@12+@24)*(@4+@16+@28)*(@4+@16+@28)*(@4+@16+@28)*(@4+@16+@28))) {rate_params}"
          rate_params_template = "r_{region}crA{era},r_{region}crB{era},r_{region}crC{era},r_{region}crD{era},r_{region}crE{era},r_{region}crG{era},r_{region}crH{era},r_{bin_cr}{era},r_{region}cr{other_bin_cr}{era},r_{region}cr{other1_bin_cr}{era},r_{region}cr{other2_bin_cr}{era},r_{region}cr{other3_bin_cr}{era}"
          rate_params = []
          for era in eras:
               rate_params.append(rate_params_template.format(
                    region=region,
                    era=era,
                    bin_cr=bin_cr,
                    other_bin_cr=F_bins[0],
                    other1_bin_cr=F_bins[1],
                    other2_bin_cr=F_bins[2],
                    other3_bin_cr=F_bins[3]
               ))
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               era = era,
               bin_cr = bin_cr,
               other_bin_cr = F_bins[0],
               other1_bin_cr = F_bins[1],
               other2_bin_cr = F_bins[2],
               other3_bin_cr = F_bins[3],
               region=region,
               rate_params=",".join(rate_params)
          )
          self.extras.add(template)

     def add_6ABCD_rate_param(self, name, channel, process, era, bin_cr, region=""):
          """
          This function assumes the following form of ABCD regions:

          |  B  |  D  |  F  
          + ----+-----+----
          |  A  |  C  |  E
          + ----+-----+----

          And calculates:
          F^{pred}_i = D_i * (D_0+D_1+D_2+D_3+D_4) * E * A / (B * C * C)
          """
          # name rateParam bin process initial_value [min,max]
          rera = "r" + era
          template = "{name} rateParam {channel} {process} @3*(@4+@5+@6+@7+@8)*@9*@0/(@1*@2*@2) {rera}_{region}crA,{rera}_{region}crB,{rera}_{region}crC,{rera}_{bin_cr},{rera}_{region}crD0,{rera}_{region}crD1,{rera}_{region}crD2,{rera}_{region}crD3,{rera}_{region}crD4,{rera}_{region}crE"
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               rera = rera,
               bin_cr = bin_cr,
               region=region
          )
          self.extras.add(template)

     def add_manual_MCstats(self, process):
          """
          Declare that a process should have a manual MC stats uncertainty added.
          The actual adding of MC stats to the card is done after all processes are added.
          """
          self.do_manualMCstats += [process]

     def _add_manual_MCstats(self, process):
          """
          Add gamma uncertainty to account for poor MC stats for a process.
          For non-zero yields, we extract the raw count and scale factor from the shape histogram.
          (This is an approximation, and is not valid for histograms with events with large weights.)
          For zero yields, don't include a systematic.
          """
          line = "{analysis}_statSignal_{bin} gmN {prologue} {raw_count} {scale_factor} {epilogue}"
          shape = self.shape_file[process]
          if len(shape.values()) > 1: raise ValueError("Written to support only one bin.")
          val = shape.values()[0]
          var = shape.variances()[0]
          
          if var == 0:
               return
          else:
               raw_count = ((val**2) / var) # raw_count = ( raw_count * scale_factor )**2 / ( sqrt(raw_count) * scale_factor )**2
               scale_factor = val / raw_count # scale_factor = raw_count * scale_factor / raw_count
               raw_count = max(round(raw_count), 0)
               scale_factor = round(scale_factor, 5)
          logging.info("Adding manualMCStats for process: " + process + " with raw_count: " +  str(raw_count) + " and scale_factor: " + str(scale_factor))
     
          prologue, epilogue = "", ""
          found_process = False
          for iprocess, _ in self.rates:
               if iprocess == process: 
                    found_process = True
                    continue
               if not found_process: prologue += " - "
               if found_process: epilogue += " - "

          line = line.format(analysis=self.analysis, bin=self.channel, raw_count=raw_count, scale_factor=scale_factor, prologue=prologue, epilogue=epilogue)
          self.dc_file.append(line)

     def dump(self):
          # adding shapes
          for line in self.shapes:
               self.dc_file.append(line)
          self.dc_file.append("-"*30)
          # adding observation
          for line in self.observation:
               self.dc_file.append(line)
          self.dc_file.append("-"*30)
          # bin lines
          bins_line = "{0:<8}".format("bin")
          proc_line = "{0:<8}".format("process")
          indx_line = "{0:<8}".format("process")
          rate_line = "{0:<8}".format("rate")
          for i, tup in enumerate(self.rates):
               bins_line += "{0:>15}".format(self.channel)
               proc_line += "{0:>15}".format(tup[0])
               if self.process_indx_map:
                    indx_line += "{0:>15}".format(self.process_indx_map[tup[0]])
               else:
                    indx_line += "{0:>15}".format(i - self.nsignal + 1)
               rate_line += "{0:>15}".format("%.3f" % tup[1])
          self.dc_file.append(bins_line)
          self.dc_file.append(proc_line)
          self.dc_file.append(indx_line)
          self.dc_file.append(rate_line)
          self.dc_file.append("-"*30)
          for nuisance in sorted(self.nuisances.keys()):
               scale = self.nuisances[nuisance]
               line_ = "{0:<8}".format(nuisance)
               for process, _ in self.rates:
                    if process in scale:
                         line_ += "{0:>15}".format("%.3f" % scale[process])
                    else:
                         line_ += "{0:>15}".format("-")
               self.dc_file.append(line_)
          self.dc_file += self.extras
          for process, _ in self.rates:
               if process in self.do_manualMCstats:
                    self._add_manual_MCstats(process)
          logging.debug("Writing datacard to {}".format(self.dc_name))
          with open(self.dc_name, "w") as fout:
               fout.write("\n".join(self.dc_file))
