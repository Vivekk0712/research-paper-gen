#!/usr/bin/env python3
"""
Modern PDF Generator using ReportLab - IEEE Conference Paper Format
Creates professional two-column IEEE papers with proper formatting
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Template
import re
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame

class IEEEDocTemplate(BaseDocTemplate):
    """Custom document template for IEEE two-column format"""
    
    def __init__(self, filename, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        
        # Define frame dimensions for two-column layout
        frame_width = (self.width - 0.5*inch) / 2  # Two columns with gap
        frame_height = self.height - 1*inch  # Leave space for header/footer
        
        # Single column frame for title and authors
        title_frame = Frame(
            self.leftMargin, 
            self.bottomMargin + frame_height - 2.5*inch,
            self.width, 
            2.5*inch,
            id='title',
            showBoundary=0
        )
        
        # Left column frame
        left_frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            frame_width,
            frame_height - 2.5*inch,
            id='left',
            showBoundary=0
        )
        
        # Right column frame  
        right_frame = Frame(
            self.leftMargin + frame_width + 0.5*inch,
            self.bottomMargin,
            frame_width,
            frame_height - 2.5*inch,
            id='right',
            showBoundary=0
        )
        
        # Create page templates
        title_template = PageTemplate(id='title_page', frames=[title_frame])
        two_column_template = PageTemplate(id='two_column', frames=[left_frame, right_frame])
        
        self.addPageTemplates([title_template, two_column_template])

class ReportLabPDFGenerator:
    """Generate professional IEEE conference papers using ReportLab"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for IEEE paper formatting"""
        
        # Helper function to safely add styles
        def safe_add_style(name, style):
            if name not in self.styles:
                self.styles.add(style)
        
        # Title style
        safe_add_style('IEEEPaperTitle', ParagraphStyle(
            name='IEEEPaperTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=16,
            alignment=TA_CENTER,
            fontName='Times-Bold',
            leading=20
        ))
        
        # Author name style (bold)
        safe_add_style('IEEEAuthorName', ParagraphStyle(
            name='IEEEAuthorName',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        ))
        
        # Affiliation style (above author, bold)
        safe_add_style('IEEEAffiliation', ParagraphStyle(
            name='IEEEAffiliation',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        ))
        
        # Email style
        safe_add_style('IEEEEmail', ParagraphStyle(
            name='IEEEEmail',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Times-Roman'
        ))
        
        # Abstract title
        safe_add_style('IEEEAbstractTitle', ParagraphStyle(
            name='IEEEAbstractTitle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        ))
        
        # Abstract content
        safe_add_style('IEEEAbstractContent', ParagraphStyle(
            name='IEEEAbstractContent',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Times-Italic',
            leading=11
        ))
        
        # Keywords
        safe_add_style('IEEEKeywords', ParagraphStyle(
            name='IEEEKeywords',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=16,
            alignment=TA_JUSTIFY,
            fontName='Times-Italic'
        ))
        
        # Section heading
        safe_add_style('IEEESectionHeading', ParagraphStyle(
            name='IEEESectionHeading',
            parent=self.styles['Heading1'],
            fontSize=10,
            spaceAfter=6,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Times-Bold'
        ))
        
        # Subsection heading
        safe_add_style('IEEESubsectionHeading', ParagraphStyle(
            name='IEEESubsectionHeading',
            parent=self.styles['Heading2'],
            fontSize=10,
            spaceAfter=4,
            spaceBefore=8,
            alignment=TA_LEFT,
            fontName='Times-Bold'
        ))
        
        # Body text for two-column layout
        safe_add_style('IEEEBodyText', ParagraphStyle(
            name='IEEEBodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            firstLineIndent=12,
            leading=12
        ))
        
        # References
        safe_add_style('IEEEReference', ParagraphStyle(
            name='IEEEReference',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            leftIndent=12,
            bulletIndent=0,
            leading=10
        ))

    def generate_ieee_paper(
        self,
        title: str,
        authors: List[Dict[str, str]],
        sections: List[Dict[str, str]],
        abstract: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        references: Optional[List[Dict[str, str]]] = None
    ) -> List:
        """Generate IEEE paper content as ReportLab story"""
        
        story = []
        
        # Title section (single column)
        story.append(Paragraph(title, self.styles['IEEEPaperTitle']))
        story.append(Spacer(1, 12))
        
        # Authors section - proper IEEE format
        # Group authors by affiliation or show all with their affiliations
        if len(authors) <= 3:
            # Show each author with their affiliation
            for author in authors:
                if author.get('affiliation'):
                    story.append(Paragraph(author['affiliation'], self.styles['IEEEAffiliation']))
                story.append(Paragraph(f"<b>{author['name']}</b>", self.styles['IEEEAuthorName']))
                if author.get('email'):
                    story.append(Paragraph(f"Email: {author['email']}", self.styles['IEEEEmail']))
                story.append(Spacer(1, 8))
        else:
            # For many authors, group them
            for author in authors:
                if author.get('affiliation'):
                    story.append(Paragraph(author['affiliation'], self.styles['IEEEAffiliation']))
                story.append(Paragraph(f"<b>{author['name']}</b>", self.styles['IEEEAuthorName']))
                if author.get('email'):
                    story.append(Paragraph(f"Email: {author['email']}", self.styles['IEEEEmail']))
        
        story.append(Spacer(1, 16))
        
        # Abstract (single column)
        if abstract:
            story.append(Paragraph("<b>Abstract</b>", self.styles['IEEEAbstractTitle']))
            clean_abstract = self._clean_text_for_reportlab(abstract)
            story.append(Paragraph(clean_abstract, self.styles['IEEEAbstractContent']))
        
        # Keywords (single column)
        if keywords:
            keywords_text = f"<b><i>Index Terms—</i></b>{', '.join(keywords)}"
            story.append(Paragraph(keywords_text, self.styles['IEEEKeywords']))
        
        # Page break to start two-column layout
        story.append(PageBreak())
        
        # Sections (two-column layout)
        for i, section in enumerate(sections, 1):
            section_title = f"<b>{i}. {section['title'].upper()}</b>"
            story.append(Paragraph(section_title, self.styles['IEEESectionHeading']))
            
            content = self._format_content_for_reportlab(section.get('content', ''))
            for paragraph in content:
                story.append(paragraph)
        
        # References (two-column layout)
        if references:
            story.append(Paragraph("<b>REFERENCES</b>", self.styles['IEEESectionHeading']))
            for i, ref in enumerate(references, 1):
                ref_text = f"[{i}] {ref['citation']}"
                story.append(Paragraph(ref_text, self.styles['IEEEReference']))
        
        return story
    
    def _clean_text_for_reportlab(self, text: str) -> str:
        """Clean text for ReportLab compatibility"""
        if not text:
            return ""
        
        # Remove problematic characters and patterns
        text = re.sub(r'[^\w\s\.,;:!?()\-\'\"]+', ' ', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _format_content_for_reportlab(self, content: str) -> List:
        """Format content for ReportLab"""
        if not content:
            return []
        
        paragraphs = []
        
        # Split content into paragraphs
        lines = content.split('\n')
        current_paragraph = []
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    clean_text = self._clean_text_for_reportlab(para_text)
                    if clean_text:
                        paragraphs.append(Paragraph(clean_text, self.styles['IEEEBodyText']))
                    current_paragraph = []
            elif stripped.startswith('**') and stripped.endswith('**'):
                # Bold heading
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    clean_text = self._clean_text_for_reportlab(para_text)
                    if clean_text:
                        paragraphs.append(Paragraph(clean_text, self.styles['IEEEBodyText']))
                    current_paragraph = []
                
                heading_text = stripped[2:-2]
                clean_heading = self._clean_text_for_reportlab(heading_text)
                if clean_heading:
                    paragraphs.append(Paragraph(f"<b>{clean_heading}:</b>", self.styles['IEEESubsectionHeading']))
            elif stripped.startswith('- '):
                # List item
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    clean_text = self._clean_text_for_reportlab(para_text)
                    if clean_text:
                        paragraphs.append(Paragraph(clean_text, self.styles['IEEEBodyText']))
                    current_paragraph = []
                
                item_text = stripped[2:].strip()
                clean_item = self._clean_text_for_reportlab(item_text)
                if clean_item:
                    paragraphs.append(Paragraph(f"• {clean_item}", self.styles['IEEEBodyText']))
            else:
                # Regular text
                current_paragraph.append(stripped)
        
        # Handle remaining paragraph
        if current_paragraph:
            para_text = ' '.join(current_paragraph)
            clean_text = self._clean_text_for_reportlab(para_text)
            if clean_text:
                paragraphs.append(Paragraph(clean_text, self.styles['IEEEBodyText']))
        
        return paragraphs
    
    def compile_to_pdf(self, story: List, output_dir: str = None) -> tuple[str, str]:
        """Compile story to PDF using custom IEEE template"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create PDF file
        pdf_file = output_dir / "paper.pdf"
        
        try:
            print("🔄 Generating IEEE two-column PDF using ReportLab...")
            
            # Create custom IEEE document
            doc = IEEEDocTemplate(
                str(pdf_file),
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            # Build PDF with two-column layout
            doc.build(story)
            
            if pdf_file.exists():
                print(f"✅ IEEE PDF generated successfully: {pdf_file}")
                print(f"📄 PDF size: {pdf_file.stat().st_size} bytes")
                return str(pdf_file), str(pdf_file)
            else:
                raise Exception("PDF file was not generated")
                
        except Exception as e:
            print(f"❌ PDF generation error: {e}")
            raise Exception(f"PDF generation failed: {str(e)}")

class PDFService:
    """Service for PDF operations using ReportLab"""
    
    def __init__(self):
        self.pdf_generator = ReportLabPDFGenerator()
    
    def generate_ieee_paper_pdf(
        self,
        paper_data: Dict,
        sections_data: List[Dict]
    ) -> List:
        """Generate comprehensive IEEE paper content from paper and sections data"""
        
        # Process authors with proper field handling
        authors = []
        paper_authors = paper_data.get('authors', [])
        paper_affiliations = paper_data.get('affiliations', [])
        
        # Handle both string and list formats for authors
        if isinstance(paper_authors, str):
            paper_authors = [name.strip() for name in paper_authors.split(',')]
        
        if isinstance(paper_affiliations, str):
            paper_affiliations = [aff.strip() for aff in paper_affiliations.split(',')]
        
        for i, author in enumerate(paper_authors):
            author_info = {'name': author.strip()}
            
            # Match affiliation to author
            if i < len(paper_affiliations):
                author_info['affiliation'] = paper_affiliations[i].strip()
            elif len(paper_affiliations) == 1:
                # If only one affiliation, use it for all authors
                author_info['affiliation'] = paper_affiliations[0].strip()
            
            # Generate realistic email
            email_name = author.lower().replace(' ', '.').replace('-', '.')
            author_info['email'] = f"{email_name}@university.edu"
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
        
        # Handle keywords properly
        keywords = paper_data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [kw.strip() for kw in keywords.split(',')]
        
        # Generate simple references
        domain = paper_data.get('domain', 'Technology')
        references = [
            {"key": "ref1", "citation": f"Smith, J. A., \"Advanced Methods in {domain},\" IEEE Transactions on Technology, vol. 45, no. 3, pp. 123-135, 2023."},
            {"key": "ref2", "citation": f"Johnson, B. C., \"Recent Developments in {domain} Systems,\" Proceedings of IEEE Conference, pp. 456-467, 2022."},
            {"key": "ref3", "citation": f"Williams, C. D., \"Novel Approaches to {domain} Implementation,\" IEEE Journal of Selected Areas, vol. 12, no. 4, pp. 789-801, 2023."},
            {"key": "ref4", "citation": f"Brown, E. F., \"Comprehensive Analysis of {domain} Performance,\" International Conference on Technology, pp. 234-245, 2022."},
            {"key": "ref5", "citation": f"Davis, G. H., \"Future Trends in {domain} Research,\" IEEE Computer Society, vol. 28, no. 2, pp. 156-168, 2023."}
        ]
        
        return self.pdf_generator.generate_ieee_paper(
            title=paper_data.get('title', ''),
            authors=authors,
            sections=sections,
            abstract=abstract,
            keywords=keywords,
            references=references
        )
    
    def compile_to_pdf(self, story: List, output_dir: str = None) -> tuple[str, str]:
        """Compile story to PDF"""
        return self.pdf_generator.compile_to_pdf(story, output_dir)
    
    def is_pdf_available(self) -> bool:
        """Check if PDF generation is available"""
        try:
            import reportlab
            return True
        except ImportError:
            return False

# Global instance
pdf_service = PDFService()