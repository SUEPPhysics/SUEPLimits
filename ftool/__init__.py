from __future__ import division

import numpy as np
import uproot
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
     def __init__(self, files, observable="SUEP_nconst_Cluster ", name = "QCD",
                  channel="", kfactor=1.0, ptype="background",
                  luminosity= 1.0, rebin=1, bins=[], normalise=True,
                  xsections=None, mergecat=True, binrange=None):
          self._files  = files
          self.observable = observable
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
               if ptype.lower() != "data":
                   _scale = self.lumi* 1000.0 #

               if self.name == "expected":
                    systs = [] 
                    A = {}
                    B = {}
                    C = {}
                    D = {}
                    E = {}
                    F = {}
                    G = {}
                    H = {}
                    for name in _file.keys():
                        name = name.replace(";1", "")
                        ABCD_obs = self.observable.split("I_")[1]
                        if "2D" in name: continue
                        if ABCD_obs not in name: continue
                        if "up" in name:
                            sys = name.split("Cluster_")[1]
                            systs.append(sys)
                        elif "down" in name: 
                            sys = name.split("Cluster_")[1]
                            systs.append(sys)
                        else: 
                            sys = ""
                            if "I_" in name: systs.append("nom")

                        if "A_"+ABCD_obs == name: A["nom"] = _file["A_"+ABCD_obs].to_boost()
                        if "B_"+ABCD_obs == name: B["nom"] = _file["B_"+ABCD_obs].to_boost()
                        if "C_"+ABCD_obs == name: C["nom"] = _file["C_"+ABCD_obs].to_boost()
                        if "D_"+ABCD_obs == name: D["nom"] = _file["D_"+ABCD_obs].to_boost()
                        if "E_"+ABCD_obs == name: E["nom"] = _file["E_"+ABCD_obs].to_boost()
                        if "F_"+ABCD_obs == name: F["nom"] = _file["F_"+ABCD_obs].to_boost()
                        if "G_"+ABCD_obs == name: G["nom"] = _file["G_"+ABCD_obs].to_boost()
                        if "H_"+ABCD_obs == name: H["nom"] = _file["H_"+ABCD_obs].to_boost()
                        
                        if "A_"+ABCD_obs+"_"+sys == name: A[sys] = _file["A_"+ABCD_obs+"_"+sys].to_boost()
                        if "B_"+ABCD_obs+"_"+sys == name: B[sys] = _file["B_"+ABCD_obs+"_"+sys].to_boost()
                        if "C_"+ABCD_obs+"_"+sys == name: C[sys] = _file["C_"+ABCD_obs+"_"+sys].to_boost()
                        if "D_"+ABCD_obs+"_"+sys == name: D[sys] = _file["D_"+ABCD_obs+"_"+sys].to_boost()
                        if "E_"+ABCD_obs+"_"+sys == name: E[sys] = _file["E_"+ABCD_obs+"_"+sys].to_boost()
                        if "F_"+ABCD_obs+"_"+sys == name: F[sys] = _file["F_"+ABCD_obs+"_"+sys].to_boost()
                        if "G_"+ABCD_obs+"_"+sys == name: G[sys] = _file["G_"+ABCD_obs+"_"+sys].to_boost()
                        if "H_"+ABCD_obs+"_"+sys == name: H[sys] = _file["H_"+ABCD_obs+"_"+sys].to_boost()

                    for syst in systs:
                        name = ABCD_obs+"_"+syst
                        current_bins, current_edges, exp_freq, exp_var = self.ABCD_9regions_errorProp(A=A[syst],B=B[syst],C=C[syst],D=D[syst],E=E[syst],F=F[syst],G=G[syst],H=H[syst])
                        newhist = bh.Histogram(bh.axis.Variable(current_edges),storage=bh.storage.Weight())
                        newhist[:] = np.stack([exp_freq, exp_var], axis=-1)

                        #### merge bins
                        if self.rebin >= 1 and newhist.values().ndim == 1:#written only for 1D right now
                            newhist = newhist[::bh.rebin(self.rebin)]
                        
                        ####merge bins to specified array
                        if len(self.bins)!=0 and newhist.values().ndim == 1:#written only for 1D right now
                            newhist = self.rebin_piecewise(newhist, self.bins, 'bh')
                        
                        newhist.name = name
                        if name in self.nominal.keys():
                             self.nominal[name] += newhist
                        else:
                             self.nominal[name] = newhist

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

     def add_nominal(self, process, shape):
          value = shape.sum()["value"]
          self.rates.append((process, value))
          self.shape_file[process] = shape
          self.nominal_hist = shape

     def add_qcd_scales(self, process, cardname, qcd_scales):
          nuisance = "{:<20} shape".format(cardname)
          if isinstance(qcd_scales, list):
               shapes = []
               for sh in qcd_scales:
                    uncert_up = np.abs(self.nominal_hist - sh[0])
                    uncert_dw = np.abs(self.nominal_hist - sh[1])
                    
                    var_up = np.divide(
                        uncert_up, self.nominal_hist.frequencies, 
                        out=np.zeros_like(uncert_up), 
                        where=self.nominal_hist.frequencies!=0
                    )
                    var_dw = np.divide(
                        uncert_dw, self.nominal_hist.frequencies, 
                        out=np.zeros_like(uncert_up), 
                        where=self.nominal_hist.frequencies!=0
                    )
                    uncert_up[var_up >= 0.95] = 0 
                    uncert_dw[var_dw >= 0.95] = 0 
                    
                    uncert = np.maximum(uncert_up,uncert_dw)
                    
                    uncert_r =  np.divide(
                        uncert, self.nominal_hist.frequencies, 
                        out=np.zeros_like(uncert)*-1, 
                        where=self.nominal_hist.frequencies!=0
                    )
                    shapes.append(uncert)
               shapes = np.array(shapes)
               uncert = shapes.max(axis=0)
               #h_uncert = physt.histogram1d.Histogram1D(
               #     self.nominal_hist.binning, uncert,
               #     errors2=np.zeros_like(uncert)
               #)
               shape = (self.nominal_hist - uncert, self.nominal_hist + uncert)
               self.add_nuisance(process, nuisance, 1.0)
               self.shape_file[process + "_" + cardname + "Up"  ] = shape[0]
               self.shape_file[process + "_" + cardname + "Down"] = shape[1]
          else:
               raise ValueError("add_qcd_scales: the qcd_scales should be a list!")

     def add_custom_shape_nuisance(self, process, cardname, range, vmin=0.1, vmax=10):
        nuisance = "{:<20} shape".format(cardname)
        hist_up = self.nominal_hist.copy()
        hist_dw = self.nominal_hist.copy()
        #making range of values to edit histogram
        mask = lambda h: (h.bin_right_edges> range[0]) & ((h.bin_right_edges<=range[1]))
        hist_up.frequencies[mask(hist_up)] = hist_up.frequencies[mask(hist_up)] * vmin
        hist_dw.frequencies[mask(hist_dw)] = hist_dw.frequencies[mask(hist_dw)] * vmax
        self.add_nuisance(process, nuisance, 1.0)
        
        self.shape_file[process + "_" + cardname + "Up"  ] = hist_up
        self.shape_file[process + "_" + cardname + "Down"] = hist_dw
                
     def add_shape_nuisance(self, process, cardname, shape, symmetric=False):
          nuisance = "{:<20} shape".format(cardname)
          print('add shape nuisance test')
          

          if shape[0] is not None:
          # and (
          #           (shape[0].values()[shape[0].values()>0].shape[0]) and
          #           (shape[1].values()[shape[1].values()>0].shape[0])
          # ): # Why do we veto these empty histograms for up or down variations? 
               print('add shape nuisance test 2')

               if symmetric: # apply a symmetric variation to up using nominal and down
                
                    h_down = shape[1] #Taking down variation
                    h_nom = self.nominal_hist
                    
                    h_up = bh.Histogram(bh.axis.Variable(h_nom.to_numpy()[1]), storage=bh.storage.Weight())
                    h_up_vals = 2*h_nom.values() - h_down.values() # Calculate a symmetric variation
                    h_up_vals = np.where(h_up_vals<0, 0, h_up_vals) # Set potentially negative counts (if h_down>2*h_up) to 0
                    h_up_vars = h_down.variances() 
                    h_up[:] = np.stack([h_up_vals, h_up_vars], axis=-1) 
                    
                    shape = (h_up, h_down)
                    
               self.add_nuisance(process, nuisance, 1.0)
               self.shape_file[process + "_" + cardname + "Up"  ] = shape[0]
               self.shape_file[process + "_" + cardname + "Down"] = shape[1]

     def add_rate_param(self, name, channel, process, vmin=0.1, vmax=10):
          # name rateParam bin process initial_value [min,max]
          template = "{name} rateParam {channel} {process} 1 [{vmin},{vmax}]"
          template = template.format(
               name = name,
               channel = channel,
               process = process,
               vmin = vmin,
               vmax = vmax
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
