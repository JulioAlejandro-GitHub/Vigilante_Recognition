import pytest
import time
from datetime import datetime
from src.recognition_queue.queue import RecognitionQueue
from src.core.models.domain import RecognitionJob

def test_queue_put_and_get():
    queue = RecognitionQueue(maxsize=10)
    job = RecognitionJob(
        camera_id=1,
        source_type="test",
        source_ref="test",
        timestamp=datetime.utcnow()
    )

    # Should put successfully
    assert queue.put(job, cooldown_seconds=0) is True
    assert queue.qsize() == 1

    # Should retrieve the exact job
    retrieved_job = queue.get()
    assert retrieved_job == job
    assert queue.qsize() == 0

def test_queue_cooldown_mechanism():
    queue = RecognitionQueue(maxsize=10)
    job1 = RecognitionJob(
        camera_id=2,
        source_type="test",
        source_ref="test",
        timestamp=datetime.utcnow()
    )

    # First job should go through
    assert queue.put(job1, cooldown_seconds=1.0) is True

    # Second job with same timestamp and camera_id should be ignored
    assert queue.put(job1, cooldown_seconds=1.0) is False
    assert queue.qsize() == 1

def test_queue_full():
    queue = RecognitionQueue(maxsize=1)
    job1 = RecognitionJob(
        camera_id=3,
        source_type="test",
        source_ref="test",
        timestamp=datetime.utcnow()
    )
    job2 = RecognitionJob(
        camera_id=4,
        source_type="test",
        source_ref="test",
        timestamp=datetime.utcnow()
    )

    assert queue.put(job1, cooldown_seconds=0) is True
    assert queue.put(job2, cooldown_seconds=0) is False # Cola llena
    assert queue.qsize() == 1

def test_queue_get_timeout():
    queue = RecognitionQueue(maxsize=10)
    # Should return None after timeout
    start_time = time.time()
    job = queue.get(timeout=0.5)
    end_time = time.time()

    assert job is None
    assert end_time - start_time >= 0.5
