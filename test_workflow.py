#!/usr/bin/env python3
"""
End-to-end workflow test for IEEE Paper Generator
Tests the complete pipeline: Upload → Process → Generate → Export
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
TEST_FILES_DIR = Path("test_files")

def test_api_connection():
    """Test basic API connection"""
    print("🔗 Testing API connection...")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ API connection successful")
            return True
        else:
            print(f"❌ API connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_latex_status():
    """Test LaTeX availability"""
    print("📄 Testing LaTeX status...")
    try:
        response = requests.get(f"{API_BASE}/api/latex/status")
        if response.status_code == 200:
            data = response.json()
            if data['latex_available']:
                print("✅ LaTeX is available - PDF export will work")
            else:
                print("⚠️ LaTeX not available - only text/LaTeX export will work")
            return True
        else:
            print(f"❌ LaTeX status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LaTeX status error: {e}")
        return False

def create_test_paper():
    """Create a test paper"""
    print("📝 Creating test paper...")
    
    paper_data = {
        "title": "AI-Powered Research Paper Generation: A Novel Approach",
        "domain": "Artificial Intelligence",
        "authors": ["Dr. John Smith", "Dr. Jane Doe"],
        "affiliations": ["MIT", "Stanford University"],
        "keywords": ["AI", "NLP", "Research", "Automation", "LaTeX"]
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/papers", json=paper_data)
        if response.status_code == 200:
            paper = response.json()
            print(f"✅ Paper created successfully: {paper['paper_id']}")
            return paper['paper_id']
        else:
            print(f"❌ Paper creation failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Paper creation error: {e}")
        return None

def create_test_file():
    """Create a test PDF file for upload"""
    print("📄 Creating test file...")
    
    # Create test files directory
    TEST_FILES_DIR.mkdir(exist_ok=True)
    
    # Create a simple text file (simulating PDF content)
    test_content = """
    Research Paper: Machine Learning Applications
    
    Abstract:
    This paper presents a comprehensive study of machine learning applications
    in various domains. We explore different algorithms and their effectiveness
    in solving real-world problems.
    
    Introduction:
    Machine learning has revolutionized the way we approach complex problems.
    This study examines the current state of the art and future directions.
    
    Literature Review:
    Previous studies have shown significant progress in this field.
    Notable works include Smith et al. (2020) and Johnson et al. (2021).
    
    Methodology:
    We employed a systematic approach using various ML algorithms including
    neural networks, decision trees, and support vector machines.
    
    Results:
    Our experiments show promising results with accuracy rates exceeding 95%.
    The proposed method outperforms existing approaches by 15%.
    
    Conclusion:
    This work contributes to the advancement of machine learning applications
    and opens new avenues for future research.
    
    References:
    [1] Smith, J. et al. "Advanced ML Techniques" (2020)
    [2] Johnson, A. et al. "AI Applications" (2021)
    """
    
    test_file = TEST_FILES_DIR / "test_paper.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"✅ Test file created: {test_file}")
    return test_file

def upload_test_file(paper_id, file_path):
    """Upload test file to paper"""
    print("📤 Uploading test file...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'files': (file_path.name, f, 'text/plain')}
            response = requests.post(f"{API_BASE}/api/papers/{paper_id}/upload", files=files)
        
        if response.status_code == 200:
            uploaded_files = response.json()
            print(f"✅ File uploaded successfully: {len(uploaded_files)} files")
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return False

def generate_content(paper_id, section_name):
    """Generate content for a section"""
    print(f"🧠 Generating content for: {section_name}")
    
    try:
        generation_data = {
            "paper_id": paper_id,
            "section_name": section_name
        }
        
        response = requests.post(f"{API_BASE}/api/generate", json=generation_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Content generated for {section_name}")
            print(f"Preview: {result['content'][:100]}...")
            return True
        else:
            print(f"❌ Content generation failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Content generation error: {e}")
        return False

def export_paper(paper_id, format_type):
    """Export paper in specified format"""
    print(f"📥 Exporting paper as {format_type}...")
    
    try:
        if format_type == "text":
            response = requests.get(f"{API_BASE}/api/papers/{paper_id}/export")
        elif format_type == "latex":
            response = requests.get(f"{API_BASE}/api/papers/{paper_id}/export/latex")
        elif format_type == "pdf":
            response = requests.get(f"{API_BASE}/api/papers/{paper_id}/export/pdf")
        else:
            print(f"❌ Unknown format: {format_type}")
            return False
        
        if response.status_code == 200:
            if format_type == "pdf":
                # Save PDF file
                with open(f"test_output.pdf", "wb") as f:
                    f.write(response.content)
                print(f"✅ PDF exported successfully: test_output.pdf")
            else:
                data = response.json()
                if format_type == "latex":
                    # Save LaTeX file
                    with open("test_output.tex", "w") as f:
                        f.write(data['latex'])
                    print(f"✅ LaTeX exported successfully: test_output.tex")
                else:
                    # Save text file
                    with open("test_output.txt", "w") as f:
                        f.write(data['paper'])
                    print(f"✅ Text exported successfully: test_output.txt")
            return True
        else:
            print(f"❌ Export failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Export error: {e}")
        return False

def main():
    """Run complete workflow test"""
    print("🚀 IEEE Paper Generator - Complete Workflow Test")
    print("=" * 60)
    
    # Test 1: API Connection
    if not test_api_connection():
        print("❌ Cannot proceed without API connection")
        return False
    
    # Test 2: LaTeX Status
    test_latex_status()
    
    # Test 3: Create Paper
    paper_id = create_test_paper()
    if not paper_id:
        print("❌ Cannot proceed without paper creation")
        return False
    
    # Test 4: Create and Upload File
    test_file = create_test_file()
    if not upload_test_file(paper_id, test_file):
        print("❌ File upload failed")
        return False
    
    # Wait a moment for processing
    print("⏳ Waiting for file processing...")
    time.sleep(2)
    
    # Test 5: Generate Content
    sections = ["Abstract", "Introduction", "Literature Review"]
    for section in sections:
        if not generate_content(paper_id, section):
            print(f"❌ Failed to generate {section}")
            return False
        time.sleep(1)  # Brief pause between generations
    
    # Test 6: Export in Different Formats
    print("\n📥 Testing exports...")
    
    # Export as text
    if not export_paper(paper_id, "text"):
        print("❌ Text export failed")
        return False
    
    # Export as LaTeX
    if not export_paper(paper_id, "latex"):
        print("❌ LaTeX export failed")
        return False
    
    # Export as PDF (if LaTeX available)
    try:
        if not export_paper(paper_id, "pdf"):
            print("⚠️ PDF export failed (LaTeX might not be available)")
    except:
        print("⚠️ PDF export not available")
    
    print("\n" + "=" * 60)
    print("🎉 WORKFLOW TEST COMPLETED SUCCESSFULLY!")
    print("✅ All core functionality is working")
    print("\nGenerated files:")
    print("- test_output.txt (Plain text)")
    print("- test_output.tex (IEEE LaTeX)")
    if os.path.exists("test_output.pdf"):
        print("- test_output.pdf (Compiled PDF)")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)