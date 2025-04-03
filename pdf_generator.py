import os
import tempfile
import subprocess
import shutil
import uuid

FERPA_FILE = 'uploads/form-templates/ferpa.tex'
FERPA_OUTPUT = 'uploads/forms'
NAME_SSN_FILE = 'uploads/form-templates/name_ssn_change.tex'
NAME_SSN_OUTPUT = 'uploads/forms'

def return_choice(choices, keyword):
    if keyword in choices:
        return "yes"
        
    return "no"

def generate_ferpa(data):

    # Generate unique ID for the PDF
    unique_id = str(uuid.uuid4())

    # Unique file paths
    tex_file_path = os.path.join(FERPA_OUTPUT, f"ferpa_form_{unique_id}.tex")
    pdf_file_path = f"ferpa_form_{unique_id}.pdf"
    
    # Read the LaTeX template and replace placeholders
    with open(FERPA_FILE, "r") as file:
        latex_content = file.read()

    for key, value in data.items():
        latex_content = latex_content.replace(f"{{{{{key}}}}}", value)

    # Save the modified LaTeX file
    with open(tex_file_path, "w") as file:
        file.write(latex_content)

    # Compile
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", FERPA_OUTPUT, tex_file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Return path to PDF
    return pdf_file_path

def generate_ssn_name(data):

    # Generate unique ID for the PDF
    unique_id = str(uuid.uuid4())

    # Unique file paths
    tex_file_path = os.path.join(NAME_SSN_OUTPUT, f"name_form_{unique_id}.tex")
    pdf_file_path = f"name_form_{unique_id}.pdf"

    # Read the LaTeX template and replace placeholders
    with open(NAME_SSN_FILE, "r") as file:
        latex_content = file.read()

    for key, value in data.items():
        latex_content = latex_content.replace(f"{{{{{key}}}}}", value)

    # Save the modified LaTeX file
    with open(tex_file_path, "w") as file:
        file.write(latex_content)

    # Compile
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", NAME_SSN_OUTPUT, tex_file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Return the generated PDF
    return pdf_file_path
