import os
import subprocess

def generate_pot_files(docs_dir: str, output_dir: str):
    """
    Generate .pot files using Sphinx's gettext builder.
    
    :param docs_dir: Directory containing the documentation source files
    :param output_dir: Directory where .pot files will be saved
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Run Sphinx gettext builder
        subprocess.run(
            ["sphinx-build", "-b", "gettext", docs_dir, output_dir],
            check=True
        )
        print(f"Successfully generated .pot files in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating .pot files: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    docs_dir = "/files/ah/docs"  # Adjust this path if necessary
    output_dir = "/files/ah/docs/_build/gettext"
    generate_pot_files(docs_dir, output_dir)
