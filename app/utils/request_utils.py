import os, tempfile, subprocess, shutil, uuid
from flask import current_app

# Check if file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Return yes/no for LaTeX check
def return_choice(choices, keyword):
    if keyword in choices:
        return "yes"
    return "no"

def return_choice_bool(choice):
    if choice:
        return "Yes"
    return "No"

def generate_ferpa(data):
    # Custom LaTeX file path
    FERPA_FILE = os.path.join(current_app.config['BASE_DIR'], 'uploads', 'form-templates', 'ferpa.tex')

    # Generate unique ID for the PDF
    unique_id = str(uuid.uuid4())

    # Unique file paths
    tex_file_path = os.path.join(current_app.config['FORM_FOLDER'], f"ferpa_form_{unique_id}.tex")
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
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", current_app.config['FORM_FOLDER'], tex_file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Return path to PDF
    return pdf_file_path

def generate_ssn_name(data):
    # Custom LaTeX file path
    NAME_SSN_FILE = os.path.join(current_app.config['BASE_DIR'], 'uploads', 'form-templates', 'name_ssn_change.tex') 

    # Generate unique ID for the PDF
    unique_id = str(uuid.uuid4())

    # Unique file paths
    tex_file_path = os.path.join(current_app.config['FORM_FOLDER'], f"name_form_{unique_id}.tex")
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
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", current_app.config['FORM_FOLDER'], tex_file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Return the generated PDF
    return pdf_file_path

def generate_withdrawal(data):
    # Custom LaTeX file path
    NAME_WITHDRAWAL_FILE = os.path.join(current_app.config['BASE_DIR'], 'uploads', 'form-templates', 'medical_withdrawal.tex')

    # Generate unique ID for the PDF
    unique_id = str(uuid.uuid4())

    # Unique file paths
    tex_file_path = os.path.join(current_app.config['FORM_FOLDER'], f"withdrawal_form_{unique_id}.tex")
    pdf_file_path = f"withdrawal_form_{unique_id}.pdf"

    # Read the LaTeX template and replace placeholders
    with open(NAME_WITHDRAWAL_FILE, "r") as file:
        latex_content = file.read()

    for key, value in data.items():
        latex_content = latex_content.replace(f"{{{{{key}}}}}", value)
    
    # Save the modified LaTeX file
    with open(tex_file_path, "w") as file:
        file.write(latex_content)

    # Compile
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", current_app.config['FORM_FOLDER'], tex_file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Return the generated PDF
    return pdf_file_path


def generate_drop(data):
    # Custom LaTeX file path
    STUDENT_DROP_FILE = os.path.join(current_app.config['BASE_DIR'], 'uploads', 'form-templates', 'student_drop.tex')

    # Generate unique ID for the PDF
    unique_id = str(uuid.uuid4())

    # Unique file paths
    tex_file_path = os.path.join(current_app.config['FORM_FOLDER'], f"drop_form_{unique_id}.tex")
    pdf_file_path = f"drop_form_{unique_id}.pdf"

    # Read the LaTeX template and replace placeholders
    with open(STUDENT_DROP_FILE, "r") as file:
        latex_content = file.read()

    for key, value in data.items():
        latex_content = latex_content.replace(f"{{{{{key}}}}}", value)
    
    # Save the modified LaTeX file
    with open(tex_file_path, "w") as file:
        file.write(latex_content)

    # Compile
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", current_app.config['FORM_FOLDER'], tex_file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Return the generated PDF
    return pdf_file_path