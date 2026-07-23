import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Run the YOLOv11 SORT bat counting pipeline"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to the YAML configuration file"
    )

    args = parser.parse_args()

    print("Starting bat counter...")
    print(f"Using config: {args.config}")

    command = [
        sys.executable,
        "-m",
        "src.tracking",
        "--config",
        args.config
    ]

    subprocess.run(command, check=True)

    print("Bat counting complete.")


if __name__ == "__main__":
    main()
