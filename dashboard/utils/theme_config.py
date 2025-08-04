"""
Theme configuration for dashboard charts and components
"""
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


def get_plotly_theme():
    """Get Plotly theme configuration based on Streamlit theme"""
    # Default to dark theme colors
    theme_config = {
        'dark': {
            'bg_color': 'rgba(0,0,0,0)',  # Transparent background
            'paper_color': 'rgba(14, 17, 23, 0.8)',  # Semi-transparent dark
            'text_color': '#FAFAFA',
            'grid_color': 'rgba(255, 255, 255, 0.1)',
            'line_colors': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E'],
            'template': 'plotly_dark'
        },
        'light': {
            'bg_color': 'rgba(255,255,255,0)',  # Transparent background  
            'paper_color': 'rgba(255, 255, 255, 0.8)',
            'text_color': '#262730',
            'grid_color': 'rgba(0, 0, 0, 0.1)',
            'line_colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'template': 'plotly_white'
        }
    }
    
    # Try to detect theme (default to dark for better appearance)
    # Streamlit doesn't expose theme directly, so we default to dark
    current_theme = 'dark'
    
    return theme_config[current_theme]


def apply_plotly_theme(fig):
    """Apply theme to a Plotly figure"""
    theme = get_plotly_theme()
    
    fig.update_layout(
        template=theme['template'],
        plot_bgcolor=theme['bg_color'],
        paper_bgcolor=theme['bg_color'],
        font_color=theme['text_color'],
        xaxis=dict(
            gridcolor=theme['grid_color'],
            zerolinecolor=theme['grid_color'],
        ),
        yaxis=dict(
            gridcolor=theme['grid_color'],
            zerolinecolor=theme['grid_color'],
        ),
        colorway=theme['line_colors']
    )
    
    return fig


def create_dark_theme_chart(chart_type, *args, **kwargs):
    """Create a chart with dark theme applied"""
    if chart_type == 'line':
        fig = px.line(*args, **kwargs)
    elif chart_type == 'bar':
        fig = px.bar(*args, **kwargs)
    elif chart_type == 'scatter':
        fig = px.scatter(*args, **kwargs)
    elif chart_type == 'area':
        fig = px.area(*args, **kwargs)
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")
    
    return apply_plotly_theme(fig)


def style_metric_delta(delta_color):
    """Style metric delta for dark theme visibility"""
    if delta_color == "normal":
        return "color: #4CAF50;"  # Green
    elif delta_color == "inverse":
        return "color: #F44336;"  # Red  
    else:
        return "color: #9E9E9E;"  # Gray


def get_gauge_colors():
    """Get gauge chart colors for dark theme"""
    theme = get_plotly_theme()
    
    return {
        'bar_color': '#2E86AB',
        'bgcolor': theme['bg_color'],
        'bordercolor': theme['text_color'],
        'steps': [
            {'range': [0, 50], 'color': "rgba(255, 255, 255, 0.1)"},
            {'range': [50, 80], 'color': "rgba(255, 235, 59, 0.3)"},
            {'range': [80, 100], 'color': "rgba(244, 67, 54, 0.3)"}
        ],
        'threshold': {
            'line': {'color': "#F44336", 'width': 4},
            'thickness': 0.75,
            'value': 90
        }
    }


def create_styled_gauge(value, title, max_value=100):
    """Create a styled gauge chart for dark theme"""
    colors = get_gauge_colors()
    theme = get_plotly_theme()
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'color': theme['text_color']}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': colors['bar_color']},
            'bgcolor': colors['bgcolor'],
            'borderwidth': 2,
            'bordercolor': colors['bordercolor'],
            'steps': colors['steps'],
            'threshold': colors['threshold']
        }
    ))
    
    fig.update_layout(
        paper_bgcolor=theme['bg_color'],
        plot_bgcolor=theme['bg_color'],
        font={'color': theme['text_color']},
        height=300
    )
    
    return fig


# CSS for dark theme compatibility
DARK_THEME_CSS = """
<style>
    /* Fix Plotly toolbar visibility in dark mode */
    .modebar {
        background-color: rgba(0, 0, 0, 0.5) !important;
    }
    
    .modebar-btn {
        color: #FAFAFA !important;
    }
    
    /* Fix metric containers */
    [data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    /* Fix dataframe styling */
    .dataframe {
        color: #FAFAFA !important;
    }
    
    /* Improve visibility of various elements */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #FAFAFA;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background-color: #2E86AB;
    }
</style>
"""


def inject_dark_theme_css():
    """Inject CSS for better dark theme support"""
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)