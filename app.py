from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import re
import pandas as pd
import docx2txt
from PyPDF2 import PdfReader

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_details_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf = PdfReader(file)
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        phone_numbers = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text)
        return emails, phone_numbers, text


def extract_details_from_docx(file_path):
    text = docx2txt.process(file_path)
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phone_numbers = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text)
    return emails, phone_numbers, text


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            if filename.endswith('.pdf'):
                emails, phone_numbers, text = extract_details_from_pdf(file_path)
            elif filename.endswith('.docx'):
                emails, phone_numbers, text = extract_details_from_docx(file_path)
            else:
                return "Unsupported file format"

            data = {
                'Email': emails,
                'Phone Number': phone_numbers,
                'Text': [text]
            }
            df = pd.DataFrame(data)
            output_file = 'output.xlsx'
            df.to_excel(output_file, index=False)
            return send_file(output_file, as_attachment=True)

    return render_template('templates/upload.html')


if __name__ == '__main__':
    app.run(debug=True)
