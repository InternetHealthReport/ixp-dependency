# Following the Data Trail: An Analysis of IXP Dependencies

This is the accompanying repository for the PAM 2024 paper “Following the Data Trail: An
Analysis of IXP Dependencies”. Here you can find the data and scripts required to
replicate the plots and analysis from the paper (and more). For updated weekly dependency data
please refer to [the main website.]()

This repository is self-contained and contains the entire data pipeline from the raw
data to the final figures. However, there are some files that mark the source of the
pipeline, i.e., they represent a data snapshot that can not be replicated after the
fact. For example, we crawled IXP looking glasses (`raw-data/lg-dumps`) and while we
link to the code to produce these dumps yourselves, you can not replicate the dumps in
this repository (except if you own a time machine). We list these sources below.

## Folder Structure

The general folder structure is as follows:

- `figs`: Figures
- `plots`: Plot scripts to create figures
- `raw-data`: Raw data snapshots
- `stats`: Processed data used for plotting
- `stats-script`: Scripts to process data either from raw data or from other processed data
- `tools`: Miscellaneous helper functions

Note that the structure is not perfect, i.e., there are some scripts in the `raw-data`
folder, and some data files in the `figs` folder.

Most Python scripts have a bash script with the same name that is used to automatically
run the script on multiple files (and also shows which files were used as input for the
parameters).

## Data Sources

The following files are “sources” in the sense that there is no script to create them:

- All files in the `raw-data` folder. Please refer to the README in the folder.
- Hegemony scores in `stats/hegemony`. These scores are based on one week of CAIDA Ark
  and four week of RIPE Atlas traceroutes. Including the entire hegemony pipeline here
  would drastically increase the size of the repository. The AS Hegemony pipeline is
  available [here](https://github.com/InternetHealthReport/as-hegemony) for BGP data, in
  combination with [this
  repository](https://github.com/InternetHealthReport/network-dependency) to transform
  traceroutes to a suitable format. However, there is no polished explanation for these
  repositories yet, which we will provide in the future.
- IXP outage traceroute statistics (`stats/ixp-outages`). We actually expanded and
  generalized the scripts used to create this data and moved them to a [separate
  repository](https://github.com/m-appel/atlas-traceroute-outage-inspector).
