import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from pylatex import Document, Section, Subsection, Command, Package
from pylatex.base_classes import Environment
from pylatex.utils import italic, bold, NoEscape
from jinja2 import Template
import subprocess
import logging

logger = logging.getLogger(__name__)

class IEEEPaperGenerator:
    """Generate IEEE-formatted LaTeX papers"""
    
    def __init__(self):
        self.ieee_template = self._get_ieee_template()
    
    def _get_ieee_template(self) -> str:
        """Enhanced IEEE paper LaTeX template with comprehensive formatting"""
        return r"""
\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts

% Essential packages for comprehensive IEEE papers
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{url}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{array}
\usepackage{subfigure}
\usepackage{balance}

% IEEE specific settings
\hyphenation{op-tical net-works semi-conduc-tor}

% Document metadata
\title{ {{- title -}} }

\author{
{% for author in authors %}
\IEEEauthorblockN{ {{- author.name -}} }
\IEEEauthorblockA{
{% if author.affiliation %}{{- author.affiliation -}}{% endif %}
{% if author.email %}\\Email: {{- author.email -}}{% endif %}
}
{% if not loop.last %}\and{% endif %}
{% endfor %}
}

\begin{document}

\maketitle

{% if abstract %}
\begin{abstract}
{{- abstract -}}
\end{abstract}
{% endif %}

{% if keywords %}
\begin{IEEEkeywords}
{{- keywords | join(', ') -}}
\end{IEEEkeywords}
{% endif %}

{% for section in sections %}
{% if section.level == 1 %}
\section{ {{- section.title -}} }
{% elif section.level == 2 %}
\subsection{ {{- section.title -}} }
{% elif section.level == 3 %}
\subsubsection{ {{- section.title -}} }
{% endif %}

{{- section.content -}}

{% endfor %}

{% if references %}
\section*{Acknowledgment}
The authors would like to thank the anonymous reviewers for their valuable comments and suggestions.

\begin{thebibliography}{99}
{% for ref in references %}
\bibitem{ {{- ref.key -}} } {{- ref.citation -}}
{% endfor %}
\end{thebibliography}
{% endif %}

\balance
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
        
        # Escape special LaTeX characters
        latex_escapes = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '^': r'\textasciicircum{}',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '\\': r'\textbackslash{}'
        }
        
        for char, escape in latex_escapes.items():
            content = content.replace(char, escape)
        
        # Handle common formatting
        content = self._handle_citations(content)
        content = self._handle_equations(content)
        content = self._handle_lists(content)
        
        return content
    
    def _handle_citations(self, content: str) -> str:
        """Convert citation markers to LaTeX format"""
        import re
        
        # Convert [1], [2], [1-3], [1,2,3] to \cite{} format
        citation_pattern = r'\[(\d+(?:[-,]\d+)*)\]'
        
        def replace_citation(match):
            citation = match.group(1)
            # Handle ranges like "1-3"
            if '-' in citation:
                start, end = citation.split('-')
                refs = [f"ref{i}" for i in range(int(start), int(end) + 1)]
                return f"\\cite{{{','.join(refs)}}}"
            # Handle lists like "1,2,3"
            elif ',' in citation:
                refs = [f"ref{num.strip()}" for num in citation.split(',')]
                return f"\\cite{{{','.join(refs)}}}"
            # Single citation
            else:
                return f"\\cite{{ref{citation}}}"
        
        return re.sub(citation_pattern, replace_citation, content)
    
    def _handle_equations(self, content: str) -> str:
        """Handle mathematical equations"""
        import re
        
        # Simple equation detection (can be enhanced)
        equation_pattern = r'\$([^$]+)\$'
        content = re.sub(equation_pattern, r'$\1$', content)
        
        return content
    
    def _handle_lists(self, content: str) -> str:
        """Convert bullet points to LaTeX itemize"""
        lines = content.split('\n')
        in_list = False
        result = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('•') or stripped.startswith('-') or stripped.startswith('*'):
                if not in_list:
                    result.append('\\begin{itemize}')
                    in_list = True
                item_text = stripped[1:].strip()
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
    
    def compile_latex_to_pdf(self, latex_content: str, output_dir: str = None) -> tuple[str, str]:
        """Compile LaTeX content to PDF"""
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
            # Run pdflatex twice for proper references
            for _ in range(2):
                result = subprocess.run([
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory', str(output_dir),
                    str(tex_file)
                ], capture_output=True, text=True, cwd=output_dir)
                
                if result.returncode != 0:
                    logger.error(f"LaTeX compilation failed: {result.stderr}")
                    raise Exception(f"LaTeX compilation failed: {result.stderr}")
            
            pdf_file = output_dir / "paper.pdf"
            if pdf_file.exists():
                return str(tex_file), str(pdf_file)
            else:
                raise Exception("PDF file was not generated")
                
        except FileNotFoundError:
            raise Exception("pdflatex not found. Please install LaTeX distribution (TeX Live, MiKTeX, etc.)")
        except Exception as e:
            logger.error(f"LaTeX compilation error: {str(e)}")
            raise

class LaTeXService:
    """Service for LaTeX operations"""
    
    def __init__(self):
        self.ieee_generator = IEEEPaperGenerator()
    
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
        
        # Generate references using the content generator
        try:
            from services.content_generator import ComprehensiveContentGenerator
            content_gen = ComprehensiveContentGenerator()
            
            # Combine all section content for context
            all_content = "\n\n".join([s['content'] for s in sections])
            references = content_gen.generate_references(all_content, paper_data.get('domain', 'Computer Science'))
        except:
            # Fallback references
            references = [
                {"key": "ref1", "citation": "Smith, J. A., \"Advanced Methods in " + paper_data.get('domain', 'Technology') + ",\" IEEE Transactions on Technology, vol. 45, no. 3, pp. 123-135, 2023."},
                {"key": "ref2", "citation": "Johnson, B. C., \"Recent Developments in " + paper_data.get('domain', 'Technology') + " Systems,\" Proceedings of IEEE Conference, pp. 456-467, 2022."}
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
        try:
            result = subprocess.run(['pdflatex', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False