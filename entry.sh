#!/bin/bash

Help()
{
    echo "Create prefix-to-ASN mapping from RIS and Routeviews RIBs."
    echo
    echo "Full pipeline is index -> fetch -> transform -> create."
    echo "All commands require at least a timestamp in the format YYYY-MM-DDTHH:MM."
    echo "Options after the command are passed to the respective Python script."
    echo "Use 'command -h' to see the available options for the command."
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
        python3 build-index.py ${@:2}
    ;;
    fetch)
        python3 fetch-snapshots.py ${@:2}
    ;;
    transform)
        python3 transform-snapshots.py ${@:2}
    ;;
    create)
        python3 create-merged-rtree.py ${@:2}
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