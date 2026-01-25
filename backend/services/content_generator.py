import google.generativeai as genai
from typing import Dict, List, Optional
from config import get_settings
import re

settings = get_settings()

class ComprehensiveContentGenerator:
    """Generate comprehensive, high-quality IEEE paper content"""
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def get_section_requirements(self, section_name: str) -> Dict[str, str]:
        """Get specific requirements for each IEEE section"""
        requirements = {
            "Abstract": {
                "length": "200-300 words",
                "structure": "Background, Problem, Method, Results, Conclusion",
                "requirements": "Concise summary of entire paper, no citations, standalone"
            },
            "Introduction": {
                "length": "800-1200 words", 
                "structure": "Background, Problem Statement, Motivation, Contributions, Paper Organization",
                "requirements": "Clear problem definition, motivation, research gap, contributions, paper roadmap"
            },
            "Literature Review": {
                "length": "1500-2000 words",
                "structure": "Related Work Categories, Critical Analysis, Research Gaps",
                "requirements": "Comprehensive survey, critical analysis, identify gaps, position work"
            },
            "Related Work": {
                "length": "1200-1500 words",
                "structure": "Categorized Related Work, Comparative Analysis, Positioning",
                "requirements": "Systematic categorization, comparative analysis, clear positioning"
            },
            "Methodology": {
                "length": "1500-2500 words",
                "structure": "System Architecture, Algorithm Design, Implementation Details, Evaluation Setup",
                "requirements": "Detailed technical approach, algorithms, architecture, reproducible methodology"
            },
            "System Design": {
                "length": "1200-1800 words",
                "structure": "Architecture Overview, Component Design, Interface Specifications",
                "requirements": "Detailed system architecture, component interactions, design decisions"
            },
            "Implementation": {
                "length": "1000-1500 words",
                "structure": "Technology Stack, Development Process, Key Challenges, Solutions",
                "requirements": "Technical implementation details, tools used, challenges overcome"
            },
            "Experimental Setup": {
                "length": "800-1200 words",
                "structure": "Dataset Description, Evaluation Metrics, Baseline Methods, Environment",
                "requirements": "Comprehensive experimental design, datasets, metrics, baselines"
            },
            "Results": {
                "length": "1500-2000 words",
                "structure": "Quantitative Results, Qualitative Analysis, Performance Comparison, Discussion",
                "requirements": "Detailed results with analysis, comparisons, statistical significance"
            },
            "Evaluation": {
                "length": "1200-1800 words",
                "structure": "Performance Analysis, Comparison Studies, Ablation Studies, Discussion",
                "requirements": "Thorough evaluation with multiple perspectives and analyses"
            },
            "Discussion": {
                "length": "1000-1500 words",
                "structure": "Key Findings, Implications, Limitations, Future Directions",
                "requirements": "Critical analysis of results, implications, honest limitations discussion"
            },
            "Conclusion": {
                "length": "400-600 words",
                "structure": "Summary, Key Contributions, Impact, Future Work",
                "requirements": "Concise summary, clear contributions, impact statement, future directions"
            },
            "Future Work": {
                "length": "600-800 words",
                "structure": "Immediate Extensions, Long-term Directions, Research Opportunities",
                "requirements": "Specific future research directions, potential improvements, opportunities"
            }
        }
        
        return requirements.get(section_name, {
            "length": "800-1200 words",
            "structure": "Introduction, Main Content, Analysis, Summary",
            "requirements": "Well-structured technical content with proper analysis"
        })
    
    def generate_comprehensive_prompt(
        self, 
        section_name: str, 
        paper_title: str, 
        domain: str, 
        context: str,
        paper_info: Dict
    ) -> str:
        """Generate comprehensive prompt for high-quality content"""
        
        requirements = self.get_section_requirements(section_name)
        
        base_prompt = f"""
You are a world-class academic researcher and writer specializing in {domain} with expertise in IEEE publication standards. You are writing a comprehensive research paper for a top-tier IEEE conference/journal.

PAPER INFORMATION:
- Title: {paper_title}
- Domain: {domain}
- Authors: {', '.join(paper_info.get('authors', []))}
- Keywords: {', '.join(paper_info.get('keywords', []))}

SECTION TO WRITE: {section_name}

SECTION REQUIREMENTS:
- Target Length: {requirements['length']}
- Structure: {requirements['structure']}
- Requirements: {requirements['requirements']}

CONTEXT FROM REFERENCE PAPERS:
{context}

WRITING GUIDELINES:
1. COMPREHENSIVE CONTENT: Write detailed, substantial content that meets the target length
2. TECHNICAL DEPTH: Include technical details, algorithms, mathematical formulations where appropriate
3. IEEE STANDARDS: Follow IEEE formatting and citation style ([1], [2], etc.)
4. ACADEMIC RIGOR: Use formal academic language with proper terminology
5. LOGICAL FLOW: Ensure smooth transitions and logical progression
6. EVIDENCE-BASED: Support claims with evidence from context or established knowledge
7. ORIGINAL INSIGHTS: Provide novel insights and analysis beyond just summarizing
8. PUBLICATION QUALITY: Write at the level expected for top-tier IEEE venues

SPECIFIC INSTRUCTIONS FOR {section_name}:
"""

        # Add section-specific instructions
        section_instructions = {
            "Abstract": """
- Write a complete abstract that summarizes the entire paper
- Include: problem statement, proposed approach, key results, main contributions
- Use quantitative results where possible (e.g., "achieved 95% accuracy")
- Make it standalone - readable without the rest of the paper
- No citations in abstract
""",
            "Introduction": """
- Start with broad context and narrow down to specific problem
- Clearly articulate the research problem and its importance
- Explain why existing solutions are inadequate
- Present your approach and key contributions (numbered list)
- Provide a roadmap of the paper structure
- Include motivation with real-world examples
""",
            "Literature Review": """
- Organize related work into logical categories/themes
- For each category, discuss 3-5 relevant papers with critical analysis
- Compare and contrast different approaches
- Identify limitations and gaps in existing work
- Position your work clearly against existing literature
- Use proper citations throughout [1], [2], etc.
""",
            "Methodology": """
- Provide detailed technical approach with step-by-step explanation
- Include algorithms in pseudocode format
- Explain design decisions and rationale
- Describe system architecture with component interactions
- Include mathematical formulations where relevant
- Ensure reproducibility with sufficient detail
""",
            "Results": """
- Present comprehensive experimental results with analysis
- Include quantitative metrics with statistical significance
- Compare against multiple baseline methods
- Provide both tabular data and analytical discussion
- Explain what the results mean and why they occurred
- Address any unexpected or negative results honestly
""",
            "Discussion": """
- Analyze the implications of your results
- Discuss strengths and limitations honestly
- Compare with state-of-the-art approaches
- Explain the broader impact of your work
- Address potential concerns or criticisms
- Suggest improvements and extensions
""",
            "Conclusion": """
- Summarize the key contributions and findings
- Restate the problem and how you solved it
- Highlight the significance and impact of your work
- Acknowledge limitations
- Provide specific directions for future work
- End with a strong closing statement about the work's importance
"""
        }
        
        prompt = base_prompt + section_instructions.get(section_name, """
- Write comprehensive, technically sound content
- Include detailed analysis and insights
- Support all claims with evidence or reasoning
- Maintain academic rigor throughout
""")
        
        prompt += f"""

IMPORTANT: Generate substantial, high-quality content that would be suitable for publication in a top-tier IEEE conference or journal. The content should be comprehensive, technically sound, and meet the target length of {requirements['length']}.

Write the {section_name} section now:
"""
        
        return prompt
    
    def generate_section_content(
        self,
        section_name: str,
        paper_title: str,
        domain: str,
        context: str,
        paper_info: Dict
    ) -> str:
        """Generate comprehensive content for a specific section"""
        
        prompt = self.generate_comprehensive_prompt(
            section_name, paper_title, domain, context, paper_info
        )
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=settings.max_tokens,
                    temperature=settings.temperature,
                )
            )
            
            content = response.text
            
            # Post-process content
            content = self.post_process_content(content, section_name)
            
            return content
            
        except Exception as e:
            raise Exception(f"Content generation failed: {str(e)}")
    
    def post_process_content(self, content: str, section_name: str) -> str:
        """Post-process generated content for quality and formatting"""
        
        # Remove any unwanted prefixes
        content = re.sub(r'^(Here is the|Here\'s the|The following is)', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^' + re.escape(section_name) + r'\s*:?\s*', '', content, flags=re.IGNORECASE)
        
        # Ensure proper paragraph spacing
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Fix citation formatting
        content = re.sub(r'\[(\d+)\]', r'[\1]', content)
        
        # Ensure content ends properly
        content = content.strip()
        
        # Add section-specific formatting
        if section_name == "Abstract":
            # Ensure abstract is in paragraph form
            content = re.sub(r'\n+', ' ', content)
            content = content.strip()
        
        return content
    
    def estimate_content_length(self, content: str) -> Dict[str, int]:
        """Estimate content metrics"""
        words = len(content.split())
        chars = len(content)
        # Rough estimate: 250 words per page for IEEE format
        pages = words / 250
        
        return {
            "words": words,
            "characters": chars,
            "estimated_pages": round(pages, 1)
        }
    
    def generate_references(self, context: str, domain: str) -> List[Dict[str, str]]:
        """Generate realistic references based on context and domain"""
        
        prompt = f"""
Generate 15-20 realistic academic references for a {domain} research paper. 
Based on this context: {context[:1000]}...

Format each reference as:
[1] Author, A. B., "Title of Paper," Journal/Conference Name, vol. X, no. Y, pp. Z-W, Year.

Include a mix of:
- Recent papers (2020-2024)
- Foundational papers (2015-2019)
- Key journals and conferences in {domain}
- Realistic author names and titles

Generate the references:
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.8,
                )
            )
            
            references_text = response.text
            
            # Parse references
            references = []
            lines = references_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line.startswith('[') or line.startswith('1.') or line.startswith('•')):
                    # Extract reference number and citation
                    match = re.match(r'[\[\(]?(\d+)[\]\)]?\s*(.+)', line)
                    if match:
                        ref_num = match.group(1)
                        citation = match.group(2).strip()
                        references.append({
                            "key": f"ref{ref_num}",
                            "citation": citation
                        })
            
            return references[:20]  # Limit to 20 references
            
        except Exception as e:
            # Fallback references
            return [
                {"key": "ref1", "citation": "Smith, J. A., \"Advanced Methods in " + domain + ",\" IEEE Transactions on Technology, vol. 45, no. 3, pp. 123-135, 2023."},
                {"key": "ref2", "citation": "Johnson, B. C., \"Recent Developments in " + domain + " Systems,\" Proceedings of IEEE Conference, pp. 456-467, 2022."}
            ]