#!/usr/bin/env python3
"""
Clean LaTeX Service for IEEE Conference Papers
Generates professional IEEE papers that compile reliably with MiKTeX
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import re

class IEEELaTeXGenerator:
    """Generate clean IEEE LaTeX papers that compile without errors"""
    
    def get_ieee_template(self) -> str:
        """Clean IEEE conference paper template with enhanced section headings"""
        return r"""\documentclass[conference,10pt]{IEEEtran}
\IEEEoverridecommandlockouts

% Packages
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{balance}
\usepackage{titlesec}

% Prevent text overflow
\sloppy
\hyphenpenalty=5000
\tolerance=1000

% Enhanced section formatting - bigger and bolder
\titleformat{\section}
  {\normalfont\fontsize{11}{13}\bfseries\scshape}
  {\thesection.}
  {0.5em}
  {}

\titleformat{\subsection}
  {\normalfont\fontsize{10.5}{12}\bfseries}
  {\thesubsection}
  {0.5em}
  {}

% Add more spacing around sections
\titlespacing*{\section}{0pt}{12pt plus 2pt minus 2pt}{8pt plus 2pt minus 2pt}
\titlespacing*{\subsection}{0pt}{10pt plus 2pt minus 2pt}{6pt plus 2pt minus 2pt}

% Title
\title{<<TITLE>>}

% Authors
<<AUTHORS>>

\begin{document}
\maketitle

% Abstract
<<ABSTRACT>>

% Keywords
<<KEYWORDS>>

% Sections
<<SECTIONS>>

% References
<<REFERENCES>>

% Balance columns on last page
\balance

