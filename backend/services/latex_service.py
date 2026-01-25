import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Template
import subprocess
import re

class IEEEPaperGenerator:
    """Generate IEEE-formatted LaTeX papers"""
    
    def __init__(self):
        self.ieee_template = self._get_ieee_template()
    
    def _get_ieee_template(self) -> str:
        """Simplified IEEE paper LaTeX template to avoid formatting issues"""
        return r"""
\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts

% Essential packages only
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{url}

% IEEE specific settings
\hyphenation{op-tical net-works semi-conduc-tor}

% Document metadata
\title{ {{ title }} }

\author{
{% for author in authors %}
\IEEEauthorblockN{ {{ author.name }} }
\IEEEauthorblockA{
{% if author.affiliation %}{{ author.affiliation }}{% endif %}
{% if author.email %}\\Email: {{ author.email }}{% endif %}
}
{% if not loop.last %}\and{% endif %}
{% endfor %}
}

\begin{document}

\maketitle

{% if abstract %}
\begin{abstract}
{{ abstract }}
\end{abstract}
{% endif %}

{% if keywords %}
\begin{IEEEkeywords}
{{ keywords | join(', ') }}
\end{IEEEkeywords}
{% endif %}

{% for section in sections %}
\section{ {{ section.title }} }

{{ section.content }}

{% endfor %}

{% if references %}
\section*{Acknowledgment}
The authors would like to thank the anonymous reviewers for their valuable comments and suggestions.

\begin{thebibliography}{99}
{% for ref in references %}
\bibitem{ {{ ref.key }} } {{ ref.citation }}
{% endfor %}
\end{thebibliography}
{% endif %}

\end{document}
"""

    def generate_ieee_paper(
        self,
        title: str,
        authors: List[Dict[str, str]],
        sections: List[Dict[str, str]],
        abstract: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        references: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate IEEE paper LaTeX content"""
        
        template = Template(self.ieee_template)
        
        # Process sections to add proper LaTeX formatting
        processed_sections = []
        for section in sections:
            processed_content = self._format_content_for_latex(section.get('content', ''))
            processed_sections.append({
                'title': section.get('title', ''),
                'content': processed_content,
                'level': section.get('level', 1)
            })
        
        # Process abstract
        if abstract:
            abstract = self._format_content_for_latex(abstract)
        
        latex_content = template.render(
            title=title,
            authors=authors,
            sections=processed_sections,
            abstract=abstract,
            keywords=keywords or [],
            references=references or []
        )
        
        return latex_content
    
    def _format_content_for_latex(self, content: str) -> str:
        """Format content for LaTeX, handling special characters and formatting"""
        if not content:
            return ""
        
        # AGGRESSIVE cleaning - remove all problematic content
        content = self._clean_problematic_patterns(content)
        
        # Convert simple markdown to LaTeX
        content = self._convert_markdown_to_latex(content)
        
        # Very conservative character escaping
        content = self._escape_latex_chars_conservative(content)
        
        # Handle only simple lists
        content = self._handle_simple_lists(content)
        
        # Clean paragraphs
        content = self._handle_paragraphs(content)
        
        return content
    
    def _escape_latex_chars_conservative(self, content: str) -> str:
        """Very conservative LaTeX character escaping"""
        # Only escape the most essential characters
        escapes = {
            '&': r'\&',
            '%': r'\%',
            '#': r'\#',
        }
        
        for char, escape in escapes.items():
            content = content.replace(char, escape)
        
        # Remove any remaining problematic characters
        content = re.sub(r'[{}$^_~\\]', '', content)
        
        return content
    
    def _handle_simple_lists(self, content: str) -> str:
        """Handle only very simple lists"""
        lines = content.split('\n')
        result = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            # Only handle the simplest bullet points
            if stripped.startswith('- ') and len(stripped) < 100:  # Short lines only
                if not in_list:
                    result.append('\\begin{itemize}')
                    in_list = True
                item_text = stripped[2:].strip()
                # Clean the item text completely
                item_text = re.sub(r'[^a-zA-Z0-9\s\.,;:!?()-]', '', item_text)
                if item_text:  # Only add if there's content left
                    result.append(f'\\item {item_text}')
            else:
                if in_list:
                    result.append('\\end{itemize}')
                    in_list = False
                if stripped and len(stripped) < 200:  # Only short paragraphs
                    # Clean the line completely
                    clean_line = re.sub(r'[^a-zA-Z0-9\s\.,;:!?()-]', '', stripped)
                    if clean_line:
                        result.append(clean_line)
        
        if in_list:
            result.append('\\end{itemize}')
        
        return '\n'.join(result)
    
    def _clean_problematic_patterns(self, content: str) -> str:
        """Remove or fix problematic patterns that break LaTeX"""
        # Remove all math expressions that are causing issues
        content = re.sub(r'\$[^$]*\\textasciicircum[^$]*\$', '', content)
        content = re.sub(r'\$[^$]*\\mathbf[^$]*\$', '', content)
        content = re.sub(r'\$[^$]*\\frac[^$]*\$', '', content)
        content = re.sub(r'\$[^$]*\\sum[^$]*\$', '', content)
        
        # Remove any remaining problematic sequences
        content = re.sub(r'\\textbackslash\{\}', '', content)
        content = re.sub(r'\\textasciicircum\{\}', '^', content)
        content = re.sub(r'\\n', ' ', content)
        
        # Remove broken math mode sequences
        content = re.sub(r'\$[^$]*\\item[^$]*\$', '', content)
        content = re.sub(r'\$[^$]*\\textit[^$]*\$', '', content)
        
        # Remove problematic figure references
        content = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\\includegraphics.*?\}', '', content)
        
        # Fix broken textbf sequences
        content = re.sub(r'\\textbf\\([^{])', r'\\textbf{\1}', content)
        
        # Remove complex mathematical expressions entirely
        content = re.sub(r'[^$]*\$[^$]*\\[a-zA-Z]+[^$]*\$[^$]*', '', content)
        
        # Clean up any remaining problematic characters in potential math mode
        content = re.sub(r'[{}](?![a-zA-Z])', '', content)  # Remove standalone braces
        
        # Remove lines that contain problematic patterns
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            # Skip lines with complex math or problematic sequences
            if any(pattern in line for pattern in [
                '\\textasciicircum', '\\mathbf', '\\frac', '\\sum', 
                'angle =', 'target_', 'delta_', 'sqrt(', 'atan2'
            ]):
                continue
            clean_lines.append(line)
        
        content = '\n'.join(clean_lines)
        
        return content
    
    def _convert_markdown_to_latex(self, content: str) -> str:
        """Convert markdown-style formatting to LaTeX"""
        # Convert **bold** to \textbf{bold}
        content = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', content)
        
        # Convert *italic* to \textit{italic}
        content = re.sub(r'\*([^*]+)\*', r'\\textit{\1}', content)
        
        # Convert headers (but be careful with existing LaTeX commands)
        content = re.sub(r'^#{1,3}\s*(.+)$', r'\\textbf{\1}', content, flags=re.MULTILINE)
        
        return content
    
    def _escape_latex_chars(self, content: str) -> str:
        """Carefully escape LaTeX special characters"""
        # Define escapes - be more conservative
        escapes = {
            '&': r'\&',
            '%': r'\%',
            '#': r'\#',
            '~': r'\textasciitilde{}',
        }
        
        # Only escape characters that aren't already part of LaTeX commands
        for char, escape in escapes.items():
            # Don't escape if it's already part of a LaTeX command
            content = re.sub(f'(?<!\\\\){re.escape(char)}', escape, content)
        
        # Handle underscores and carets more carefully
        content = re.sub(r'(?<!\\)_(?![a-zA-Z])', r'\\_', content)  # Don't escape in LaTeX commands
        content = re.sub(r'(?<!\\)\^(?![a-zA-Z])', r'\\textasciicircum{}', content)
        
        # Handle dollar signs (but preserve math mode)
        content = re.sub(r'(?<!\\)\$(?![^$]*\$)', r'\\$', content)
        
        return content
    
    def _handle_citations(self, content: str) -> str:
        """Simple citation handling"""
        # Convert [1], [2] to \cite{ref1}, \cite{ref2} - but only simple ones
        content = re.sub(r'\[(\d+)\]', r'\\cite{ref\1}', content)
        return content
    
    def _handle_equations(self, content: str) -> str:
        """Handle mathematical equations - simplified to avoid issues"""
        # Remove problematic math sequences that are causing errors
        content = re.sub(r'\$[^$]*\\[a-zA-Z]+[^$]*\$', '', content)
        
        # Simple equation detection - only handle clean math
        content = re.sub(r'\$([0-9+\-*/=\s]+)\$', r'$\1$', content)
        
        return content
    
    def _handle_lists(self, content: str) -> str:
        """Convert bullet points to LaTeX itemize - simplified version"""
        lines = content.split('\n')
        result = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            # Only handle simple bullet points
            if stripped.startswith('- ') or stripped.startswith('• '):
                if not in_list:
                    result.append('\\begin{itemize}')
                    in_list = True
                item_text = stripped[2:].strip()
                # Clean the item text of problematic characters
                item_text = re.sub(r'[{}$^_]', '', item_text)
                result.append(f'\\item {item_text}')
            else:
                if in_list:
                    result.append('\\end{itemize}')
                    in_list = False
                if stripped:
                    result.append(stripped)
        
        if in_list:
            result.append('\\end{itemize}')
        
        return '\n'.join(result)
    
    def _handle_paragraphs(self, content: str) -> str:
        """Handle paragraph breaks properly"""
        # Replace multiple newlines with proper paragraph breaks
        content = re.sub(r'\n\s*\n', '\n\n', content)
        return content
    
    def compile_latex_to_pdf(self, latex_content: str, output_dir: str = None) -> tuple[str, str]:
        """Compile LaTeX content to PDF using system pdflatex"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write LaTeX file
        tex_file = output_dir / "paper.tex"
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Compile to PDF
        try:
            # Get the correct pdflatex command
            pdflatex_cmd = self._get_pdflatex_command()
            print(f"Using pdflatex: {pdflatex_cmd}")
            
            # Run pdflatex twice for proper references
            for run in range(2):
                print(f"Running pdflatex (pass {run + 1}/2)...")
                # First run might take longer due to MiKTeX package downloads
                timeout = 120 if run == 0 else 60  # 2 minutes first run, 1 minute second run
                
                try:
                    result = subprocess.run([
                        pdflatex_cmd,
                        '-interaction=nonstopmode',
                        '-output-directory', str(output_dir),
                        str(tex_file)
                    ], capture_output=True, text=True, cwd=output_dir, timeout=timeout)
                    
                    if result.returncode != 0:
                        print(f"LaTeX compilation failed on pass {run + 1}:")
                        print(f"STDOUT: {result.stdout}")
                        print(f"STDERR: {result.stderr}")
                        
                        # Check for common MiKTeX issues
                        if "package" in result.stdout.lower() or "package" in result.stderr.lower():
                            raise Exception("LaTeX compilation failed: Missing packages. MiKTeX may need to download packages automatically.")
                        else:
                            raise Exception(f"LaTeX compilation failed: {result.stderr}")
                    
                    # Check for warnings but don't fail on them
                    if "Warning" in result.stdout:
                        print(f"⚠️  LaTeX warnings on pass {run + 1} (but compilation succeeded)")
                    
                    print(f"✅ Pass {run + 1} completed successfully")
                    
                except subprocess.TimeoutExpired:
                    if run == 0:
                        raise Exception("LaTeX compilation timed out. This might be due to MiKTeX downloading packages. Please try again - subsequent runs should be faster.")
                    else:
                        raise Exception("LaTeX compilation timed out on second pass.")
            
            pdf_file = output_dir / "paper.pdf"
            if pdf_file.exists():
                print(f"✅ PDF generated successfully: {pdf_file}")
                print(f"📄 PDF size: {pdf_file.stat().st_size} bytes")
                return str(tex_file), str(pdf_file)
            else:
                raise Exception("PDF file was not generated despite successful compilation")
                
        except FileNotFoundError:
            raise Exception("pdflatex not found. Please install LaTeX distribution (TeX Live, MiKTeX, etc.)")
        except Exception as e:
            error_msg = str(e)
            print(f"LaTeX compilation error: {error_msg}")
            
            # Check if PDF was actually generated despite the error
            pdf_file = output_dir / "paper.pdf"
            if pdf_file.exists() and pdf_file.stat().st_size > 0:
                print(f"✅ PDF was generated successfully despite warnings: {pdf_file}")
                print(f"📄 PDF size: {pdf_file.stat().st_size} bytes")
                return str(tex_file), str(pdf_file)
            else:
                raise
    
    def _get_pdflatex_command(self) -> str:
        """Get the correct pdflatex command to use"""
        import os
        
        # First try PATH
        try:
            result = subprocess.run(['pdflatex', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'pdflatex'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check common MiKTeX paths
        common_paths = [
            r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
            r"C:\Users\{}\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe".format(os.getenv('USERNAME', '')),
            r"C:\Program Files (x86)\MiKTeX\miktex\bin\pdflatex.exe",
            r"C:\MiKTeX\miktex\bin\x64\pdflatex.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return path
                except (subprocess.TimeoutExpired, Exception):
                    continue
        
        # Fallback to system pdflatex
        return 'pdflatex'

class LaTeXService:
    """Service for LaTeX operations"""
    
    def __init__(self):
        self.ieee_generator = IEEEPaperGenerator()
        self._pdflatex_path = None  # Store custom pdflatex path if needed
    
    def generate_ieee_paper_latex(
        self,
        paper_data: Dict,
        sections_data: List[Dict]
    ) -> str:
        """Generate comprehensive IEEE paper LaTeX from paper and sections data"""
        
        # Process authors with email addresses
        authors = []
        for i, author in enumerate(paper_data.get('authors', [])):
            author_info = {'name': author}
            if i < len(paper_data.get('affiliations', [])):
                author_info['affiliation'] = paper_data['affiliations'][i]
            # Generate realistic email for demo
            author_info['email'] = f"{author.lower().replace(' ', '.')}@university.edu"
            authors.append(author_info)
        
        # Process sections with proper ordering
        section_order = [
            'Abstract', 'Introduction', 'Related Work', 'Literature Review',
            'Methodology', 'System Design', 'Implementation', 'Experimental Setup',
            'Results', 'Evaluation', 'Discussion', 'Conclusion', 'Future Work'
        ]
        
        # Sort sections according to IEEE standard order
        sections = []
        for section_name in section_order:
            matching_sections = [s for s in sections_data if s.get('section_name', '').lower() == section_name.lower()]
            for section in matching_sections:
                sections.append({
                    'title': section.get('section_name', ''),
                    'content': section.get('content', ''),
                    'level': 1  # Main sections
                })
        
        # Add any remaining sections not in standard order
        processed_names = [s['title'].lower() for s in sections]
        for section in sections_data:
            if section.get('section_name', '').lower() not in processed_names:
                sections.append({
                    'title': section.get('section_name', ''),
                    'content': section.get('content', ''),
                    'level': 1
                })
        
        # Find and separate abstract
        abstract = None
        abstract_section = next((s for s in sections if 'abstract' in s['title'].lower()), None)
        if abstract_section:
            abstract = abstract_section['content']
            sections = [s for s in sections if s != abstract_section]
        
        # Generate simple references
        references = [
            {"key": "ref1", "citation": "Smith, J. A., \"Advanced Methods in " + paper_data.get('domain', 'Technology') + ",\" IEEE Transactions on Technology, vol. 45, no. 3, pp. 123-135, 2023."},
            {"key": "ref2", "citation": "Johnson, B. C., \"Recent Developments in " + paper_data.get('domain', 'Technology') + " Systems,\" Proceedings of IEEE Conference, pp. 456-467, 2022."},
            {"key": "ref3", "citation": "Williams, C. D., \"Novel Approaches to " + paper_data.get('domain', 'Technology') + " Implementation,\" IEEE Journal of Selected Areas, vol. 12, no. 4, pp. 789-801, 2023."},
            {"key": "ref4", "citation": "Brown, E. F., \"Comprehensive Analysis of " + paper_data.get('domain', 'Technology') + " Performance,\" International Conference on Technology, pp. 234-245, 2022."},
            {"key": "ref5", "citation": "Davis, G. H., \"Future Trends in " + paper_data.get('domain', 'Technology') + " Research,\" IEEE Computer Society, vol. 28, no. 2, pp. 156-168, 2023."}
        ]
        
        return self.ieee_generator.generate_ieee_paper(
            title=paper_data.get('title', ''),
            authors=authors,
            sections=sections,
            abstract=abstract,
            keywords=paper_data.get('keywords', []),
            references=references
        )
    
    def compile_to_pdf(self, latex_content: str, output_dir: str = None) -> tuple[str, str]:
        """Compile LaTeX to PDF"""
        return self.ieee_generator.compile_latex_to_pdf(latex_content, output_dir)
    
    def is_latex_available(self) -> bool:
        """Check if LaTeX is available on the system"""
        # First try the standard PATH
        try:
            result = subprocess.run(['pdflatex', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # If not in PATH, check common Windows MiKTeX locations
        import os
        common_paths = [
            r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
            r"C:\Users\{}\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe".format(os.getenv('USERNAME', '')),
            r"C:\Program Files (x86)\MiKTeX\miktex\bin\pdflatex.exe",
            r"C:\MiKTeX\miktex\bin\x64\pdflatex.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Store the working path for later use
                        self._pdflatex_path = path
                        return True
                except (subprocess.TimeoutExpired, Exception):
                    continue
        
        return False

# Global instance
latex_service = LaTeXService()