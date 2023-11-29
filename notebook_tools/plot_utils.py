import matplotlib.pyplot as plt
import numpy as np
import glob
import re
import os
import uproot
from scipy import interpolate
import json
import pandas as pd
import math
from matplotlib import ticker
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.legend_handler import HandlerLine2D
import mplhep as hep
from scipy.ndimage import gaussian_filter1d

np.seterr(divide='ignore', invalid='ignore')

decaysLabels = {
    'hadronic' : r"$A^' \rightarrow e^{+}e^{-}$ ($15\%$), $\mu^{+}\mu^{-}$ ($15\%$), $\pi^{+}\pi^{-}$ ($70\%$)",
    'leptonic' : r"$A^' \rightarrow e^{+}e^{-}$ ($40\%$), $\mu^{+}\mu^{-}$ ($40\%$), $\pi^{+}\pi^{-}$ ($20\%$)",
    'generic' : r"$A^' \rightarrow \pi^{+}\pi^{-}$ ($100\%$) "
}
decaysColors = {
    'generic': 'black',
    'hadronic': 'red',
    'leptonic': 'blue'
}
decaysMarkers = {
    'generic': 'o',
    'leptonic': 's',
    'hadronic': '^'
}

lumis = {
    2016 : 36.3, #36.308
    2017 : 41.5, #41.471 
    2018 : 59.8, #59.817
    'combined' : round(59.8+41.5+ 36.3)
}


def get_limits(fn): # Returns quantile vs limits
    f = uproot.open(fn)
    limit = f["limit"]['limit'].array(library="np")
    quant = f["limit"]['quantileExpected'].array(library="np")
    return np.stack([quant,limit]) 

def get_SUEP_file(ms=125, mphi=2, temp=1, decay='generic', path="../", method='AsymptoticLimits', quant=""): # Returns filename
    if temp < 10:
        tem = "{0:.2f}".format(temp)
    else:
        tem = "{0:.1f}".format(temp)
    tem = str(tem).replace(".","p")
    fname = os.path.join(
        "{}higgsCombineGluGluToSUEP_HT1000_T{}_mS{:.3f}_mPhi{:.3f}_T{:.3f}_mode{}_TuneCP5_13TeV-pythia8.{}.mH125{}.root".format(path, tem, ms, mphi, temp, decay, method, quant)
    )
    if os.path.isfile(fname):
        return fname
    else:
        print(f"WARNING: No file {fname} found.")
        return None


def xs_scale(proc, file="../config/xsections_SUEP.json"):
    xsec = -1.0
    with open(file) as file:
        MC_xsecs = json.load(file)
    xsec  = MC_xsecs[proc]["xsec"]
    # xsec *= MC_xsecs[proc]["kr"] # this is fine commented out!
    # xsec *= MC_xsecs[proc]["br"] # this is fine commented out!
    assert xsec > 0, "{} has a null cross section!".format(proc)
    return xsec


def log_interp1d(xx, yy, kind='linear'):
    logx = np.log(xx)
    logy = np.log(yy)
    lin_interp = interpolate.interp1d(logx, logy, bounds_error=False, fill_value="extrapolate", kind=kind)
    log_interp = lambda zz: np.power(np.e, lin_interp(np.log(zz)))
    return log_interp


def interp_limit(limit, sigma=3):
    x, y = limit.T
    t  = np.linspace(0, 1, len(x))
    t2 = np.linspace(-0.9, 1.2, 100)

    x2 = np.interp(t2, t, x)
    y2 = np.interp(t2, t, y)
    
    x3 = gaussian_filter1d(x2, sigma)
    y3 = gaussian_filter1d(y2, sigma)
    x4 = np.interp(t, t2, x3)
    y4 = np.interp(t, t2, y3)

    return x3, y3


def get_params_from_sample_name(sample):
    pattern = r'_T(\d+p?\d*)_mS(\d+\.\d+)_mPhi(\d+\.\d+)_T(\d+\.\d+)_mode(\w+)_TuneCP5'

    # Use re.search to find the first occurrence of the pattern in the sample name
    match = re.search(pattern, sample)

    if match:
        # Extract the matched groups and convert them to the appropriate data types
        temp = float(match.group(1).replace('p','.'))
        mS = float(match.group(2))
        mPhi = float(match.group(3))
        decay = match.group(5)

        # Return the extracted parameters as a tuple
        return mS, mPhi, temp, decay
    else:
        # Return None if no match is found
        return None
    

def get_sample_name_from_params(ms, mphi, temp, decay):
    temp_p = temp
    if temp_p > 10:
        temp_p = "{temp:.1f}".format(temp=temp_p).replace(".","p")
    else:
        temp_p = "{temp:.2f}".format(temp=temp_p).replace(".","p")
    return f"GluGluToSUEP_HT1000_T{temp_p}_mS{ms:.3f}_mPhi{mphi:.3f}_T{temp:.3f}_mode{decay}_TuneCP5_13TeV-pythia8"


