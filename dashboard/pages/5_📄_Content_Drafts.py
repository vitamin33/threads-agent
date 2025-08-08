"""
Content Drafts Management - View, edit, and manage generated content
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Content Drafts - Threads Agent", page_icon="📄", layout="wide"
)

st.title("📄 Content Drafts Management")
st.markdown("View, edit, and publish your AI-generated content across platforms")

# Import API client
from services.api_client import get_api_client

api_client = get_api_client()

# Get content posts and stats
content_posts = api_client.get_content_posts(limit=50)
content_stats = api_client.get_content_stats()

# Stats Overview
st.markdown("### 📊 Content Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "📝 Total Drafts",
        content_stats.get("draft_count", 0),
        f"+{content_stats.get('posts_today', 0)} today",
    )

with col2:
    st.metric("✅ Ready to Publish", content_stats.get("ready_count", 0))

with col3:
    st.metric("⏰ Scheduled", content_stats.get("scheduled_count", 0))

with col4:
    st.metric("🚀 Published", content_stats.get("published_count", 0))

with col5:
    avg_quality = content_stats.get("avg_quality_score", 0)
    quality_delta = "Good" if avg_quality > 0.7 else "Needs work"
    st.metric("🎯 Avg Quality", f"{avg_quality:.1f}", quality_delta)

st.divider()

# Content Management Section
if content_posts:
    st.markdown("### 📋 Content Drafts")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Draft", "Ready", "Scheduled", "Published"],
            index=0,
        )

    with col2:
        sort_option = st.selectbox(
            "Sort by", ["Newest First", "Oldest First", "Quality Score"], index=0
        )

    with col3:
        show_count = st.slider("Show items", 5, 50, 20)

    # Display content cards
    for i, post in enumerate(content_posts[:show_count]):
        if i >= show_count:
            break

        with st.expander(
            f"📝 {post.get('hook', 'Untitled')[:80]}... | "
            f"Quality: {post.get('quality_score', 0):.1f} | "
            f"Created: {post.get('created_at', 'Unknown')[:10]}",
            expanded=False,
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### 🎣 Hook")
                hook_text = st.text_area(
                    "Hook",
                    value=post.get("hook", ""),
                    height=100,
                    key=f"hook_{post['id']}",
                )

                st.markdown("#### 📝 Body")
                body_text = st.text_area(
                    "Body",
                    value=post.get("body", ""),
                    height=200,
                    key=f"body_{post['id']}",
                )

                # Update button
                if st.button("💾 Save Changes", key=f"save_{post['id']}"):
                    updates = {"hook": hook_text, "body": body_text}
                    result = api_client.update_content_post(post["id"], updates)
                    if result.get("success", True):
                        st.success("✅ Content updated successfully!")
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Update failed: {result.get('error', 'Unknown error')}"
                        )

            with col2:
                st.markdown("#### 📊 Details")
                st.info(f"""
                **ID**: {post["id"]}
                **Persona**: {post.get("persona_id", "Unknown")}
                **Status**: {post.get("status", "draft").title()}
                **Quality Score**: {post.get("quality_score", 0):.1f}
                **Tokens Used**: {post.get("tokens_used", 0)}
                **Created**: {post.get("created_at", "Unknown")[:16]}
                """)

                st.markdown("#### 🌐 Platform Adaptation")

                # Platform selection for adaptation
                platforms = st.multiselect(
                    "Select platforms to adapt for:",
                    ["dev.to", "linkedin", "threads", "medium"],
                    default=["dev.to", "linkedin"],
                    key=f"platforms_{post['id']}",
                )

                if st.button("🔄 Adapt Content", key=f"adapt_{post['id']}"):
                    if platforms:
                        adapted_content = api_client.adapt_content_for_platforms(
                            post["id"], platforms
                        )

                        if adapted_content:
                            st.success(
                                f"✅ Content adapted for {len(adapted_content)} platforms!"
                            )

                            # Show adapted content
                            for adapted in adapted_content:
                                platform = adapted["platform"]
                                with st.expander(f"📱 {platform.title()} Version"):
                                    st.markdown(f"**Title**: {adapted['title']}")
                                    st.markdown("**Content**:")
                                    st.text_area(
                                        "Adapted content",
                                        value=adapted["content"],
                                        height=150,
                                        key=f"adapted_{post['id']}_{platform}",
                                    )
                                    st.markdown(
                                        f"**Hashtags**: {' '.join(adapted['hashtags'])}"
                                    )
                                    st.markdown(f"**CTA**: {adapted['call_to_action']}")
                                    st.metric(
                                        "Expected Engagement",
                                        f"{adapted['estimated_engagement']:.1f}%",
                                    )
                        else:
                            st.error("❌ Failed to adapt content")
                    else:
                        st.warning("⚠️ Please select at least one platform")

                st.markdown("#### 🚀 Actions")

                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    if st.button("✅ Mark Ready", key=f"ready_{post['id']}"):
                        result = api_client.update_content_post(
                            post["id"], {"status": "ready"}
                        )
                        if result.get("success", True):
                            st.success("✅ Marked as ready!")
                            st.rerun()

                with action_col2:
                    if st.button("⏰ Schedule", key=f"schedule_{post['id']}"):
                        st.info("📅 Scheduling feature coming soon!")

                # Danger zone
                with st.expander("⚠️ Danger Zone"):
                    if st.button(
                        "🗑️ Delete", key=f"delete_{post['id']}", type="secondary"
                    ):
                        st.error("🚫 Delete functionality not yet implemented")

else:
    st.info("📝 No content drafts found. Generate some content to get started!")

    if st.button("🤖 Generate Content"):
        st.info("Redirecting to Content Pipeline...")

# Bulk Actions
if content_posts:
    st.divider()
    st.markdown("### 🔄 Bulk Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ Mark All as Ready"):
            st.info("Bulk ready action coming soon!")

    with col2:
        if st.button("📱 Bulk Platform Adapt"):
            st.info("Bulk adaptation coming soon!")

    with col3:
        if st.button("📅 Bulk Schedule"):
            st.info("Bulk scheduling coming soon!")

    with col4:
        if st.button("📊 Export All"):
            # Create downloadable export
            df = pd.DataFrame(content_posts)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"content_drafts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

# Analytics Section
st.divider()
st.markdown("### 📈 Content Analytics")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📊 Quality Distribution")
    if content_posts:
        quality_scores = [
            post.get("quality_score", 0)
            for post in content_posts
            if post.get("quality_score")
        ]
        if quality_scores:
            quality_ranges = {
                "Excellent (0.8-1.0)": len([q for q in quality_scores if q >= 0.8]),
                "Good (0.6-0.8)": len([q for q in quality_scores if 0.6 <= q < 0.8]),
                "Fair (0.4-0.6)": len([q for q in quality_scores if 0.4 <= q < 0.6]),
                "Needs Work (0.0-0.4)": len([q for q in quality_scores if q < 0.4]),
            }

            for range_name, count in quality_ranges.items():
                if count > 0:
                    percentage = (count / len(quality_scores)) * 100
                    st.metric(range_name, f"{count} posts", f"{percentage:.1f}%")
        else:
            st.info("No quality scores available yet")
    else:
        st.info("No content available for analysis")

with col2:
    st.markdown("#### 🗓️ Creation Timeline")
    if content_posts:
        # Group by creation date
        creation_dates = {}
        for post in content_posts:
            date_str = post.get("created_at", "")[:10]  # Get date part
            if date_str:
                creation_dates[date_str] = creation_dates.get(date_str, 0) + 1

        if creation_dates:
            sorted_dates = sorted(creation_dates.items())
            for date, count in sorted_dates[-7:]:  # Show last 7 days
                st.metric(f"📅 {date}", f"{count} posts")
        else:
            st.info("No creation timeline data available")
    else:
        st.info("No content available for timeline analysis")

# Tips Section
st.divider()
st.markdown("### 💡 Content Management Tips")

with st.expander("📝 Writing Tips"):
    st.markdown("""
    - **Hook Quality**: Aim for hooks that create curiosity or promise value
    - **Platform Adaptation**: Each platform has different audience expectations
    - **Quality Scores**: Aim for 0.7+ for best engagement
    - **Timing**: Schedule posts for optimal platform-specific times
    """)

with st.expander("🚀 Publishing Strategy"):
    st.markdown("""
    - **Dev.to**: Technical tutorials and deep dives perform best
    - **LinkedIn**: Professional insights and career content  
    - **Threads**: Conversational, shorter-form content
    - **Medium**: Long-form thought leadership articles
    """)
