"""Concurrent processing tests for emotion trajectory mapping system."""

import pytest
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper


class TestEmotionConcurrency:
    """Test concurrent processing capabilities for emotion analysis."""

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    @pytest.fixture
    def trajectory_mapper(self):
        """Create trajectory mapper instance."""
        return TrajectoryMapper()

    @pytest.fixture
    def test_content_pool(self):
        """Pool of test content for concurrent processing."""
        return [
            {
                "id": f"content_{i}",
                "segments": [
                    f"Content piece {i} begins with neutral tone.",
                    f"Building excitement in content {i} now!",
                    f"Peak emotional moment for content {i}!",
                    f"Resolution and conclusion for content {i}.",
                ],
            }
            for i in range(200)  # Large pool for testing
        ]

    def test_concurrent_emotion_analysis_100_threads(
        self, emotion_analyzer, test_content_pool
    ):
        """Test 100+ concurrent emotion analyses with threading."""
        content_batch = test_content_pool[:100]
        results = []
        errors = []

        def analyze_single_content(content_item):
            """Analyze single content item."""
            try:
                start_time = time.time()
                text = " ".join(content_item["segments"])
                result = emotion_analyzer.analyze_emotions(text)

                processing_time = (time.time() - start_time) * 1000

                return {
                    "content_id": content_item["id"],
                    "result": result,
                    "processing_time_ms": processing_time,
                }
            except Exception as e:
                errors.append({"content_id": content_item["id"], "error": str(e)})
                return None

        # Execute with ThreadPoolExecutor
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=100) as executor:
            future_to_content = {
                executor.submit(analyze_single_content, content): content
                for content in content_batch
            }

            for future in as_completed(future_to_content):
                result = future.result()
                if result:
                    results.append(result)

        total_time = (time.time() - start_time) * 1000

        # Assertions
        assert len(errors) == 0, (
            f"Concurrent processing errors: {errors[:5]}"
        )  # Show first 5 errors
        assert len(results) == 100, f"Expected 100 results, got {len(results)}"

        # Performance requirements
        assert total_time < 30000, (
            f"100 concurrent analyses took {total_time:.2f}ms (>30s)"
        )

        # Individual processing times should be reasonable
        processing_times = [r["processing_time_ms"] for r in results]
        avg_processing_time = statistics.mean(processing_times)
        max_processing_time = max(processing_times)

        assert avg_processing_time < 500, (
            f"Average processing time {avg_processing_time:.2f}ms too high"
        )
        assert max_processing_time < 2000, (
            f"Max processing time {max_processing_time:.2f}ms too high"
        )

        # Verify result quality
        for result in results:
            assert "emotions" in result["result"]
            assert "confidence" in result["result"]
            assert len(result["result"]["emotions"]) == 8

    def test_concurrent_trajectory_mapping_50_threads(
        self, trajectory_mapper, test_content_pool
    ):
        """Test concurrent trajectory mapping with 50 threads."""
        content_batch = test_content_pool[:50]
        results = []
        errors = []

        def map_trajectory(content_item):
            """Map trajectory for single content item."""
            try:
                start_time = time.time()
                result = trajectory_mapper.map_emotion_trajectory(
                    content_item["segments"]
                )
                processing_time = (time.time() - start_time) * 1000

                return {
                    "content_id": content_item["id"],
                    "result": result,
                    "processing_time_ms": processing_time,
                }
            except Exception as e:
                errors.append({"content_id": content_item["id"], "error": str(e)})
                return None

        # Execute concurrently
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(map_trajectory, content) for content in content_batch
            ]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        total_time = (time.time() - start_time) * 1000

        # Assertions
        assert len(errors) == 0, f"Trajectory mapping errors: {errors}"
        assert len(results) == 50
        assert total_time < 25000, (
            f"50 concurrent trajectory mappings took {total_time:.2f}ms"
        )

        # Verify all trajectory results
        for result in results:
            trajectory = result["result"]
            assert trajectory["arc_type"] in [
                "rising",
                "falling",
                "roller_coaster",
                "steady",
            ]
            assert len(trajectory["emotion_progression"]) == 4  # 4 segments per content
            assert "emotional_variance" in trajectory

    @pytest.mark.asyncio
    async def test_async_concurrent_processing(
        self, emotion_analyzer, test_content_pool
    ):
        """Test async concurrent processing with asyncio."""
        content_batch = test_content_pool[:75]

        async def async_analyze(content_item):
            """Async wrapper for emotion analysis."""
            loop = asyncio.get_event_loop()
            text = " ".join(content_item["segments"])

            start_time = time.time()
            result = await loop.run_in_executor(
                None, emotion_analyzer.analyze_emotions, text
            )
            processing_time = (time.time() - start_time) * 1000

            return {
                "content_id": content_item["id"],
                "result": result,
                "processing_time_ms": processing_time,
            }

        # Execute async batch
        start_time = time.time()

        tasks = [async_analyze(content) for content in content_batch]
        results = await asyncio.gather(*tasks)

        total_time = (time.time() - start_time) * 1000

        # Assertions
        assert len(results) == 75
        assert total_time < 20000, f"75 async analyses took {total_time:.2f}ms"

        # Verify async results
        for result in results:
            assert "emotions" in result["result"]
            assert result["processing_time_ms"] < 1000  # Individual timeout

    def test_mixed_workload_concurrency(
        self, emotion_analyzer, trajectory_mapper, test_content_pool
    ):
        """Test mixed workload of emotion analysis and trajectory mapping."""
        content_batch = test_content_pool[:60]

        results = []
        errors = []

        def mixed_analysis(content_item, analysis_type):
            """Perform either emotion analysis or trajectory mapping."""
            try:
                start_time = time.time()

                if analysis_type == "emotion":
                    text = " ".join(content_item["segments"])
                    result = emotion_analyzer.analyze_emotions(text)
                    result_type = "emotion_analysis"
                else:
                    result = trajectory_mapper.map_emotion_trajectory(
                        content_item["segments"]
                    )
                    result_type = "trajectory_mapping"

                processing_time = (time.time() - start_time) * 1000

                return {
                    "content_id": content_item["id"],
                    "result_type": result_type,
                    "result": result,
                    "processing_time_ms": processing_time,
                }
            except Exception as e:
                errors.append({"content_id": content_item["id"], "error": str(e)})
                return None

        # Create mixed workload
        tasks = []
        with ThreadPoolExecutor(max_workers=60) as executor:
            for i, content in enumerate(content_batch):
                analysis_type = "emotion" if i % 2 == 0 else "trajectory"
                task = executor.submit(mixed_analysis, content, analysis_type)
                tasks.append(task)

            start_time = time.time()
            for future in as_completed(tasks):
                result = future.result()
                if result:
                    results.append(result)
            total_time = (time.time() - start_time) * 1000

        # Assertions
        assert len(errors) == 0, f"Mixed workload errors: {errors}"
        assert len(results) == 60
        assert total_time < 30000, f"Mixed workload took {total_time:.2f}ms"

        # Verify result distribution
        emotion_results = [r for r in results if r["result_type"] == "emotion_analysis"]
        trajectory_results = [
            r for r in results if r["result_type"] == "trajectory_mapping"
        ]

        assert len(emotion_results) == 30  # Half the batch
        assert len(trajectory_results) == 30  # Half the batch

    def test_resource_contention_handling(self, emotion_analyzer, test_content_pool):
        """Test handling of resource contention under high load."""
        import psutil
        import os

        # Monitor system resources
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        process.cpu_percent()

        content_batch = test_content_pool[:120]
        results = []

        def resource_intensive_analysis(content_item):
            """Analysis that simulates resource usage."""
            text = " ".join(content_item["segments"])

            # Multiple analyses to increase resource usage
            analysis_results = []
            for _ in range(3):
                result = emotion_analyzer.analyze_emotions(text)
                analysis_results.append(result)

            return {"content_id": content_item["id"], "results": analysis_results}

        # Execute with high contention
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=120) as executor:  # High worker count
            futures = [
                executor.submit(resource_intensive_analysis, content)
                for content in content_batch
            ]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        total_time = (time.time() - start_time) * 1000

        # Check resource usage
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Assertions
        assert len(results) == 120
        assert total_time < 60000, f"Resource contention test took {total_time:.2f}ms"
        assert memory_growth < 200, f"Excessive memory growth: {memory_growth:.2f}MB"

        # Verify all results are valid
        for result in results:
            assert len(result["results"]) == 3  # 3 analyses per content

    def test_error_isolation_in_concurrent_processing(
        self, emotion_analyzer, test_content_pool
    ):
        """Test that errors in one thread don't affect others."""
        content_batch = test_content_pool[:50]

        # Add some problematic content
        problematic_content = [
            {"id": "error_1", "segments": [""] * 4},  # Empty segments
            {"id": "error_2", "segments": ["🎉" * 10000] * 4},  # Emoji overload
            {"id": "error_3", "segments": [None] * 4},  # None values
        ]

        mixed_batch = content_batch[:47] + problematic_content

        results = []
        errors = []

        def robust_analysis(content_item):
            """Analysis with error handling."""
            try:
                if any(seg is None for seg in content_item["segments"]):
                    raise ValueError("None segment found")

                text = " ".join(str(seg) for seg in content_item["segments"])
                result = emotion_analyzer.analyze_emotions(text)

                return {
                    "content_id": content_item["id"],
                    "result": result,
                    "status": "success",
                }
            except Exception as e:
                errors.append({"content_id": content_item["id"], "error": str(e)})
                return {
                    "content_id": content_item["id"],
                    "result": None,
                    "status": "error",
                }

        # Execute with error-prone content
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(robust_analysis, content) for content in mixed_batch
            ]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # Separate successful and failed results
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]

        # Assertions
        # With improved error handling, empty strings and emojis are now handled successfully
        assert len(successful) >= 47, (
            f"Expected at least 47 successful analyses, got {len(successful)}"
        )
        assert len(failed) <= 3, (
            f"Expected at most 3 failed analyses, got {len(failed)}"
        )
        assert len(errors) == 3, "Should have 3 recorded errors"

        # Verify successful analyses are unaffected
        for result in successful:
            assert "emotions" in result["result"]
            assert result["result"]["confidence"] > 0

    def test_scalability_stress_test(self, trajectory_mapper, test_content_pool):
        """Test system scalability under increasing load."""
        # Test with increasing batch sizes
        batch_sizes = [10, 25, 50, 75, 100]
        results_by_batch = {}

        for batch_size in batch_sizes:
            content_batch = test_content_pool[:batch_size]

            def trajectory_analysis(content_item):
                start_time = time.time()
                trajectory_mapper.map_emotion_trajectory(content_item["segments"])
                processing_time = (time.time() - start_time) * 1000
                return processing_time

            # Execute batch
            batch_start = time.time()

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                processing_times = list(
                    executor.map(trajectory_analysis, content_batch)
                )

            batch_total_time = (time.time() - batch_start) * 1000

            results_by_batch[batch_size] = {
                "total_time_ms": batch_total_time,
                "avg_processing_time_ms": statistics.mean(processing_times),
                "max_processing_time_ms": max(processing_times),
                "throughput_per_second": batch_size / (batch_total_time / 1000),
            }

        # Analyze scalability
        for batch_size, metrics in results_by_batch.items():
            print(
                f"Batch {batch_size}: {metrics['throughput_per_second']:.2f} analyses/sec"
            )

            # Performance should not degrade drastically with size
            assert metrics["avg_processing_time_ms"] < 1000, (
                f"Batch {batch_size} avg time too high"
            )
            assert metrics["max_processing_time_ms"] < 3000, (
                f"Batch {batch_size} max time too high"
            )

        # Throughput should scale reasonably
        small_throughput = results_by_batch[10]["throughput_per_second"]
        large_throughput = results_by_batch[100]["throughput_per_second"]

        # Large batch should have higher absolute throughput (even if lower per-item efficiency)
        assert large_throughput > small_throughput * 2, (
            "Throughput should scale with batch size"
        )

    def test_memory_stability_under_load(self, emotion_analyzer, test_content_pool):
        """Test memory stability during sustained concurrent load."""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_samples = []

        # Sample memory usage over multiple batches
        for batch_num in range(5):  # 5 batches of concurrent processing
            initial_memory = process.memory_info().rss / 1024 / 1024

            content_batch = test_content_pool[
                batch_num * 20 : (batch_num + 1) * 20
            ]  # 20 items per batch

            def memory_test_analysis(content_item):
                text = " ".join(content_item["segments"])
                return emotion_analyzer.analyze_emotions(text)

            # Process batch concurrently
            with ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(memory_test_analysis, content_batch))

            gc.collect()  # Force garbage collection
            final_memory = process.memory_info().rss / 1024 / 1024

            memory_samples.append(
                {
                    "batch": batch_num,
                    "initial_mb": initial_memory,
                    "final_mb": final_memory,
                    "growth_mb": final_memory - initial_memory,
                }
            )

            # Verify batch completed successfully
            assert len(results) == 20
            assert all("emotions" in r for r in results)

        # Check memory stability
        total_growth = memory_samples[-1]["final_mb"] - memory_samples[0]["initial_mb"]
        max_batch_growth = max(sample["growth_mb"] for sample in memory_samples)

        assert total_growth < 100, f"Total memory growth {total_growth:.2f}MB too high"
        assert max_batch_growth < 30, (
            f"Single batch growth {max_batch_growth:.2f}MB too high"
        )

    def test_thread_safety_verification(self, emotion_analyzer):
        """Comprehensive thread safety verification."""
        shared_data = {"counter": 0, "results": []}
        lock = threading.Lock()

        def thread_safe_analysis(thread_id):
            """Thread-safe analysis with shared data access."""
            for i in range(10):
                text = f"Thread {thread_id} analysis {i} with emotional content!"
                result = emotion_analyzer.analyze_emotions(text)

                # Thread-safe update of shared data
                with lock:
                    shared_data["counter"] += 1
                    shared_data["results"].append(
                        {
                            "thread_id": thread_id,
                            "analysis_id": i,
                            "dominant_emotion": max(
                                result["emotions"], key=result["emotions"].get
                            ),
                        }
                    )

        # Start multiple threads
        threads = []
        for thread_id in range(20):
            thread = threading.Thread(target=thread_safe_analysis, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30.0)  # 30 second timeout

        # Verify thread safety
        assert shared_data["counter"] == 200  # 20 threads × 10 analyses
        assert len(shared_data["results"]) == 200

        # Verify no data corruption
        thread_ids = set(r["thread_id"] for r in shared_data["results"])
        assert len(thread_ids) == 20  # All threads contributed

        # Each thread should have exactly 10 results
        for thread_id in range(20):
            thread_results = [
                r for r in shared_data["results"] if r["thread_id"] == thread_id
            ]
            assert len(thread_results) == 10, (
                f"Thread {thread_id} has {len(thread_results)} results"
            )

    def test_deadlock_prevention(self, emotion_analyzer, trajectory_mapper):
        """Test prevention of deadlocks in concurrent scenarios."""
        import time

        # Simulate complex interdependent operations
        def complex_operation(operation_id):
            """Operation that uses both emotion analyzer and trajectory mapper."""
            try:
                # Phase 1: Emotion analysis
                text = f"Complex operation {operation_id} with emotional content!"
                emotion_result = emotion_analyzer.analyze_emotions(text)

                # Small delay to encourage potential deadlock conditions
                time.sleep(0.001)

                # Phase 2: Trajectory mapping using emotion result
                segments = [
                    f"Segment 1 for operation {operation_id}",
                    f"Segment 2 with {max(emotion_result['emotions'], key=emotion_result['emotions'].get)} emotion",
                    f"Final segment for operation {operation_id}",
                ]

                trajectory_result = trajectory_mapper.map_emotion_trajectory(segments)

                return {
                    "operation_id": operation_id,
                    "emotion_result": emotion_result,
                    "trajectory_result": trajectory_result,
                    "success": True,
                }

            except Exception as e:
                return {"operation_id": operation_id, "error": str(e), "success": False}

        # Execute many complex operations concurrently
        results = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(complex_operation, i) for i in range(100)]

            # Use timeout to detect potential deadlocks
            for future in as_completed(futures, timeout=60):  # 60 second timeout
                result = future.result()
                results.append(result)

        execution_time = time.time() - start_time

        # Verify no deadlocks occurred
        assert len(results) == 100, "All operations should complete"
        assert execution_time < 45, (
            f"Operations took {execution_time:.2f}s, possible deadlock"
        )

        # Verify all operations succeeded
        successful_operations = [r for r in results if r["success"]]
        failed_operations = [r for r in results if not r["success"]]

        assert len(successful_operations) == 100, (
            f"Expected 100 successful operations, got {len(successful_operations)}"
        )
        assert len(failed_operations) == 0, f"Unexpected failures: {failed_operations}"