def filter_samples(ms=None, mphi=None, temp=None, decay=None, file='../config/xsections_SUEP.json'):
    """
    Get all possible combinations of parmaters from the full sample list.
    """
    
    # load in all the samples that should exist
    with open(file) as json_file:
        samples = list(json.load(json_file).keys())

    # filter them by the parameters you want
    combinations = []
    for sample in samples:
        _ms, _mphi, _temp, _decay = get_params_from_sample_name(sample) 
        if ms is not None and ms != _ms: continue
        if mphi is not None and mphi != _mphi: continue
        if temp is not None and temp != _temp: continue
        if decay is not None and decay != _decay: continue
        if [_ms, _mphi, _temp, _decay] not in combinations:
            combinations.append([_ms, _mphi, _temp, _decay])

    return combinations


def get_unique_combinations(variables: list, ms=None, mphi=None, temp=None, decay=None,
                            file='../config/xsections_SUEP.json'):
    """
    From the full sample list, return a list of possible combinations of parameters.
    For each variable specified in 'variables', the list of combinations will be integrated over that variable.
    For each variable specificed as ms, mphi, temp, decay, that variable will be fixed to the value specified.

    Returns: [(mS, mPhi, Temp, decay),...] integrated over the variables specified.
    """
    lower_variables = [v.lower() for v in variables]
    integrate_ms, integrate_mphi, integrate_temp, integrate_decay = False, False, False, False
    if 'ms' in lower_variables: integrate_ms = True
    if 'mphi' in lower_variables: integrate_mphi = True
    if 'temp' in lower_variables: integrate_temp = True
    if 'decay' in lower_variables: integrate_decay = True

    combinations = filter_samples(file=file, ms=ms, mphi=mphi, temp=temp, decay=decay)

    unique_combinations = []
    for c in combinations:
        this = []
        if not integrate_ms: this.append(c[0])
        if not integrate_mphi: this.append(c[1])
        if not integrate_temp: this.append(c[2])
        if not integrate_decay: this.append(c[3])
        if this not in unique_combinations: unique_combinations.append(this)

    return unique_combinations
        

def get_scan_limits(ms=None, mphi=None, temp=None, decay=None, path="../", file='../config/xsections_SUEP.json', method='AsymptoticLimits'):
    """
    Get all existing limits for a given set of parameters.
    Leave a parameter blank as None to get all possible values for that parameter.

    returns: list of lists of parameters [[ms, mphi, temp, decay, xsec], [quant, limit]]
    """

    selected_params = filter_samples(ms=ms, mphi=mphi, temp=temp, decay=decay, file=file)

    # add the xsec to the list
    for i in range(len(selected_params)):
        p = selected_params[i]
        sample_name = get_sample_name_from_params(p[0], p[1], p[2], p[3])
        xsec = xs_scale(sample_name, file=file)
        selected_params[i] = p + [xsec]

    # check if combine produced the 5 expected limits
    good_selected_params = []

    for sample in selected_params:
        try:
            if method == 'AsymptoticLimits':
                limit = get_limits(get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method))
            elif method == 'HybridNew':
                exp = get_limits(get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method, quant='.quant0.500'))
                s1p = get_limits(get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method, quant='.quant0.840'))
                s1m = get_limits(get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method, quant='.quant0.160'))
                s2p = get_limits(get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method, quant='.quant0.975'))
                s2m = get_limits(get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method, quant='.quant0.025'))
                obs = get_limits(get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method, quant=''))
                limit = np.hstack((s2p, s1p, exp, s1m, s2m, obs))
            if limit.shape == (2,6):
                limit[1,:] *= sample[4] # scale the r limit by the theoretical xsec to get limit on xsec
                good_selected_params.append([sample, limit])
            else:
                print('Bad limits', get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method))
        except Exception as e:
            print(e)
            print("File doesn't exit", get_SUEP_file(path=path, ms=sample[0], mphi=sample[1], temp=sample[2], decay=sample[3], method=method))

    return good_selected_params

def savefig(fig, outDir, outName=None):
    """
    Saves a matplotlib figure as png and pdf.
    """
    if outName is None:
        outName = fig.get_label()
    fig.savefig(outDir + outName + '.pdf', bbox_inches='tight')
    fig.savefig(outDir + outName + '.png', dpi=100, bbox_inches='tight')

