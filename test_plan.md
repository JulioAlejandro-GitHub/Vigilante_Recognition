1. Install deepface and insightface dependencies (`pip install deepface insightface mxnet onnxruntime`)
2. Define models in `src/repositories/models.py` for `PersonaModel`, `PersonaEmbeddingModel`, `RecognitionEngineResultModel`
3. Create `src/services/recognition/engine_interface.py` defining the `RecognitionEngine` interface and `EngineResult` dataclass to match expected output format.
4. Implement `src/services/recognition/insightface_service.py` that loads InsightFace, extracts embeddings, and compares with DB using numpy/cosine similarity.
5. Implement `src/services/recognition/deepface_service.py` that acts as fallback for ambiguous results.
6. Modify `src/recognition_orchestrator/orchestrator.py`:
    - Read `persona_embedding` cache to memory or load as needed.
    - Loop through YOLO detections, crop the face (or pass the whole frame with the bbox) to the engines.
    - Run InsightFace. If similarity is in the gray area, run DeepFace.
    - Write engine results to `recognition_engine_result`.
    - Update `recognition_face` with the final assigned persona and similarity.
7. Update `.env.example` and `src/config/settings.py` for thresholds (e.g. `INSIGHTFACE_THRESHOLD`, `DEEPFACE_THRESHOLD`, etc).
8. Verify everything works.