\end{document}
"""
    
    def generate_authors_block(self, authors: List[Dict[str, str]]) -> str:
        """Generate properly formatted author block"""
        if not authors:
            return ""
        
        # Group authors by affiliation
        affiliation_groups = {}
        for author in authors:
            aff = author.get('affiliation', 'Unknown Institution')
            if aff not in affiliation_groups:
                affiliation_groups[aff] = []
            affiliation_groups[aff].append(author)
        
        # Generate author block
        author_lines = []
        author_lines.append(r"\author{")
        
        # If all authors share same affiliation
        if len(affiliation_groups) == 1:
            aff = list(affiliation_groups.keys())[0]
            author_names = [a['name'] for a in authors]
            
            author_lines.append(r"\IEEEauthorblockN{" + ", ".join(author_names) + "}")
            author_lines.append(r"\IEEEauthorblockA{" + aff + r"\\")
            
            # Add emails
            emails = [f"{a['name']}: {a.get('email', '')}" for a in authors if a.get('email')]
            if emails:
                author_lines.append(r"Email: " + ", ".join([a.get('email', '') for a in authors if a.get('email')]))
            author_lines.append("}")
        else:
            # Multiple affiliations
            for i, (aff, auth_list) in enumerate(affiliation_groups.items()):
                if i > 0:
                    author_lines.append(r"\and")
                
                author_names = [a['name'] for a in auth_list]
                author_lines.append(r"\IEEEauthorblockN{" + ", ".join(author_names) + "}")
                author_lines.append(r"\IEEEauthorblockA{" + aff + r"\\")
                
                emails = [a.get('email', '') for a in auth_list if a.get('email')]
                if emails:
                    author_lines.append(r"Email: " + ", ".join(emails))
                author_lines.append("}")
        
        author_lines.append("}")
        return "\n".join(author_lines)
    
    def clean_text_for_latex(self, text: str) -> str:
        """Clean text for LaTeX - escape special characters but preserve math and formatting"""
        if not text:
            return ""
        
        # CRITICAL: Remove Unicode artifacts and normalize text
        # Remove soft hyphens (U+00AD) that cause broken words
        text = text.replace('\u00ad', '')
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\u200c', '')  # Zero-width non-joiner
        text = text.replace('\u200d', '')  # Zero-width joiner
        text = text.replace('\ufeff', '')  # Zero-width no-break space
        
        # Normalize quotes and dashes
        text = text.replace('\u2018', "'")  # Left single quote
        text = text.replace('\u2019', "'")  # Right single quote
        text = text.replace('\u201c', '"')  # Left double quote
        text = text.replace('\u201d', '"')  # Right double quote
        text = text.replace('\u2013', '--')  # En dash
        text = text.replace('\u2014', '---')  # Em dash
        text = text.replace('\u2026', '...')  # Ellipsis
        
        # Remove any other problematic Unicode characters
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        
        # First, protect math expressions by temporarily replacing them
        math_expressions = []
        
        # Find and protect inline math $...$
        def protect_math(match):
            math_expressions.append(match.group(0))
            return f"MATH_PLACEHOLDER_{len(math_expressions)-1}"
        
        text = re.sub(r'\$[^\$]+\$', protect_math, text)
        
        # Find and protect display math \[...\]
        text = re.sub(r'\\\[.*?\\\]', protect_math, text, flags=re.DOTALL)
        
        # Handle inline bold text before escaping - be more careful
        # Only match if we have proper opening and closing **
        text = re.sub(r'\*\*([^*\n]+?)\*\*', r'\\textbf{\1}', text)
        
        # Handle inline italic text - be more careful
        # Only match single * that are properly paired and not part of **
        # Use negative lookbehind and lookahead to avoid matching **
        text = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', text)
        
        # Split by LaTeX commands to preserve them
        parts = re.split(r'(\\textbf\{[^}]+\}|\\textit\{[^}]+\}|\\[a-zA-Z]+\{[^}]+\}|MATH_PLACEHOLDER_\d+)', text)
        
        cleaned_parts = []
        for part in parts:
            if (part.startswith(r'\textbf{') or part.startswith(r'\textit{') or 
                part.startswith('MATH_PLACEHOLDER_') or part.startswith('\\')):
                # This is a LaTeX command or math placeholder, keep it as is
                cleaned_parts.append(part)
            else:
                # Escape special characters in regular text
                replacements = {
                    '&': r'\&',
                    '%': r'\%',
                    '#': r'\#',
                    '_': r'\_',
                    '{': r'\{',
                    '}': r'\}',
                    '~': r'\textasciitilde{}',
                    '^': r'\textasciicircum{}',
                }
                
                for char, replacement in replacements.items():
                    part = part.replace(char, replacement)
                
                cleaned_parts.append(part)
        
        result = ''.join(cleaned_parts)
        
        # Restore math expressions
        for i, math_expr in enumerate(math_expressions):
            result = result.replace(f"MATH_PLACEHOLDER_{i}", math_expr)
        
        # Final safety check - remove any unmatched * that might have slipped through
        result = result.replace('*', '')
        
        return result
    
    def remove_redundant_subsection_headings(self, content: str, section_title: str) -> str:
        """Remove redundant subsection headings that duplicate the section title"""
        if not content or not section_title:
            return content
        
        # Extract the core section name (e.g., "Introduction" from "I. INTRODUCTION")
        section_core = re.sub(r'^[IVX]+\.\s+', '', section_title, flags=re.IGNORECASE)
        section_core = section_core.strip().lower()
        
        # Pattern to match redundant subsection headings like:
        # "I-A Introduction", "I.A Introduction", "A. Introduction", etc.
        patterns = [
            # Roman numeral with letter: "I-A Introduction", "II-B Background"
            rf'^[IVX]+-[A-Z]\s+{re.escape(section_core)}\s*$',
            rf'^[IVX]+\.[A-Z]\s+{re.escape(section_core)}\s*$',
            # Just letter: "A. Introduction", "B. Background"
            rf'^[A-Z]\.\s+{re.escape(section_core)}\s*$',
            # Number with letter: "1-A Introduction"
            rf'^\d+-[A-Z]\s+{re.escape(section_core)}\s*$',
            rf'^\d+\.[A-Z]\s+{re.escape(section_core)}\s*$',
            # Just the section name as a heading
            rf'^{re.escape(section_core)}\s*$',
        ]
        
        lines = content.split('\n')
        cleaned_lines = []
        skip_next_empty = False
        
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            is_redundant = False
            
            # Check if this line matches any redundant pattern
            for pattern in patterns:
                if re.match(pattern, line_lower, flags=re.IGNORECASE):
                    is_redundant = True
                    skip_next_empty = True
                    break
            
            # Also check if it's a bold version: **I-A Introduction**
            if not is_redundant and line.strip().startswith('**') and line.strip().endswith('**'):
                inner = line.strip()[2:-2].strip().lower()
                for pattern in patterns:
                    if re.match(pattern, inner, flags=re.IGNORECASE):
                        is_redundant = True
                        skip_next_empty = True
                        break
            
            if is_redundant:
                continue
            
            # Skip empty lines immediately after redundant headings
            if skip_next_empty and not line.strip():
                skip_next_empty = False
                continue
            
            skip_next_empty = False
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def format_content(self, content: str, section_title: str = "") -> str:
        """Format content for LaTeX - handle all AI-generated formats including math"""
        if not content:
            return ""
        
        # First, remove redundant subsection headings
        if section_title:
            content = self.remove_redundant_subsection_headings(content, section_title)
        
        # Remove any stray backslashes at the start
        content = content.replace('\\\\', '').strip()
        
        # Handle markdown headers (##, ###) - convert to subsections
        content = re.sub(r'^###\s+(.+)$', r'**\1**', content, flags=re.MULTILINE)
        content = re.sub(r'^##\s+(.+)$', r'**\1**', content, flags=re.MULTILINE)
        
        # Handle pseudocode blocks - remove the markers
        content = re.sub(r"'''pseudocode", '', content)
        content = re.sub(r"'''", '', content)
        content = re.sub(r'```pseudocode', '', content)
        content = re.sub(r'```', '', content)
        
        # Handle mathematical expressions
        # Convert inline math: $expression$ stays as is
        # Convert display math: $$expression$$ to \[expression\]
        content = re.sub(r'\$\$([^\$]+)\$\$', r'\\[\1\\]', content)
        
        # Handle common math symbols that might be written as text
        content = content.replace('ˆ', '^')  # Fix caret symbol
        content = content.replace('∥', r'\\|')  # Norm symbol
        content = content.replace('≥', r'\\geq ')
        content = content.replace('≤', r'\\leq ')
        content = content.replace('×', r'\\times ')
        content = content.replace('÷', r'\\div ')
        content = content.replace('∑', r'\\sum ')
        content = content.replace('∏', r'\\prod ')
        content = content.replace('∫', r'\\int ')
        content = content.replace('√', r'\\sqrt ')
        content = content.replace('∞', r'\\infty ')
        content = content.replace('α', r'\\alpha ')
        content = content.replace('β', r'\\beta ')
        content = content.replace('γ', r'\\gamma ')
        content = content.replace('δ', r'\\delta ')
        content = content.replace('θ', r'\\theta ')
        content = content.replace('λ', r'\\lambda ')
        content = content.replace('μ', r'\\mu ')
        content = content.replace('σ', r'\\sigma ')
        content = content.replace('π', r'\\pi ')
        
        # The AI is generating LaTeX commands - we need to clean them up
        # Remove figure references and labels
        content = re.sub(r'\\label\{[^}]+\}', '', content)
        content = re.sub(r'\\ref\{[^}]+\}', '', content)
        content = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\\includegraphics.*?\}', '', content)
        
        # Handle sections/subsections that AI might generate
        content = re.sub(r'\\section\{([^}]+)\}', r'\n\n\1\n', content)
        content = re.sub(r'\\subsection\{([^}]+)\}', r'\n**\1**\n', content)
        content = re.sub(r'\\subsubsection\{([^}]+)\}', r'\n**\1**\n', content)
        
        # Handle itemize/enumerate environments
        content = re.sub(r'\\begin\{itemize\}', '', content)
        content = re.sub(r'\\end\{itemize\}', '', content)
        content = re.sub(r'\\begin\{enumerate\}', '', content)
        content = re.sub(r'\\end\{enumerate\}', '', content)
        
        # Handle item commands
        content = re.sub(r'\\item\s+', '- ', content)
        
        # Handle textbf, textit commands
        content = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', content)
        content = re.sub(r'\\textit\{([^}]+)\}', r'*\1*', content)
        
        # Remove any remaining LaTeX commands (but preserve math mode $...$)
        # Be careful not to remove $ signs that are part of math
        content = re.sub(r'\\[a-zA-Z]+\{([^}]+)\}', r'\1', content)
        content = re.sub(r'\\[a-zA-Z]+(?![a-zA-Z])', '', content)
        
        # Now process the cleaned content
        lines = []
        paragraphs = content.split('\n\n')
        in_itemize = False
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if it's a bold heading (subsection)
            if para.startswith('**') and para.endswith('**') and '\n' not in para:
                # Close any open itemize
                if in_itemize:
                    lines.append(r'\end{itemize}')
                    lines.append("")  # Add spacing after list
                    in_itemize = False
                
                heading = para[2:-2].strip()
                # Remove any numbering like "A. " or "1. "
                heading = re.sub(r'^[A-Z]\.\s+', '', heading)
                heading = re.sub(r'^\d+\.\s+', '', heading)
                lines.append("")  # Add spacing before subsection
                lines.append(f"\\subsection{{{self.clean_text_for_latex(heading)}}}")
                lines.append("")  # Add spacing after subsection
                continue
            
            # Check for list items
            if para.startswith('- '):
                if not in_itemize:
                    lines.append(r'\begin{itemize}')
                    in_itemize = True
                item = para[2:].strip()
                # Handle inline bold in list items - be more careful
                item = re.sub(r'\*\*([^*\n]+?)\*\*', r'\\textbf{\1}', item)
                # Handle inline italic - avoid matching **
                item = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', item)
                # Remove any remaining asterisks
                item = item.replace('*', '')
                lines.append(f"\\item {self.clean_text_for_latex(item)}")
                continue
            
            # Check for numbered list items with bold
            if re.match(r'^\d+\.\s+\*\*', para):
                # Close any open itemize
                if in_itemize:
                    lines.append(r'\end{itemize}')
                    in_itemize = False
                
                # Extract the bold part as subsection
                match = re.match(r'^\d+\.\s+\*\*([^*]+)\*\*:?\s*(.*)', para, re.DOTALL)
                if match:
                    heading = match.group(1).strip()
                    rest = match.group(2).strip()
                    lines.append(f"\\subsection{{{self.clean_text_for_latex(heading)}}}")
                    if rest:
                        # Handle inline bold in the rest - be more careful
                        rest = re.sub(r'\*\*([^*\n]+?)\*\*', r'\\textbf{\1}', rest)
                        rest = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', rest)
                        # Remove any remaining asterisks
                        rest = rest.replace('*', '')
                        lines.append(self.clean_text_for_latex(rest))
                continue
            
            # Regular paragraph
            if in_itemize:
                lines.append(r'\end{itemize}')
                lines.append("")  # Add spacing after list
                in_itemize = False
            
            # Handle inline bold text - be more careful with matching
            para = re.sub(r'\*\*([^*\n]+?)\*\*', r'\\textbf{\1}', para)
            # Handle inline italic text - avoid matching ** 
            para = re.sub(r'(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', para)
            
            # Remove any remaining unmatched asterisks
            para = para.replace('*', '')
            
            cleaned_para = self.clean_text_for_latex(para)
            if cleaned_para.strip():  # Only add non-empty paragraphs
                lines.append(cleaned_para)
                lines.append("")  # Empty line between paragraphs
        
        # Close any remaining itemize
        if in_itemize:
            lines.append(r'\end{itemize}')
        
        return "\n".join(lines)
    
    def generate_ieee_paper(
        self,
        title: str,
        authors: List[Dict[str, str]],
        sections: List[Dict[str, str]],
        abstract: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        references: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate complete IEEE paper LaTeX"""
        
        template = self.get_ieee_template()
        
        # Replace title
        template = template.replace("<<TITLE>>", self.clean_text_for_latex(title))
        
        # Replace authors
        authors_block = self.generate_authors_block(authors)
        template = template.replace("<<AUTHORS>>", authors_block)
        
        # Replace abstract
        if abstract:
            abstract_text = f"\\begin{{abstract}}\n{self.clean_text_for_latex(abstract)}\n\\end{{abstract}}"
            template = template.replace("<<ABSTRACT>>", abstract_text)
        else:
            template = template.replace("<<ABSTRACT>>", "")
        
        # Replace keywords
        if keywords:
            kw_text = f"\\begin{{IEEEkeywords}}\n{', '.join([self.clean_text_for_latex(k) for k in keywords])}\n\\end{{IEEEkeywords}}"
            template = template.replace("<<KEYWORDS>>", kw_text)
        else:
            template = template.replace("<<KEYWORDS>>", "")
        
        # Replace sections
        sections_text = []
        for i, section in enumerate(sections, 1):
            section_title = section.get('title', f'Section {i}')
            section_content = section.get('content', '')
            
            # Add section with proper spacing
            sections_text.append(f"\\section{{{self.clean_text_for_latex(section_title)}}}")
            sections_text.append("")  # Empty line after section title
            
            formatted_content = self.format_content(section_content, section_title)
            if formatted_content:
                sections_text.append(formatted_content)
                sections_text.append("")  # Empty line after section content
        
        template = template.replace("<<SECTIONS>>", "\n".join(sections_text))
        
        # Replace references
        if references:
            ref_text = [r"\begin{thebibliography}{99}"]
            for i, ref in enumerate(references, 1):
                citation = self.clean_text_for_latex(ref.get('citation', ''))
                ref_text.append(f"\\bibitem{{ref{i}}} {citation}")
            ref_text.append(r"\end{thebibliography}")
            template = template.replace("<<REFERENCES>>", "\n".join(ref_text))
        else:
            template = template.replace("<<REFERENCES>>", "")
        
        return template
    
    def compile_to_pdf(self, latex_content: str, output_dir: str = None) -> tuple[str, str]:
        """Compile LaTeX to PDF using MiKTeX"""
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
            pdflatex_cmd = self._get_pdflatex_command()
            print(f"Using pdflatex: {pdflatex_cmd}")
            
            # Run pdflatex twice for proper references
            for run in range(2):
                print(f"Running pdflatex (pass {run + 1}/2)...")
                
                result = subprocess.run([
                    pdflatex_cmd,
                    '-interaction=nonstopmode',
                    '-output-directory', str(output_dir),
                    str(tex_file)
                ], capture_output=True, text=True, cwd=output_dir, timeout=120)
                
                if result.returncode != 0:
                    print(f"LaTeX compilation warnings on pass {run + 1}")
                    print(f"STDOUT: {result.stdout[-500:]}")  # Last 500 chars
            
            pdf_file = output_dir / "paper.pdf"
            if pdf_file.exists() and pdf_file.stat().st_size > 1000:
                print(f"✅ PDF generated successfully: {pdf_file}")
                print(f"📄 PDF size: {pdf_file.stat().st_size} bytes")
                return str(tex_file), str(pdf_file)
            else:
                raise Exception("PDF file was not generated or is too small")
                
        except Exception as e:
            print(f"LaTeX compilation error: {e}")
            raise
    
    def _get_pdflatex_command(self) -> str:
        """Get the correct pdflatex command"""
        import os
        
        # Try PATH first
        try:
            result = subprocess.run(['pdflatex', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'pdflatex'
        except:
            pass
        
        # Check common MiKTeX paths
        common_paths = [
            r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
            r"C:\Users\{}\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe".format(os.getenv('USERNAME', '')),
            r"C:\Program Files (x86)\MiKTeX\miktex\bin\pdflatex.exe",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return 'pdflatex'

class LaTeXService:
    """Service for LaTeX operations"""
    
    def __init__(self):
        self.generator = IEEELaTeXGenerator()
    
    def generate_ieee_paper_latex(self, paper_data: Dict, sections_data: List[Dict]) -> str:
        """Generate IEEE paper LaTeX from paper and sections data"""
        
        # Process authors
        authors = []
        paper_authors = paper_data.get('authors', [])
        paper_affiliations = paper_data.get('affiliations', [])
        
        if isinstance(paper_authors, str):
            paper_authors = [a.strip() for a in paper_authors.split(',')]
        if isinstance(paper_affiliations, str):
            paper_affiliations = [a.strip() for a in paper_affiliations.split(',')]
        
        for i, author in enumerate(paper_authors):
            author_info = {'name': author.strip()}
            if i < len(paper_affiliations):
                author_info['affiliation'] = paper_affiliations[i].strip()
            elif len(paper_affiliations) == 1:
                author_info['affiliation'] = paper_affiliations[0].strip()
            
            email_name = author.lower().replace(' ', '.').replace('-', '.')
            author_info['email'] = f"{email_name}@university.edu"
            authors.append(author_info)
        
        # Process sections
        sections = []
        for section in sections_data:
            if section.get('section_name', '').lower() != 'abstract':
                sections.append({
                    'title': section.get('section_name', ''),
                    'content': section.get('content', '')
                })
        
        # Get abstract
        abstract = None
        abstract_section = next((s for s in sections_data if 'abstract' in s.get('section_name', '').lower()), None)
        if abstract_section:
            abstract = abstract_section.get('content', '')
        
        # Get keywords
        keywords = paper_data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',')]
        
        # Generate references
        domain = paper_data.get('domain', 'Technology')
        references = [
            {"citation": f"Smith, J. A., ``Advanced Methods in {domain},'' IEEE Transactions, vol. 45, no. 3, pp. 123-135, 2023."},
            {"citation": f"Johnson, B. C., ``Recent Developments in {domain},'' IEEE Conference, pp. 456-467, 2022."},
            {"citation": f"Williams, C. D., ``Novel Approaches to {domain},'' IEEE Journal, vol. 12, no. 4, pp. 789-801, 2023."},
        ]
        
        return self.generator.generate_ieee_paper(
            title=paper_data.get('title', ''),
            authors=authors,
            sections=sections,
            abstract=abstract,
            keywords=keywords,
            references=references
        )
    
    def compile_to_pdf(self, latex_content: str, output_dir: str = None) -> tuple[str, str]:
        """Compile LaTeX to PDF"""
        return self.generator.compile_to_pdf(latex_content, output_dir)
    
    def is_latex_available(self) -> bool:
        """Check if LaTeX is available"""
        try:
            pdflatex_cmd = self.generator._get_pdflatex_command()
            result = subprocess.run([pdflatex_cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

# Global instance
latex_service = LaTeXService()