def plot_ms_limits(temp, mphi, decay, path='../', verbose=False, method='AsymptoticLimits'):
    """
    Make 1D Brazil plot for some choice of mPhi, temp, and decay, scanning over mS.
    """
    
    limits = get_scan_limits(path=path, temp=temp, mphi=mphi, decay=decay, method=method)
    masses = np.array([l[0][0] for l in limits])
    xsec = np.array([l[0][4] for l in limits])

    _exp = np.array([l[1][1][2] for l in limits])
    _s1p = np.array([l[1][1][1] for l in limits]) 
    _s1m = np.array([l[1][1][3] for l in limits]) 
    _s2p = np.array([l[1][1][0] for l in limits]) 
    _s2m = np.array([l[1][1][4] for l in limits]) 
    _obs = np.array([l[1][1][5] for l in limits])    
    
    # Define interpolation
    exp_limit = log_interp1d(masses, _exp) 
    s1p_limit = log_interp1d(masses, _s1p)
    s1m_limit = log_interp1d(masses, _s1m)
    s2p_limit = log_interp1d(masses, _s2p)
    s2m_limit = log_interp1d(masses, _s2m)
    obs_limit = log_interp1d(masses, _obs)
    th_limit =  log_interp1d(masses, xsec)
    
    if verbose:
        sorted_masses = np.array(masses)[np.argsort(masses)]
        sorted_obs = np.array(_obs)[np.argsort(masses)]
        sorted_exp = np.array(_exp)[np.argsort(masses)]
        for mS, obs, exp in zip(sorted_masses, sorted_obs, sorted_exp):
            # print the first 5 digits after the decimal of the obs, exp
            print("{} {:.5g} {:.5g}".format(mS, obs, exp))

    # Make 1D limit plot
    fig = plt.figure(figsize=(10,10))
    ax = fig.subplots()
        
    xvar = np.linspace(100,2050,1000)

    # Plot observed limits
    ax.plot(masses, _obs,'.', ms=12, color='black', label="Observed") 
    ax.plot(xvar,obs_limit(xvar), #*.101,#* 0.101* 2/3,
             "-", ms=12, color='black')
    
    #Plot expected limits including brazil bands
    ax.plot(xvar,th_limit(xvar), #*.101,#* 0.101* 2/3,
         "--", ms=12, color='blue', label="$\sigma_{theory}$")
    ax.plot(xvar, exp_limit(xvar), ls="--", ms=12, color='black', label="Median expected")
    ax.fill_between(xvar, s2m_limit(xvar), s2p_limit(xvar), color="#FFCC01", lw=0, label="Expected 95% CL")
    ax.fill_between(xvar, s1m_limit(xvar), s1p_limit(xvar), color="#00CC00", lw=0, label="Expected 68% CL")
    
    # Just to make everything look nice
    ax.set_ylabel(r"$\sigma$ (pb)")
    ax.set_xlabel(r"$m_{S}$ (GeV)") 
    ax.legend(loc="upper left", fontsize=20)

    _ = ax.text(
        0.65, 0.75, r"$T_D$ = {} GeV""\n""$m_{{\phi}}$ = {} GeV""\n""{}".format(temp,mphi,decaysLabels[decay]),
        fontsize=25, horizontalalignment='left', 
        verticalalignment='bottom', 
        transform=ax.transAxes,
    )
    
    hep.cms.label(llabel='Preliminary', data=False, lumi=lumis['combined'], ax=ax) # To add CMS lumi scripts

    ax.grid(visible=True, which='major', color='grey', linestyle='--', alpha=0.3)
    ax.set_ylim(1e-6,9e7)
    ax.set_yscale("log")
    
    y_major = ticker.LogLocator(base = 10.0, numticks = 20)
    ax.yaxis.set_major_locator(y_major)
    y_minor = ticker.LogLocator(base = 10.0, subs = np.arange(1.0, 10.0) * 0.1, numticks = 100)
    ax.yaxis.set_minor_locator(y_minor)
    ax.yaxis.set_minor_formatter(ticker.NullFormatter())
    fig.tight_layout()

    fig.set_label("limits1D_T{:.1f}_mphi{:.1f}_{}".format(temp,mphi, decay))

    return fig

