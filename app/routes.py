from flask import Blueprint, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
import speech_recognition as sr
from pydub import AudioSegment
import pytesseract
from PIL import Image
from transformers import pipeline
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

main = Blueprint('main', __name__)
summarizer = pipeline("summarization")

def summarize_text(text):
    summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']

def generate_pdf(text, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    lines = text.split('\n')
    y = height - 40
    for line in lines:
        c.drawString(30, y, line)
        y -= 20
    c.save()

def audio_to_text(file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(file_path)
    audio.export("temp.wav", format="wav")
    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
    os.remove("temp.wav")
    return text

def image_to_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload', methods=['POST'])
def upload():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(file_path)
            # Process the file (convert audio to text, image to text, summarize)
            return redirect(url_for('main.index'))

    if 'audio' in request.files and 'image' in request.files:
        audio_file = request.files['audio']
        image_file = request.files['image']

        if audio_file.filename == '' or image_file.filename == '':
            return redirect(request.url)

        if audio_file and image_file:
            audio_filename = secure_filename(audio_file.filename)
            image_filename = secure_filename(image_file.filename)

            audio_path = os.path.join('uploads', audio_filename)
            image_path = os.path.join('uploads', image_filename)

            audio_file.save(audio_path)
            image_file.save(image_path)

            audio_text = audio_to_text(audio_path)
            image_text = image_to_text(image_path)

            combined_text = audio_text + "\n" + image_text
            summary = summarize_text(combined_text)

            pdf_path = os.path.join('uploads', 'summary.pdf')
            generate_pdf(summary, pdf_path)

            return redirect(url_for('main.index'))

    return redirect(request.url)
