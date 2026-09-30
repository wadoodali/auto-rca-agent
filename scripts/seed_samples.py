from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples"

def create_sample_directories() -> None:
    #Create the directory structure for sample production incidents.
    incident_directories = (
        SAMPLES_DIR / "incident_01",
        SAMPLES_DIR / "incident_02",
    )
    for directory in incident_directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    create_sample_directories()
    print("Sample incident directories created.")