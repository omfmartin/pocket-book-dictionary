# Wiktionary to PocketBook Dictionary Converter

Transforms Wiktionary content from Kiwix zim files into PocketBook-compatible dictionaries in either Lingvo DSL or XDXF format. Supports extracting entries for specific languages (e.g., extracting only Russian entries from English Wiktionary).

## System Requirements

- Linux-based operating system
- Wine (install on Ubuntu with `sudo apt-get install wine`)
- Zimdump from zim-tools (`sudo apt-get install zim-tools`)
- Python 3 (typically pre-installed or available via `sudo apt-get install python3`)
- Python dependencies: BeautifulSoup4, tqdm (install via `pip install -r requirements.txt`)

**Additional Resources:**
- Wiktionary zim files for your language from [Kiwix Library](https://library.kiwix.org/)
- PocketBook converter tool from [PocketBook Support](https://www.pocketbook-int.com/ge/support/pocketbook-touch)
- Language files at [LanguageFiles GitHub Repository](https://github.com/Markismus/LanguageFilesPocketbookConverter/tree/main)

## Project Structure

```
/
├── converter/           # Converter.exe, language directories, Instruction.rtf
├── data/                # Zim files and dumped data
├── dict/                # Processed .dsl and .xdxf files and final dictionary outputs
└── src/                 # Python scripts (e.g., main.py) for data processing
```

## Installation and Usage

### Setting Up the Environment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/omfmartin/pocket-book-dictionary
   cd pocket-book-dictionary
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
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
   python src/main.py -i data/ca/A -o dict/ca.xdxf -s ca -t ca -f xdxf
   ```
   
   **Extract specific language entries from a different Wiktionary:**
   ```bash
   python src/main.py -i data/en/A -o dict/ru_from_en.xdxf -s en -t ru -e ru -f xdxf
   ```
   This example extracts Russian entries from English Wiktionary files.
   
   **Process with performance optimizations:**
   ```bash
   python src/main.py -i data/en/A -o dict/en.xdxf -s en -t en -f xdxf --batch-size 2000 -j 8
   ```
   This processes files in batches of 2000 using 8 parallel processes.
   
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
   - `--batch-size`: Number of files to process in each batch (default: 1000)
   - `--temp-dir`: Directory for temporary files (default: system temp directory)
   - `--excluded-sections`: Sections to exclude from extraction (default: Translations, Miscellany, See also, etc.)

### Performance Considerations

- Increase `--batch-size` for faster processing, but higher memory usage
- Adjust `-j` (jobs) based on your CPU cores for optimal performance
- The script uses a two-phase approach to efficiently process large datasets:
  1. Initial scan to identify valid entries
  2. Detailed processing of only valid entries
- For very large dictionaries, consider processing directory by directory

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
- **Slow processing**: Increase `--batch-size` and `-j` values, ensure you're not processing hidden files
- **Missing entries**: Check language codes and ensure proper language section extraction
- **Encoding issues**: The script uses UTF-8 encoding; ensure your source files are properly encoded

## Advanced Usage

### Custom Section Exclusion

To customize which sections are excluded from the dictionary:

```bash
python src/main.py -i data/en/A -o dict/en.dsl -s en -t en -f lingvo --excluded-sections "Translations" "Etymology" "Pronunciation"
```

This will exclude the specified sections from the output dictionary.
