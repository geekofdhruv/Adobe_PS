MODEL_NAME = 'all-MiniLM-L6-v2' 
BATCH_SIZE = 32  # Optimized for CPU performance

# --- Directory Paths ---
# These paths are relative to the docker container's working directory.
INPUT_DIR = "input"
OUTPUT_DIR = "output"
OUTLINE_DIR = "./output_round1a"

# --- Persona & Job Definition ---
# These values will be used to formulate the master query.
# For a real-world scenario, these would be dynamic inputs.
PERSONA = "Travel Planner"
JOB_TO_BE_DONE = "Plan a trip of 4 days for a group of 10 college friends."

# --- Retrieval Parameters ---
TOP_K_SECTIONS = 5      # How many main sections to retrieve from MMR
TOP_K_SUBSECTIONS = 5  # How many top sections to summarize
MMR_DIVERSITY = 0.5 