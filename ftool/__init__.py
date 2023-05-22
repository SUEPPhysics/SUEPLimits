from __future__ import division

import numpy as np
import uproot
import json
import os
import re
from . import methods
import boost_histogram as bh
from sympy import symbols, diff, sqrt

__all__ = ['datacard', 'datagroup', "plot", "methods"]

def draw_ratio(nom, uph, dwh, name):
     import matplotlib.pyplot as plt
     plt.style.use('physics.mplstyle')
     _up = uph.frequencies
     _dw = dwh.frequencies
     _nm = nom.frequencies
     x = nom.bin_centers
     plt.figure(figsize=(7,4))
     plt.title(name)
     plt.hist(
          nom.bin_centers, bins=nom.numpy_bins,
          weights=np.divide(_up-_nm, _nm, out=np.zeros_like(_up), where=_nm!=0),
          histtype="step", label="up", lw=2
     )
     plt.hist(
          nom.bin_centers, bins=nom.numpy_bins,
          weights=np.divide(_dw-_nm, _nm, out=np.zeros_like(_dw), where=_nm!=0),
          histtype="step", label="down", lw=2
     )
     plt.axhline(0, ls="--", color="black", alpha=0.5)
     plt.legend(loc="best")
     plt.xlabel("observable")
     plt.ylabel("ratio to nominal")
     #plt.ylim([-2,2])
     plt.xlim([min(nom.numpy_bins),max(nom.numpy_bins)])
     plt.savefig("plots/"+name + ".png")

class datagroup:
     def __init__(self, files, observable="SUEP_nconst_Cluster ", era = 2018,  
                  name = "QCD", channel="", kfactor=1.0, ptype="background",
                  luminosity= 1.0, rebin=1, bins=[], normalise=True,
                  xsections=None, mergecat=True, binrange=None):
          self._files  = files
          self.observable = observable
          self.era     = era
          self.name    = name
          self.ptype   = ptype
          self.lumi    = luminosity
          self.xsec    = xsections
          self.outfile = None
          self.channel = channel
          self.nominal = {}
          self.systvar = set()
          self.rebin   = rebin
          self.bins = np.array(bins).astype(np.float)
          self.binrange= binrange # dropping bins the same way as droping elements in numpy arrays a[1:3]

          for fn in self._files:
               _proc = os.path.basename(fn).replace(".root","")
               _file = uproot.open(fn)
               if not _file:
                    raise ValueError("%s is not a valid rootfile" % self.name)

               histograms = None

               _scale = 1
               #if ptype.lower() != "data":
               #    _scale = self.lumi * self.xs_scale(proc=self.name)
               #     _scale = .0001

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
                        if "up" in name:
                            sys = name.split("Cluster70_")[1]
                            systs.append(sys)
                        elif "down" in name:
                            sys = name.split("Cluster70_")[1]
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
                            newhist = self.rebin_piecewise(newhist, self.bins, 'bh')
                        
                        name = self.channel + "_" + name
                        newhist.name = name
                        if name in self.nominal.keys():
                             self.nominal[name] += newhist# * 0.0 + 1.0
                        else:
                             self.nominal[name] = newhist#  * 0.0 + 1.0

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
                            newhist = self.rebin_piecewise(newhist, self.bins, 'bh')
                        
                        name = self.channel + "_" + name
                        newhist.name = name
                        if name in self.nominal.keys():
                             self.nominal[name] += newhist
                        else:
                             self.nominal[name] = newhist

                        try:
                             self.systvar.add(re.search("sys_[\w.]+", name).group())
                        except:
                             pass

          self.merged = {}
          self.merged = {i: (i, c) for i,c  in self.nominal.items()}


     
     def check_shape(self, histogram):
          for ibin in range(histogram.numbins+1):
               if histogram[ibin] < 0:
                    histogram[ibin] = 0
          return histogram

     def get(self, systvar, merged=True):
          shapeUp, shapeDown= None, None
          for n, hist in self.merged.items():
               if "Inverted" in n: continue
               if "up" not in n and "down" not in n and systvar=="nom":
                    return hist[1]
               elif systvar in n:
                    if "up" in n:
                         shapeUp = hist[1]
                    if "down" in n:
                         shapeDown= hist[1]
          return (shapeUp, shapeDown)

     def ABCD_9regions_errorProp(self, A, B, C, D, E, F, G, H):
         """
         Does 9 region ABCD using error propagation of the statistical
         uncerantities of the regions. We need to scale histogram F or H
         by some factor 'alpha' (defined in exp). For example, for F,
         the new variance is:
         variance = F_value**2 * sigma_alpha**2 + alpha**2 * F_variance**2
         """

         # define the scaling factor function
         a, b, c, d, e, f, g, h = symbols('A B C D E F G H')
         sum_var = 'x'
         if sum_var == 'x':#currently nconst 
              exp = f * h**2 * d**2 * b**2 * g**-1 * c**-1 * a**-1 * e**-4
              SR_exp = F.copy()
              current_bins, current_edges = F.to_numpy()
         elif sum_var == 'y':#currently S1
              exp = h * d**2 * b**2 * f**2 * g**-1 * c**-1 * a**-1 * e**-4
              SR_exp = H.copy()
              current_bins, current_edges = H.to_numpy()
         # defines lists of variables (sympy symbols) and accumulators (hist.sum())
         variables = [a, b, c, d, e, f, g, h]
         accs = [A.sum(), B.sum(), C.sum(), D.sum(),
                 E.sum(), F.sum(), G.sum(), H.sum()] 
         # calculate scaling factor by substituting values of the histograms' sums for the sympy symbols
         alpha = exp.copy()
         for var, acc in zip(variables, accs):
             alpha = alpha.subs(var, acc.value)
             
         # calculate the error on the scaling factor
         variance = 0
         for var, acc in zip(variables, accs):
             der = diff(exp, var)
             var = abs(acc.variance)
             variance += der**2 * var
         for var, acc in zip(variables, accs):
             variance = variance.subs(var, acc.value)
         sigma_alpha = sqrt(variance)

         # define SR_exp and propagate the error on the scaling factor to the bin variances
         new_val = SR_exp.values() * alpha
         new_var = SR_exp.values()**2 * float(sigma_alpha)**2 + float(alpha)**2 * abs(SR_exp.variances())
         return current_bins, current_edges, new_val, new_var
     
     def rebin_piecewise(self, h_in, bins, histtype='hist'):
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

     def xs_scale(self, proc):
         xsec = 1.0
         with open(f"config/xsections_{self.era}.json") as file:
            MC_xsecs = json.load(file)
         print('PROC',proc)
         xsec  = MC_xsecs[proc]["xsec"]
         xsec *= MC_xsecs[proc]["kr"]
         xsec *= MC_xsecs[proc]["br"]
         xsec *= 1000.0
         assert xsec > 0, "{} has a null cross section!".format(proc)
         return xsec


