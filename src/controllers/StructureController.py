from .BaseController import BaseController
from models.ChunkModel import ChunkModel
from typing import List
import json
import logging


class StructureController(BaseController):
    
    def __init__(self, generation_client):
        super().__init__()
        self.generation_client = generation_client
        self.logger = logging.getLogger(__name__)
    
    # async def analyze_lecture_structure(
    #     self, 
    #     chunk_model: ChunkModel,
    #     project_id: str,
    #     max_topics: int = None
    # ):
    #     """
    #     Analyze chunks and extract topics/subtitles structure
    #     """
        
    #     # 1. Get all chunks for this project
    #     chunks = await chunk_model.get_chunks_by_project_id(
    #         project_id=project_id,
    #         page_no=1,
    #         page_size=1000  # Get all chunks
    #     )
    #     print("Chunks retrieved:", len(chunks))

    #     if not chunks or len(chunks) == 0:
    #         self.logger.error(f"No chunks found for project {project_id}")
    #         return None
        
    #     # 2. Combine chunks into full text (limit for context window)
    #     # For books, analyze first 100 chunks instead of 20
    #     full_text = "\n\n".join([chunk.chunk_text for chunk in chunks])
    #     # full_text = full_text[:200000]  # Increase to 20k characters
    #     print("FULL TEXT for LLM:\n", full_text)  # Print first 2000 chars
        
    #     # 3. Build prompt for LLM
    #     prompt = self._build_structure_prompt(full_text, max_topics)
        
    #     # 4. Call LLM
    #     try:
    #         response = self.generation_client.generate_text(
    #             prompt=prompt,
    #             temperature=self.app_settings.GENERATION_DAFAULT_TEMPERATURE,
    #             max_output_tokens=self.app_settings.GENERATION_DAFAULT_MAX_TOKENS
    #         )
            
    #         # 5. Parse JSON response
    #         structure = self._parse_structure_response(response)
    #         return structure
            
    #     except Exception as e:
    #         self.logger.error(f"Error analyzing structure: {e}")
    #         return None
    
    
    async def analyze_lecture_structure(
    self, 
    chunk_model: ChunkModel,
    project_id: str,
    max_topics: int = None
):
        chunks = await chunk_model.get_chunks_by_project_id(
            project_id=project_id,
            page_no=1,
            page_size=1000
        )
        
        if not chunks:
            return None
        
        self.logger.info(f"Analyzing {len(chunks)} chunks")
        
        # Split into sections (every 50 chunks = ~1 chapter)
        section_size = 50
        all_topics = []
        
        for i in range(0, len(chunks), section_size):
            section_chunks = chunks[i:i+section_size]
            section_text = "\n\n".join([c.chunk_text for c in section_chunks])
            section_text = section_text[:15000]  # Limit each section
            
            self.logger.info(f"Analyzing section {i//section_size + 1}")
            
            # Analyze this section
            prompt = self._build_structure_prompt(section_text, max_topics)
            response = self.generation_client.generate_text(
                prompt=prompt,
                temperature=self.app_settings.GENERATION_DAFAULT_TEMPERATURE,
                max_output_tokens=self.app_settings.GENERATION_DAFAULT_MAX_TOKENS
            )
            
            structure = self._parse_structure_response(response)
            if structure and "topics" in structure:
                all_topics.extend(structure["topics"])
        
        # Combine all sections and fix ordering
        for idx, topic in enumerate(all_topics):
            topic["order"] = idx + 1
        
        return {"topics": all_topics}
    
    def _build_structure_prompt(self, text: str, max_topics: int=None) -> str:
        """Build prompt for structure analysis"""
        
        # Start the JSON for the model
        prompt = f"""You are an academic document structure extractor.

Extract the structure from this document.

Rules:
1. Identify main topics (major sections)
2. Under each topic, extract subtopics
3. Use exact wording from the document
4. Do not invent content
5. Return ONLY valid JSON, no explanations

Required JSON format:
{{
  "topics": [
    {{
      "title": "Topic Name",
      "order": 1,
      "subtitles": [
        {{"title": "Subtitle 1", "order": 1}},
        {{"title": "Subtitle 2", "order": 2}}
      ]
    }}
  ]
}}

Content:
{text}

Output JSON only:"""
        return prompt
    
    def _parse_structure_response(self, response: str) -> dict:
        response = response.strip()
        
        print("Raw LLM response:", response)
        
        # Remove markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            # Find content between first ``` and last ```
            parts = response.split("```")
            if len(parts) >= 3:
                response = parts[1]  # Content between first and second ```
            else:
                response = response.replace("```", "")
        
        response = response.strip()
        
        self.logger.info(f"After markdown removal: {response[:200]}")
        
        # Determine if it's an object {...} or array [...]
        is_object = response.strip().startswith("{")
        is_array = response.strip().startswith("[")
        
        # Extract JSON
        if is_object:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx]
        elif is_array:
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1
            if start_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx]
        
        response = response.strip()
        
        self.logger.info(f"Final JSON to parse: {response[:200]}")
        
        try:
            structure = json.loads(response)
            
            # If it's an array, wrap it
            if isinstance(structure, list):
                structure = {"topics": structure}
            
            # Validate
            if "topics" not in structure:
                self.logger.error("Response missing 'topics' field")
                return self._create_fallback_structure("")
            
            self.logger.info(f"Successfully parsed structure with {len(structure['topics'])} topics")
            return structure
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse failed: {e}")
            self.logger.error(f"Attempted to parse: {response[:500]}")
            return self._create_fallback_structure(response)

    def _create_fallback_structure(self, text: str) -> dict:
        """Create a simple fallback structure when JSON parsing fails"""
        return {
            "topics": [
                {
                    "title": "Document Content",
                    "order": 1,
                    "subtitles": [
                        {"title": "Main Content", "order": 1}
                    ]
                }
            ]
        }