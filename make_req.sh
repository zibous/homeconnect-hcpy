#!/bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

echo "Create the requirements.txt..."
# pipreqs ./ --debug --force  --ignore .history,test,homeassistant
pipreqs ./  --force  --ignore .history,test,homeassistant

# echo "Make the documentation..."
# pdoc3 bosch.py hcpy --force --html -o docs --skip-errors

echo "======================================================================"
echo "Result:"
echo "======================================================================"
echo ""
cat requirements.txt