class datacard:
     def __init__(self, name, channel="ch1"):
          self.dc_file = []
          self.name = []
          self.nsignal = 1
          self.channel = channel
          self.dc_file.append("imax * number of categories")
          self.dc_file.append("jmax * number of samples minus one")
          self.dc_file.append("kmax * number of nuisance parameters")
          self.dc_file.append("-" * 30)

          self.shapes = []
          self.observation = []
          self.rates = []
          self.nuisances = {}
          self.extras = set()
          self.dc_name = "cards-{}/shapes-{}.dat".format(name, channel)
          if not os.path.isdir(os.path.dirname(self.dc_name)):
               os.mkdir(os.path.dirname(self.dc_name))

          self.shape_file = uproot.recreate(
               "cards-{}/shapes-{}.root".format(name, channel)
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
          if process == 'expected': 
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
          template = "{name} rateParam {channel} {process} {rate}" # apply no fixed range for floating rateparam
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               rate = rate,
               # vmin = vmin, 
               # vmax = vmax
          )
          self.extras.add(template)

     def add_ABCD_rate_param(self, name, channel, process, era, F):
          # name rateParam bin process initial_value [min,max]
          rera = "r" + era
          #template = "{name} rateParam {channel} {process} @5*(@8+@9+@10)*@7*@7*@3*@3*@1*@1/(@6*@2*@0*@4*@4*@4*@4) {rera}_cat_crA,{rera}_cat_crB,{rera}_cat_crC,{rera}_cat_crD,{rera}_cat_crE,{rera}_{F},{rera}_cat_crG,{rera}_cat_crH,{rera}_Bin1crF,{rera}_Bin2crF,{rera}_Bin3crF"
          template = "{name} rateParam {channel} {process} @5*(@8+@9+@10+@11)*@7*@7*@3*@3*@1*@1/(@6*@2*@0*@4*@4*@4*@4) {rera}_cat_crA,{rera}_cat_crB,{rera}_cat_crC,{rera}_cat_crD,{rera}_cat_crE,{rera}_{F},{rera}_cat_crG,{rera}_cat_crH,{rera}_Bin1crF,{rera}_Bin2crF,{rera}_Bin3crF,{rera}_Bin4crF"
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               rera = rera,
               F = F
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
          with open(self.dc_name, "w") as fout:
               fout.write("\n".join(self.dc_file))