def plot_ms_limits_all_decays(temp, mphi, ref_decay='generic', path='../', verbose=False, method='AsymptoticLimits'):
    """
    Make 1D Brazil plot for some choice of mPhi, temp, and decay, scanning over mS.
    """
    
    all_decays = [c[0] for c in get_unique_combinations(['ms','mphi','temp'])]
    # make sure the ref_decay is first
    all_decays = sorted(all_decays, key=lambda x: x != ref_decay)
    
    fig = plt.figure(figsize=(10,10))
    ax = fig.subplots()
    
    xvar = np.linspace(125,2000,1000)
        
    legend_objects, legend_labels = [], []
    for decay in all_decays:
                
        limits = get_scan_limits(path=path, temp=temp, mphi=mphi, decay=decay, method=method)
                
        masses = np.array([l[0][0] for l in limits])
        xsec = np.array([l[0][4] for l in limits])

        _exp = np.array([l[1][1][2] for l in limits])
        _s1p = np.array([l[1][1][1] for l in limits]) 
        _s1m = np.array([l[1][1][3] for l in limits]) 
        _s2p = np.array([l[1][1][0] for l in limits]) 
        _s2m = np.array([l[1][1][4] for l in limits]) 
        _obs = np.array([l[1][1][5] for l in limits])    
        
        # Define interpolation
        exp_limit = log_interp1d(masses, _exp) 
        s1p_limit = log_interp1d(masses, _s1p)
        s1m_limit = log_interp1d(masses, _s1m)
        s2p_limit = log_interp1d(masses, _s2p)
        s2m_limit = log_interp1d(masses, _s2m)
        obs_limit = log_interp1d(masses, _obs)
        th_limit =  log_interp1d(masses, xsec)
        
        if decay == ref_decay:
            _theoryline, = ax.plot(xvar,th_limit(xvar), "--", ms=12, color='magenta')
            legend_objects.append(_theoryline)
            legend_labels.append("$\sigma_{theory}$")
    
        if verbose:
            sorted_masses = np.array(masses)[np.argsort(masses)]
            sorted_obs = np.array(_obs)[np.argsort(masses)]
            sorted_exp = np.array(_exp)[np.argsort(masses)]
            sorted_s1p = np.array(_s1p)[np.argsort(masses)]
            sorted_s1m = np.array(_s1m)[np.argsort(masses)]
            sorted_s2p = np.array(_s2p)[np.argsort(masses)]
            sorted_s2m = np.array(_s2m)[np.argsort(masses)]
            from prettytable import PrettyTable
            x = PrettyTable()
            x.field_names = ["mS", "Obs", "-2 Sigma", "-1 Sigma", "Exp", "+1 Sigma", "+2 Sigma"]
            x.add_rows(np.stack([sorted_masses, sorted_obs, sorted_s2m, sorted_s1m, sorted_exp, sorted_s1p, sorted_s2p]).T)
            x.float_format = '.7'
            print(x)
            
        # Plot observed limits
        _marker, = ax.plot(masses, _obs,marker=decaysMarkers[decay], ms=10, ls='none', color=decaysColors[decay]) 
        _line, = ax.plot(xvar, obs_limit(xvar), "-", ms=12, color=decaysColors[decay])
        _expline, = ax.plot(xvar, exp_limit(xvar), ls="--", ms=12, color=decaysColors[decay])
        _label, = ax.plot(0,0,ls='none',color='white')
        
        legend_objects += [_label, (_marker, _line), _expline]
        legend_labels += [decaysLabels[decay], "Observed", "Median expected"]
    
        if decay == ref_decay:
            _s2line = ax.fill_between(xvar, s2m_limit(xvar), s2p_limit(xvar), color="#FFCC01", lw=0)
            _s1line = ax.fill_between(xvar, s1m_limit(xvar), s1p_limit(xvar), color="#00CC00", lw=0)
            legend_objects += [_s2line, _s1line]
            legend_labels += ["Expected 95% CL", "Expected 68% CL"]

    ax.set_ylabel(r"$\sigma$ (pb)")
    ax.set_xlabel(r"$m_{S}$ (GeV)") 
    leg = ax.legend(legend_objects, legend_labels, handler_map = {legend_objects[0] : HandlerLine2D(marker_pad = 0)}, 
           loc=(0.35, 0.4), fontsize=18)
    #ax.legend(loc="upper right", fontsize=12)
    
    for item, label in zip(leg.legendHandles, leg.texts):
        if "rightarrow" in label._text:
            width=item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            # label.set_position((-4*width,0))
            label.set_position((-1.5*width,0))

    _ = ax.text(
        0.05, 0.8, r"$T_D$ = {} GeV""\n""$m_{{\phi}}$ = {} GeV""\n".format(temp,mphi),
        fontsize=25, horizontalalignment='left', 
        verticalalignment='bottom', 
        transform=ax.transAxes,
    )

    hep.cms.label(llabel='Preliminary', data=False, lumi=lumis['combined'], ax=ax) # To add CMS lumi scripts

    ax.grid(visible=True, which='major', color='grey', linestyle='--', alpha=0.3)
    ax.set_ylim(1e-6,9e7)
    ax.set_yscale("log")

    y_major = ticker.LogLocator(base = 10.0, numticks = 20)
    ax.yaxis.set_major_locator(y_major)
    y_minor = ticker.LogLocator(base = 10.0, subs = np.arange(1.0, 10.0) * 0.1, numticks = 100)
    ax.yaxis.set_minor_locator(y_minor)
    ax.yaxis.set_minor_formatter(ticker.NullFormatter())
    fig.tight_layout()
    
    fig.set_label("limits1D_T{:.1f}_mphi{:.1f}".format(temp,mphi))

    return fig

