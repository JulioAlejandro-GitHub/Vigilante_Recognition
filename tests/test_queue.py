import time
from datetime import datetime
from src.core.models.domain import RecognitionJob
from src.recognition_queue.queue import RecognitionQueue

def test_recognition_queue_cooldown():
    queue = RecognitionQueue(maxsize=10)

    job1 = RecognitionJob(
        camera_id=1,
        source_type="test",
        source_ref="test",
        frame_data=b"dummy",
        timestamp=datetime.fromtimestamp(100),
        metadata={}
    )

    # First job should be accepted
    assert queue.put(job1, cooldown_seconds=2.0) == True
    assert queue.qsize() == 1

    # Second job with same timestamp + 1s (which is < 2.0s cooldown) should be rejected
    job2 = RecognitionJob(
        camera_id=1,
        source_type="test",
        source_ref="test",
        frame_data=b"dummy",
        timestamp=datetime.fromtimestamp(101),
        metadata={}
    )
    assert queue.put(job2, cooldown_seconds=2.0) == False
    assert queue.qsize() == 1

    # Third job with timestamp + 3s (which is > 2.0s cooldown) should be accepted
    job3 = RecognitionJob(
        camera_id=1,
        source_type="test",
        source_ref="test",
        frame_data=b"dummy",
        timestamp=datetime.fromtimestamp(103),
        metadata={}
    )
    assert queue.put(job3, cooldown_seconds=2.0) == True
    assert queue.qsize() == 2

def test_recognition_queue_maxsize():
    queue = RecognitionQueue(maxsize=1)

    job1 = RecognitionJob(
        camera_id=1,
        source_type="test",
        source_ref="test",
        frame_data=b"dummy",
        timestamp=datetime.fromtimestamp(100),
        metadata={}
    )

    # First job should be accepted
    assert queue.put(job1, cooldown_seconds=0.0) == True

    # Queue is full, second job (even from different camera) should be rejected
    job2 = RecognitionJob(
        camera_id=2,
        source_type="test",
        source_ref="test",
        frame_data=b"dummy",
        timestamp=datetime.fromtimestamp(100),
        metadata={}
    )

    assert queue.put(job2, cooldown_seconds=0.0) == False
