This is the accompanying repository for the PAM 2024 paper "Following the Data
Trail: An Analysis of IXP Dependencies". Use the three buttons above to access:

1. Data to reproduce the plots and analysis from the paper.
1. Weekly updated data (in form of CSV files) for bulk data downloads.
1. An API that provides more fine-grained access to the weekly data.

## Data Format (Archive)

The table below shows a data snippet (from the archive data) highlighting all
columns and data variations.


|   id    |        timebin         |   hege   | af | nbsamples | origin_type | origin_name | dependency_type | dependency_name |
|---------|------------------------|----------|----|-----------|-------------|-------------|-----------------|-----------------|
| 1608913 | 2024-01-29 00:00:00+00 |     0.76 |  4 |        31 | AS          |        2501 | AS              | 2497            |
| 1486945 | 2024-01-29 00:00:00+00 | 0.102125 |  4 |      1112 | AS          |        9498 | IX              | 31              |
| 1464692 | 2024-01-29 00:00:00+00 | 0.109375 |  4 |       158 | AS          |       45232 | MB              | 31;9498         |
| 1436188 | 2024-01-29 00:00:00+00 | 0.152929 |  4 |      1112 | AS          |        7713 | IP              | 80.81.193.22    |

- **id**: A running database identifier which can be ignored.
- **timebin**: The timestamp at which the data was produced. Data is produced
  every week at midnight UTC from Sunday to Monday. See below for more
  information.
- **hege**: The hegemony score. **Warning:** We include scores below 0.1 in this
  data, i.e., not all entries are dependencies as defined in the paper.
- **af**: The IP address family of the result. Always 4 (IPv4) for now.
- **nbsamples**: The number of samples (in terms of unique source probe ASes) on
  which the data is based. We only include scores where nbsamples is ≥ 10.
- **origin_type**: The type of the origin (called "dependent" in the paper).
  This is the *target AS* of the traceroute, the term "origin" is used for
  consistency with the original AS Hegemony format (which stems from BGP). The
  origin type is mostly "AS", although there are a few exceptions that are a
  side effect of the data production pipeline.
- **origin_name**: The AS number of the origin (if origin_type is "AS").
- **dependency_type**: The type of the dependency (on which origin *depends*).
  The value of this field defines how dependency_name should be interpreted.
  - **AS**: AS number
  - **IX**: A PeeringDB IX id, e.g., [31 for DE-CIX
    Frankfurt](https://www.peeringdb.com/ix/31)
  - **MB**: An IXP member in the format `ix_id;asn`, e.g., `31;9498` refers to
    the DE-CIX Frankfurt member AS9498
  - **IP**: An interface IP of a peering LAN router
- **dependency_name**: See above.

### Working with the data

Below are some examples (based on [Python's pandas](https://pandas.pydata.org/) syntax):

```python
import pandas as pd

df = pd.read_csv('ihr_tr_hegemony_2024-01-29.csv')
# Get all dependents (as defined in the paper) of AS2497.
df[(df.hege >= 0.1) & (df.dependency_type == 'AS') & (df.dependency_name == '2497')]
# Get all ASes depending on some IXP.
df[(df.hege >= 0.1) & (df.dependency_type == 'IX')]
# Get the Hegemony score (if available) between AS2501 and AS2497.
df[(df.origin_type == 'AS') & (df.origin_name == '2501') & (df.dependency_type == 'AS') & (df.dependency_name == '2497')]
```

## Data Format (API)

The API has almost the same format as the archive files. Scroll to the
[tr_hegemony](https://ihr.iijlab.net/ihr/en-us/api) section of the API page for
a description of the available parameters. Due to the way the internal database
is designed, there are additional "af" parameters, origin_af and dependency_af,
which can be ignored for now (they are always 4).

### Working with the API

Here are the same examples as above, but retrieved from the API:
- [Get all dependents (as defined in the paper) of
  AS2497.](https://ihr.iijlab.net/ihr/api/tr_hegemony/?timebin=2024-01-29T00%3A00&dependency_name=2497&dependency_type=AS&hege__gte=0.1)
- [Get all ASes depending on some
  IXP.](https://ihr.iijlab.net/ihr/api/tr_hegemony/?timebin=2024-01-29T00%3A00&dependency_type=IX&hege__gte=0.1)
- [Get the Hegemony score (if available) between AS2501 and
  AS2497.](https://ihr.iijlab.net/ihr/api/tr_hegemony/?timebin=2024-01-29T00%3A00&origin_name=2501&dependency_name=2497&origin_type=AS&dependency_type=AS)

## Data Production Interval

We produce data once a week at midnight UTC from Sunday to Monday. This means
the only available timebins are always ending on `T00:00`. Since we only include
RIPE Atlas data for now (due to ease of access), the results are based on **four
weeks** of traceroute data (filtered by a list of probe ASes, which is updated
weekly, as described in the paper).

Therefore, data with in timebin `2024-01-29T00:00` is based on traceroute
results from `2024-01-01T00:00` to `2024-01-29T00:00`.
