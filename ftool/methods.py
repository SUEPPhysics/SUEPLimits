import numpy as np
import uproot
import uproot3_methods as uproot_methods

def from_physt(histogram):
    import physt.binnings
    import physt.histogram1d

    class TH1(uproot_methods.classes.TH1.Methods, list):
        pass

    class TAxis(object):
        def __init__(self, fNbins, fXmin, fXmax):
            self._fNbins = fNbins
            self._fXmin = fXmin
            self._fXmax = fXmax

    out = TH1.__new__(TH1)

    if isinstance(histogram.binning, physt.binnings.FixedWidthBinning):
        out._fXaxis = TAxis(histogram.binning.bin_count,
                            histogram.binning.first_edge,
                            histogram.binning.last_edge)
    elif isinstance(histogram.binning, physt.binnings.NumpyBinning):
        out._fXaxis = TAxis(histogram.binning.bin_count,
                            histogram.binning.first_edge,
                            histogram.binning.last_edge)
        out._fXaxis._fXbins = histogram.binning.numpy_bins.astype(">f8")
    else:
        raise NotImplementedError(histogram.binning)

    centers = histogram.bin_centers
    content = histogram.frequencies

    out._fSumw2 = [0] + list(histogram.errors2) + [0]

    mean = histogram.mean()
    variance = histogram.variance()
    out._fEntries = content.sum()   # is there a #entries independent of weights?
    out._fTsumw = content.sum()
    out._fTsumw2 = histogram.errors2.sum()
    if mean is None:
        out._fTsumwx = (content * centers).sum()
    else:
        out._fTsumwx = mean * out._fTsumw
    if mean is None or variance is None:
        out._fTsumwx2 = (content * centers**2).sum()
    else:
        out._fTsumwx2 = (mean**2 + variance) * out._fTsumw2

    if histogram.name is not None:
        out._fTitle = histogram.name
    else:
        out._fTitle = b""

    out._classname, content = uproot_methods.classes.TH1._histtype(content)

    valuesarray = np.empty(len(content) + 2, dtype=content.dtype)
    valuesarray[1:-1] = content
    valuesarray[0] = histogram.underflow
    valuesarray[-1] = histogram.overflow

    out.extend(valuesarray)

    return out
