import os, math, optparse, ROOT
from array import array
from simple_plot import getCanvas, doLegend

ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(True)

def fitFe(rfile,calib=True):
    tf = ROOT.TFile.Open(rfile)
    histo_sig = tf.Get("energyfe_diff" if calib else "integralfe_diff")
    histo_sig.SetMarkerColor(ROOT.kBlack)
    histo_sig.SetLineColor(ROOT.kBlack)
    histo_sig.GetXaxis().SetTitle('energy (keV)' if calib else 'I_{SC} (counts)')
    histo_sig.GetXaxis().SetTitleSize(0.05)
    histo_sig.GetYaxis().SetTitle('superclusters (bkg subtracted)')
    
    c = getCanvas()
    histo_sig.Draw("pe 1")

    par = array( 'd', 6*[0.] )

    xmin1,xmax1 = (3,9) if calib else (1600,3400)
    xmin2,xmax2 = (11,16) if calib else (4400,6000)    
    g1 = ROOT.TF1("g1","gaus",xmin1,xmax1);
    g2 = ROOT.TF1("g2","gaus",xmin2,xmax2);
    total = ROOT.TF1('total','gaus(0)+gaus(3)',xmin1,xmax2)
    total.SetLineColor(ROOT.kBlue+1)
    histo_sig.Fit('g1','RS')
    histo_sig.Fit('g2','R+S')
    mean  = g1.GetParameter(1); mErr = g1.GetParError(1)
    sigma = g1.GetParameter(2); mSigma = g1.GetParError(2)
    lat = ROOT.TLatex()
    unit = 'keV' if calib else 'counts'
    ndigits = 2 if calib else 0
    lat.SetNDC(); lat.SetTextFont(42); lat.SetTextSize(0.03)
    lat.DrawLatex(0.55, 0.70, "m_{{1}} = {m:.{nd}f} #pm {em:.{nd}f} {unit}".format(m=mean,em=mErr,unit=unit,nd=ndigits))
    lat.DrawLatex(0.55, 0.65, "#sigma_{{1}} = {s:.{nd}f} #pm {es:.{nd}f} {unit}".format(s=sigma,es=mSigma,unit=unit,nd=ndigits))

    mean  = g2.GetParameter(1); mErr = g2.GetParError(1)
    sigma = g2.GetParameter(2); mSigma = g2.GetParError(2)
    lat.DrawLatex(0.55, 0.50, "m_{{2}} = {m:.{nd}f} #pm {em:.{nd}f} {unit}".format(m=mean,em=mErr,unit=unit,nd=ndigits))
    lat.DrawLatex(0.55, 0.45, "#sigma_{{2}} = {s:.{nd}f} #pm {es:.{nd}f} {unit}".format(s=sigma,es=mSigma,unit=unit,nd=ndigits))



    par1 = g1.GetParameters()
    par2 = g2.GetParameters()

    par[0], par[1], par[2] = par1[0], par1[1], par1[2]
    par[3], par[4], par[5] = par2[0], par2[1], par2[2]
    total.SetParameters( par )
    histo_sig.Fit( total, 'R+' )
    
    c.SaveAs('fe_diff_simplefit.pdf')
    

def makeEff(f1,histo1,f2,histo2,plotdir):
    # numerator: selected events
    tf1 = ROOT.TFile.Open(f1)
    hpass = tf1.Get(histo1)
    hpass.GetYaxis().SetTitle('efficiency')
    hpass.GetXaxis().SetRangeUser(0,140)
    
    # denominator: all events
    tf2 = ROOT.TFile.Open(f2)
    htotal = tf2.Get(histo2)
    htotal.GetYaxis().SetTitle('efficiency')
    htotal.GetXaxis().SetRangeUser(0,140)

    ## default is 68% CL
    teffi68 = ROOT.TEfficiency(hpass,htotal)
    teffi68.SetStatisticOption(ROOT.TEfficiency.kFCP);
    teffi68.SetFillStyle(3004);
    teffi68.SetFillColor(ROOT.kRed);
    teffi68.SetMarkerStyle(ROOT.kFullSquare);
    teffi68.SetMarkerSize(2)
    teffi68.SetLineWidth(2)
    teffi68.SetMarkerColor(ROOT.kBlack);

    ## copy current TEfficiency object and set new confidence level
    teffi90 = ROOT.TEfficiency(teffi68);
    teffi90.SetStatisticOption(ROOT.TEfficiency.kFCP);
    teffi90.SetConfidenceLevel(0.90);
    teffi90.SetFillStyle(3005);
    teffi90.SetFillColor(ROOT.kBlue);
 
    c = getCanvas()
    if histo1.startswith('fe'):
        c.SetLogy()
    teffi68.Draw("A4")
    teffi68.Draw("same pe1")
    teffi90.Draw("same4")

    
    ## add legend
    histos = [teffi68,teffi90]
    labels = ['95%','68%']
    styles = ['F','F']
    legend = doLegend(histos,labels,styles,corner='TL' if histo1.startswith('fe') else 'BL')
    legend.Draw('same')
    
    for ext in ['png','pdf']:
        c.SaveAs('{odir}/{var}_effi.{ext}'.format(odir=plotdir,var=histo1,ext=ext))
    

### this is meant to be run on top of ROOT files produced by simple_plots, not on the trees
if __name__ == "__main__":

    parser = optparse.OptionParser(usage='usage: %prog [opts] ', version='%prog 1.0')
    parser.add_option('', '--make'   , type='string'       , default='fitfe' , help='run ambe_miscellanea.py (options = fitfe, efficiency)')
    parser.add_option('', '--outdir' , type='string'       , default='./'    , help='output directory with directory structure and plots')
    parser.add_option('', '--source' , type='string'       , default='ambe'  , help='in case of efficiency plotting, make it for fe/ambe')
    (options, args) = parser.parse_args()
                 
    if  options.make == 'fitfe':
        fitFe('plots/ambe/clusters_3sourcesNloCalNeutronsFex1_2020_05_05/energy.root')
    if  options.make == 'fitfeuncalib':
        fitFe('plots/ambe/clusters_3sourcesNloCalNeutronsFex1_2020_05_05/integral.root',calib=False)

    ## usages:
    # AmBe efficiency:> python ambe_miscellanea.py --make efficiency --source ambe --outdir './'
    # Fe55 efficiency:> python ambe_miscellanea.py --make efficiency --source fe --outdir './'
    if options.make == 'efficiency':
        var = 'energy' if options.source=='fe' else 'energyExt'
        prefix = '' if options.source=='ambe' else ('fe_' if options.source=='fe' else 'cosm_')
        makeEff('plots/ambe/clusters_3sourcesNloCalNeutronsDensityGt11_2020_05_06/'+var+'.root',prefix+var,
                'plots/ambe/clusters_3sourcesNloCalNeutrons_2020_05_05/'+var+'.root',           prefix+var,
                options.outdir)
                
                
