# WPBD - Wiktionary PocketBook Dictionary Converter

WPBD (Wiktionary PocketBook Dictionary) transforms Wiktionary content from Kiwix zim files into PocketBook-compatible dictionaries in either Lingvo DSL or XDXF format. It supports extracting entries for specific languages (e.g., extracting only Russian entries from English Wiktionary) and filtering by writing systems for optimized processing.

## System Requirements

- Linux-based operating system
- Wine (install on Ubuntu with `sudo apt-get install wine`)
- Zimdump from zim-tools (`sudo apt-get install zim-tools`)
- Python 3.6+ (typically pre-installed or available via `sudo apt-get install python3`)
- Python dependencies: lxml, tqdm (installed automatically when you install the package)

**Additional Resources:**
- Wiktionary zim files for your language from [Kiwix Library](https://library.kiwix.org/)
- PocketBook converter tool from [PocketBook Support](https://www.pocketbook-int.com/ge/support/pocketbook-touch)
- Language files at [LanguageFiles GitHub Repository](https://github.com/Markismus/LanguageFilesPocketbookConverter/tree/main)

## Project Structure

```
├── converter/           # Converter.exe, language directories, Instruction.rtf
├── data/                # Zim files and dumped data
├── dict/                # Processed .dsl and .xdxf files and final dictionary outputs
├── pyproject.toml       # Package configuration
└── src/
    └── wpbd/           # Main package directory
        ├── __init__.py   # Package initialization
        ├── __main__.py   # Entry point script
        ├── parsers.py    # HTML parsing functions
        ├── extractors.py # Definition extraction
        ├── formatters.py # Output formatting
        ├── config.py     # Configuration and constants
        └── utils/
            ├── __init__.py
            ├── text.py   # Text processing utilities
            ├── scripts.py # Script/language detection
            └── logging.py # Logging utilities
```

## Installation and Usage

### Setting Up the Environment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/omfmartin/wpbd
   cd wpbd
   ```

2. **Install the Package**
   ```bash
   # For development (editable install)
   pip install -e .
   
   # For regular installation
   pip install .
   ```

   Alternatively, create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

### Data Processing

1. **Download Wiktionary Zim File**
   - Get the latest file for your language from [Kiwix](https://library.kiwix.org/)
   - Example: `wiktionary_ca_all_maxi_2024-06.zim` for Catalan
   - Place in the `data` directory

2. **Extract Zim Content**
   ```bash
   zimdump dump --dir=data/ca data/raw/wiktionary_ca_all_maxi_2024-06.zim
   ```

3. **Process the HTML Files**
   
   You can choose between two output formats and specify which language entries to extract:
   
   **Standard dictionary for single language:**
   ```bash
   wpbd -i data/ca/A -o dict/ca.xdxf -s ca -t ca -f xdxf
   ```
   
   **Extract specific language entries from a different Wiktionary:**
   ```bash
   wpbd -i data/en/A -o dict/ru_from_en.xdxf -s en -t ru -e ru -f xdxf
   ```
   This example extracts Russian entries from English Wiktionary files.
   
   **Filter by writing system (script):**
   ```bash
   wpbd -i data/en/A -o dict/cyrillic_from_en.xdxf -s en -t ru -e ru -f xdxf --scripts cyrillic
   ```
   This example processes only files with Cyrillic characters, significantly improving performance when targeting specific languages.

   **Combined optimizations example:**
   ```bash
   wpbd -i data/en/A -o dict/latin_en.xdxf -s en -t en -f xdxf --batch-size 5000 -j 16 --scripts latin
   ```
   Processes only Latin script words in batches of 5000 using 16 parallel processes for maximum performance.
   
   **Parameters:**
   - `-i, --input`: Input directory containing HTML files
   - `-o, --output`: Output file path (.dsl or .xdxf extension recommended)
   - `-s, --source-lang`: Source language code of the Wiktionary (e.g., en for English Wiktionary)
   - `-t, --target-lang`: Target language code for translations
   - `-e, --entry-lang`: Language of entries to extract (optional, use to extract specific language entries)
   - `-n, --name`: Dictionary name (default: "Wiktionary Dictionary")
   - `-f, --format`: Output format, either "lingvo" or "xdxf" (default is xdxf)
   - `-j, --jobs`: Number of parallel processes to use (default: number of CPU cores)
   - `-l, --limit`: Limit the number of files to process (0 for no limit, default: 0)
   - `--batch-size`: Number of files to process in each batch (default: 10000)
   - `--temp-dir`: Directory for temporary files (default: system temp directory)
   - `--excluded-sections`: Sections to exclude from extraction (default: Translations, Miscellany, See also, etc.)
   - `--scripts`: Filter files by writing system (e.g., latin, cyrillic, greek, chinese, japanese)
   - `--debug`: Enable detailed debug logging

### Performance Considerations

- **Script Filtering**: Use `--scripts` to dramatically reduce processing time by only including relevant writing systems
  - Available options: latin, cyrillic, greek, chinese, japanese, korean, arabic, hebrew, devanagari, thai
  - For example, when working with Russian entries, use `--scripts cyrillic` to skip non-Cyrillic words
  - For Western European languages, use `--scripts latin` to focus on Latin alphabet words

- **Optimized Processing**: WPBD uses lxml for HTML parsing (5-10x faster than BeautifulSoup)

- **Parallel Processing**: Adjust `-j` (jobs) based on your CPU cores for optimal performance
  - For modern multi-core processors, values between 8-16 can significantly improve speed

- **Batch Size**: Increase `--batch-size` for faster processing, but higher memory usage
  - Values between 5000-10000 offer good performance on systems with 16GB+ RAM

- **Workflow Strategy**: For very large dictionaries, consider:
  1. First filtering by script to reduce the dataset
  2. Processing directory by directory with appropriate batch sizes
  3. Combining outputs for final conversion

### Conversion to PocketBook Format

1. **Run the Converter**
   
   The PocketBook converter tool supports both DSL and XDXF formats:
   
   For Lingvo DSL files:
   ```bash
   wine converter/converter.exe dict/ca.dsl converter/ca
   ```
   
   For XDXF files:
   ```bash
   wine converter/converter.exe dict/ca.xdxf converter/ca
   ```
   
   Output files will be generated in the `converter/ca` directory in both cases.

### Deploy to Your E-Reader

- Connect your PocketBook via USB
- Copy the generated files to `system/dictionaries` on your device
- Eject safely and restart your device
- Access your new dictionary through the PocketBook dictionary interface

## Troubleshooting

- **Memory issues**: Reduce `--batch-size` to use less RAM
- **Slow processing**: Use script filtering with `--scripts`, increase `--batch-size` and `-j` values
- **Missing entries**: Check language codes and ensure proper language section extraction
- **Encoding issues**: WPBD uses UTF-8 encoding; ensure your source files are properly encoded
- **Import errors**: If you installed with pip but get import errors, check that your virtual environment is activated

## Advanced Usage

### Custom Section Exclusion

To customize which sections are excluded from the dictionary:

```bash
wpbd -i data/en/A -o dict/en.dsl -s en -t en -f lingvo --excluded-sections "Translations" "Etymology" "Pronunciation"
```

This will exclude the specified sections from the output dictionary.

### Combining Multiple Script Filters

To process words in multiple writing systems simultaneously:

```bash
wpbd -i data/en/A -o dict/mixed_script.xdxf -s en -t en -f xdxf --scripts latin cyrillic greek
```

This processes words in Latin, Cyrillic, and Greek scripts while skipping all others.

### Processing Multiple Directories

For large dictionaries, you may want to process directories separately and then combine:

```bash
# Process each alphabet directory
wpbd -i data/en/A -o dict/en_A.xdxf -s en -t en -f xdxf
wpbd -i data/en/B -o dict/en_B.xdxf -s en -t en -f xdxf
# ...and so on

# Combine results (you'll need to create a script for this)
cat dict/en_header.xdxf dict/en_A_content.xdxf dict/en_B_content.xdxf ... dict/en_footer.xdxf > dict/en_complete.xdxf
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Kiwix project for their excellent Wiktionary zim files
- PocketBook for their dictionary converter
- Contributors to the various language files and dictionaries
