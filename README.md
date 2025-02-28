# Wiktionary to PocketBook Dictionary Converter

Tansforms Wiktionary content from Kiwix zim files into a PocketBook dictionary.

## System Requirements
- Linux-based operating system
- Wine (install on Ubuntu with `sudo apt-get install wine`)
- Zimdump from zim-tools (`sudo apt-get install zim-tools`)
- Python 3 (typically pre-installed or available via `sudo apt-get install python3`)

**Additional Resources:**
- Wiktionary zim files for your language from [Kiwix Library](https://library.kiwix.org/)
- PocketBook converter tool from [PocketBook Support](https://www.pocketbook-int.com/ge/support/pocketbook-touch)
- Language files at [LanguageFiles GitHub Repository](https://github.com/Markismus/LanguageFilesPocketbookConverter/tree/main)

## Project Structure
```
/
├── converter/           # Converter.exe, language directories, Instruction.rtf
├── data/                # Zim files and dumped data
├── dict/                # Processed .dsl files and final dictionary outputs
└── src/                 # Python scripts (e.g., main.py) for data processing
```

## Installation and Usage

### Setting Up the Environment
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/yourprojectname
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
   zimdump dump --dir=data/ca data/wiktionary_ca_all_maxi_2024-06.zim
   ```

3. **Process the HTML Files**
   ```bash
   python src/main.py -i data/ca/ -o dict/ca.dsl -s ca -t ca
   ```
   This creates a .dsl dictionary file from the extracted HTML content.

### Conversion to PocketBook Format
1. **Run the Converter**
   ```bash
   wine converter/converter.exe dict/ca.dsl converter/ca
   ```
   Output files will be generated in `converter/ca` directory.

2. **Deploy to Your E-Reader**
   - Connect your PocketBook via USB
   - Copy the generated files to `system/dictionaries` on your device
   - Eject safely and restart your device
   - Access your new dictionary through the PocketBook dictionary interface

