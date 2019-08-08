from __future__ import division

import numpy as np
import uproot
import uproot_methods
import os
import re
import physt

__all__ = ['datacard', 'datagroup', "plot"]


class datagroup:
     def __init__(self, files, observable="measMET", name = "DY",
                  channel="", kfactor=1.0, ptype="background",
                  luminosity= 1.0, rebin=1, normalise=True,
                  xsections=None, mergecat=True):
          self._files  = files
          self.name    = name
          self.ptype   = ptype
          self.lumi    = luminosity
          self.xsec    = xsections
          self.outfile = None
          self.channel = channel
          self.nominal = {}
          self.systvar = set()

          for fn in self._files:
               _proc = os.path.basename(fn).replace(".root","")
               _file = uproot.open(fn)

               if not _file:
                    raise "%s is not a valid rootfile" % self._name

               _scale = 1
               if ptype.lower() != "data":
                    _scale  = self.xs_scale(ufile=_file, proc=_proc)
                    _scale *= kfactor

               histograms = None
               if isinstance(channel, str):
                    histograms = _file.allitems(
                         filterclass=lambda cls: issubclass(
                              cls, uproot_methods.classes.TH1.Methods
                         ),
                         filtername =lambda name: (
                              observable in name.decode("utf-8") and channel in name.decode("utf-8")
                         )
                    )
                    histograms.sort(reverse=True)
                    mergecat = False

               else:
                    histograms = _file.allitems(
                         filterclass=lambda cls: issubclass(
                              cls, uproot_methods.classes.TH1.Methods
                         ),
                         filtername =lambda name: (
                              observable in name.decode("utf-8") and np.any(
                                   [cat in name.decode("utf-8") for cat in channel]
                              )
                         )
                    )
                    histograms.sort(reverse=True)
                    self.channel = [
                         "cat0Jet" if "catSignal-0jet" in n else n for n in self.channel
                    ]
                    self.channel = [
                         "cat1Jet" if "catSignal-1jet" in n else n for n in self.channel
                    ]

               for name, roothist in histograms:
                    name = name.decode("utf-8")
                    name = name.replace(_proc, self.name)
                    name = name.replace(";1", "")

                    if ptype.lower() == "signal":
                         name = name.replace(self.name, "signal")
                    if "catSignal-0jet" in name:
                         name = name.replace("catSignal-0jet", "cat0Jet")
                    if "catSignal-1jet" in name:
                         name = name.replace("catSignal-1jet", "cat1Jet")

                    roothist = self.check_shape(roothist)
                    newhist = roothist.physt() * _scale
                    newhist.name = name

                    if rebin > 1:
                         newhist.merge_bins(rebin)
                    if name in self.nominal.keys():
                         self.nominal[name] += newhist
                    else:
                         self.nominal[name] = newhist

                    try:
                         self.systvar.add(re.search("sys_[\w.]+", name).group())
                    except:
                         pass

          if mergecat:
            # merging the nominal
            self.merged = {}
            for syst in self.systvar:
                m_hist = self.merge_cat(self.nominal, lambda elem: syst in elem[0])
                self.merged[m_hist[0]] = m_hist
            m_hist = self.merge_cat(self.nominal, lambda elem: "sys" not in elem[0])
            self.merged[m_hist[0]] = m_hist
          else:
            self.merged = self.nominal

     def check_shape(self, histogram):
          for ibin in range(histogram.numbins+1):
               if histogram[ibin] < 0:
                    histogram[ibin] = 0
          return histogram

     def merge_cat(self, hitograms, callback):
          filtredhist = dict()
          for (key, value) in hitograms.items():
               if callback((key, value)):
                    filtredhist[key] = value
          merged_hist = []
          merged_bins = []
          merged_cent = []
          first=True
          #return filtredhist
          iteration = sorted(
               filtredhist.items(),
               key=lambda pair: self.channel.index(pair[0].split("_")[2])
          )
          for name, h in iteration:
               if first:
                    merged_bins = h.numpy_bins
                    merged_cent = h.bin_centers
                    merged_hist = h.frequencies
                    first = False
               else:
                    merged_bins = np.concatenate(
                         [merged_bins, merged_bins[-1] - h.numpy_bins[0:1] + h.numpy_bins[1:] ]
                    )
                    merged_cent = np.concatenate([merged_cent, merged_cent[-1] + h.bin_centers])
                    merged_hist = np.concatenate([merged_hist, h.frequencies])

          cat = re.search('cat(.*)', name).group().split("_")[0]
          if len(merged_hist):
               new_hist = physt.histogram(
                    merged_cent,
                    bins=physt.binnings.NumpyBinning(merged_bins),
                    weights=merged_hist
               )
               return name.replace("_" + cat, ""), new_hist
          else:
               return

     def get(self, systvar, merged=True):
          shapeUp, shapeDown= None, None
          for n, hist in self.merged.items():
               if systvar.replace("nom","") in n and systvar=="nom":
                    return hist[1]
               elif systvar in n:
                    if "Up" in n:
                         shapeUp = hist[1]
                    if "Down" in n:
                         shapeDown= hist[1]
          return (shapeUp, shapeDown)

     def save(self, filename=None, working_dir="fitroom", force=True):
          if not filename:
               filename = "histograms-" + self.name + ".root"
               if "signal" in self.ptype:
                    filename = filename.replace(self.name, "signal")
                    self.name = self.name.replace(self.name, "signal")
          self.outfile = working_dir + "/" + filename
          if os.path.isdir(self.outfile) or force:
               fout = uproot.recreate(self.outfile, compression=uproot.ZLIB(4))
               for name, hist in self.merged.items():
                    name = name.replace("_sys", "")
                    if "data" in name:
                         name = name.replace("data", "data_obs")
                    fout[name] = uproot_methods.classes.TH1.from_numpy(hist)
               fout.close()

     def xs_scale(self, ufile, proc):
          scale = self.lumi/ufile["Runs"].array("genEventCount").sum()
          original_xsec = np.abs(ufile["Events"].array("xsecscale")[0])
          xsec  = self.xsec[proc]["xsec"]
          xsec *= self.xsec[proc]["kr"]
          xsec *= self.xsec[proc]["br"]
          xsec *= 1000.0
          assert xsec > 0, "{} has a null cross section!".format(proc)

          pos_fraction = np.mean(
               (1.0+ufile["Events"].array("xsecscale")/original_xsec)/2.0
          )
          scale *= xsec/original_xsec
          scale /= pos_fraction

          return scale



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
        value = shape.total
        self.dc_file.append("bin          {0:>10}".format(self.channel))
        self.dc_file.append("observation  {0:>10}".format(value))
        self.shape_file["data_obs"] = shape

    def add_nuisance(self, process, name, value):
        if name not in self.nuisances:
            self.nuisances[name] = {}
        self.nuisances[name][process] = value

    def add_nominal(self, process, shape):
        value = shape.total
        self.rates.append((process, value))
        self.shape_file[process] = shape

    def add_shape_nuisance(self, process, name, cardname, shape):
        nuisance = "{:<20} shape".format(cardname)
        if shape[0] is not None:
            self.add_nuisance(process, nuisance, 1.0)
            self.shape_file[process + "_" + cardname + "Up"  ] = shape[0]
            self.shape_file[process + "_" + cardname + "Down"] = shape[1]

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
