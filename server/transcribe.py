from flask import Blueprint, render_template, flash, request, current_app
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from .forms import UploadFileForm
from .models import db, Transcription, TranscriptionSegment
import requests

transcribe = Blueprint("transcribe", __name__)

ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "flac", "webm"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"


def transcribe_with_whisper(audio_file_path):
    whisper_url = "http://192.168.2.114:9000/asr?encode=true&task=transcribe&word_timestamps=true&output=json"

    with open(audio_file_path, "rb") as audio_file:
        files = {"audio_file": audio_file}
        response = requests.post(whisper_url, files=files)

    if response.status_code == 200:
        result = response.json()
        formatted_segments = []
        for segment in result.get("segments", []):
            start_time = format_time(segment["start"])
            end_time = format_time(segment["end"])
            formatted_segments.append(
                {"timestamp": f"{start_time} - {end_time}", "text": segment["text"]}
            )
        return formatted_segments
    else:
        return None


@transcribe.route("/home/transcribe", methods=["GET", "POST"])
@login_required
def transcribe_audio():
    form = UploadFileForm()
    transcriptions = []
    success_count = 0

    if form.validate_on_submit():
        files = request.files.getlist("files")
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, "static", "files")
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                transcription = transcribe_with_whisper(file_path)

                if transcription:
                    # Store in database
                    new_transcription = Transcription(
                        filename=filename, file_path=file_path, user_id=current_user.id
                    )
                    db.session.add(new_transcription)
                    db.session.flush()

                    for segment in transcription:
                        start_time, end_time = segment["timestamp"].split(" - ")
                        new_segment = TranscriptionSegment(
                            start_time=start_time,
                            end_time=end_time,
                            text=segment["text"],
                            transcription_id=new_transcription.id,
                        )
                        db.session.add(new_segment)

                    transcriptions.append(
                        {"filename": filename, "segments": transcription}
                    )
                    success_count += 1
                else:
                    flash(f"Transcription failed for {filename}", "error")
            else:
                flash(
                    f'Invalid file type for {file.filename}. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}',
                    "error",
                )

        if success_count > 0:
            db.session.commit()
            flash(
                f'Successfully uploaded and transcribed {success_count} file{"s" if success_count > 1 else ""}.',
                "success",
            )

    return render_template("transcribe.html", form=form, transcriptions=transcriptions)
