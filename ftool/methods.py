import numpy as np

def from_boost(histogram):
    import boost_histogram as hist

    out = hist.Histogram(hist.axis.Regular(10, 0.0, 1.0))
    out._fXaxis = histogram.axes.centers
    centers = histogram.axes.centers
    content = histogram.values()
    out._fSumw2 = list(histogram.variances())

    mean = histogram.sum()["value"] / histogram.size
    variance = histogram.variances()
    out._fEntries = content.sum()   # is there a #entries independent of weights?
    out._fTsumw = content.sum()
    out._fTsumw2 = histogram.sum()["variance"]
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

    #valuesarray = np.empty(len(content) + 2, dtype=content.dtype)
    #valuesarray[1:-1] = content
    #valuesarray[0] = histogram.underflow
    #valuesarray[-1] = histogram.overflow

    #out.extend(valuesarray)

    return out

