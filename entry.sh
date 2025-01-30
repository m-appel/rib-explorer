#!/bin/bash

Help()
{
    echo "Create prefix-to-ASN mapping from RIS and Routeviews RIBs."
    echo
    echo "Full pipeline is index -> fetch -> transform -> create."
    echo "All commands (except 'index') require at least a timestamp in the format YYYY-MM-DDTHH:MM."
    echo "Options after the command are passed to the respective Python script (except for 'all', see below)."
    echo "Use 'command -h' to see the available options for the other commands."
    echo
    echo "The 'all' command runs the entire pipeline and thus needs options for multiple scripts. By default"
    echo "it only includes the option for --min-collector-count so if you want to use different options, run"
    echo "the 'create' command by itself."
    echo
    echo "Syntax for 'all': all timestamp num-fetchers num-transformers min-collector-count"
    echo
    echo "Syntax: command timestamp [options]"
    echo
    echo "commands:"
    echo "index              Build the index file"
    echo "fetch              Fetch RIBs from RIS and Routeviews"
    echo "transform          Transform RIBs into radix trees"
    echo "create             Create a prefix-to-ASN mapping"
    echo "clean              Clean all input directories"
    echo "clean-data         Clean RIB files"
    echo "clean-index        Clean index files"
    echo "clean-transformed  Clean radix tree files"
    echo
}

T="$1"
case $T in
    index)
        python3 build-index.py
    ;;
    fetch)
        python3 fetch-snapshots.py "${@:2}"
    ;;
    transform)
        python3 transform-snapshots.py "${@:2}"
    ;;
    create)
        python3 create-merged-rtree.py "${@:2}"
    ;;
    all)
        if [ $# -ne 5 ]; then
            echo "usage: all timestamp num-fetchers num-transformers min-collector-count"
            exit 1
        fi
        python3 build-index.py
        python3 fetch-snapshots.py -n "$3" "$2"
        python3 transform-snapshots.py -w -n "$4" "$2"
        python3 create-merged-rtree.py -w --min-collector-count "$5" "$2"
    ;;
    clean-data)
        rm -r data/*
    ;;
    clean-index)
        rm -r indexes/*
    ;;
    clean-transformed)
        rm -r transformed/*
    ;;
    clean)
        rm -r data/*
        rm -r indexes/*
        rm -r transformed/*
    ;;
    *)
        Help
    ;;
esac
