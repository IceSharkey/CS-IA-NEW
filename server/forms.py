from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import InputRequired, DataRequired


class UploadFileForm(FlaskForm):
    files = FileField(
        "Files", validators=[InputRequired()], render_kw={"multiple": True}
    )
    submit = SubmitField("Upload Files")


class KeywordSearchForm(FlaskForm):
    keyword = StringField("Keyword", validators=[DataRequired()])
    submit = SubmitField("Search")