def plot_mPhi_temp_limits(ms:int, decay:str, path:str, tricontour:str ='log', calculateWithoutPlotting=False, showPoints=False, method='AsymptoticLimits'): 
    """
    Make 2D limit plot for some choice of mS and decay, scanning over T and mPhi.
    Inputs:
        mS: scalar mass
        decay: decay channel
        path: path to the directory containing the higgsCombined files
        tricontour: 'log' or 'lin' to interpolate through log(mu) or mu
        calculateWithoutPlotting: if True, the function returns the interpolated limits without plotting them
        showPoints: shows were the actual samples are
    Outputs:
        fig: figure object
    """
    
    if tricontour not in ['log','lin']: #tricontour decides whether we interpolate through mu ('lin') or log(mu) ('log')
        raise Exception("tricontour should be 'log' or 'lin'")

    scan_limits = get_scan_limits(path=path, ms=ms, decay=decay, method=method)
        
    # Reorganize data
    if calculateWithoutPlotting: limit_mu = np.stack([s[1]/s[0][-1] for s in scan_limits]) 
    else: limit_mu = np.stack([s[1] for s in scan_limits]) 
    limit_mphi = np.array([s[0][1] for s in scan_limits]) 
    limit_temp =  np.array([s[0][2] for s in scan_limits])

    if tricontour == 'log':
        limit_mu[:,1,:]= np.log10(limit_mu[:,1,:]) # Convert mu to logarithm of mu 
    
    data = pd.DataFrame(
        {
            "mH"  : np.array(limit_temp),
            "ma"  : np.array(limit_mphi),
            "m2s" : np.array(limit_mu)[:,1,0],
            "m1s" : np.array(limit_mu)[:,1,1],
            "exp" : np.array(limit_mu)[:,1,2],
            "p1s" : np.array(limit_mu)[:,1,3],
            "p2s" : np.array(limit_mu)[:,1,4],
            "obs" : np.array(limit_mu)[:,1,5],
        }
    )
    
    # Plot figure and obtain mu=1 (log(mu)=0) lines
    fig = plt.figure(figsize=(10,10))
    ax = fig.subplots()
    
    if tricontour == 'log':
        levels = np.linspace(min(data['obs']),max(data['obs']))
        contour = ax.tricontourf(limit_mphi, limit_temp, data['obs'], levels =levels, cmap="plasma")
        cb = fig.colorbar(contour)
        cb.ax.set_ylabel(r'$95\%$ CL obs. upper limit on $\sigma$ (pb)', loc='top', rotation=90, fontsize=25)
        ticks = (np.array(range(math.ceil(min(data['obs'])), math.floor(max(data['obs'])) + 1)))
        cb.set_ticks(ticks)
        labels = ['$10^{'+str(i)+'}$' for i in ticks]
        cb.set_ticklabels(labels)      

    if tricontour == 'lin':
        levels = np.logspace(np.log10(min(data['obs'])),np.log10(max(data['obs'])))
        x = ax.tricontourf(limit_mphi, limit_temp, data['obs'], levels =levels,locator=ticker.LogLocator(), cmap="plasma")
        formatter = ticker.LogFormatter(base=10, labelOnlyBase=True) 
        cb = fig.colorbar(x, format=formatter, label=r'$\mu$')
        cb.ax.set_ylabel(r'$95\%$ CL obs. upper limit on $\sigma$ (pb)', loc='top', rotation=90, fontsize=25)
        cb.locator = ticker.LogLocator(base=10.0, subs=[1.0], numdecs=7, numticks=45)
        cb.update_ticks()
     
    # Obtain values for expected mu=1 line
    
    # NOTE: suppressing +- 2 sigma (p0 and p4)
    # p0 = ax.tricontour(limit_mphi, limit_temp, limit_mu[:,1,0],levels=[0,1], colors="k", alpha=0) # -2 sigma expected
    p1 = ax.tricontour(limit_mphi, limit_temp, limit_mu[:,1,1],levels=[0,1],   colors="k", alpha=0) # -1 sigma expected
    p2 = ax.tricontour(limit_mphi, limit_temp, limit_mu[:,1,2],levels=[0,1],   colors="k", alpha=0) # median expected
    p3 = ax.tricontour(limit_mphi, limit_temp, limit_mu[:,1,3],levels=[0,1],  colors="k", alpha=0) # +1 sigma expected
    # p4 = ax.tricontour(limit_mphi, limit_temp, limit_mu[:,1,4],levels=[0,1],  colors="k", alpha=0) # +2 sigma expected
    p5 = ax.tricontour(limit_mphi, limit_temp, limit_mu[:,1,5],levels=[0,1],  colors="k", alpha=0) # observed

    if showPoints:
        ax.scatter(limit_mphi, limit_temp, marker='o', color='black', label='Signal point', s=10)
    
    if tricontour == 'log': x=0
    if tricontour == 'lin': x=1 
    # line0 = np.array(p0.collections[x].get_paths()[0].vertices)
    line1 = np.array(p1.collections[x].get_paths()[0].vertices)
    line2 = np.array(p2.collections[x].get_paths()[0].vertices)
    line3 = np.array(p3.collections[x].get_paths()[0].vertices)
    # line4 = np.array(p4.collections[x].get_paths()[0].vertices)
    line5 = np.array(p5.collections[x].get_paths()[0].vertices)

    if calculateWithoutPlotting:
        plt.close()
        return line1, line2, line3, line5

    #plot smoothed curve
    ax.plot(*line2.T, linestyle = "--", color ='red' , label=r"Median expected",linewidth =4)
    ax.plot(*line1.T,linestyle = "--", color='#00ffff', label=r"Expected $68\%$ CL",linewidth =4)
    ax.plot(*line3.T, linestyle = "--", color='#00ffff', linewidth =4)
    ax.plot(*line5.T, linestyle = "-", color='#00008b', label=r"Observed",linewidth =4)
        
    ax.set_xlabel(r"$m_{\phi}$ (GeV)", x=1, ha='right')
    ax.set_ylabel(r"$T_D$ (GeV)", y=1, ha='right')
    
    hep.cms.label(llabel='Preliminary', data=True, lumi=lumis['combined'], ax=ax) # To add CMS lumi scripts
    
    _ = ax.text(
        0.05, 0.85, r"$m_{{s}} = {}$ GeV""\n""{}".format(str(ms), decaysLabels[decay]),
        fontsize=20, horizontalalignment='left', 
        verticalalignment='bottom', 
        transform=ax.transAxes
    )
    
    ax.set_xlim([1, 8.5])
    ax.set_ylim([0, 35])     
    ax.legend(loc="upper right", fontsize=20)
    fig.tight_layout()
    
    fig.set_label("limits2D_mS{:.1f}_{}".format(ms, decay))
     
    return fig


