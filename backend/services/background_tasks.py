"""
Background task service for long-running operations
"""

import asyncio
import threading
from typing import Dict, Any
from services.content_generator import ComprehensiveContentGenerator
from services.file_processor import FileProcessor
from supabase import create_client
from config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_key)

class BackgroundTaskManager:
    def __init__(self):
        self.tasks = {}
        self.content_generator = ComprehensiveContentGenerator()
        self.file_processor = FileProcessor()
    
    def start_paper_generation(self, paper_id: str) -> str:
        """Start background paper generation task"""
        task_id = f"generate_paper_{paper_id}"
        
        # Start the task in a separate thread
        thread = threading.Thread(
            target=self._generate_complete_paper_background,
            args=(paper_id, task_id)
        )
        thread.daemon = True
        thread.start()
        
        self.tasks[task_id] = {
            "status": "started",
            "paper_id": paper_id,
            "thread": thread
        }
        
        return task_id
    
    def _generate_complete_paper_background(self, paper_id: str, task_id: str):
        """Background task for generating complete paper"""
        try:
            # Update task status
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = "running"
            
            print(f"Background: Starting paper generation for {paper_id}")
            
            # Get paper info
            paper_result = supabase.table("papers").select("*").eq("paper_id", paper_id).execute()
            if not paper_result.data:
                raise Exception("Paper not found")
            
            paper = paper_result.data[0]
            
            # Update paper status (without metadata if column doesn't exist)
            try:
                supabase.table("papers").update({"status": "generating"}).eq("paper_id", paper_id).execute()
            except Exception as e:
                print(f"Warning: Could not update paper status: {str(e)}")
            
            # Define sections
            comprehensive_sections = [
                "Abstract", "Introduction", "Literature Review", "Methodology",
                "System Design", "Implementation", "Experimental Setup",
                "Results", "Discussion", "Conclusion", "Future Work"
            ]
            
            # Generate context
            query = f"comprehensive research paper {paper['title']} {paper['domain']}"
            query_embedding = self.file_processor.generate_embeddings(query)
            
            chunks_result = supabase.rpc("match_documents", {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": 20,
                "paper_id": str(paper_id)
            }).execute()
            
            context = ""
            if chunks_result.data:
                context = "\n\n".join([chunk["content"] for chunk in chunks_result.data])
            
            # Check which sections already exist
            existing_sections_result = supabase.table("sections").select("section_name").eq("paper_id", paper_id).execute()
            existing_sections = set(section["section_name"] for section in existing_sections_result.data)
            
            print(f"Background: Found {len(existing_sections)} existing sections: {existing_sections}")
            
            # Group sections into pairs for batch generation
            remaining_sections = [s for s in comprehensive_sections if s not in existing_sections]
            section_pairs = []
            
            # Create pairs of sections
            for i in range(0, len(remaining_sections), 2):
                if i + 1 < len(remaining_sections):
                    section_pairs.append([remaining_sections[i], remaining_sections[i + 1]])
                else:
                    section_pairs.append([remaining_sections[i]])  # Single section if odd number
            
            print(f"Background: Will generate {len(section_pairs)} batches: {section_pairs}")
            
            generated_sections = []
            total_words = 0
            
            # Generate sections in pairs to reduce API calls
            for batch_idx, section_batch in enumerate(section_pairs):
                try:
                    print(f"Background: Generating batch {batch_idx + 1}/{len(section_pairs)}: {section_batch}")
                    
                    # Update progress
                    current_section_name = " & ".join(section_batch)
                    completed_count = len(existing_sections) + len(generated_sections)
                    
                    try:
                        progress = {
                            "current_section": current_section_name,
                            "completed_sections": completed_count,
                            "total_sections": len(comprehensive_sections),
                            "progress_percentage": round((completed_count / len(comprehensive_sections)) * 100)
                        }
                        
                        supabase.table("papers").update({
                            "status": f"generating_batch_{batch_idx + 1}",
                            "metadata": progress
                        }).eq("paper_id", paper_id).execute()
                    except Exception:
                        supabase.table("papers").update({
                            "status": f"generating_batch_{batch_idx + 1}"
                        }).eq("paper_id", paper_id).execute()
                    
                    # Add delay between batches
                    if batch_idx > 0:
                        import time
                        time.sleep(15)  # Longer delay between batches
                    
                    # Generate content for the batch
                    if len(section_batch) > 1:
                        # Multi-section generation
                        batch_content = self.content_generator.generate_multiple_sections_content(
                            section_names=section_batch,
                            paper_title=paper['title'],
                            domain=paper['domain'],
                            context=context,
                            paper_info=paper
                        )
                    else:
                        # Single section generation
                        section_name = section_batch[0]
                        generated_content = self.content_generator.generate_section_content(
                            section_name=section_name,
                            paper_title=paper['title'],
                            domain=paper['domain'],
                            context=context,
                            paper_info=paper
                        )
                        batch_content = {section_name: generated_content}
                    
                    # Save each section from the batch
                    for section_name, generated_content in batch_content.items():
                        try:
                            # Calculate metrics
                            metrics = self.content_generator.estimate_content_length(generated_content)
                            total_words += metrics["words"]
                            
                            # Get section index for ordering
                            section_index = comprehensive_sections.index(section_name)
                            
                            # Save section
                            section_data = {
                                "paper_id": str(paper_id),
                                "section_name": section_name,
                                "content": generated_content,
                                "order_index": section_index
                            }
                            
                            try:
                                section_data["metadata"] = {
                                    "word_count": metrics["words"],
                                    "estimated_pages": metrics["estimated_pages"],
                                    "generation_timestamp": "now()"
                                }
                                section_result = supabase.table("sections").insert(section_data).execute()
                            except Exception as db_error:
                                if "metadata" in str(db_error):
                                    section_data.pop("metadata", None)
                                    section_result = supabase.table("sections").insert(section_data).execute()
                                else:
                                    raise db_error
                            
                            if section_result.data:
                                generated_sections.append({
                                    "section_id": section_result.data[0]["section_id"],
                                    "section_name": section_name,
                                    "word_count": metrics["words"],
                                    "estimated_pages": metrics["estimated_pages"]
                                })
                                print(f"Background: ✅ Generated {section_name}: {metrics['words']} words")
                        
                        except Exception as e:
                            print(f"Background: ❌ Error saving {section_name}: {str(e)}")
                            continue
                
                except Exception as e:
                    print(f"Background: ❌ Error generating batch {section_batch}: {str(e)}")
                    continue
            
            # Complete the task
            total_pages = total_words / 250
            final_status = {
                "completed_sections": len(generated_sections),
                "total_sections": len(comprehensive_sections),
                "progress_percentage": 100,
                "total_words": total_words,
                "estimated_pages": round(total_pages, 1)
            }
            
            try:
                supabase.table("papers").update({
                    "status": "completed",
                    "metadata": final_status
                }).eq("paper_id", paper_id).execute()
            except Exception:
                # If metadata column doesn't exist in papers table
                supabase.table("papers").update({
                    "status": "completed"
                }).eq("paper_id", paper_id).execute()
            
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["result"] = {
                    "sections_generated": len(generated_sections),
                    "total_words": total_words,
                    "estimated_pages": round(total_pages, 1),
                    "sections": generated_sections
                }
            
            print(f"Background: ✅ Paper generation completed for {paper_id}")
            
        except Exception as e:
            print(f"Background: ❌ Paper generation failed for {paper_id}: {str(e)}")
            
            # Update paper status to error
            try:
                supabase.table("papers").update({
                    "status": "error",
                    "metadata": {"error": str(e)}
                }).eq("paper_id", paper_id).execute()
            except Exception:
                supabase.table("papers").update({
                    "status": "error"
                }).eq("paper_id", paper_id).execute()
            
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a background task"""
        return self.tasks.get(task_id, {"status": "not_found"})

# Global instance
background_task_manager = BackgroundTaskManager()