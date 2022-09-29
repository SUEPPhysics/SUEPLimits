from __future__ import division

import numpy as np
import uproot
import os
import re
from . import methods
import boost_histogram as bh

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
                  luminosity= 1.0, rebin=1, rebin_piecewise=[], normalise=True,
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
          self.rebin_piecewise = np.array(rebin_piecewise).astype(np.float)
          self.binrange= binrange # dropping bins the same way as droping elements in numpy arrays a[1:3]

          for fn in self._files:
               _proc = os.path.basename(fn).replace(".root","")
               _file = uproot.open(fn)

               if not _file:
                    raise ValueError("%s is not a valid rootfile" % self.name)

               histograms = None

               _scale = 1
               print(self.name,ptype)
               if ptype.lower() != "data":
                    _scale = self.lumi* 1000.0 #

               if self.name == "expected":
                    systs = [] 
                    A = B = C = D = E = F = G = H = {}
                    for name in _file.keys():
                        name = name.replace(";1", "")
                        ABCD_obs = self.observable.split("I_")[1]
                        if "UP" in name: continue
                        if "DOWN" in name: continue
                        if "JEC" in name: continue
                        if "2D" in name: continue
                        if ABCD_obs not in name: continue
                        if "up" in name:
                            sys = name.split("Cluster_")[1]
                            systs.append(sys)
                        elif "down" in name: 
                            sys = name.split("Cluster_")[1]
                            systs.append(sys)
                        else: #continue 
                            sys = ""
                            systs.append("nom")


                        if "A_"+ABCD_obs == name: A["nom"] = _file["A_"+ABCD_obs].to_boost()
                        if "B_"+ABCD_obs == name: B["nom"] = _file["B_"+ABCD_obs].to_boost()
                        if "C_"+ABCD_obs == name: C["nom"] = _file["C_"+ABCD_obs].to_boost()
                        if "D_"+ABCD_obs == name: D["nom"] = _file["D_"+ABCD_obs].to_boost()
                        if "E_"+ABCD_obs == name: E["nom"] = _file["E_"+ABCD_obs].to_boost()
                        if "F_"+ABCD_obs == name: F["nom"] = _file["F_"+ABCD_obs].to_boost()
                        if "G_"+ABCD_obs == name: G["nom"] = _file["G_"+ABCD_obs].to_boost()
                        if "H_"+ABCD_obs == name: H["nom"] = _file["H_"+ABCD_obs].to_boost()

                        if "A_"+ABCD_obs+"_"+sys in name: A[sys] = _file["A_"+ABCD_obs+"_"+sys].to_boost()
                        if "B_"+ABCD_obs+"_"+sys in name: B[sys] = _file["B_"+ABCD_obs+"_"+sys].to_boost()                      
                        if "C_"+ABCD_obs+"_"+sys in name: C[sys] = _file["C_"+ABCD_obs+"_"+sys].to_boost()
                        if "D_"+ABCD_obs+"_"+sys in name: D[sys] = _file["D_"+ABCD_obs+"_"+sys].to_boost()
                        if "E_"+ABCD_obs+"_"+sys in name: E[sys] = _file["E_"+ABCD_obs+"_"+sys].to_boost()
                        if "F_"+ABCD_obs+"_"+sys in name: F[sys] = _file["F_"+ABCD_obs+"_"+sys].to_boost()
                        if "G_"+ABCD_obs+"_"+sys in name: G[sys] = _file["G_"+ABCD_obs+"_"+sys].to_boost()
                        if "H_"+ABCD_obs+"_"+sys in name: H[sys] = _file["H_"+ABCD_obs+"_"+sys].to_boost()

                    for syst in systs:
                        name = ABCD_obs+"_"+syst
                        current_bins, current_edges = F[syst].to_numpy()
                        exp_freq = F[syst].values() #* F[syst].values().sum()**3 * (G[syst].values().sum() * C[syst].values().sum() / A[syst].values().sum()) * \
                                 #((H[syst].values().sum() / E[syst].values().sum())**4) \
                                 #* (G[syst].values().sum() * F[syst].values().sum() / D[syst].values().sum())**-2 \
                                 #* (H[syst].values().sum() * C[syst].values().sum() / B[syst].values().sum())**-2
                        exp_var = F[syst].variances()
                        newhist = bh.Histogram(bh.axis.Variable(current_edges),storage=bh.storage.Weight())
                        newhist[:] = np.stack([exp_freq, exp_var], axis=-1)

                        #### merge bins
                        if self.rebin >= 1 and newhist.values().ndim == 1:#written only for 1D right now
                            newhist = newhist[::bh.rebin(self.rebin)]
                        
                        ####merge bins to specified array
                        if len(self.rebin_piecewise)!=0 and newhist.values().ndim == 1:#written only for 1D right now
                             current_bins, current_edges = newhist.to_numpy()
                             #current_bins = newhist.axes.edges #Confused Chad. This returns a 'boost_histogram.axis.ArrayTuple' which cannot be cast into np,array?
                             new_freq = self.rebin_piecewise_constant(current_edges, newhist.values(), self.rebin_piecewise)
                             new_variances = self.rebin_piecewise_constant(current_bins, newhist.variances(), self.rebin_piecewise)
                             newhist = bh.Histogram(bh.axis.Variable(self.rebin_piecewise),storage=bh.storage.Weight())
                             newhist[:] = np.stack([new_freq, new_variances], axis=-1)
                        
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
                        if len(self.rebin_piecewise)!=0 and newhist.values().ndim == 1:#written only for 1D right now
                             current_bins, current_edges = newhist.to_numpy()
                             #current_bins = newhist.axes.edges #Confused Chad. This returns a 'boost_histogram.axis.ArrayTuple' which cannot be cast into np,array?
                             new_freq = self.rebin_piecewise_constant(current_edges, newhist.values(), self.rebin_piecewise)
                             new_variances = self.rebin_piecewise_constant(current_bins, newhist.variances(), self.rebin_piecewise)
                             newhist = bh.Histogram(bh.axis.Variable(self.rebin_piecewise),storage=bh.storage.Weight())
                             newhist[:] = np.stack([new_freq, new_variances], axis=-1)
                        
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
               if "trackUP" in n: continue #Remove after Luca fix
               if "trackDOWN" in n: continue #Remove after Luca fix
               if "JEC" in n: continue
               if "up" not in n and "down" not in n and systvar=="nom":
                    return hist[1]
               elif systvar in n:
                    if "up" in n:
                         shapeUp = hist[1]
                    if "down" in n:
                         shapeDown= hist[1]
          return (shapeUp, shapeDown)

     
     #for rebinning to new array. see: https://github.com/jhykes/rebin (rebin.py) 
     def rebin_piecewise_constant(self,x1, y1, x2):
          x1 = np.asarray(x1)
          y1 = np.asarray(y1)
          x2 = np.asarray(x2)

          # the fractional bin locations of the new bins in the old bins
          i_place = np.interp(x2, x1, np.arange(len(x1)))
          cum_sum = np.r_[[0], np.cumsum(y1)]
            
          # calculate bins where lower and upper bin edges span
          # greater than or equal to one original bin.
          # This is the contribution from the 'intact' bins (not including the
          # fractional start and end parts.
          whole_bins = np.floor(i_place[1:]) - np.ceil(i_place[:-1]) >= 1.
          start = cum_sum[np.ceil(i_place[:-1]).astype(int)]
          finish = cum_sum[np.floor(i_place[1:]).astype(int)]
          y2 = np.where(whole_bins, finish - start, 0.)
          bin_loc = np.clip(np.floor(i_place).astype(int), 0, len(y1) - 1)
        
          # fractional contribution for bins where the new bin edges are in the same
          # original bin.
          same_cell = np.floor(i_place[1:]) == np.floor(i_place[:-1])
          frac = i_place[1:] - i_place[:-1]
          contrib = (frac * y1[bin_loc[:-1]])
          y2 += np.where(same_cell, contrib, 0.)
        
          # fractional contribution for bins where the left and right bin edges are in
          # different original bins.
          different_cell = np.floor(i_place[1:]) > np.floor(i_place[:-1])
          frac_left = np.ceil(i_place[:-1]) - i_place[:-1]
          contrib = (frac_left * y1[bin_loc[:-1]])
          frac_right = i_place[1:] - np.floor(i_place[1:])
          contrib += (frac_right * y1[bin_loc[1:]])
          y2 += np.where(different_cell, contrib, 0.)
        
          return y2


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
  
     def add_shape_nuisance(self, process, cardname, shape, symmetrise=False):
          nuisance = "{:<20} shape".format(cardname)
          if shape[0] is not None and (
                    (shape[0].values()[shape[0].values()>0].shape[0]) and
                    (shape[1].values()[shape[1].values()>0].shape[0])
          ):
               if shape[0] == shape[1]:
                    shape = (2 * self.nominal_hist - shape[0], shape[1])
               if symmetrise: 
                    uncert = np.maximum(np.abs(self.nominal_hist - shape[0]), 
                                        np.abs(self.nominal_hist - shape[1]))
                    shape = (self.nominal_hist - uncert, self.nominal_hist + uncert)
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
