"""
Simple paper parsing utilities for development
Handles common academic paper formats
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json


class PaperParser:
    """Parse research papers into structured content"""
    
    @staticmethod
    def parse_text_file(file_path: str) -> Dict[str, str]:
        """
        Parse a plain text research paper
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary with parsed sections
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return PaperParser._parse_text_content(content)
            
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return {'content': '', 'title': 'Unknown'}
    
    @staticmethod
    def _parse_text_content(content: str) -> Dict[str, str]:
        """Parse text content into sections"""
        
        # Try to extract title (first non-empty line or line with title pattern)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        title = "Research Paper"
        if lines:
            # Look for common title patterns
            for i, line in enumerate(lines[:5]):  # Check first 5 lines
                if (len(line) > 10 and 
                    not line.lower().startswith(('abstract', 'introduction', 'author', 'university', 'email')) and
                    not re.match(r'^\d+\.', line)):  # Not numbered
                    title = line
                    break
        
        # Clean content
        cleaned_content = content.strip()
        
        # Try to extract abstract
        abstract_match = re.search(
            r'(?:^|\n)(?:abstract|summary)[\s\n]*:?\s*\n?(.*?)(?=\n(?:keywords?|introduction|1\.|method|background|related work))',
            content, 
            re.IGNORECASE | re.DOTALL
        )
        abstract = abstract_match.group(1).strip() if abstract_match else ""
        
        # Extract sections using common patterns
        sections = PaperParser._extract_sections(content)
        
        return {
            'title': title,
            'abstract': abstract,
            'content': cleaned_content,
            'sections': sections,
            'word_count': len(cleaned_content.split())
        }
    
    @staticmethod
    def _extract_sections(content: str) -> List[Dict[str, str]]:
        """Extract main sections from paper"""
        sections = []
        
        # Common section patterns
        section_patterns = [
            r'(?:^|\n)(\d+\.?\s*)([A-Z][A-Za-z\s]+)(?:\n|$)',  # Numbered sections
            r'(?:^|\n)([A-Z][A-Z\s]{2,})(?:\n|$)',  # ALL CAPS headings
            r'(?:^|\n)(Introduction|Background|Method|Results|Discussion|Conclusion|References)(?:\n|$)',  # Common headings
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                section_title = match.group().strip()
                start_pos = match.end()
                
                # Find content until next section or end
                next_section = re.search(
                    r'(?:\n\d+\.?\s*[A-Z][A-Za-z\s]+|\n[A-Z][A-Z\s]{2,}|\nReferences|\nBibliography)',
                    content[start_pos:],
                    re.IGNORECASE | re.MULTILINE
                )
                
                if next_section:
                    section_content = content[start_pos:start_pos + next_section.start()].strip()
                else:
                    section_content = content[start_pos:].strip()
                
                if len(section_content) > 50:  # Minimum section length
                    sections.append({
                        'title': section_title,
                        'content': section_content[:2000]  # Limit section length
                    })
        
        return sections


class MockPaperDatabase:
    """Mock database of research papers for development"""
    
    def __init__(self, papers_dir: str = "samples/papers/"):
        self.papers_dir = Path(papers_dir)
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self._create_sample_papers()
    
    def _create_sample_papers(self):
        """Create sample papers for testing"""
        
        # Sample AI paper
        ai_paper = """
Attention Is All You Need

Abstract:
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

1. Introduction
The goal of reducing sequential computation also forms the foundation of the Extended Neural GPU, ByteNet and ConvS2S, all of which use convolutional neural networks as basic building block, computing hidden representations in parallel for all input and output positions.

2. Background
Self-attention, sometimes called intra-attention is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. Self-attention has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations.

3. Model Architecture
The Transformer follows this overall architecture using stacked self-attention and point-wise, fully connected layers for both the encoder and decoder, shown in the left and right halves of Figure 1, respectively.

3.1 Encoder and Decoder Stacks
The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers. The first is a multi-head self-attention mechanism, and the second is a simple, position-wise fully connected feed-forward network.

4. Experiments
We trained on the standard WMT 2014 English-German dataset consisting of about 4.5 million sentence pairs. Sentences were encoded using byte-pair encoding, which has a shared source-target vocabulary of about 37000 tokens.

5. Results
On the WMT 2014 English-to-German translation task, the big Transformer model (Transformer (big) in the table) outperforms the best previously reported models (including ensembles) by more than 2.0 BLEU, establishing a new single-model state-of-the-art BLEU score of 28.4.

6. Conclusion
In this work, we presented the Transformer, the first sequence transduction model based entirely on attention, replacing the recurrent layers most commonly used in encoder-decoder architectures with multi-headed self-attention.
        """
        
        # Sample ML paper
        ml_paper = """
Deep Residual Learning for Image Recognition

Abstract:
Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.

1. Introduction
Deep convolutional neural networks have led to a series of breakthroughs for image classification. Deep networks naturally integrate low/mid/high-level features and classifiers in an end-to-end multilayer fashion, and the "levels" of features can be enriched by the number of stacked layers (depth).

2. Related Work
Residual Representations. In image recognition, VLAD and Fisher Vector are residual representations that encode residual vectors with respect to a dictionary. In low-level vision and computer graphics, for solving Partial Differential Equations (PDEs), the widely used Multigrid method reformulates the system as subproblems at multiple scales.

3. Deep Residual Learning
Let us consider H(x) as an underlying mapping to be fit by a few stacked layers (not necessarily the entire net), with x denoting the inputs to the first of these layers. If one hypothesizes that multiple nonlinear layers can asymptotically approximate complicated functions, then it is equivalent to hypothesize that they can asymptotically approximate the residual functions.

4. Experiments
We evaluate ResNet on ImageNet 2012 classification dataset that consists of 1.28 million training images and 50K validation images from 1000 classes. We also provide results on CIFAR-10 dataset.

5. Results
Our extremely deep residual nets are easy to optimize, but the counterpart "plain" nets (that simply stack layers) exhibit higher training error when the depth increases. We show that our ResNet with 152 layers achieves 3.57% top-5 error.

6. Conclusion
We have presented a simple, highly modular network architecture for image recognition. Our residual networks are easier to optimize, and can gain accuracy from considerably increased depth.
        """
        
        # Save sample papers
        sample_papers = [
            ("transformer_attention.txt", ai_paper),
            ("resnet_residual.txt", ml_paper)
        ]
        
        for filename, content in sample_papers:
            paper_path = self.papers_dir / filename
            if not paper_path.exists():
                with open(paper_path, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
    
    def get_available_papers(self) -> List[Dict[str, str]]:
        """Get list of available papers"""
        papers = []
        
        for paper_file in self.papers_dir.glob("*.txt"):
            try:
                parsed = PaperParser.parse_text_file(str(paper_file))
                papers.append({
                    'id': paper_file.stem,
                    'filename': paper_file.name,
                    'title': parsed['title'],
                    'word_count': parsed['word_count'],
                    'has_abstract': bool(parsed['abstract'])
                })
            except Exception as e:
                print(f"⚠️  Could not process {paper_file}: {e}")
        
        return papers
    
    def get_paper_content(self, paper_id: str) -> Optional[Dict[str, str]]:
        """Get full paper content by ID"""
        paper_path = self.papers_dir / f"{paper_id}.txt"
        
        if not paper_path.exists():
            return None
        
        return PaperParser.parse_text_file(str(paper_path))


def create_paper_database() -> MockPaperDatabase:
    """Create and return paper database instance"""
    return MockPaperDatabase()


# Simple demo function
async def demo_paper_processing():
    """Demo paper processing and indexing"""
    print("🔬 Paper Processing Demo")
    print("=" * 50)
    
    # Create database
    db = create_paper_database()
    papers = db.get_available_papers()
    
    print(f"📚 Found {len(papers)} sample papers:")
    for paper in papers:
        print(f"  - {paper['title']} ({paper['word_count']} words)")
    
    if papers:
        # Get first paper content
        paper = papers[0]
        content = db.get_paper_content(paper['id'])
        
        print(f"\n📖 Sample content from '{content['title']}':")
        print(f"Abstract: {content['abstract'][:200]}...")
        print(f"Sections found: {len(content['sections'])}")
        
        return content
    
    return None


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_paper_processing())