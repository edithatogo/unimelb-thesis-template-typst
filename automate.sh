#!/bin/bash

# Simple automation script for thesis compilation

if [ "$1" = "compile" ]; then
    echo "Compiling thesis..."
    typst compile thesis.typ
elif [ "$1" = "watch" ]; then
    echo "Starting watch mode..."
    typst watch thesis.typ
else
    echo "Usage: $0 [compile|watch]"
    echo "  compile - Compile thesis to PDF"
    echo "  watch   - Watch for changes and recompile"
fi
