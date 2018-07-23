#!/bin/bash
# Positional arguments: input volume, reference volume, output volume, output matrix, dof, input volume to register, registered volume
flirt -in $1 -ref $2 -out $3 -omat $4 -dof $5 && flirt -ref $2 -in $6 -applyxfm -init $4 -out $7 -noresample

