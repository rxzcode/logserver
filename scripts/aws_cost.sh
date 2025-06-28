#!/bin/bash

# Portable date for macOS and Linux
START_DATE=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

aws ce get-cost-and-usage \
  --time-period Start=$START_DATE,End=$END_DATE \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output json | \
jq -r '
  def lpad($width): tostring | if (length < $width) then (" " * ($width - length)) + . else . end;

  .ResultsByTime[].Groups[]
  | select(.Metrics.UnblendedCost.Amount | tonumber > 0)
  | {service: .Keys[0], cost: (.Metrics.UnblendedCost.Amount | tonumber)}
' | jq -s '
  def lpad($width): tostring | if (length < $width) then (" " * ($width - length)) + . else . end;

  . as $items
  | ($items | map(.cost) | reduce .[] as $c (0; if $c > . then $c else . end)) as $max
  | ($items | map(.cost) | add) as $total
  | ($total / 30) as $daily_avg
  | (
      $items[] |
      (
        (.service | if length > 30 then (.[:27] + "...") else . end | lpad(35)) + " | " +
        (("*" * ((.cost / $max * 40) | floor)) + " \(.cost) USD")
      )
    ),
    "------------------------------------------------------------",
    ("Total" | lpad(35)) + " | \($total) USD",
    ("Average Daily Cost" | lpad(35)) + " | \($daily_avg | .*100 | round / 100 | tostring) USD"
'
