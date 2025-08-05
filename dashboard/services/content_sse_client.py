"""
SSE Client for real-time content generation updates
"""
import streamlit as st
import requests
import json
import time
import threading
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import sseclient


class ContentGenerationSSE:
    """Client for receiving real-time updates from content generation tasks"""
    
    def __init__(self, celery_worker_url: str = "http://localhost:8081"):
        self.celery_worker_url = celery_worker_url
        self.is_connected = False
        self.thread = None
        self.stop_flag = threading.Event()
        
    def connect_to_task(self, task_id: str, progress_callback: Callable, completion_callback: Callable):
        """Connect to SSE endpoint for a specific task"""
        def stream_events():
            try:
                # Connect to Celery Worker SSE endpoint
                headers = {'Accept': 'text/event-stream'}
                response = requests.get(
                    f"{self.celery_worker_url}/sse/{task_id}",
                    headers=headers,
                    stream=True
                )
                
                client = sseclient.SSEClient(response)
                
                for event in client.events():
                    if self.stop_flag.is_set():
                        break
                        
                    try:
                        data = json.loads(event.data)
                        
                        # Handle different event types
                        if data.get('type') == 'progress':
                            progress_callback({
                                'progress': data.get('progress', 0),
                                'message': data.get('message', 'Processing...'),
                                'stage': data.get('stage', 'unknown')
                            })
                            
                        elif data.get('type') == 'complete':
                            completion_callback({
                                'success': True,
                                'content': data.get('content', {}),
                                'duration': data.get('duration', 0)
                            })
                            break
                            
                        elif data.get('type') == 'error':
                            completion_callback({
                                'success': False,
                                'error': data.get('error', 'Unknown error'),
                                'duration': data.get('duration', 0)
                            })
                            break
                            
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                completion_callback({
                    'success': False,
                    'error': f"SSE connection error: {str(e)}"
                })
                
        self.stop_flag.clear()
        self.thread = threading.Thread(target=stream_events, daemon=True)
        self.thread.start()
        self.is_connected = True
        
    def disconnect(self):
        """Disconnect from SSE stream"""
        self.stop_flag.set()
        self.is_connected = False
        

class ContentGenerationTracker:
    """Tracks content generation progress in Streamlit"""
    
    def __init__(self):
        self.sse_client = ContentGenerationSSE()
        
    def track_generation(self, task_id: str, container):
        """Track content generation with progress updates"""
        
        # Progress state
        if f'gen_progress_{task_id}' not in st.session_state:
            st.session_state[f'gen_progress_{task_id}'] = {
                'progress': 0,
                'message': 'Initializing...',
                'stage': 'init',
                'complete': False,
                'result': None
            }
            
        def update_progress(data: Dict[str, Any]):
            """Update progress in session state"""
            st.session_state[f'gen_progress_{task_id}'].update({
                'progress': data.get('progress', 0),
                'message': data.get('message', ''),
                'stage': data.get('stage', '')
            })
            
        def handle_completion(data: Dict[str, Any]):
            """Handle task completion"""
            st.session_state[f'gen_progress_{task_id}'].update({
                'complete': True,
                'result': data
            })
            
        # Start tracking
        self.sse_client.connect_to_task(task_id, update_progress, handle_completion)
        
        # Display progress
        with container:
            state = st.session_state[f'gen_progress_{task_id}']
            
            if not state['complete']:
                # Show progress
                progress = state['progress'] / 100.0
                st.progress(progress)
                
                # Stage indicators
                stages = {
                    'init': '🚀 Initializing',
                    'fetch_trends': '🔍 Analyzing trends',
                    'generate_hook': '🎣 Creating hook',
                    'generate_body': '📝 Writing content',
                    'optimize': '✨ Optimizing for engagement',
                    'finalize': '🎯 Finalizing'
                }
                
                current_stage = stages.get(state['stage'], state['stage'])
                st.markdown(f"**{current_stage}**")
                st.caption(state['message'])
                
                # Estimated time
                if progress > 0:
                    elapsed = (datetime.now() - st.session_state.get(f'start_time_{task_id}', datetime.now())).seconds
                    if progress > 0.1:  # Avoid division by very small numbers
                        estimated_total = elapsed / progress
                        remaining = estimated_total - elapsed
                        st.caption(f"⏱️ Est. time remaining: {int(remaining)}s")
                        
            else:
                # Show result
                result = state['result']
                if result['success']:
                    st.success("✅ Content generated successfully!")
                    
                    # Display generated content
                    content = result.get('content', {})
                    if content.get('hook'):
                        st.markdown("### 🎣 Hook")
                        st.info(content['hook'])
                        
                    if content.get('body'):
                        st.markdown("### 📝 Content")
                        st.text_area("Generated content", content['body'], height=300)
                        
                    if content.get('hashtags'):
                        st.markdown("### 🏷️ Hashtags")
                        st.write(' '.join(content['hashtags']))
                        
                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Duration", f"{result.get('duration', 0):.1f}s")
                    with col2:
                        st.metric("Tokens Used", content.get('tokens_used', 0))
                    with col3:
                        st.metric("Quality Score", f"{content.get('quality_score', 0):.1f}")
                        
                else:
                    st.error(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
                    
                # Disconnect SSE
                self.sse_client.disconnect()
                

def create_mock_sse_demo(container):
    """Create a demo of SSE progress tracking"""
    
    # Simulate progress updates
    progress_states = [
        {'progress': 10, 'message': 'Fetching recent achievements...', 'stage': 'init'},
        {'progress': 25, 'message': 'Analyzing trending topics...', 'stage': 'fetch_trends'},
        {'progress': 40, 'message': 'Generating viral hook...', 'stage': 'generate_hook'},
        {'progress': 60, 'message': 'Writing main content...', 'stage': 'generate_body'},
        {'progress': 80, 'message': 'Optimizing for engagement...', 'stage': 'optimize'},
        {'progress': 95, 'message': 'Final touches...', 'stage': 'finalize'},
        {'progress': 100, 'message': 'Complete!', 'stage': 'complete'}
    ]
    
    # Simulate SSE updates
    for state in progress_states:
        with container.container():
            progress = state['progress'] / 100.0
            st.progress(progress)
            st.markdown(f"**{state['stage'].title()}**")
            st.caption(state['message'])
            
        time.sleep(1)  # Simulate processing time
        
    # Show completion
    with container.container():
        st.success("✅ Content generated successfully!")
        st.markdown("### Generated Content")
        st.info("🎣 **Hook**: Stop what you're doing! Here's how I cut our API response time by 78%...")
        st.text_area(
            "Content", 
            "When I first looked at our API performance metrics, I nearly fell off my chair...",
            height=200
        )