# LaTeX Installation Guide for PDF Export

To enable PDF export functionality, you need to install a LaTeX distribution on your system.

## Windows

### Option 1: MiKTeX (Recommended)
1. Download MiKTeX from: https://miktex.org/download
2. Run the installer and follow the setup wizard
3. Choose "Install missing packages on-the-fly: Yes"
4. Restart your backend server after installation

### Option 2: TeX Live
1. Download TeX Live from: https://www.tug.org/texlive/acquire-netinst.html
2. Run the installer (this may take a while as it's a large installation)
3. Restart your backend server after installation

## macOS

### Using Homebrew (Recommended)
```bash
brew install --cask mactex
```

### Manual Installation
1. Download MacTeX from: https://www.tug.org/mactex/
2. Run the installer package
3. Restart your backend server after installation

## Linux

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install texlive-full
```

### CentOS/RHEL/Fedora
```bash
sudo yum install texlive-scheme-full
# or for newer versions:
sudo dnf install texlive-scheme-full
```

## Verification

After installation, verify that LaTeX is working:

```bash
pdflatex --version
```

You should see version information if LaTeX is properly installed.

## Restart Backend

After installing LaTeX, restart your backend server:

```bash
# In the backend directory
python start.py
```

The PDF export button should now be enabled in the frontend.

## Troubleshooting

### Common Issues

1. **"pdflatex not found" error**
   - Make sure LaTeX is in your system PATH
   - Restart your terminal/command prompt after installation
   - Restart the backend server

2. **"LaTeX compilation failed" error**
   - Check that all required LaTeX packages are installed
   - MiKTeX will automatically install missing packages
   - For TeX Live, you may need to install additional packages manually

3. **Permission errors**
   - Make sure the backend has write permissions to the temp directory
   - On Linux/macOS, check file permissions

### Package Requirements

The IEEE paper template requires these LaTeX packages:
- IEEEtran (IEEE document class)
- cite (citation management)
- amsmath, amssymb, amsfonts (math symbols)
- graphicx (graphics support)
- hyperref (hyperlinks)
- booktabs (table formatting)

Most LaTeX distributions include these packages by default.

## Testing

Once LaTeX is installed:

1. Generate some paper sections in the frontend
2. Click the "Export PDF" button
3. A properly formatted IEEE paper PDF should download

The PDF will include:
- IEEE conference paper formatting
- Proper title page with authors and affiliations
- Abstract and keywords
- All generated sections in order
- Bibliography with sample references
- Professional IEEE styling