param (
    [string]$algo = "SPYCC",
    [int]$chaincount = 40,
    [int]$start = 20200101,
    [int]$end = 20200401,
    [int]$seed = 42
)

lean data generate --start $start --end $end --tickers $algo --security-type Equity --resolution Minute --include-coarse False  --data-density Dense --market usa --random-seed $seed --update
lean data generate --start $start --end $end --tickers $algo --security-type Option --resolution Minute --include-coarse False  --data-density Dense --market usa --chain-symbol-count $chaincount --random-seed $seed --verbose