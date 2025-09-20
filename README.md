# SL Transit REPL

An interactive command-line tool (with auto-completion and command history) for querying real time departure data from Stockholm's public transit system (SL) using Trafiklab APIs.

This is **not** intended as library/wrapper for programmatically accessing the Trafiklab APIs.

## Features

### 🚇 **Departure Queries**
- Get real-time departure information for any transit stop
- Filter by line, direction, transport mode, and forecast window

### 🔍 **Site Lookup**
- Find transit stops by ID or name search
- Fuzzy name matching with diacritic support (åäö → aao); also searches aliases and alternative names

## Installation

### Requirements
```bash
pip install requests prompt-toolkit rich unidecode pyyaml
```

### Setup
The tool automatically creates a cache directory and downloads site data on first use.

## Usage

### Starting the REPL
```bash
python departures.py
```

### Basic Commands

#### Departure Queries
```bash
# Basic departure lookup
1002

# Filter by line (Green line)
1002 line:17

# Filter by direction and line
1002 line:17 direction:1

# Filter by transport mode
1002 transport:BUS

# Set forecast window (default: 60 minutes)
1002 forecast:30

# Show direction numbers in output
1002 show_numbers:true

# Debug mode (show HTTP headers)
1002 debug:true
```

#### Site Lookup
```bash
# Find site by ID
lookup:id 1002

# Find sites by name (fuzzy search)
lookup:name odenplan
lookup:name central
lookup:name åkeshov    # Works with Swedish characters
```

#### Other Commands
```bash
# Show detailed help
help

# Exit the program
quit
```

### Example Session
TBD - Add screenshots

## Configuration
### Time Thresholds
- **Departure Forecast Duration**: 60 minutes (default)
- **Warning Threshold**: 15 minutes (highlights urgent departures)
- **Delay Threshold**: 5 minutes (highlights significant delays)

## API Integration

Uses official data from SL via the [sites and depatures APIs](https://www.trafiklab.se/api/our-apis/sl/transport/) from [Trafiklab](https://www.trafiklab.se/). No API key needed for these APIs, so try to be respectful in your usage 😄.

## Class Usage

The tool is built around the `SLTransitREPL` class _could_ be imported for use in other scripts. Not exactly the intended usage, but knock yourself out.

```python
from departures import SLTransitREPL

# Create REPL instance with custom cache directory
repl = SLTransitREPL(cache_dir="/path/to/cache")

# Run interactive session
repl.run()

# Or use individual methods programmatically
site = repl._find_site_by_id(1002)
sites = repl._find_sites_by_substring("central")
```

## Files

- **Cache**: `cache/sites.json` (site data)
- **History**: `~/.sl_transit_repl_history` (command history)
- **Config**: Line colors and thresholds defined in class constants