def plot_summary_limits_mPhi_temp(decay, path='../', method='AsymptoticLimits'):
    
    samples = get_unique_combinations(['mphi', 'temp'], decay=decay)
    
    # sort by mS
    samples = np.array(samples)[np.argsort([s[0] for s in samples])]
            
    lines = []
    for sample in samples:
        lines.append(plot_mPhi_temp_limits(ms=float(sample[0]), decay=decay, 
                                    tricontour='log', path=path,
                                    calculateWithoutPlotting=True, method=method)) 
    # Define colours
    cmap = plt.cm.jet
    colors = cmap(np.linspace(0, 1, len(lines)))

    # Plot mu=1 lines 
    fig = plt.figure(figsize=(16,9))
    ax = fig.subplots()
    
    mA = {'leptonic':0.5,'hadronic':0.7,'generic':1.0}
    x=np.array([2*mA[decay],8])

    legend_elements = []
    legend_labels = []
    legend_elements.append(Line2D([0],[0], linestyle = '-',c='black'))
    legend_labels.append('Observed')
    legend_elements.append(Line2D([0],[0], linestyle = '-',c='white'))
    legend_labels.append('Expected (median, 68%):')
    for i, line in enumerate(lines):
        line1,line2,line3,line5 = line
        x1,y1 = interp_limit(line1, 4) 
        x2,y2 = interp_limit(line2, 4)
        x3,y3 = interp_limit(line3, 4)
        x5,y5 = interp_limit(line5, 4)

        _expline, = ax.plot(x2,y2, linestyle = '--', lw=2, c=colors[i])
        ax.plot(x5,y5, linestyle = '-',c='black')

        y1_interp = np.interp(x2, x1, y1)
        y3_interp = np.interp(x2, x3, y3)
        
        upper_bound = np.minimum(x2*4, y1_interp)
        
        band = ax.fill_between(x2, y3_interp, upper_bound, color=colors[i],alpha=0.2)
        legend_elements.append((mpatches.Patch(facecolor=colors[i], alpha=0.2), _expline))
        legend_labels.append('$m_{{S}}$ = {} GeV'.format(round(float(samples[i][0]))))

    # Annotate figure
    ax.set_xlabel(r"$m_{\phi}$ (GeV)", x=1, ha='right')
    ax.set_ylabel(r"$T_D$ (GeV)", y=1, ha='right')
    hep.cms.label(llabel='Preliminary', data=False, lumi=lumis['combined'], ax=ax) # To add CMS lumi scripts
    ax.text(7.7, 14, decaysLabels[decay], horizontalalignment='right', verticalalignment='center',fontsize=18)

    # Plot theoretically excluded regions
    ax.plot(x, [4 * xi for xi in x], '--',color='black')
    ax.plot(x, [0.25 * xi for xi in x], '--',color='black')
    ax.plot([2*mA[decay]]*50, np.linspace(0.5,15,50),color='black',marker=(1,2,45),markersize =20, alpha =0.5)
    ax.plot([8]*50, np.linspace(0.5,15,50),color='black',marker=(1,2,-135),markersize =30, alpha =0.5)
    ax.text(8.4, 5, 'few hard tracks', horizontalalignment='right', verticalalignment='center',fontsize=16,rotation=-90)
    ax.text(2*mA[decay]-0.15, 5, r"$m_{\phi}<2m_{A^'}$", horizontalalignment='right', verticalalignment='center',fontsize=20,rotation=-90)
    ax.text(3, 11.5, r'$T_D/m_{\phi}=4$', horizontalalignment='right', verticalalignment='center',fontsize=20,rotation =55)
    ax.text(6, 0.75, r'$T_D/m_{\phi}=0.25$', horizontalalignment='right', verticalalignment='center',fontsize=20,rotation =6)

    ax.set_xlim([2*mA[decay]-0.6, 12])
    ax.set_ylim([0.0, 15])
    
    leg = ax.legend(legend_elements, legend_labels, loc=(0.70, 0.05), fontsize=20, handler_map = {legend_elements[0] : HandlerLine2D(marker_pad = 0)})
    
    for item, label in zip(leg.legendHandles, leg.texts):
        if "Expected" in label._text:
            width=item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            label.set_position((-1.5*width,0))
    
    fig.tight_layout()
    
    fig.set_label('limits3D_{}'.format(decay))

    return fig


