#!/usr/bin/env python3

import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import unidecode
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.table import Table


class SLTransitREPL:
    """Self-contained class for SL Transit departure queries with interactive REPL interface."""

    # Class constants
    BASE_URL = "https://transport.integration.sl.se/v1"
    TRANSPORT_MODES = ["BUS", "TRAM", "METRO", "TRAIN", "FERRY", "SHIP", "TAXI"]
    VALID_PARAMS = {
        "site": r"\d+",
        "transport": f"({'|'.join(TRANSPORT_MODES)})",
        "line": r"\d+",
        "direction": r"[12]",
        "forecast": r"\d+",
        "show_numbers": r"(?:true|false|TRUE|FALSE)",
        "debug": r"(?:true|false|TRUE|FALSE)",
    }
    DEFAULT_FORECAST = 60

    # Color configuration for transport modes
    TRANSPORT_COLORS = {
        "BUS": "red3",  # #BF616A variant
        "TRAM": "orange3",
        "METRO": "blue3",  # #007FC8 variant
        "TRAIN": "magenta",
        "FERRY": "purple",
        "SHIP": "dark_green",
        "TAXI": "yellow",
    }

    # Line colors configuration from Stockholm transit system (terminal-friendly approximations)
    # the names are for reference only, not used in code for anything
    # full subway map link on this SL page: https://sl.se/reseplanering/kartor/spartrafikkartor
    LINE_COLORS = defaultdict(
        lambda: {"color": "white", "name": "Unknown Line"},
        {
            "12": {"color": "green4", "name": "Nockebybanan"},
            "21": {"color": "purple", "name": "Lidingöbanan"},
            "25": {"color": "light_sea_green", "name": "Saltsjöbanan"},
            "26": {"color": "light_sea_green", "name": "Saltsjöbanan"},
            "27": {"color": "purple3", "name": "Roslagsbanan"},
            "28": {"color": "purple3", "name": "Roslagsbanan"},
            "29": {"color": "purple3", "name": "Roslagsbanan"},
            "30": {"color": "orange3", "name": "Tvärbanan"},
            "31": {"color": "orange3", "name": "Tvärbanan"},
            "7": {"color": "grey58", "name": "Spårväg City"},
            "10": {"color": "blue", "name": "Blue Line - Hjulsta to Kungsträdgården"},
            "11": {"color": "blue", "name": "Blue Line - Akalla to Kungsträdgården"},
            "13": {"color": "red", "name": "Red Line - Norsborg to Ropsten"},
            "14": {"color": "red", "name": "Red Line - Fruängen to Mörby centrum"},
            "17": {"color": "green", "name": "Green Line - Åkeshov to Skarpnäck"},
            "18": {"color": "green", "name": "Green Line - Alvik to Farsta strand"},
            "19": {
                "color": "green",
                "name": "Green Line - Hässelby strand to Hagsätra",
            },
            "40": {
                "color": TRANSPORT_COLORS["TRAIN"],
                "name": "Pendeltåg - Uppsala C to Södertälje centrum",
            },
            "41": {
                "color": TRANSPORT_COLORS["TRAIN"],
                "name": "Pendeltåg - Märsta to Södertälje centrum",
            },
            "42X": {
                "color": TRANSPORT_COLORS["TRAIN"],
                "name": "Pendeltåg - Märsta to Nynäshamn",
            },
            "43": {
                "color": TRANSPORT_COLORS["TRAIN"],
                "name": "Pendeltåg - Bålsta to Nynäshamn",
            },
            "44": {
                "color": TRANSPORT_COLORS["TRAIN"],
                "name": "Pendeltåg - Kallhäll to Tumba",
            },
            "48": {
                "color": TRANSPORT_COLORS["TRAIN"],
                "name": "Pendeltåg - Södertälje centrum to Gnesta",
            },
        },
    )

    # Time-based color thresholds (in minutes)
    TIME_WARNING_THRESHOLD = 15  # <15min gets green color
    TIME_DELAY_THRESHOLD = 5  # >5min difference gets red color

    def __init__(self, app_dir: str | Path | None = None):
        """Initialize the SL Transit REPL.

        Args:
            app_dir: Optional path to application directory. If None, uses '~/.sl_transit_repl'.

        The application directory will contain the following files:
        - cache/sites.json: Cached sites data
        - .repl_history: History file for the REPL
        """
        # Set up app directory
        if app_dir:
            self.app_dir = Path(app_dir).expanduser()
        else:
            self.app_dir = Path.home() / ".sl_transit_repl"

        self.app_dir.mkdir(exist_ok=True)

        # Set up paths within app directory
        self.cache_dir = self.app_dir / "cache"
        self.sites_json = self.cache_dir / "sites.json"
        self.history_file = str(self.app_dir / ".repl_history")

        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize console and load sites
        self.console = Console()
        self.sites = self._load_sites()

        # Build search indices for site lookup functionality
        self._build_search_indices()

    def _fetch_sites(self) -> dict[str, dict[str, Any]]:
        """Fetch all sites from the API and return as a dictionary keyed by site ID."""
        try:
            response = requests.get(f"{self.BASE_URL}/sites")
            response.raise_for_status()
            sites = response.json()

            # Transform the list into a dictionary keyed by site ID
            return {str(site["id"]): site for site in sites}
        except requests.RequestException as e:
            self.console.print(f"[red]Error fetching sites: {str(e)}[/red]")
            return {}

    def _load_sites(self) -> dict[str, dict[str, Any]]:
        """Load sites dictionary from JSON file or fetch from API if needed."""
        sites = {}
        need_fetch = True

        try:
            if self.sites_json.exists():
                with self.sites_json.open("r") as f:
                    cache_data = json.load(f)

                    # Handle new format with metadata
                    if (
                        isinstance(cache_data, dict)
                        and "metadata" in cache_data
                        and "sites" in cache_data
                    ):
                        sites = cache_data["sites"]
                        fetch_date_str = cache_data["metadata"].get("fetch_date")
                        if fetch_date_str:
                            # Store metadata for potential future use
                            self._cache_metadata = cache_data["metadata"]
                            need_fetch = self._is_cache_stale()
                        else:
                            # No fetch date, treat as stale
                            need_fetch = True
                        # Don't set need_fetch = False here if we have metadata
        except (json.JSONDecodeError, OSError) as e:
            self.console.print(
                f"[yellow]Warning: Could not read sites cache: {e}[/yellow]"
            )

        if need_fetch:
            sites = self._fetch_sites()
            self._save_sites(sites)

        return sites

    def _save_sites(self, sites: dict[str, dict[str, Any]]) -> None:
        """Save sites dictionary to JSON file with metadata including fetch timestamp."""
        try:
            cache_data = {
                "metadata": {
                    "fetch_date": datetime.now().isoformat(),
                    "version": "1.0",
                },
                "sites": sites,
            }
            with self.sites_json.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            self.console.print(
                f"[yellow]Warning: Could not save sites cache: {e}[/yellow]"
            )

    def _is_cache_stale(self, max_age_hours: int = 24) -> bool:
        """Check if the cached data is stale based on fetch date.

        Args:
            max_age_hours: Maximum age of cache in hours before considering it stale

        Returns:
            True if cache is stale or no metadata available, False otherwise
        """
        if not hasattr(self, "_cache_metadata") or not self._cache_metadata:
            return True

        fetch_date_str = self._cache_metadata.get("fetch_date")
        if not fetch_date_str:
            return True

        try:
            fetch_date = datetime.fromisoformat(fetch_date_str)
            age = (
                datetime.now() - fetch_date
            ).total_seconds() / 3600  # Convert to hours
            return age > max_age_hours
        except (ValueError, TypeError):
            return True

    def _get_site_info(self, site_id: str) -> dict[str, Any] | None:
        """Get site information and validate it exists."""
        if site_id not in self.sites:
            self.console.print(
                f"[red]Error: Site ID {site_id} not found in known sites.[/red]"
            )
            self.console.print(
                f"[yellow]Hint: Delete {self.sites_json} to refresh the sites cache.[/yellow]"
            )
            return None
        return self.sites[site_id]

    def _build_search_indices(self) -> None:
        """Build search indices for site lookup functionality."""
        self.idx_by_id: dict[int, dict] = {}
        self.idx_by_name: list[
            tuple[str, dict]
        ] = []  # List of (normalized_name, site_data) tuples

        # Convert sites dict to list format like site_search.py expects
        sites_list = list(self.sites.values())

        for site in sites_list:
            # Index by ID
            self.idx_by_id[site["id"]] = site

            # Create normalized name for fuzzy matching
            normalized_name = self._normalize_text(site["name"])
            self.idx_by_name.append((normalized_name, site))

            # Also index aliases if they exist
            if "alias" in site:
                for alias in site["alias"]:
                    normalized_alias = self._normalize_text(alias)
                    self.idx_by_name.append((normalized_alias, site))

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing diacritics and converting to lowercase."""
        return unidecode.unidecode(text.lower())

    def _find_site_by_id(self, site_id: int) -> dict | None:
        """Find a site by its ID."""
        return self.idx_by_id.get(site_id)

    def _find_sites_by_substring(self, substring: str) -> list[dict]:
        """Find sites where the name contains the given substring.
        Matches are diacritic-insensitive and case-insensitive."""
        normalized_query = self._normalize_text(substring)
        results = []
        seen = set()  # To avoid duplicates

        for norm_name, site in self.idx_by_name:
            if normalized_query in norm_name and site["id"] not in seen:
                results.append(site)
                seen.add(site["id"])

        return sorted(results, key=lambda x: x["name"])

    def _create_site_table(self, sites: list[dict] | dict, title: str) -> Table:
        """Create a rich table for displaying site results."""
        if not isinstance(sites, list):
            sites = [sites]

        table = Table(title=title, show_header=True)
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Aliases", style="yellow")
        table.add_column("Abbreviation", style="blue")
        table.add_column("Coordinates", style="magenta")

        for site in sites:
            if site:  # Skip None results
                aliases = ", ".join(site.get("alias", [])) if "alias" in site else ""
                coords = f"{site['lat']:.4f}, {site['lon']:.4f}"
                table.add_row(
                    str(site["id"]),
                    site["name"],
                    aliases,
                    site.get("abbreviation", ""),
                    coords,
                )

        return table

    def _create_departure_table(
        self, departures: list, show_direction_numbers: bool = False
    ) -> Table:
        """Create a rich table for departures."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Line")
        table.add_column("Transport")
        table.add_column("Direction")
        table.add_column("Scheduled")
        table.add_column("Expected")
        table.add_column("Status")
        table.add_column("Platform")

        for dep in departures:
            line = dep["line"].get("designation", str(dep["line"]["id"]))
            transport = dep["line"].get("transport_mode", "N/A")
            direction_code = dep.get("direction_code", "N/A")
            direction = dep.get("direction", "N/A")

            # Format direction with number if requested
            if show_direction_numbers and direction_code != "N/A":
                direction = f"({direction_code}) {direction}"

            scheduled_time = datetime.fromisoformat(dep["scheduled"])
            expected_time = (
                datetime.fromisoformat(dep["expected"])
                if "expected" in dep
                else scheduled_time
            )
            scheduled = scheduled_time.strftime("%H:%M")
            expected = expected_time.strftime("%H:%M")
            status = dep["state"]
            platform = dep["stop_point"].get("designation", "N/A")

            # Apply colors
            # Line color (and direction gets same color)
            line_color = self.LINE_COLORS[line]["color"]
            colored_line = f"[{line_color}]{line}[/{line_color}]"
            colored_direction = f"[{line_color}]{direction}[/{line_color}]"

            # Transport color
            # transport_color = self.TRANSPORT_COLORS.get(transport, "white")
            # colored_transport = f"[{transport_color}]{transport}[/{transport_color}]"

            # Status color
            if status == "CANCELLED":
                colored_status = f"[red3]{status}[/red3]"
            elif status == "ATSTOP":
                colored_status = f"[bold]{status}[/bold]"
            elif status == "EXPECTED":
                colored_status = f"[dim]{status}[/dim]"
            else:
                colored_status = status

            # Time colors - check if within warning threshold or delayed
            # Use timezone-aware datetime if the parsed times have timezone info
            if scheduled_time.tzinfo is not None:
                now = datetime.now(scheduled_time.tzinfo)
            else:
                now = datetime.now()

            scheduled_diff = (scheduled_time - now).total_seconds() / 60
            expected_diff = (expected_time - now).total_seconds() / 60
            time_delay = abs((expected_time - scheduled_time).total_seconds() / 60)

            # Color scheduled time if within 15 minutes
            if 0 <= scheduled_diff <= self.TIME_WARNING_THRESHOLD:
                colored_scheduled = f"[dark_cyan]{scheduled}[/dark_cyan]"
            else:
                colored_scheduled = f"[dim]{scheduled}[/dim]"

            # Color expected time based on proximity and delay
            if 0 <= expected_diff <= self.TIME_WARNING_THRESHOLD:
                colored_expected = f"[dark_cyan]{expected}[/dark_cyan]"
            elif time_delay > self.TIME_DELAY_THRESHOLD:
                colored_expected = f"[red]{expected}[/red]"
            else:
                colored_expected = f"[dim]{expected}[/dim]"

            table.add_row(
                colored_line,
                transport,  # colored_transport seemed too distracting
                colored_direction,
                colored_scheduled,
                colored_expected,
                colored_status,
                platform,
            )

        return table

    def _get_departures(
        self,
        site_id: int,
        params: dict[str, Any],
        show_direction_numbers: bool = False,
        debug: bool = False,
        site_info: dict[str, Any] | None = None,
    ) -> None:
        """Fetch and display departures for a given site ID."""
        try:
            # Remove show_numbers from API params if present
            api_params = params.copy()
            api_params.pop("show_numbers", None)

            # Extract headers from underscore-prefixed parameters
            headers = {}
            for param, value in list(api_params.items()):
                if param.startswith("_"):
                    # Remove underscore prefix and use as header name
                    header_name = param[1:].replace("_", "-")
                    headers[header_name] = value
                    api_params.pop(param)

            if debug:
                self.console.print("\n[bold yellow]Request Headers:[/bold yellow]")
                for header, value in headers.items():
                    self.console.print(f"{header}: {value}")
                self.console.print("\n")

            # cache busting
            api_params["_t"] = str(
                int(time.time() * 1000)
            )  # Current timestamp in milliseconds

            response = requests.get(
                f"{self.BASE_URL}/sites/{site_id}/departures",
                params=api_params,
                headers=headers,
            )

            if debug:
                self.console.print("\n[bold yellow]Response Headers:[/bold yellow]")
                for header, value in response.headers.items():
                    self.console.print(f"{header}: {value}")
                self.console.print("\n")

            data = response.json()

            if not data.get("departures"):
                self.console.print(
                    "[yellow]No departures found for the given criteria.[/yellow]"
                )
                return

            # Display site information
            if site_info:
                site_name = site_info["name"]
                self.console.print(
                    f"\n[bold white]Site: {site_name} ({site_id})[/bold white]"
                )
                if site_info.get("note"):
                    self.console.print(f"[blue]{site_info['note']}[/blue]")
            else:
                self.console.print(f"\n[bold blue]Site ID: {site_id}[/bold blue]")

            table = self._create_departure_table(
                data["departures"], show_direction_numbers
            )
            self.console.print(table)

            # Display any deviations
            if data.get("stop_deviations"):
                self.console.print("\n[bold red]Deviations:[/bold red]")
                for dev in data["stop_deviations"]:
                    self.console.print(f"- {dev['message']}")

        except requests.RequestException as e:
            self.console.print(f"[red]Error fetching departures: {str(e)}[/red]")

    def _parse_query(self, query: str) -> tuple[bool, dict[str, str]]:
        """Parse the input query and return parameters."""
        # Initialize parameters
        params = {}

        # Split the query into parts
        parts = query.strip().split()

        if not parts:
            return False, {"error": ""}

        # Check for special commands first
        first_part = parts[0].lower()

        if first_part == "help":
            return True, {"command": "help"}

        if first_part.startswith("lookup:"):
            lookup_type = first_part.split(":", 1)[1].lower()
            if lookup_type not in ["id", "name"]:
                return False, {
                    "error": f"Invalid lookup type: {lookup_type}. Must be 'id' or 'name'"
                }

            if len(parts) < 2:
                return False, {"error": f"Lookup {lookup_type} requires a search term"}

            search_term = " ".join(parts[1:])  # Join all remaining parts as search term

            return True, {
                "command": "lookup",
                "lookup_type": lookup_type,
                "search_term": search_term,
            }

        # If first part doesn't have a label, assume it's the site ID
        if ":" not in parts[0]:
            if not re.match(r"^\d+$", parts[0]):
                return False, {"error": f"Invalid site ID: {parts[0]}"}
            params["site"] = parts[0]
            parts = parts[1:]

        # Process labeled parameters
        for part in parts:
            if ":" not in part:
                return False, {
                    "error": f"Invalid parameter format: {part}. Must be param:value"
                }

            param, value = part.split(":", 1)
            param = param.lower()

            # Skip validation for underscore-prefixed parameters
            if param.startswith("_"):
                params[param] = value
                continue

            if param in ("transport"):
                value = value.upper()
            else:
                value = value.lower()

            # Validate parameter name
            if param not in self.VALID_PARAMS:
                return False, {"error": f"Invalid parameter name: {param}"}

            # Validate parameter value
            if not re.match(f"^{self.VALID_PARAMS[param]}$", value):
                return False, {"error": f"Invalid value for {param}: {value}"}

            params[param] = value

        # Ensure site ID is provided for departure queries
        if "site" not in params:
            return False, {"error": "Site ID is required"}

        return True, params

    def _create_completer(self) -> WordCompleter:
        """Create a completer for parameters and values."""
        words = []

        # Add special commands
        words.extend(["help", "lookup:id", "lookup:name"])

        # Add parameter names with colon
        for param in self.VALID_PARAMS:
            words.append(f"{param}:")
        # Add transport modes with prefix
        for mode in self.TRANSPORT_MODES:
            words.append(f"transport:{mode}")
        # Add directions with prefix
        words.extend(["direction:1", "direction:2"])
        # Add show_numbers options
        words.extend(["show_numbers:true", "show_numbers:false"])

        return WordCompleter(words, ignore_case=True, pattern=re.compile(r"^|[^\w:]"))

    def _show_help(self) -> None:
        """Display help information for available commands."""
        from rich.panel import Panel

        help_text = """[bold cyan]Available Commands:[/bold cyan]

[bold yellow]Departure Queries:[/bold yellow]
  [green]<site_id>[/green]                           - Get departures for site (e.g., 1002)
  [green]site:<site_id>[/green]                      - Explicit site parameter
  [green]<site_id> line:<line_id>[/green]            - Filter by line (e.g., 1002 line:17)
  [green]<site_id> direction:<1|2>[/green]           - Filter by direction
  [green]<site_id> transport:<mode>[/green]          - Filter by transport mode
  [green]<site_id> forecast:<minutes>[/green]        - Set forecast window (default: 60)
  [green]<site_id> show_numbers:true[/green]         - Show direction numbers
  [green]<site_id> debug:true[/green]                - Show request/response headers

[bold yellow]Site Lookup:[/bold yellow]
  [green]lookup:id <site_id>[/green]                 - Find site by ID (e.g., lookup:id 1002)
  [green]lookup:name <search_term>[/green]           - Find sites by name (e.g., lookup:name odenplan)

[bold yellow]Other Commands:[/bold yellow]
  [green]help[/green]                                - Show this help message
  [green]quit[/green]                                - Exit the program

[bold yellow]Transport Modes:[/bold yellow]
  BUS, TRAM, METRO, TRAIN, FERRY, SHIP, TAXI

[bold yellow]Examples:[/bold yellow]
  1002                                  - Basic departure lookup
  1002 line:17 direction:1              - Green line towards Åkeshov
  lookup:name central                   - Find stations with "central" in name
  lookup:id 9001                        - Find specific station by ID"""

        panel = Panel(
            help_text,
            title="[bold white]SL Transit REPL Help[/bold white]",
            border_style="blue",
        )
        self.console.print(panel)

    def run(self) -> None:
        """Run the interactive REPL session."""
        self.console.print("[bold blue]SL Transport REPL[/bold blue]")
        self.console.print("Examples:")
        self.console.print(
            "  1002                                              (departure query: just site ID)"
        )
        self.console.print(
            "  1002 line:17 direction:1                          (departure query: with line and direction)"
        )
        self.console.print(
            "  lookup:id 1002                                    (site lookup: find site by ID)"
        )
        self.console.print(
            "  lookup:name odenplan                               (site lookup: find sites by name)"
        )
        self.console.print(
            "  help                                              (show detailed help)"
        )
        self.console.print("\nEnter 'quit' to exit")
        self.console.print("Use ↑/↓ arrows to access command history\n")

        # Check sites data availability
        if not self.sites:
            self.console.print(
                "[red]Warning: No sites data available. Some features will be limited.[/red]"
            )

        try:
            self._run_loop()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Program interrupted by user[/yellow]")
            raise

    def _run_loop(self) -> None:
        completer = self._create_completer()
        history = FileHistory(self.history_file)
        # prompt_text = "Enter query (site[:id] [transport:mode] [line:id] [direction:1|2] [forecast:minutes] [show_numbers:true|false] [debug:true|false]): "
        prompt_text = "Enter query (site[:id] [line:id] [forecast:minutes]): "

        while True:
            # Get query with history support
            try:
                query = prompt(
                    prompt_text,
                    completer=completer,
                    history=history,
                    complete_while_typing=True,
                ).strip()
            except EOFError:
                break

            if query.lower() == "quit":
                break

            # Parse and validate query
            valid, result = self._parse_query(query)
            if not valid:
                if result["error"]:
                    self.console.print(f"[red]{result['error']}[/red]")
                continue

            # Handle special commands
            command = result.get("command")

            if command == "help":
                self._show_help()
                self.console.print("\n---\n")
                continue

            elif command == "lookup":
                lookup_type = result["lookup_type"]
                search_term = result["search_term"]

                if lookup_type == "id":
                    try:
                        site_id = int(search_term)
                        site = self._find_site_by_id(site_id)
                        if site:
                            table = self._create_site_table(
                                site, f"Site with ID {site_id}"
                            )
                            self.console.print(table)
                        else:
                            self.console.print(
                                f"[red]No site found with ID {site_id}[/red]"
                            )
                    except ValueError:
                        self.console.print(
                            "[red]Invalid ID format. Please enter a number.[/red]"
                        )

                elif lookup_type == "name":
                    sites = self._find_sites_by_substring(search_term)
                    if sites:
                        table = self._create_site_table(
                            sites, f"Sites matching '{search_term}'"
                        )
                        self.console.print(table)
                    else:
                        self.console.print(
                            f"[red]No sites found containing '{search_term}'[/red]"
                        )

                self.console.print("\n---\n")
                continue

            # Build API parameters for departure queries
            api_params = {"forecast": result.get("forecast", self.DEFAULT_FORECAST)}

            if "transport" in result:
                api_params["transport"] = result["transport"]
            if "direction" in result:
                api_params["direction"] = result["direction"]
            if "line" in result:
                api_params["line"] = result["line"]

            # Get show_numbers preference
            show_direction_numbers = result.get("show_numbers", "").lower() == "true"

            # Get debug preference
            debug = result.get("debug", "").lower() == "true"

            for key, value in result.items():
                if key.startswith("_"):
                    api_params[key] = value

            site_id = str(result["site"])

            # Get site info from our dictionary
            site_info = self._get_site_info(site_id)
            if not site_info:
                continue

            # Fetch and display departures
            self._get_departures(
                int(site_id), api_params, show_direction_numbers, debug, site_info
            )
            self.console.print("\n---\n")


def main():
    """Main entry point for the sl-repl CLI command."""
    try:
        repl = SLTransitREPL()
        repl.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
