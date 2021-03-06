#!/usr/bin/env python

''' Read the output from toy max-likelihood fits and histogram the fitted mu.

'''

from RecoLuminosity.LumiDB import argparse
from HiggsAnalysis.HiggsToTauTau.scanMultiDimFit import extract_band

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("label", metavar="channel", help="channel name")
    parser.add_argument("plot", metavar="plot.png", help="Output plot")
    parser.add_argument("mlfit", metavar="ML-fit-result.root",
                        help="Result of limit.py --max-likelihood call. Looks "
                        "like higgsCombineTest.MaxLikelihoodFit.mH125.root")
    parser.add_argument("mdfit", metavar="MD-fit-result.root",
                        help="Result of limit.py --scan-likelihood call. Looks "
                        "like higgsCombineTest.MultiDim.mH125.root")
    parser.add_argument("toys", metavar="toys-result.root", nargs="+",
                        help="Multiple toy results. Looks like "
                        "higgsCombineTest.MaxLikelihoodFit.mH125.SEED.root")

    args = parser.parse_args()

    import ROOT

    canvas = ROOT.TCanvas("asdf", "asdf", 800, 800)

    real_fit = ROOT.TChain("limit")
    real_fit.Add(args.mlfit)

    toys = ROOT.TChain("limit")
    for toyfile in args.toys:
        toys.Add(toyfile)

    # Just get the first value for the actual fit
    real_fit_val = None
    real_fit_val_low = None
    real_fit_val_high = None
    for i, row in enumerate(real_fit):
        if i == 0:
            real_fit_val = row.limit
        if i == 1:
            real_fit_val_low = row.limit
        if i == 2:
            real_fit_val_high = row.limit
    print "REAL FIT: ", real_fit_val

    toy_results = []
    toy_low_results = []
    toy_high_results = []
    # Now get all the toys
    for i, row in enumerate(toys):
        if i % 4 == 0:
            toy_results.append(row.limit)
        if i % 4 == 1:
            toy_low_results.append(toy_results[-1] - row.limit)
        if i % 4 == 2:
            toy_high_results.append(row.limit - toy_results[-1])

    # likelihood scan version
    try:
        lower_bound, best_r, upper_bound, full_graph = extract_band(args.mdfit)
        scan_result = (best_r, upper_bound - best_r, best_r - lower_bound)
    except:
        print "Can't extract band from", args.mdfit
        scan_result = (1, 1, 1)

    min_value = min([real_fit_val, min(toy_results), scan_result[0]])
    max_value = max([real_fit_val, max(toy_results), scan_result[0]])
    toy_min_value = min(toy_results)
    toy_max_value = max(toy_results)

    width = max_value - min_value
    toy_width = toy_max_value - toy_min_value

    toy_hist = ROOT.TH1F("toys", "toys", 100,
                         min_value - width / 10, max_value + width / 10)
    toy_pulls = ROOT.TH1F("toys_pulls", "toys_pulls", 100, -5, 5)

    below = 0

    toy_results.sort()
    median = toy_results[len(toy_results) / 2]

    for toy, low, high in zip(toy_results, toy_low_results, toy_high_results):
        if toy < real_fit_val:
            below += 1
        toy_hist.Fill(toy)
        if toy < 1:
            toy_pulls.Fill((toy - 1) / abs(high))
        if toy > 1:
            toy_pulls.Fill((toy - 1) / abs(low))
    toy_pulls.Fit("gaus")

    toy_hist.Draw()
    toy_hist.SetLineWidth(2)

    toy_hist.GetXaxis().SetTitle("fitted signal strength")
    toy_hist.SetMinimum(0)
    toy_hist.SetMaximum(toy_hist.GetMaximum() * 2)

    line = ROOT.TLine(real_fit_val, 0, real_fit_val, toy_hist.GetMaximum())
    line.SetLineColor(ROOT.EColor.kRed)
    line.SetLineWidth(2)
    box = ROOT.TBox(real_fit_val_low, 0,
                    real_fit_val_high, toy_hist.GetMaximum())
    box.SetFillColor(ROOT.EColor.kRed - 10)
    # for the legend style
    box_copy = box.Clone()
    box_copy.SetLineColor(ROOT.EColor.kRed)

    #scan_line = ROOT.TLine(
    #    scan_result[0], 0, scan_result[0], toy_hist.GetMaximum())
    scan_line = ROOT.TGraph(1)
    scan_line.SetPoint(0, scan_result[0], 10)
    scan_line.SetMarkerStyle(21)
    scan_line.SetMarkerSize(2)

    toy_hist.Draw('same')

    legend = ROOT.TLegend(0.5, 0.8, 0.95, 0.9, "", "brNDC")
    legend.SetFillColor(ROOT.EColor.kWhite)
    legend.SetBorderSize(1)
    legend.AddEntry(toy_hist,
                    "1xSM Toys median=%0.2f" % median, "lf")
    legend.AddEntry(box_copy, "Observed", "lf")
    legend.AddEntry(scan_line, "NLL Scan Obs", "p")

    label = ROOT.TPaveText(0.5, 0.7, 0.95, 0.8, "brNDC")
    label.AddText("%0.2f%% toys < obs." % (
        100. * below / len(toy_results)))
    label.SetFillColor(ROOT.EColor.kWhite)
    label.SetBorderSize(1)
    label.Draw()

    translator = {
        'mmt': "#mu#mu#tau",
        'moriond.mmt': "Moriond #mu#mu#tau",
        'mmt_8TeV': "#mu#mu#tau 8TeV",
        'mmt_7TeV': "#mu#mu#tau 7TeV",
        'mmt_8TeV_high': "#mu#mu#tau 8TeV high",
        'mmt_8TeV_highscaled': "#mu#mu#tau 8TeV high (x10)",
        'mmt_8TeV_low': "#mu#mu#tau 8TeV low",
        'mmt_nofakes': "#mu#mu#tau no fakes",
        'emt': "e#mu#tau",
        'moriond.emt': "Moriond e#mu#tau",
        'eet': "ee#tau",
        'mtt': "#mu#tau#tau",
        'ett': "e#tau#tau",
        'moriond.llt': "Moriond LLT",
        'vhtt_wh': "LLT",
        'vhtt_wh_had': "LTT",
        'vhtt_zh': "ZH",
    }

    channel = ROOT.TPaveText(0.5, 0.6, 0.95, 0.7, "brNDC")
    channel.AddText(translator[args.label])
    channel.SetFillColor(ROOT.EColor.kWhite)
    channel.SetBorderSize(1)
    channel.Draw()

    legend.Draw()

    toy_hist.GetXaxis().SetRangeUser(
        toy_min_value - toy_width / 10.,
        toy_max_value - toy_width / 10.)

    canvas.SaveAs("toys_only_" + args.plot)

    toy_hist.GetXaxis().SetRangeUser(min_value, max_value)

    #box.Draw()
    line.Draw()
    scan_line.Draw("same,p")
    toy_hist.Draw('same')

    canvas.SaveAs(args.plot)

    toy_pulls.Draw()
    toy_pulls.SetLineWidth(2)

    toy_pulls.GetXaxis().SetTitle("signal strength pull (#mu - 1)/#sigma")
    toy_pulls.SetMinimum(0)
    toy_pulls.SetMaximum(toy_pulls.GetMaximum() * 2)
    channel.Draw()
    canvas.SaveAs("pulls_" + args.plot)
