Title: [good first issue] Optional Gemini/Vertex adapter (never in the core path)
Body: An opt-in adapter that feeds chunkcite chunks to a Gemini model
and runs verify_claims() on its answers. Must stay out of the offline
core, must not require a key to run tests, and must use synthetic data.
