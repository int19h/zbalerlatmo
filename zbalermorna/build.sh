#!/bin/sh

# Check input specified
if [ -z "$1" ]; then
  echo "No input file given.";
  exit 1;
fi

# Options
INFILE="src/$1.sfd"
OUTFILE="fonts/$1.otf"

# Generate incorporating common feature file
echo ""
echo "Building font: $INFILE -> $OUTFILE"
echo ""

fontforge -lang=ff -script build.pe $1
