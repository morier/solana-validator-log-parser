# Solana Validator Log Parser

[![CI](https://github.com/morier/solana-validator-log-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/morier/solana-validator-log-parser/actions/workflows/ci.yml)

CLI tool to parse Solana validator logs and produce operational summaries for troubleshooting and monitoring.

## Features

- Parse validator logs and summarize errors/warnings
- Detect Solana operation signals: votes, slots, RPC, gossip
- Return top repeated error fragments
- Support text and JSON output modes
- Include sample log for offline demo and CI smoke test
- Support stdin input with `--file -` for streaming pipelines

## Requirements

- Python 3.10+

## Usage

```bash
python solana_log_parser.py --file samples/validator.log --output text
python solana_log_parser.py --file samples/validator.log --output json

# stream input via stdin
Get-Content samples/validator.log | python solana_log_parser.py --file - --output json
```

## Example (JSON)

```json
{
  "total_lines": 8,
  "error_lines": 2,
  "warning_lines": 1,
  "error_rate_pct": 25.0,
  "warning_rate_pct": 12.5,
  "signal_counts": {
    "votes": 2,
    "slots": 3,
    "rpc": 2,
    "gossip": 2
  },
  "top_error_fragments": [
    ["[2026-05-06T08:00:04Z ERROR solana_core::gossip_service] connection reset by peer while sending gossip packet", 1]
  ]
}
```

## CI

GitHub Actions runs:

- Unit tests
- Sample log parse in JSON mode

## Roadmap

- Add regex profile presets for different validator versions
- Add optional severity thresholds with non-zero exit codes
