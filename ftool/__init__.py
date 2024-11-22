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
          shapeUp, shapeDown= None, None
          for n, hist in self.histograms.items():
               if "up" not in n and "down" not in n and systvar=="nom":
                    return hist
               elif systvar in n:
                    if "up" in n.lower():
                         shapeUp = hist
                    if "down" in n.lower() or "dn" in n.lower():
                         shapeDown= hist
          if shapeUp is None or shapeDown is None:
               raise ValueError("Could not find up and down variations for systematic %s" % systvar)
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

               if "expected" in self.name and "F_" in self.observable:
                    sum_var = 'x'
                    systs = [] 
                    ref_hist = {} # reference histogram that we use to make an ABCD prediction
                    for name in _file.keys():
                        name = name.replace(";1","")
                        ABCD_obs = self.observable.split("F_")[1]
                        if "2D" in name: continue
                        if ABCD_obs not in name: continue
                        if "up" in name.lower() or "down" in name.lower() or "Dn" in name.lower():
                            plotting_tag = "_" + name.split("_")[-1]
                            sys = name.replace(plotting_tag, "")
                            systs.append(sys)
                        else:
                            sys = ""
                            if "F_" in name: systs.append("nom")
                        if sum_var == 'x':
                            if "F_"+ABCD_obs == name: ref_hist["nom"] = _file["F_"+ABCD_obs].to_boost()
                            if "F_"+ABCD_obs+"_"+sys == name: ref_hist[sys] = _file["F_"+ABCD_obs+"_"+sys].to_boost()
                        elif sum_var == 'y': 
                            raise ValueError('ERROR: Not implemented yet!')
                        else:
                            raise ValueError('ERROR: Appropriate variable not chosen!')

                    for syst in systs:
                        name = ABCD_obs+"_"+syst
                        if sum_var == 'x':
                            newhist=ref_hist[syst].copy()
                        elif sum_var == 'y':
                            raise ValueError('ERROR: Not implemented yet!')
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
                         if ";" in name:
                              print("Found multiple versions of the same histogram. Continuing with the first one (;1), I hope it's correct.")
                              continue
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


class datacard:
     def __init__(self, name, channel="ch1", tag="."):
          self.dc_file = []
          self.name = []
          self.nsignal = 1
          self.channel = channel
          self.tag = tag
          self.dc_file.append("imax * number of categories")
          self.dc_file.append("jmax * number of samples minus one")
          self.dc_file.append("kmax * number of nuisance parameters")
          self.dc_file.append("-" * 30)

          self.shapes = []
          self.observation = []
          self.rates = []
          self.nuisances = {}
          self.extras = set()
          self.dc_name = "{}/cards-{}/shapes-{}.dat".format(self.tag, name, channel)
          if not os.path.isdir(os.path.dirname(self.dc_name)):
               os.makedirs(os.path.dirname(self.dc_name), exist_ok=True)
          self.shape_file = uproot.recreate(
               "{}/cards-{}/shapes-{}.root".format(self.tag, name, channel)
          )

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
          if 'expected' in process: 
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

     def add_9ABCD_rate_param(self, name, channel, process, era, bin_cr, region=""):
          # name rateParam bin process initial_value [min,max]
          F_bins = ["F0", "F1", "F2", "F3", "F4"]
          for bin in F_bins:
               if bin in bin_cr:
                    F_bins.remove(bin)
          template = "{name} rateParam {channel} {process} (@7*(@7+@8+@9+@10+@11)*@6*@6*@3*@3*@1*@1/(@5*@2*@0*@4*@4*@4*@4)) r_{region}crA{era},r_{region}crB{era},r_{region}crC{era},r_{region}crD{era},r_{region}crE{era},r_{region}crG{era},r_{region}crH{era},r_{bin_cr}{era},r_{region}cr{other_bin_cr}{era},r_{region}cr{other1_bin_cr}{era},r_{region}cr{other2_bin_cr}{era},r_{region}cr{other3_bin_cr}{era}"
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
               region=region
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

     def add_auto_stat(self):
          self.extras.add(
               "{} autoMCStats 0 0 1".format(self.channel)
          )

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
          logging.debug("Writing datacard to {}".format(self.dc_name))
          with open(self.dc_name, "w") as fout:
               fout.write("\n".join(self.dc_file))
