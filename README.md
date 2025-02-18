# IceSharkey's CS IA

# Todo

- [x] make transcription feature use Whisper API
- [ ] Integrate Llama 3.2 3b for tagging call recordings (and transcribe?)
- [ ] Report page with filtering and data visualization (via tags + date)
  - [ ] Charts
  - [ ] Tables
- [ ] Manage page for administrators
  - [ ] change roles of other users
  - [x] delete recordings
  - [x] Show full transcription of selected call + info
- [ ] user role-based access control (for 'manage')

# run

This project uses [uv](https://github.com/astral-sh/uv). You will need to set up a `.env` in the root with the following variables:

```
SECRET_KEY=GOCSPX-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_CLIENT_ID=000000000000-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
```

You will also have to change the url in `transcribe.py` to a docker container hosting a open-ai whisper service.

Then run:

```bash
uv run run.py
```
