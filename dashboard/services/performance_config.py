"""
Performance optimization configuration and utilities for the dashboard
"""
import streamlit as st
from functools import wraps
import time
import hashlib
import json
from typing import Any, Callable, Optional
from datetime import datetime, timedelta


# Cache configuration
CACHE_CONFIG = {
    'achievements': 300,      # 5 minutes
    'metrics': 60,           # 1 minute
    'health': 30,            # 30 seconds
    'analytics': 600,        # 10 minutes
    'content_pipeline': 120, # 2 minutes
}


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Log slow functions
        if execution_time > 1000:  # More than 1 second
            st.warning(f"⚠️ Slow operation: {func.__name__} took {execution_time:.2f}ms")
            
        # Store in session state for monitoring
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}
            
        st.session_state.performance_metrics[func.__name__] = {
            'last_execution_ms': execution_time,
            'timestamp': datetime.now()
        }
        
        return result
    return wrapper


def batch_api_calls(api_calls: list[Callable]) -> list[Any]:
    """Execute multiple API calls in parallel"""
    import concurrent.futures
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(call) for call in api_calls]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                st.error(f"API call failed: {e}")
                results.append(None)
                
    return results


def lazy_load_section(key: str, loader_func: Callable, placeholder_text: str = "Loading..."):
    """Lazy load a dashboard section"""
    if f"{key}_loaded" not in st.session_state:
        with st.spinner(placeholder_text):
            data = loader_func()
            st.session_state[f"{key}_data"] = data
            st.session_state[f"{key}_loaded"] = True
    
    return st.session_state.get(f"{key}_data")


def optimize_dataframe_display(df, max_rows: int = 100):
    """Optimize large dataframe display"""
    if len(df) > max_rows:
        st.info(f"Showing first {max_rows} of {len(df)} rows for performance")
        return df.head(max_rows)
    return df


def cache_api_response(cache_key: str, ttl_seconds: int = 300):
    """Decorator for caching API responses with TTL"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key including args
            key_data = f"{cache_key}:{str(args)}:{str(kwargs)}"
            cache_hash = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check session state cache
            cache_entry_key = f"cache_{cache_hash}"
            cache_time_key = f"cache_time_{cache_hash}"
            
            now = datetime.now()
            
            # Check if cached data exists and is still valid
            if (cache_entry_key in st.session_state and 
                cache_time_key in st.session_state):
                
                cache_time = st.session_state[cache_time_key]
                if now - cache_time < timedelta(seconds=ttl_seconds):
                    return st.session_state[cache_entry_key]
            
            # Cache miss - fetch new data
            result = func(*args, **kwargs)
            
            # Store in cache
            st.session_state[cache_entry_key] = result
            st.session_state[cache_time_key] = now
            
            return result
        return wrapper
    return decorator


def debounce(wait_time: float = 0.5):
    """Debounce decorator to prevent rapid repeated calls"""
    def decorator(func: Callable) -> Callable:
        func._last_call_time = 0
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            if current_time - func._last_call_time < wait_time:
                return None
                
            func._last_call_time = current_time
            return func(*args, **kwargs)
        return wrapper
    return decorator


def virtualized_list(items: list, page_size: int = 20, key: str = "list"):
    """Create a virtualized list with pagination"""
    if f"{key}_page" not in st.session_state:
        st.session_state[f"{key}_page"] = 0
        
    total_pages = (len(items) + page_size - 1) // page_size
    current_page = st.session_state[f"{key}_page"]
    
    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀️ Previous", key=f"{key}_prev", disabled=current_page == 0):
            st.session_state[f"{key}_page"] = max(0, current_page - 1)
            st.rerun()
            
    with col2:
        st.markdown(f"<center>Page {current_page + 1} of {total_pages}</center>", 
                   unsafe_allow_html=True)
        
    with col3:
        if st.button("Next ▶️", key=f"{key}_next", disabled=current_page >= total_pages - 1):
            st.session_state[f"{key}_page"] = min(total_pages - 1, current_page + 1)
            st.rerun()
    
    # Display current page items
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, len(items))
    
    return items[start_idx:end_idx]


def optimize_plotly_chart(fig, max_points: int = 1000):
    """Optimize Plotly charts by reducing data points"""
    for trace in fig.data:
        if hasattr(trace, 'x') and hasattr(trace, 'y'):
            if len(trace.x) > max_points:
                # Simple downsampling - take every nth point
                step = len(trace.x) // max_points
                trace.x = trace.x[::step]
                trace.y = trace.y[::step]
    
    # Disable some interactive features for performance
    fig.update_layout(
        hovermode='nearest',
        dragmode=False,
    )
    
    return fig


def create_performance_dashboard():
    """Create a performance monitoring dashboard section"""
    st.markdown("### ⚡ Performance Metrics")
    
    if 'performance_metrics' in st.session_state:
        metrics = st.session_state.performance_metrics
        
        # Sort by execution time
        sorted_metrics = sorted(
            metrics.items(), 
            key=lambda x: x[1]['last_execution_ms'], 
            reverse=True
        )
        
        # Display top slow operations
        st.markdown("#### 🐌 Slowest Operations")
        for func_name, data in sorted_metrics[:5]:
            exec_time = data['last_execution_ms']
            color = "🔴" if exec_time > 1000 else "🟡" if exec_time > 500 else "🟢"
            st.markdown(f"{color} **{func_name}**: {exec_time:.2f}ms")
    
    # Cache statistics
    st.markdown("#### 💾 Cache Statistics")
    cache_hits = sum(1 for key in st.session_state.keys() if key.startswith('cache_'))
    st.metric("Cache Entries", cache_hits)
    
    # Memory usage estimate
    total_size = sum(
        len(str(v)) for v in st.session_state.values()
    ) / 1024 / 1024  # Convert to MB
    
    st.metric("Session Memory", f"{total_size:.2f} MB")
    
    # Clear cache button
    if st.button("🗑️ Clear Cache"):
        keys_to_remove = [key for key in st.session_state.keys() 
                         if key.startswith('cache_')]
        for key in keys_to_remove:
            del st.session_state[key]
        st.success(f"Cleared {len(keys_to_remove)} cache entries")
        st.rerun()


# Performance tips for dashboard developers
PERFORMANCE_TIPS = """
## Dashboard Performance Best Practices

1. **Use Caching Aggressively**
   - Cache API responses with `@st.cache_data`
   - Use session state for temporary data
   - Implement TTL-based caching

2. **Optimize Data Loading**
   - Lazy load sections that aren't immediately visible
   - Paginate large datasets
   - Use virtualization for long lists

3. **Reduce Re-renders**
   - Use `st.empty()` containers for updates
   - Batch state updates
   - Debounce user inputs

4. **Optimize Charts**
   - Downsample data points for large datasets
   - Disable unnecessary chart interactions
   - Use simpler chart types when possible

5. **Monitor Performance**
   - Use the `@performance_monitor` decorator
   - Track slow operations
   - Clear cache periodically
"""