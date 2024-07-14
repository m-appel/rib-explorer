# rib-explorer

Scripts to fetch RIBs from [Route Views](http://routeviews.org/) and [RIPE
RIS](https://ris.ripe.net/docs/20_raw_data_mrt.html) and merge their information into a single
prefix-to-AS mapping. Allows creation of both current and historical mappings by specifying the
corresponding timestamp.

The mapping is conservative by default. The following prefixes are ignored:

- Prefixes with origin AS sets encoded in the RIB
- Prefixes for which peers disagree on the origin (multi-origin prefixes)
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

You can either install the dependencies or use Docker.

Install the required dependencies.

```bash
pip install -r requirements.txt
```

[bgpkit-parser](https://github.com/bgpkit/bgpkit-parser) is required to read the RIB
files.

## Docker

The Docker services come in two flavors:

1. `ribexplorer-mount`: Mount the folders in this directory in the container. Enables
   direct file access.
1. `ribexplorer-volume`: Folders are mounted from Docker volumes instead.

In both cases the `merged` folder from this directory is mounted in the container.

## Usage

All scripts can be either called directly or via `docker compose`. The Docker syntax
starts with a command (see below) and all following parameters are passed to the Python script.

Build an index of all currently available RIS and Route Views collectors.

```bash
# Direct
python3 ./build-index.py
# Docker
docker compose run --rm ribexplorer-mount index
```

Use the index file to download RIBs for all available collectors for the specified
timestamp.

```bash
# Direct
python3 ./fetch-snapshots.py YYYY-mm-ddTHH:MM
# Docker
docker compose run --rm ribexplorer-mount fetch YYYY-mm-ddTHH:MM
```

Notes:

- By default, the script fetches data with four threads in parallel. Use `-n` to adjust
  the number of threads.
- If no file that matches the exact timestamp is found, the next-closest is used, up to
  a certain threshold. The default maximum difference is 24 hours, but can be changed by adjusting
  the `max_timestamp_difference` in `fetchers/__init__.py`.

Transform the downloaded RIBs to radix trees.

```bash
# Direct
python3 ./transform-snapshots.py YYYY-mm-ddTHH:MM
# Docker
docker compose run --rm ribexplorer-mount transform YYYY-mm-ddTHH:MM
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
# Direct
python3 ./create-merged-rtree.py YYYY-mm-ddTHH:MM output.pickle.bz2
# Docker
docker compose run --rm ribexplorer-mount create YYYY-mm-ddTHH:MM output.pickle.bz2
```

Notes:

- The output file is created in the `/merged` folder by default. Use the `--output-dir`
  parameter to change this location (does not work with Docker).
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
