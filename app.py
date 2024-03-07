from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import os.path
import json
from datetime import datetime
app = Flask(__name__)
# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']
def get_google_calendar_service(username):
    creds = None
    token_file_path = f'{username}_token.json'
    if os.path.exists(token_file_path):
        try:
            with open(token_file_path, 'r') as json_file:
                creds_data = json.load(json_file)
                creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        except json.decoder.JSONDecodeError as e:
            print(f"Error loading JSON from {token_file_path}: {e}")
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                './newoauth/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file_path, 'wb') as token:
            token.write(creds.to_json().encode('utf-8'))
    service = build('calendar', 'v3', credentials=creds)
    return service
@app.route('/create_event', methods=['POST'])
def create_event():
    try:
        data = request.json
        if 'email' not in data or 'username' not in data:
            return jsonify({'error': 'Email and username are required fields.'}), 400
        email = data['email']
        username = data['username']
        service = get_google_calendar_service(username)
        event = {
            'summary': data.get('summary', 'Calendar App Meeting'),
            'location': data.get('location', 'Somewhere in Brazil'),
            'description': data.get('description', 'A meeting to discuss Calendar App Automation projects.'),
            'colorId': data.get('colorId', 3),
            'start': {
                'dateTime': data.get('startDateTime', '2024-03-01T12:00:00+05:00'),
                'timeZone': data.get('startTimeZone', 'Asia/Karachi'),
            },
            'end': {
                'dateTime': data.get('endDateTime', '2024-03-01T15:00:00+05:00'),
                'timeZone': data.get('endTimeZone', 'Asia/Karachi'),
            },
        }
        created_event = service.events().insert(calendarId=email, body=event).execute()
        return jsonify({"message": f"Event created: {created_event.get('htmlLink')}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/list_events', methods=['POST'])
def list_events():
    try:
        data = request.json
        if 'email' not in data or 'username' not in data:
            return jsonify({'error': 'Email and username are required fields.'}), 400
        email = data['email']
        username = data['username']
        service = get_google_calendar_service(username)
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId=email, timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append({"start": start, "summary": event.get('summary', '')})
        return jsonify({"events": event_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)