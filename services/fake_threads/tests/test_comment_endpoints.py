# /services/fake_threads/tests/test_comment_endpoints.py
import pytest
from fastapi.testclient import TestClient

from services.fake_threads.main import app

client = TestClient(app)


class TestCommentEndpoints:
    """Test cases for comment-related endpoints in fake_threads service."""

    def test_get_comments_returns_empty_list_for_new_post(self) -> None:
        """
        FAILING TEST: GET /posts/{post_id}/comments should return empty list for new post.
        
        This test will fail because the endpoint doesn't exist yet.
        """
        post_id = "post_123"
        
        response = client.get(f"/posts/{post_id}/comments")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_post_comment_creates_new_comment(self) -> None:
        """
        FAILING TEST: POST /posts/{post_id}/comments should create a new comment.
        
        This test will fail because the endpoint doesn't exist yet.
        """
        post_id = "post_123"
        comment_data = {
            "text": "Great post!",
            "author": "user1"
        }
        
        response = client.post(f"/posts/{post_id}/comments", json=comment_data)
        
        assert response.status_code == 201
        result = response.json()
        assert "id" in result
        assert result["text"] == "Great post!"
        assert result["author"] == "user1"
        assert result["post_id"] == post_id
        assert "timestamp" in result

    def test_get_comments_returns_created_comments(self) -> None:
        """
        FAILING TEST: GET /posts/{post_id}/comments should return previously created comments.
        
        This test will fail because the endpoint doesn't exist yet.
        """
        post_id = "post_456"
        
        # Create a comment first
        comment_data = {
            "text": "Amazing content!",
            "author": "user2"
        }
        client.post(f"/posts/{post_id}/comments", json=comment_data)
        
        # Get comments
        response = client.get(f"/posts/{post_id}/comments")
        
        assert response.status_code == 200
        comments = response.json()
        assert len(comments) == 1
        assert comments[0]["text"] == "Amazing content!"
        assert comments[0]["author"] == "user2"
        assert comments[0]["post_id"] == post_id

    def test_comments_are_isolated_by_post_id(self) -> None:
        """
        FAILING TEST: Comments should be isolated by post_id.
        
        This test will fail because the endpoint doesn't exist yet.
        """
        post_1 = "post_111"
        post_2 = "post_222"
        
        # Create comment for post_1
        client.post(f"/posts/{post_1}/comments", json={"text": "Comment 1", "author": "user1"})
        
        # Create comment for post_2  
        client.post(f"/posts/{post_2}/comments", json={"text": "Comment 2", "author": "user2"})
        
        # Check post_1 comments
        response_1 = client.get(f"/posts/{post_1}/comments")
        assert response_1.status_code == 200
        comments_1 = response_1.json()
        assert len(comments_1) == 1
        assert comments_1[0]["text"] == "Comment 1"
        
        # Check post_2 comments
        response_2 = client.get(f"/posts/{post_2}/comments")
        assert response_2.status_code == 200
        comments_2 = response_2.json()
        assert len(comments_2) == 1
        assert comments_2[0]["text"] == "Comment 2"