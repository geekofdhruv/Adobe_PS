import os
import re
import time
import json # Import json to read outline files
import fitz  # PyMuPDF
import torch
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from config import MODEL_NAME, BATCH_SIZE, INPUT_DIR, MMR_DIVERSITY, OUTLINE_DIR # Add OUTLINE_DIR to config

class DocumentRetriever:
    """
    An advanced class for document analysis that uses structured outlines for smart chunking,
    HyDE for contextual queries, and MMR for diverse section retrieval.
    """
    def __init__(self):
        self.device = self._get_device()
        self.model = self._load_model()
        self.hyde_generator = self._create_hyde_generator()

    def _get_device(self):
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        return torch.device('cpu')

    def _load_model(self):
        print(f"🧠 Loading model '{MODEL_NAME}' onto {self.device}...")
        start_time = time.time()
        model_path = './embedding_model'
        if not os.path.isdir(model_path):
            raise FileNotFoundError(f"Model directory not found at '{model_path}'.")
        model = SentenceTransformer(model_path, device=self.device)
        print(f"✅ Model loaded in {time.time() - start_time:.2f}s.")
        return model
        
    def _create_hyde_generator(self):
        # This function remains unchanged
        def generator(query):
            if "I need to" in query:
                return query.replace("I need to", "is looking for information on how to") + ". A good plan would include details on activities, dining, and logistics."
            return query + " Here is a detailed guide."
        return generator

    # --------------------------------------------------------------------------
    # NEW: Smart Chunking based on Round 1A Outline
    # --------------------------------------------------------------------------
    def _extract_sections_from_outline(self, filepath, filename, outline_data):
        """
        Extracts structured content chunks from a PDF using its pre-computed outline.
        A chunk is defined as a heading plus all text until the next heading of the same or higher level.
        """
        sections = []
        doc = fitz.open(filepath)
        
        # Add the document title as the first potential section context
        headings = [{"level": "H0", "text": outline_data.get("title", ""), "page": 1}] + outline_data["outline"]

        for i, current_heading in enumerate(headings):
            start_page = current_heading["page"]
            
            # Find the vertical position of the current heading to start extraction
            start_y = 0
            page_for_search = doc.load_page(start_page - 1)
            # Search for the heading text on its page to get its position
            search_results = page_for_search.search_for(current_heading["text"])
            if search_results:
                start_y = search_results[0].y1 # Start extracting right after the heading's bounding box
            
            # Determine the end boundary for this section
            end_page = len(doc)
            end_y = doc[end_page - 1].rect.height # Default to end of document
            
            # The section ends at the start of the next heading of the same or higher level
            for next_heading in headings[i+1:]:
                # Compare levels (H1 < H2, etc.)
                if next_heading["level"] <= current_heading["level"]:
                    end_page = next_heading["page"]
                    # Find the position of the next heading
                    next_search_results = doc[end_page - 1].search_for(next_heading["text"])
                    if next_search_results:
                        end_y = next_search_results[0].y0 # End right before the next heading's bounding box
                    break

            # Extract the text content for the defined section
            content_text = ""
            for page_num in range(start_page, end_page + 1):
                page = doc.load_page(page_num - 1)
                clip_rect = fitz.Rect(0, 0, page.rect.width, page.rect.height) # Default to full page
                
                if page_num == start_page:
                    clip_rect.y0 = start_y
                if page_num == end_page:
                    clip_rect.y1 = end_y

                content_text += page.get_text(clip=clip_rect) + " "
            
            content_text = re.sub(r'\s+', ' ', content_text).strip()

            # Create the chunk if it has meaningful content
            if len(content_text.split()) > 10:
                # The text for embedding includes the heading for crucial context
                contextual_text = f"Section: {current_heading['text']}. Content: {content_text}"
                sections.append({
                    "text": contextual_text,
                    "original_text": content_text,
                    "metadata": {
                        "document": filename,
                        "section_title": current_heading['text'],
                        "page_number": current_heading['page']
                    }
                })
        
        doc.close()
        return sections

    def _embed_texts(self, texts):
        # This function remains unchanged
        return self.model.encode(
            texts, convert_to_tensor=True, batch_size=BATCH_SIZE, show_progress_bar=True, device=self.device
        )

    # --------------------------------------------------------------------------
    # MODIFIED: process_collection to use the new chunking method
    # --------------------------------------------------------------------------
    def process_collection(self, pdf_files, persona, job_to_be_done, top_k_sections, top_k_subsections):
        # 1. Formulate the master query (unchanged)
        query = f"As a {persona}, {job_to_be_done}"
        print(f"\n🔍 Original Query: {query}")

        # 2. HyDE: Generate a hypothetical document (unchanged)
        hypothetical_doc = self.hyde_generator(query)
        print(f"📝 Hypothetical Document (HyDE): {hypothetical_doc}")
        query_embedding = self._embed_texts([hypothetical_doc])[0]

        # 3. Process all documents using the NEW outline-based chunking
        all_chunks = []
        for filename in pdf_files:
            filepath = os.path.join(INPUT_DIR, filename)
            outline_path = os.path.join(OUTLINE_DIR, filename.replace('.pdf', '.json'))

            if not os.path.exists(outline_path):
                print(f"⚠️ Warning: Outline file not found for {filename}. Skipping.")
                continue
            
            with open(outline_path, 'r') as f:
                outline_data = json.load(f)

            all_chunks.extend(self._extract_sections_from_outline(filepath, filename, outline_data))
        
        if not all_chunks:
            return {}

        chunk_texts = [chunk['text'] for chunk in all_chunks]
        chunk_embeddings = self._embed_texts(chunk_texts)
        
        # 4. Stage 1: Retrieve diverse top sections using MMR (unchanged)
        # ... (The rest of the function remains the same as your original)
        # ... from here on, the logic for MMR, summarization, and result formatting
        # ... is identical to your provided script.
        print("\n🔬 Performing Maximal Marginal Relevance (MMR) search for diverse sections...")
        top_indices = util.semantic_search(query_embedding, chunk_embeddings, top_k=top_k_sections * 5)[0]
        relevant_indices = [res['corpus_id'] for res in top_indices]
        mmr_selected_indices = self._run_mmr(query_embedding, chunk_embeddings, relevant_indices, top_k=top_k_sections)

        extracted_sections = []
        for rank, idx in enumerate(mmr_selected_indices):
            chunk = all_chunks[idx]
            score = util.cos_sim(query_embedding, chunk_embeddings[idx]).item()
            extracted_sections.append({
                "document": chunk["metadata"]["document"],
                "section_title": chunk["metadata"]["section_title"],
                "page_number": chunk["metadata"]["page_number"],
                "importance_rank": rank + 1,
                "similarity_score": round(score, 4),
                "content": chunk["original_text"]
            })

        # 5. Stage 2: Intelligent Summarization (unchanged)
        print("\n✨ Performing intelligent re-ranking and summarization for sub-sections...")
        # ... (rest of the function is identical)
        subsection_analysis = []
        for section in extracted_sections[:top_k_subsections]:
            summary = self._summarize_chunk_with_top_sentences(section['content'], query_embedding)
            subsection_analysis.append({
                "document": section["document"],
                "page_number": section["page_number"],
                "refined_text": summary
            })
            
        result = {
            "metadata": { "input_documents": pdf_files, "persona": persona, "job_to_be_done": job_to_be_done, "timestamp": datetime.utcnow().isoformat() + "Z" },
            "extracted_sections": [{k: v for k, v in sec.items() if k != 'content'} for sec in extracted_sections],
            "subsection_analysis": subsection_analysis
        }
        return result

    def _run_mmr(self, query_emb, corpus_embs, candidate_indices, top_k):
        # This function remains unchanged
        # ...
        selected_indices = []
        candidate_embs = corpus_embs[candidate_indices]
        while len(selected_indices) < min(top_k, len(candidate_indices)):
            best_score = -np.inf
            best_idx = -1
            for i in range(len(candidate_indices)):
                if i in selected_indices: continue
                relevance_score = util.cos_sim(query_emb, corpus_embs[candidate_indices[i]]).item()
                if not selected_indices:
                    redundancy = 0
                else:
                    redundancy = max([util.cos_sim(corpus_embs[candidate_indices[i]], corpus_embs[candidate_indices[j]]).item() for j in selected_indices])
                mmr_score = MMR_DIVERSITY * relevance_score - (1 - MMR_DIVERSITY) * redundancy
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            if best_idx != -1:
                selected_indices.append(best_idx)
        return [candidate_indices[i] for i in selected_indices]

    def _summarize_chunk_with_top_sentences(self, text, query_embedding):
        # This function remains unchanged
        # ...
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.split()) > 5]
        if not sentences: return text
        sentence_embeddings = self._embed_texts(sentences)
        similarities = util.pytorch_cos_sim(query_embedding, sentence_embeddings)[0].cpu().tolist()
        top_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:4]
        top_indices.sort()
        return " ".join([sentences[i] for i in top_indices])