# Test Suite for SL Transit REPL

This test suite provides comprehensive coverage for the SL Transit REPL application.

## Test Structure

```
tests/
├── unit/                    # Unit tests (138 tests)
│   ├── test_cache_management.py      # Cache staleness, metadata, file I/O
│   ├── test_query_parsing.py         # Command parsing, validation
│   ├── test_search_functionality.py  # Site search, text normalization
│   ├── test_file_io_and_errors.py    # File operations, error handling
│   ├── test_terminal_output.py       # Rich terminal display
│   └── test_cli_interface.py         # Command line interface, non-interactive mode
├── integration/             # Integration tests
│   └── test_api_integration.py       # API calls, network handling
├── fixtures/                # Test data files
│   ├── sample_sites.json
│   └── sample_departures.json
└── conftest.py             # Shared fixtures and configuration
```

## Key Test Areas

### 1. Cache Management (12 tests)
- ✅ Cache staleness detection (24-hour expiry)
- ✅ Metadata handling and timestamping
- ✅ Fresh vs stale cache behavior
- ✅ Corrupted JSON handling
- ✅ Permission error handling

### 2. Query Parsing (34 tests)
- ✅ Simple site ID queries
- ✅ Parameter validation (transport, direction, line, etc.)
- ✅ Special commands (help, lookup)
- ✅ Error handling for invalid inputs
- ✅ Case handling and normalization

### 3. Search Functionality (24 tests)
- ✅ Text normalization (diacritics, case)
- ✅ Site lookup by ID and name
- ✅ Substring matching
- ✅ Alias searching
- ✅ Result deduplication and sorting

### 4. File I/O & Error Handling (24 tests)
- ✅ App directory creation
- ✅ File permission handling
- ✅ Unicode preservation
- ✅ Initialization order
- ✅ Edge cases (readonly directories, large data)

### 5. Terminal Output Display (21 tests)
- ✅ Rich table formatting for sites and departures
- ✅ Color coding for lines, statuses, times
- ✅ Timezone-aware datetime handling
- ✅ Missing data graceful handling
- ✅ Help and completion display

### 6. Command Line Interface (21 tests)
- ✅ Single query execution (execute_query method)
- ✅ Non-interactive mode success/failure handling
- ✅ Command line argument parsing (main function)
- ✅ App directory parameter handling
- ✅ Help message and complex query parsing
- ✅ Exit code handling (success: 0, failure: 1)

### 7. API Integration (14 tests)
- ✅ Successful API calls (mocked)
- ✅ Network error handling
- ✅ Parameter passing and filtering
- ✅ Custom headers
- ✅ Cache busting
- ✅ Real API tests (skipped by default)

## Running Tests

```bash
# Run all unit tests
uv run pytest tests/unit/

# Run with coverage
uv run pytest tests/unit/ --cov=src/sl_transit_repl --cov-report=html

# Run specific test category
uv run pytest tests/unit/test_cache_management.py -v

# Run integration tests (may require network)
uv run pytest tests/integration/ -m integration

# Run all tests including skipped ones
uv run pytest tests/ --runslow
```

## Test Configuration

The test suite uses:
- **pytest** as the test runner
- **unittest.mock** for mocking external dependencies
- **tempfile** for isolated file system tests
- **parametrized tests** for comprehensive coverage
- **fixtures** for reusable test data

## Coverage

The test suite provides:
- **100% coverage** of core functionality including new CLI interface
- **Complete coverage** of both interactive and non-interactive modes
- **Argument parsing** and exit code validation
- **Timezone-aware testing** for datetime operations
- **Mock-based isolation** from external APIs
- **Edge case coverage** for error conditions
- **Cross-platform compatibility** testing
