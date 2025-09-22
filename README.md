# SL Transit REPL

A command-line tool for querying real time departure data from Stockholm's public transit system (SL) using [Trafiklab](https://www.trafiklab.se/) APIs.

**Two modes of operation:**
- **Interactive REPL** with auto-completion and command history
- **Single-query mode** for scripting and automation

This is **not** intended as library/wrapper for programmatically accessing the Trafiklab APIs.

## Features

### 🚇 **Departure Queries**
- Get real-time departure information for any transit stop
- Filter by line, direction, transport mode, and forecast window

### 🔍 **Site Lookup**
- Find transit stops by ID or name search
- Fuzzy name matching with diacritic support (åäö → aao); also searches aliases and alternative names

## Installation

### Install from PyPI
```bash
pip install sl-transit-repl
```
After installation, you can use the `sl-repl` command from anywhere (assuming the environment where sl-transit-repl is installed is active).

### Install from Source
```bash
git clone https://github.com/abonhomme/sl-transit-repl.git
cd sl-transit-repl
pip install -e .
```

### Setup
The tool automatically creates an application directory (`~/.sl_transit_repl`) and downloads site data on first use.

## Usage

### Command Line Mode (Single Queries)

**After installation:**
```bash
# Get help
sl-repl --help

# Basic departure lookup
sl-repl "1002"

# Departure lookup with filters
sl-repl "1002 line:17 direction:1"

# Site lookup by name
sl-repl "lookup:name central"

# Site lookup by ID
sl-repl "lookup:id 1002"

# Custom app directory
sl-repl --app-dir ~/my_transit_data "1002"
```

**From source (development):**
```bash
python -m src.sl_transit_repl "1002"
python -m src.sl_transit_repl "lookup:name central"
```

### Interactive REPL Mode

**After installation:**
```bash
sl-repl
```

**From source (development):**
```bash
python -m src.sl_transit_repl
```

### Interactive Commands

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

### Example Sessions

#### Command Line Mode
```bash
# Quick departure check
$ sl-repl "1002 forecast:5"

Site: Centralen (1002)
┌──────┬───────────┬──────────────┬───────────┬──────────┬──────────┬──────────┐
│ Line │ Transport │ Direction    │ Scheduled │ Expected │ Status   │ Platform │
├──────┼───────────┼──────────────┼───────────┼──────────┼──────────┼──────────┤
│ 19   │ METRO     │ Hässelby str │ 21:28     │ 21:28    │ ATSTOP   │ 1        │
│ 14   │ METRO     │ Fruängen     │ 21:29     │ 21:29    │ EXPECTED │ 2        │
└──────┴───────────┴──────────────┴───────────┴──────────┴──────────┴──────────┘

# Site search
$ sl-repl "lookup:name odenplan"

Sites matching 'odenplan'
┌──────┬───────────┬─────────┬──────────────┬──────────────────┐
│   ID │ Name      │ Aliases │ Abbreviation │ Coordinates      │
├──────┼───────────┼─────────┼──────────────┼──────────────────┤
│ 9302 │ Odenplan  │         │ ODE          │ 59.3428, 18.0496 │
└──────┴───────────┴─────────┴──────────────┴──────────────────┘
```

#### Interactive REPL Mode
```
$ sl-repl

SL Transport REPL
Examples:
  1002                      (departure query: just site ID)
  1002 line:17 direction:1  (departure query: with line and direction)
  lookup:id 1002            (site lookup: find site by ID)
  lookup:name odenplan      (site lookup: find sites by name)

Enter 'quit' to exit
Use ↑/↓ arrows to access command history

Enter query: 1002 line:17
[Results displayed...]

Enter query: quit
```

TODO: ADD SCREENSHOTS

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
from sl_transit_repl import SLTransitREPL

# Create REPL instance with default app directory
repl = SLTransitREPL()

# Or create REPL instance with custom app directory
repl = SLTransitREPL(app_dir="~/custom_transit_data")

# Run interactive session
repl.run()

# Execute single queries programmatically
success = repl.execute_query("1002 line:17")
success = repl.execute_query("lookup:name central")

# Or use individual methods programmatically
site = repl._find_site_by_id(1002)
sites = repl._find_sites_by_substring("central")
```

## Files & Directory Structure

The application creates a hidden directory in your home folder:

```
~/.sl_transit_repl/           # Main application directory
├── cache/                    # Cached API data
│   └── sites.json           # Site data with fetch timestamps
└── .repl_history            # Command history for auto-completion
```

### File Descriptions

- **`~/.sl_transit_repl/cache/sites.json`**: Cached site data from SL API with metadata including:
  - Site information (names, IDs, coordinates, aliases)
  - Fetch timestamp for cache validation
  - Version information for future compatibility

- **`~/.sl_transit_repl/.repl_history`**: Command history for the interactive REPL session
  - Enables ↑/↓ arrow key navigation through previous commands
  - Persists between sessions

- **Configuration**: Line colors, transport modes, and time thresholds are defined as class constants in the source code
