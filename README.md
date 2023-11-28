# rib-explorer

Scripts to fetch RIBs from [Route Views](http://routeviews.org/) and [RIPE
RIS](https://ris.ripe.net/docs/20_raw_data_mrt.html) and merge their information into a single
prefix-to-AS mapping. Allows creation of both current and historical mappings by specifying the
corresponding timestamp.

The mapping is conservative by default. The following prefixes are ignored:

- Prefixes with origin AS sets encoded in the RIB
- Prefixes for which peers of a collector disagree on the origin
- Prefixes for which collectors disagree on the origin
- Prefixes that are
  [not globally reachable](https://docs.python.org/3/library/ipaddress.html?highlight=ipaddress#ipaddress.IPv4Address.is_global)
  according to Python's ipaddress module, which is based on the IANA Special-Purpose Address
  Registries
  ([IPv4](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml);
   [IPv6](https://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml)).

In addition, during the merging process a minimum number or ratio of collectors can be
specified that is required to see a prefix in order for the prefix to be included in the
final radix tree.

## Setup

Install the required dependencies.

```bash
pip install -r requirements.txt
```

[bgpdump](https://github.com/RIPE-NCC/bgpdump) is required to read the RIB files.

## Usage

Build an index of all currently available RIS and Route Views collectors.

```bash
python3 ./build-index.py
```

Use the index file to download RIBs for all available collectors for the specified
timestamp.

```bash
python3 ./fetch-snapshots.py ./indexes/YYYYmmdd.index.json YYYY-mm-ddTHH:MM
```

Notes:

- By default, the script fetches data with four threads in parallel. Use `-n` to adjust
  the number of threads.
- If no file that matches the exact timestamp is found, the next-closest is used, up to
  a certain threshold. The default maximum difference is 24 hours, but can be changed by adjusting
  the `max_timestamp_difference` in `fetchers/__init__.py`.

Transform the downloaded RIBs to radix trees.

```bash
python3 ./transform-snapshots.py ./indexes/YYYYmmdd.index.json YYYY-mm-ddTHH:MM
```

Notes:

- Like above, the number of parallel threads (for computation this time) can be adjusted
  with the `-n` parameter.
- The timestamp difference threshold can be adjusted with the
  `--max-timestamp-difference` parameter to set the maximum difference in hours.
- During the transformation some sanitation is applied as well. Prefixes with origin AS
  sets are ignored and singleton sets of the form `{ASXXXX}` are resolved. In addition,
  if the peers of a collector disagree about the origin for a prefix, it is also
  ignored. **There are no AS sets in the produced radix trees.**

Merge the radix trees into a single file.

```bash
python3 ./create-merged-rtree.py ./indexes/YYYYmmdd.index.json YYYY-mm-ddTHH:MM output.pickle.bz2
```

Notes:

- If collectors disagree about the origin for a prefix, that prefix is ignored.
- A minimum number or ratio of collectors can be specified using the
  `--min-collector-ratio` or `--min-collector-count` parameters. If a prefix is seen by
  fewer collectors, it is ignored.

## Data structure of created radix trees

The transformed (per RIB) radix trees follow our usual structure:

```python
{'as': str(asn)}
```

The merged radix tree includes additional information about the collectors that see each
prefix:

```python
{
  'as': str(asn),
  'seen_by_collectors': tuple(str(collector), ...)
}
```
