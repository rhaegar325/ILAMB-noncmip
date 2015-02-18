from netCDF4 import Dataset
import numpy as np
import ilamblib as il
from constants import convert

class GPPFluxnetGlobalMTE():
    """Confront models with the gross primary production (GPP) product
    generated by Fluxnet MTE.
    """
    def __init__(self):
        self.name = "GPPFluxnetGlobalMTE"
        self.path = "/home/ncf/data/ILAMB/DATA/FLUXNET-MTE/derived/"
        self.nlat = 360
        self.nlon = 720

    def getData(self,initial_time=-1e20,final_time=1e20,output_unit=""):
        """Retrieves the confrontation data on the desired time frame and in
        the desired unit.

        Parameters
        ----------
        initial_time : float, optional
            include model results occurring after this time
        final_time : float, optional
            include model results occurring before this time
        output_unit : string, optional
            if specified, will try to convert the units of the variable 
            extract to these units given (see convert in ILAMB.constants)

        Returns
        -------
        t : numpy.ndarray
            a 1D array of times in days since 00:00:00 1/1/1850
        var : numpy.ma.core.MaskedArray
            an array of the extracted variable
        unit : string
            a description of the extracted unit
        """
        # why are these stored as separate netCDF files? Isn't I/O
        # latency worse if these are broken up and I have to build a
        # composite?
        y0   = max(int(initial_time/365.),1982)
        yf   = min(int(  final_time/365.),2005)
        ny   = yf-y0+1; nm = 12*ny
        t    = np.zeros(nm)
        var  = np.ma.zeros((nm,self.nlat,self.nlon))
        unit = ""
        lat,lon = None,None
        for y in range(ny):
            yr = y+1982
            for m in range(12):
                ind   = 12*y+m
                fname = "%s%d/gpp_0.5x0.5_%d%02d.nc" % (self.path,yr,yr,m+1)
                f = Dataset(fname)
                v = f.variables["gpp"]
                t  [ind    ] = v.time
                var[ind,...] = v[...]
                unit = v.units
                if lat is None:
                    lat = f.variables["lat"][...]
                    lon = f.variables["lon"][...]
        return t,var,unit,lat,lon+180.

    def confront(self,m):
        r"""Confronts the input model with the observational data.

        Parameters
        ----------
        m : ILAMB.ModelResult.ModelResult
            the model results                  

        Returns
        -------
        cdata : dictionary                  
            contains all outputs/metrics

        Notes
        -----
        The dictionary key "metric" will return a dictionary which
        contains the analysis results. For this confrontation we
        include the following quantities in the analysis. We define
        :math:`gpp(\mathbf{x},t)` as the mean monthly gross primary
        productivity as a function of space (:math:`\mathbf{x}`) and
        time (:math:`t`) given in units of "g m^-2 s^-1". For
        convenience, we will define here a spatially integrated
        quantity as well,
        
        .. math:: \overline{gpp}(t) = \int_A gpp(\mathbf{x},t)\ dA

        where :math:`A` refers to the area of interest.

        "PeriodMean" : float
            The mean gross primary productivity for the globe
            averaged over the time period, or

            .. math:: \frac{\int_{t_0}^{t_f} \overline{gpp}(t)\ dt}{t_f-t_0}

            in units of "g/s"
        "MonthlyMeanBias" : float
            The bias of the spatially integrated monthly mean model
            result compared to that of the observational data in units
            of "g/s"
        "MonthlyMeanRMSE" : float
            The RMSE of the spatially integrated monthly mean model
            result compared to that of the observational data in units
            of "g/s"
        "PhaseChange" : float
            The mean time difference in the annual peaks of gross
            primary production in the model result compared to the
            observational data. The annual peak time is written as
            :math:`t_{\text{peak}}(\mathbf{x},t_a)` where :math:`t_a`
            refers to the year. Then we can compute a temporally
            averaged quantity,

            .. math:: \bar{t}_{\text{peak}}(\mathbf{x}) = \frac{1}{t_{af}-t_{a0}}\int_{t_{a0}}^{t_{af}} t_{\text{peak}}(\mathbf{x},t)\ dt

            Then the phase change is given as the difference of peak
            times of the model relative to the observations,
            integrated over the area of interest, or

            .. math:: \frac{1}{A} \int_A  \left(\bar{t}_{\text{peak}}^{\text{model}}(\mathbf{x}) - \bar{t}_{\text{peak}}^{\text{obs}}(\mathbf{x})\right)\ dA

            
        
        """
        # get confrontation data
        t,gpp,unit,lat,lon = self.getData()
        il.CellAreas(lat,lon)
        


        # time limits for this confrontation, with a little padding to
        # account for differences in monthly time representations
        t0,tf = t.min()-5, t.max()+5

        # extract the time, variable, and unit of the model result
        tm,vm,um = m.extractTimeSeries("gpp",initial_time=t0,final_time=tf)
        
        # update time limits, might be less model data than observations
        t0,tf = tm.min(), tm.max()

        def SpatiallyIntegratedTimeSeries(var,areas):
            return np.ma.apply_over_axes(np.ma.sum,var*areas,[1,2]).reshape(-1)
            
        vobar = SpatiallyIntegratedTimeSeries(gpp,np.ones(gpp.shape))
        uobar = unit.replace(" m-2","")

        vmbar = SpatiallyIntegratedTimeSeries(vm,m.land_areas)
        umbar = um.replace(" m-2","")

        metric = {}
        metric["PeriodMean"]

        cdata["metric"] = metric
        

        cdata = {}
        return cdata
