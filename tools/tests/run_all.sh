#!/bin/sh
# Runs every regression test in sequence (validator + Playwright touch tests). Exit status 1 if any fails.
cd "$(dirname "$0")/../.."; rc=0
python3 tools/freeglass/validate_json.py >/tmp/t_validate.txt 2>&1 || { echo "validate FAILED"; rc=1; }
for t in freetouch savetest themetest zoomtest smalltest replaytest optionstest poweruptest shoptest rewardtest starttest autofilltest gifttest "$@"; do
  python3 tools/tests/$t.py >/tmp/t_$t.txt 2>&1 || { echo "$t exit nonzero"; rc=1; }
  echo "== $t"; tail -c 300 /tmp/t_$t.txt; grep -c "false" /tmp/t_$t.txt
done
exit $rc