def plot_xsec_limits(mphi:int, decay:str, path:str, tricontour:str ='log', calculateWithoutPlotting:bool=False):
    
    if tricontour not in ['log','lin']: #tricontour decides whether we interpolate through mu ('lin') or log(mu) ('log')
        raise Exception("tricontour should be 'log' or 'lin'")
    
    scan_limits = get_scan_limits(path=path, mphi=mphi, decay=decay)
    
    # Reorganize data
    limit_mu = np.stack([s[1]/s[0][-1] for s in scan_limits]) 
    limit_xs = np.array([s[0][-1] for s in scan_limits]) 
    limit_ms = np.array([s[0][0] for s in scan_limits]) 
    limit_temp =  np.array([s[0][2] for s in scan_limits])
    
    if tricontour == 'log':
        limit_mu[:,1,:]= np.log10(limit_mu[:,1,:]) # Convert mu to logarithm of mu 
    
    data = pd.DataFrame(
        {
            "mH"  : np.array(limit_temp),
            "ma"  : np.array(limit_ms),
            "m2s" : np.array(limit_mu)[:,1,0],
            "m1s" : np.array(limit_mu)[:,1,1],
            "exp" : np.array(limit_mu)[:,1,2],
            "p1s" : np.array(limit_mu)[:,1,3],
            "p2s" : np.array(limit_mu)[:,1,4],
            "obs" : np.array(limit_mu)[:,1,5],
            "xsec_obs": np.array(limit_mu)[:,1,5]+np.log10(limit_xs)
        }
    )    
   
    # Plot figure and obtain mu=1 (log(mu)=0) lines
    fig = plt.figure(figsize=(10,10))
    ax = fig.subplots()

    if tricontour == 'log':
        levels = np.linspace(min(data['xsec_obs']),max(data['xsec_obs']))
        contour = ax.tricontourf(limit_ms, limit_temp, data['xsec_obs'], levels =levels, cmap="Wistia")
        #get the colorbar right
        cb = fig.colorbar(contour)
        cb.ax.set_ylabel(r'$\sigma_{excluded}$ (pb)', loc='center', rotation=90, fontsize=20)
        ticks = (np.array(range(math.ceil(min(data['xsec_obs'])), math.floor(max(data['xsec_obs'])) + 1)))
        cb.set_ticks(ticks)
        labels = ['$10^{'+str(i)+'}$' for i in ticks]
        cb.set_ticklabels(labels)      

        
    if tricontour == 'lin':
        levels = np.logspace(np.log10(min(data['obs'])),np.log10(max(data['obs'])))
        x = ax.tricontourf(limit_ms, limit_temp, data['obs'], levels =levels,locator=ticker.LogLocator(), cmap="Wistia")
        formatter = ticker.LogFormatter(base=10, labelOnlyBase=True) 
        cb = fig.colorbar(format=formatter, label=r'$\mu$')
        cb.ax.set_ylabel(r'$\sigma_{excluded}$ (pb)', loc='center', rotation=90, fontsize=20)
        cb.locator = ticker.LogLocator(base=10.0, subs=[1.0], numdecs=7, numticks=45)
        cb.update_ticks()

    
    # Obtain values for expected mu=1 line
    
    # p0 = ax.tricontour(limit_ms, limit_temp, limit_mu[:,1,0],levels=[0,1], colors="k", alpha=0) # -2 sigma expected
    p1 = ax.tricontour(limit_ms, limit_temp, limit_mu[:,1,1],levels=[0,1],   colors="k", alpha=0) # -1 sigma expected
    p2 = ax.tricontour(limit_ms, limit_temp, limit_mu[:,1,2],levels=[0,1],   colors="k", alpha=0) # median expected
    p3 = ax.tricontour(limit_ms, limit_temp, limit_mu[:,1,3],levels=[0,1],  colors="k", alpha=0) # +1 sigma expected
    # p4 = ax.tricontour(limit_ms, limit_temp, limit_mu[:,1,4],levels=[0,1],  colors="k", alpha=0) # +2 sigma expected
    p5 = ax.tricontour(limit_ms, limit_temp, limit_mu[:,1,5],levels=[0,1],  colors="k", alpha=0) # observed
    
    if tricontour == 'log': x=0
    if tricontour == 'lin': x=1 
    line1 = np.array(p1.collections[x].get_paths()[0].vertices)
    line2 = np.array(p2.collections[x].get_paths()[0].vertices)
    line3 = np.array(p3.collections[x].get_paths()[0].vertices)
    #line4 = np.array(p4.collections[x].get_paths()[0].vertices)
    #line0 = np.array(p0.collections[x].get_paths()[0].vertices)
    line5 = np.array(p5.collections[x].get_paths()[0].vertices)

    if calculateWithoutPlotting:
        plt.close()
        return line1, line2, line3, line5

    #plot curve
    ax.plot(*line5.T, "b-", label="$\sigma_{excluded}=\sigma_{theory}$")
        
    ax.set_xlabel(r"$m_{s}$ (GeV)", x=1, ha='right')
    ax.set_ylabel(r"$T_D$ (GeV)", y=1, ha='right')

    _ = ax.text(
        0.05, 0.85, r"$m_{{\phi}} = {}$ GeV""\n""{}".format(str(mphi), decaysLabels[decay]),
        fontsize=20, horizontalalignment='left', 
        verticalalignment='bottom', 
        transform=ax.transAxes
    )
    hep.cms.label(llabel='Preliminary', data=False, lumi=lumis['combined'], ax=ax) # To add CMS lumi scripts

    ax.set_xlim([125, 1000])
    ax.set_ylim([mphi/4, mphi*4])     
    ax.legend(loc="upper right", fontsize=20)
    fig.tight_layout()

    fig.set_label("limits2D_mphi{:.1f}_{}".format(mphi, decay))

    return fig

