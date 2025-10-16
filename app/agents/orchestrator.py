"""
Agentic Orchestrator - Core State Machine for Paper→Podcast
Implements the autonomous workflow with self-correction and verification loops
"""

import asyncio
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.models import (
    ProcessingJob, ProcessingState, AgentState, Paper, PodcastEpisode,
    EpisodeOutline, PodcastSegment
)
from app.agents.planner import PlanningAgent
from app.agents.generator import ContentGenerationAgent
from app.agents.verifier import FactVerificationAgent
from app.agents.rewriter import ContentRewriterAgent
from app.services.nim_client import NIMClient
from app.services.rag_service import DualRAGService
from app.services.tts_service import TTSService
from app.services.audio_processor import AudioProcessor
from app.storage.opensearch_client import OpenSearchClient
from app.storage.s3_client import S3Client
from app.utils.metrics import MetricsCollector
from app.config import settings, get_budget_info


logger = structlog.get_logger(__name__)


class AgenticOrchestrator:
    """
    Main orchestrator for the agentic Paper→Podcast workflow
    
    Implements a state machine with autonomous decision-making:
    Upload → Index → Outline → Draft(segment_i) → FactCheck(i) → 
    [Rewrite if needed] → TTS(i) → Stitch → Export
    """
    
    def __init__(self):
        """Initialize the orchestrator with all required services"""
        self.nim_client = NIMClient()
        self.rag_service = DualRAGService()
        self.opensearch_client = OpenSearchClient()
        self.s3_client = S3Client()
        self.tts_service = TTSService()
        self.audio_processor = AudioProcessor()
        self.metrics_collector = MetricsCollector()
        
        # Initialize agents
        self.planning_agent = PlanningAgent(self.nim_client, self.rag_service)
        self.generation_agent = ContentGenerationAgent(self.nim_client, self.rag_service)
        self.verification_agent = FactVerificationAgent(self.nim_client, self.rag_service)
        self.rewriter_agent = ContentRewriterAgent(self.nim_client, self.rag_service)
        
        # State machine configuration
        self.state_transitions = {
            ProcessingState.UPLOADED: [ProcessingState.INDEXING, ProcessingState.FAILED],
            ProcessingState.INDEXING: [ProcessingState.PLANNING, ProcessingState.FAILED],
            ProcessingState.PLANNING: [ProcessingState.DRAFTING, ProcessingState.FAILED],
            ProcessingState.DRAFTING: [ProcessingState.FACT_CHECKING, ProcessingState.FAILED],
            ProcessingState.FACT_CHECKING: [ProcessingState.REWRITING, ProcessingState.GENERATING_AUDIO, ProcessingState.FAILED],
            ProcessingState.REWRITING: [ProcessingState.FACT_CHECKING, ProcessingState.FAILED],
            ProcessingState.GENERATING_AUDIO: [ProcessingState.STITCHING, ProcessingState.FAILED],
            ProcessingState.STITCHING: [ProcessingState.COMPLETED, ProcessingState.FAILED],
            ProcessingState.COMPLETED: [],
            ProcessingState.FAILED: []
        }
    
    async def process_paper(self, paper: Paper, options: Dict[str, Any] = None) -> ProcessingJob:
        """
        Main entry point for processing a paper into a podcast
        
        Args:
            paper: Paper object with extracted content
            options: Processing options (fast_mode, etc.)
            
        Returns:
            ProcessingJob: Job tracking object
        """
        options = options or {}
        
        # Create processing job
        job = ProcessingJob(
            paper_id=paper.paper_id,
            current_state=ProcessingState.UPLOADED
        )
        
        logger.info(
            "Starting agentic processing",
            paper_id=paper.paper_id,
            job_id=job.job_id,
            fast_mode=options.get('fast_mode', False)
        )
        
        try:
            # Initialize agent state
            agent_state = AgentState(
                current_state=ProcessingState.UPLOADED,
                can_transition_to=self.state_transitions[ProcessingState.UPLOADED]
            )
            
            # Run the autonomous workflow
            result = await self._execute_workflow(paper, job, agent_state, options)
            
            if result:
                job.current_state = ProcessingState.COMPLETED
                job.progress_percentage = 100.0
                job.end_time = datetime.now()
                
                logger.info(
                    "Processing completed successfully",
                    job_id=job.job_id,
                    total_cost=job.cost_estimate,
                    total_time=(job.end_time - job.start_time).total_seconds()
                )
            
            return job
            
        except Exception as e:
            logger.error(
                "Processing failed",
                job_id=job.job_id,
                error=str(e),
                state=job.current_state
            )
            job.current_state = ProcessingState.FAILED
            job.error_message = str(e)
            job.end_time = datetime.now()
            return job
    
    async def _execute_workflow(
        self, 
        paper: Paper, 
        job: ProcessingJob, 
        state: AgentState, 
        options: Dict[str, Any]
    ) -> bool:
        """
        Execute the autonomous workflow state machine
        
        Returns True if successful, False otherwise
        """
        max_iterations = 50  # Prevent infinite loops
        iteration = 0
        
        while state.current_state != ProcessingState.COMPLETED and iteration < max_iterations:
            iteration += 1
            
            logger.debug(
                "Processing state transition",
                job_id=job.job_id,
                current_state=state.current_state,
                iteration=iteration
            )
            
            # Check budget constraints
            if not await self._check_budget_constraints(job):
                raise Exception("Budget constraints exceeded")
            
            # Execute current state
            success = await self._execute_state(paper, job, state, options)
            
            if not success:
                if state.retry_count < state.max_retries:
                    state.retry_count += 1
                    logger.warning(
                        "State execution failed, retrying",
                        job_id=job.job_id,
                        state=state.current_state,
                        retry_count=state.retry_count
                    )
                    continue
                else:
                    logger.error(
                        "State execution failed after max retries",
                        job_id=job.job_id,
                        state=state.current_state
                    )
                    await self._transition_state(state, ProcessingState.FAILED)
                    return False
            
            # Determine next state based on current state and results
            next_state = await self._determine_next_state(state, job)
            if next_state != state.current_state:
                await self._transition_state(state, next_state)
                state.retry_count = 0  # Reset retry count on successful transition
            
            # Update job progress
            job.progress_percentage = self._calculate_progress(state.current_state)
        
        return state.current_state == ProcessingState.COMPLETED
    
    async def _execute_state(
        self, 
        paper: Paper, 
        job: ProcessingJob, 
        state: AgentState, 
        options: Dict[str, Any]
    ) -> bool:
        """Execute the current state action"""
        
        try:
            if state.current_state == ProcessingState.INDEXING:
                return await self._state_indexing(paper, job, state, options)
            
            elif state.current_state == ProcessingState.PLANNING:
                return await self._state_planning(paper, job, state, options)
            
            elif state.current_state == ProcessingState.DRAFTING:
                return await self._state_drafting(paper, job, state, options)
            
            elif state.current_state == ProcessingState.FACT_CHECKING:
                return await self._state_fact_checking(paper, job, state, options)
            
            elif state.current_state == ProcessingState.REWRITING:
                return await self._state_rewriting(paper, job, state, options)
            
            elif state.current_state == ProcessingState.GENERATING_AUDIO:
                return await self._state_generating_audio(paper, job, state, options)
            
            elif state.current_state == ProcessingState.STITCHING:
                return await self._state_stitching(paper, job, state, options)
            
            else:
                logger.warning(
                    "Unknown state",
                    job_id=job.job_id,
                    state=state.current_state
                )
                return False
                
        except Exception as e:
            logger.error(
                "State execution error",
                job_id=job.job_id,
                state=state.current_state,
                error=str(e)
            )
            return False
    
    async def _state_indexing(self, paper: Paper, job: ProcessingJob, state: AgentState, options: Dict[str, Any]) -> bool:
        """Index paper content for RAG"""
        logger.info("Starting content indexing", job_id=job.job_id)
        
        # Create dual indexes (facts + style)
        facts_indexed = await self.rag_service.index_paper_content(
            paper.paper_id,
            paper.content,
            paper.title or paper.filename
        )
        
        style_indexed = await self.rag_service.index_style_patterns()
        
        # Update metrics
        await self.metrics_collector.track_operation("indexing", job.job_id, 0.5)  # Estimated cost
        job.cost_estimate += 0.5
        
        return facts_indexed and style_indexed
    
    async def _state_planning(self, paper: Paper, job: ProcessingJob, state: AgentState, options: Dict[str, Any]) -> bool:
        """Generate episode outline using planning agent"""
        logger.info("Starting episode planning", job_id=job.job_id)
        
        outline = await self.planning_agent.create_episode_outline(
            paper,
            fast_mode=options.get('fast_mode', False)
        )
        
        if outline:
            job.outline = outline
            state.state_data['outline_created'] = True
            
            # Update cost estimate
            tokens_used = len(paper.content.split()) * 2  # Rough estimate
            job.tokens_used += tokens_used
            job.cost_estimate += await self._estimate_cost(tokens_used)
            
            return True
        
        return False
    
    async def _state_drafting(self, paper: Paper, job: ProcessingJob, state: AgentState, options: Dict[str, Any]) -> bool:
        """Generate script content for segments"""
        logger.info("Starting script drafting", job_id=job.job_id)
        
        if not job.outline:
            return False
        
        # Get current segment or start with first
        current_segment_idx = state.state_data.get('current_segment', 0)
        
        if current_segment_idx >= len(job.outline.segments):
            # All segments drafted
            return True
        
        segment = job.outline.segments[current_segment_idx]
        
        # Generate script for current segment
        script_lines = await self.generation_agent.generate_segment_script(
            segment,
            paper,
            job.outline
        )
        
        if script_lines:
            segment.script_lines = script_lines
            segment.is_complete = True
            
            # Update state to process next segment
            state.state_data['current_segment'] = current_segment_idx + 1
            
            # Update metrics
            tokens_used = sum(len(line.text.split()) for line in script_lines) * 3
            job.tokens_used += tokens_used
            job.cost_estimate += await self._estimate_cost(tokens_used)
            
            return True
        
        return False
    
    async def _state_fact_checking(self, paper: Paper, job: ProcessingJob, state: AgentState, options: Dict[str, Any]) -> bool:
        """Verify script content against source material"""
        logger.info("Starting fact verification", job_id=job.job_id)
        
        if not job.outline:
            return False
        
        current_segment_idx = state.state_data.get('current_segment', 1) - 1  # Last drafted segment
        
        if current_segment_idx < 0 or current_segment_idx >= len(job.outline.segments):
            return False
        
        segment = job.outline.segments[current_segment_idx]
        
        # Verify each script line
        verification_results = await self.verification_agent.verify_segment(
            segment,
            paper
        )
        
        # Update script lines with verification results
        needs_rewrite = False
        for i, (line, verification) in enumerate(zip(segment.script_lines, verification_results)):
            line.is_verified = verification['is_verified']
            line.citations = verification['citations']
            line.needs_rewrite = not verification['is_verified']
            
            if line.needs_rewrite:
                needs_rewrite = True
        
        # Update segment verification status
        segment.verification_passed = not needs_rewrite
        
        # Set next state based on verification results
        if needs_rewrite:
            state.state_data['needs_rewrite'] = True
        else:
            state.state_data['needs_rewrite'] = False
        
        # Update metrics
        tokens_used = len(' '.join([line.text for line in segment.script_lines]).split()) * 2
        job.tokens_used += tokens_used
        job.cost_estimate += await self._estimate_cost(tokens_used)
        
        return True
    
    async def _state_rewriting(self, paper: Paper, job: ProcessingJob, state: AgentState, options: Dict[str, Any]) -> bool:
        """Rewrite unverified content"""
        logger.info("Starting content rewriting", job_id=job.job_id)
        
        if not job.outline:
            return False
        
        current_segment_idx = state.state_data.get('current_segment', 1) - 1
        segment = job.outline.segments[current_segment_idx]
        
        # Rewrite lines that need rewriting
        rewritten_lines = await self.rewriter_agent.rewrite_unverified_lines(
            segment,
            paper
        )
        
        if rewritten_lines:
            # Replace unverified lines
            for i, line in enumerate(segment.script_lines):
                if line.needs_rewrite and i < len(rewritten_lines):
                    segment.script_lines[i] = rewritten_lines[i]
            
            # Clear rewrite flags
            state.state_data['needs_rewrite'] = False
            
            # Update metrics
            tokens_used = sum(len(line.text.split()) for line in rewritten_lines) * 2
            job.tokens_used += tokens_used
            job.cost_estimate += await self._estimate_cost(tokens_used)
            
            return True
        
        return False
    
    async def _state_generating_audio(self, paper: Paper, job: ProcessingJob, state: AgentState, options: Dict[str, Any]) -> bool:
        """Generate audio for verified segments"""
        logger.info("Starting audio generation", job_id=job.job_id)
        
        if not job.outline:
            return False
        
        # Generate audio for all completed and verified segments
        audio_files = []
        
        for segment in job.outline.segments:
            if segment.is_complete and segment.verification_passed:
                audio_url = await self.tts_service.generate_segment_audio(segment)
                if audio_url:
                    segment.audio_url = audio_url
                    audio_files.append(audio_url)
        
        if len(audio_files) == len(job.outline.segments):
            state.state_data['audio_generated'] = True
            
            # Update cost estimate (TTS costs)
            total_text = sum(len(' '.join([line.text for line in seg.script_lines])) 
                           for seg in job.outline.segments)
            tts_cost = total_text * 0.000016  # AWS Polly pricing estimate
            job.cost_estimate += tts_cost
            
            return True
        
        return False
    
    async def _state_stitching(self, paper: Paper, job: ProcessingJob, state: AgentState, options: Dict[str, Any]) -> bool:
        """Stitch audio segments into final episode"""
        logger.info("Starting audio stitching", job_id=job.job_id)
        
        if not job.outline or not all(seg.audio_url for seg in job.outline.segments):
            return False
        
        # Collect audio URLs in order
        audio_urls = [seg.audio_url for seg in job.outline.segments]
        
        # Stitch together with transitions
        final_audio_url = await self.audio_processor.stitch_segments(
            audio_urls,
            job.job_id
        )
        
        if final_audio_url:
            # Create final episode object
            episode = PodcastEpisode(
                paper_id=paper.paper_id,
                job_id=job.job_id,
                outline=job.outline,
                segments=job.outline.segments,
                audio_url=final_audio_url,
                total_duration=sum(seg.actual_duration or seg.duration_target 
                                 for seg in job.outline.segments),
                citation_count=sum(len(line.citations) 
                                 for seg in job.outline.segments 
                                 for line in seg.script_lines),
                verification_rate=self._calculate_verification_rate(job.outline.segments),
                total_cost=job.cost_estimate,
                processing_time=(datetime.now() - job.start_time).total_seconds()
            )
            
            # Store episode metadata
            await self._store_episode(episode)
            
            state.state_data['episode_id'] = episode.episode_id
            return True
        
        return False
    
    async def _determine_next_state(self, state: AgentState, job: ProcessingJob) -> ProcessingState:
        """Determine next state based on current state and results"""
        
        if state.current_state == ProcessingState.INDEXING:
            return ProcessingState.PLANNING
        
        elif state.current_state == ProcessingState.PLANNING:
            return ProcessingState.DRAFTING
        
        elif state.current_state == ProcessingState.DRAFTING:
            # Check if more segments need drafting
            current_segment = state.state_data.get('current_segment', 0)
            if job.outline and current_segment < len(job.outline.segments):
                return ProcessingState.DRAFTING  # Continue drafting
            else:
                return ProcessingState.FACT_CHECKING
        
        elif state.current_state == ProcessingState.FACT_CHECKING:
            # Check if rewriting is needed
            if state.state_data.get('needs_rewrite', False):
                return ProcessingState.REWRITING
            else:
                # Check if more segments need fact-checking
                current_segment = state.state_data.get('current_segment', 0)
                if job.outline and current_segment < len(job.outline.segments):
                    return ProcessingState.DRAFTING  # Back to draft next segment
                else:
                    return ProcessingState.GENERATING_AUDIO
        
        elif state.current_state == ProcessingState.REWRITING:
            return ProcessingState.FACT_CHECKING  # Re-verify after rewriting
        
        elif state.current_state == ProcessingState.GENERATING_AUDIO:
            return ProcessingState.STITCHING
        
        elif state.current_state == ProcessingState.STITCHING:
            return ProcessingState.COMPLETED
        
        else:
            return ProcessingState.FAILED
    
    async def _transition_state(self, state: AgentState, new_state: ProcessingState):
        """Transition to new state with validation"""
        if not state.can_transition(new_state):
            raise ValueError(f"Invalid transition from {state.current_state} to {new_state}")
        
        state.previous_state = state.current_state
        state.current_state = new_state
        state.can_transition_to = self.state_transitions.get(new_state, [])
        
        logger.debug(
            "State transition",
            from_state=state.previous_state,
            to_state=state.current_state
        )
    
    async def _check_budget_constraints(self, job: ProcessingJob) -> bool:
        """Check if processing can continue within budget"""
        budget_info = get_budget_info()
        
        if job.cost_estimate >= budget_info['max_cost']:
            logger.warning(
                "Budget limit reached",
                job_id=job.job_id,
                cost_estimate=job.cost_estimate,
                max_cost=budget_info['max_cost']
            )
            return False
        
        return True
    
    async def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token usage"""
        # Rough estimate based on NVIDIA NIM pricing
        return tokens * 0.0001  # $0.0001 per token estimate
    
    def _calculate_progress(self, state: ProcessingState) -> float:
        """Calculate progress percentage based on current state"""
        state_progress = {
            ProcessingState.UPLOADED: 0.0,
            ProcessingState.INDEXING: 10.0,
            ProcessingState.PLANNING: 20.0,
            ProcessingState.DRAFTING: 50.0,
            ProcessingState.FACT_CHECKING: 70.0,
            ProcessingState.REWRITING: 75.0,
            ProcessingState.GENERATING_AUDIO: 85.0,
            ProcessingState.STITCHING: 95.0,
            ProcessingState.COMPLETED: 100.0,
            ProcessingState.FAILED: 0.0
        }
        return state_progress.get(state, 0.0)
    
    def _calculate_verification_rate(self, segments: List[PodcastSegment]) -> float:
        """Calculate percentage of verified content"""
        total_lines = sum(len(seg.script_lines) for seg in segments)
        if total_lines == 0:
            return 0.0
        
        verified_lines = sum(
            sum(1 for line in seg.script_lines if line.is_verified)
            for seg in segments
        )
        
        return verified_lines / total_lines
    
    async def _store_episode(self, episode: PodcastEpisode):
        """Store episode data for retrieval"""
        # Store in OpenSearch for searchability
        await self.opensearch_client.index_episode(episode)
        
        # Store metadata in S3
        await self.s3_client.store_episode_metadata(episode)
    
    async def get_job_status(self, job_id: str) -> Optional[ProcessingJob]:
        """Get current status of a processing job"""
        # This would typically fetch from a database or cache
        # For hackathon demo, we'll implement a simple in-memory store
        pass
    
    async def regenerate_segment(self, job_id: str, segment_id: str, options: Dict[str, Any] = None) -> bool:
        """Regenerate a specific segment (key feature for demo)"""
        logger.info(
            "Regenerating segment",
            job_id=job_id,
            segment_id=segment_id,
            options=options
        )
        
        # This would implement segment-specific regeneration
        # Key differentiator for the hackathon submission
        pass