import pylab as plt
import numpy as np

def UseLatexPltOptions(fsize=18):
    params = {'axes.titlesize':fsize,
              'axes.labelsize':fsize,
              'font.size':fsize,
              'legend.fontsize':fsize,
              'xtick.labelsize':fsize,
              'ytick.labelsize':fsize}
    plt.rcParams.update(params)
    plt.rc('text', usetex=True)
    plt.rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})

def ConfrontationTableASCII(cname,M):
    
    # determine header info
    head = None
    for m in M:
        if cname in m.confrontations.keys():
            head = m.confrontations[cname]["metric"].keys()
            break
    if head is None: return ""

    # we need to sort the header, I will use a score based on words I
    # find the in header text
    def _columnval(name):
        val = 1
        if "Score"       in name: val *= 2**4
        if "Interannual" in name: val *= 2**3
        if "RMSE"        in name: val *= 2**2
        if "Bias"        in name: val *= 2**1
        return val
    head   = sorted(head,key=_columnval)
    metric = m.confrontations[cname]["metric"]

    # what is the longest model name?
    lenM = 0
    for m in M: lenM = max(lenM,len(m.name))
    lenM += 1

    # how long is a line?
    lineL = lenM
    for h in head: lineL += len(h)+2

    s  = "".join(["-"]*lineL) + "\n"
    s += ("{0:>%d}" % lenM).format("ModelName")
    for h in head: s += ("{0:>%d}" % (len(h)+2)).format(h)
    s += "\n" + ("{0:>%d}" % lenM).format("")
    for h in head: s += ("{0:>%d}" % (len(h)+2)).format(metric[h]["unit"])
    s += "\n" + "".join(["-"]*lineL)

    # print the table
    for m in M:
        s += ("\n{0:>%d}" % lenM).format(m.name)
        if cname in m.confrontations.keys():
            for h in head: s += ("{0:>%d,.3f}" % (len(h)+2)).format(m.confrontations[cname]["metric"][h]["var"])
        else:
            for h in head: s += ("{0:>%d}" % (len(h)+2)).format("~")
    return s

def GlobalPlot(lat,lon,var,biome="global",ax=None):
    from mpl_toolkits.basemap import Basemap
    from pylab import cm
    from matplotlib.colors import from_levels_and_colors
    from constants import biomes
    lats,lons = biomes[biome]
    print lats
    print lons
    print lat.min(),lat.max()
    print lon.min(),lon.max()
    bmap = Basemap(projection='cyl',
                   llcrnrlon=lons[ 0],llcrnrlat=lats[ 0],
                   urcrnrlon=lons[-1],urcrnrlat=lats[-1],
                   resolution='c',ax=ax)
    alon = lon-180
    nroll = np.argmin(np.abs(lon-180))
    #alon  = np.roll(lon,nroll); lon[:nroll] -= 360
    #x,y   = bmap(alon,lat)
    #ax    = bmap.pcolormesh(x,y,np.roll(var,nroll,axis=1),zorder=2)
    x,y   = bmap(alon,lat)
    ax    = bmap.pcolormesh(x,y,var,zorder=2)
    #bmap.drawmeridians(np.arange(-150,151,30),labels=[0,0,0,1],zorder=1,dashes=[1000000,1],linewidth=0.5)
    bmap.drawmeridians(np.arange(   0,361,30),labels=[0,0,0,1],zorder=1,dashes=[1000000,1],linewidth=0.5)
    bmap.drawparallels(np.arange( -90, 91,30),labels=[1,0,0,0],zorder=1,dashes=[1000000,1],linewidth=0.5)
    bmap.drawcoastlines(linewidth=0.5)
    bmap.colorbar(ax) 