def plot_summary_limits_mS_temp(decay, path='../'):

    samples = get_unique_combinations(['ms', 'temp'], decay=decay)

    lines = []
    for sample in samples:
        lines.append(plot_xsec_limits(mphi=sample[0], decay=decay, 
                                    tricontour='log', path=path,
                                    calculateWithoutPlotting=True))
        
    # Define colours
    cmap = plt.cm.jet
    colors = cmap(np.linspace(0., 1., len(lines)))

    fig = plt.figure(figsize=(12,9))
    ax = fig.subplots()

    for i, line in enumerate(lines):
        line1,line2,line3,line5 = line
        x1,y1 = interp_limit(line1, 2) #Expected $95\%$ CL
        x2,y2 = interp_limit(line2, 2)
        x3,y3 = interp_limit(line3, 2)
        x5,y5 = interp_limit(line5, 2)

        ax.plot(x2,y2,linestyle = '--', label=r"$m_{{\phi}}$ = {} GeV".format(samples[i][0]),c=colors[i])
        ax.plot(x5,y5, linestyle = '-',c='black')

        y1_interp = np.interp(x2, x1, y1)
        y3_interp = np.interp(x2, x3, y3)
        ax.fill_between(x2,y1_interp, y3_interp, color=colors[i],alpha=0.2)

    # Annotate figure
    ax.set_xlabel(r"$m_{s}$ (GeV)", x=1, ha='right')
    ax.set_ylabel(r"$T_D$ (GeV)", y=1, ha='right')
    hep.cms.label(llabel='Preliminary', data=False, lumi=137, ax=ax) # To add CMS lumi scripts
    ax.text(600,9, decaysLabels[decay], horizontalalignment='right', verticalalignment='center',fontsize=20)

    ax.set_xlim([0., 1050])
    ax.set_ylim([0,10 ])

    legend = ax.legend(loc='center left', bbox_to_anchor=(0.6, 0.3),frameon=False , fontsize=20, title= 'Expected 95% CL $\pm 1\sigma$')
    legend.get_title().set_fontsize(20)
    ax.text(700,5,'— observed')

    fig.tight_layout()

    fig.set_label('limits3D_mS_temp_{}'.format(decay))

    return fig