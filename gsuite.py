import os.path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#the scopes determin permissions the application will have to different application types
#for more info see here:
#https://developers.google.com/identity/protocols/oauth2/scopes
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',\
                    'https://www.googleapis.com/auth/documents.readonly',\
                    'https://www.googleapis.com/auth/drive.metadata.readonly',\
                    'https://www.googleapis.com/auth/calendar.events']

#this module contains functions that are used by various google api services, including:
#Sheets, Docs, Drive, Calendar

#authentication - for all services
#authenication method was adapted from: https://developers.google.com/sheets/api/quickstart/python
def get_my_credentials():
    """Shows basic usage of the Sheets API.
    Input: None
    Output : credentials object
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

#Service creation functions
#in order to use google apis it is necessary to create a service for each of the document types
def create_gdoc_service(creds):
    """
    Input:
    creds: object
    Output:
    service: object
    Google docs service, uses version 1, needs verified credentials created or
    obtained by running get_my_credentials()
    """
    service = build('docs', 'v1', credentials=creds)
    return service

def build_gcal_service(creds):
    """
    Input:
    creds: object
    Output:
    service: object
    Google calendar service, uses version 3, needs verified credentials created or
    obtained by running get_my_credentials()
    """
    service = build('calendar', 'v3', credentials=creds)
    return service

def build_gdrive_service(creds):
    """
    Input:
    creds: object
    Output:
    service: object
    Google drive service, uses version 2. Version 3 is also currently available but it
    is not compatible with google calendar attachments function.
    This function needs verified credentials created or obtained by running get_my_credentials()
    """
    #https://developers.google.com/drive/api/guides/v2-to-v3-reference
    service =build('drive', 'v2', credentials=creds)
    return service

#google drive API
def get_gdrive_file(file_id, drive_service):
    """
    Input:
    file_id : str - file ID string
    drive_service : object - gdrive service
    Output:
    file : object
    Abstracts retrieval of file meta data from the files in the google drive.
    Takes in file_id (can be obtained from the document link) and drive service
    object created by build_gdrive_service
    """
    file = drive_service.files().get(fileId=file_id).execute()
    return file

#google sheets API
def get_events_gsheet_content(creds, googsheetid):
    """
    Input
    creds : object
    googsheetid : str
    Output:
    result: dict
    This function incorporates service build, since the application only requires one
    specific gsheet. It takes in credentials and sheet id and returns content in the form
    of json which can be treated as a nested dicitonary of lists with nested dicitonaries
    """
    try:
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        #https://stackoverflow.com/questions/64767184/how-to-read-a-link-from-a-cell-in-google-spreadsheet-if-its-inside-href-tag-gs
        fields = "sheets(data(rowData(values(hyperlink,formattedValue))))"
        result = sheet.get(spreadsheetId=googsheetid,
                                             fields=fields).execute()
        if not result:
            print('No data found.')
            return
    except HttpError as err:
        print(err)
    return result

def extract_gsheet_row_data(content):
    """
    Input:
    content : dict
    Output:
    row_date : dict
    extracts data from a gsheet row, given the json content obtained by get_events_gsheet_content
    """
    return  content['sheets'][0]['data'][0]['rowData']

def get_gsheet_formatted_value(data_row, index):
    """
    Input:
    row_data : dict
    index : int
    Output:
    value : str
    returns text from a particular row (data_row) and column (index)
    """
    return data_row['values'][index]['formattedValue']

#google docs API

def get_gdoc_content(doc_service, doc_id):
    """
    Input:
    doc_service : obj
    doc_id : str
    Output:
    doc_dict : dict
    this returns contents of a google doc in a json format that can be treated as
    a dictionary of lists with nexted dictionaries, etc. Reading the document in this
    format allows to access meta data such as the hyper links which are necessary
    for this application. The function requires service object and document id
    """
    document = doc_service.documents().get(documentId=doc_id).execute()
    doc_json = json.dumps(document, indent=4, sort_keys=True)
    doc_dict = json.loads(doc_json)
    return doc_dict

def get_table_ix_from_gdoc(dict):
    """
    Input:
    dict : dict
    Output:
    dict_list : list
    This function returns the indices of the tables that contain data. It takes in
    json content of the google doc.
    """
    table_marker = 'table'
    dict_list = []
    for ix, item in enumerate(dict['body']['content']):
        if table_marker in item:
            dict_list.append(ix)
    return dict_list

def get_text_from_gdoc_table_cell(dict, table_ix, row_ix, col_ix):
    """
    Input:
    dict : dict
    table_ix : int
    row_ix  : int
    col_ix : int
    Output:
    text_val : str
    Abstracts parsing of the document json to identify the necessary table cells from
    json doc content (dict), table index (obtained from get_table_ix_from_gdoc), the row
    of the table and the column of the table.  It returns the text in a particular cell
    """
    try:
        text_val = dict['body']['content'][table_ix]['table']['tableRows'][row_ix]['tableCells'][col_ix]['content'][0]['paragraph']['elements'][0]['textRun']['content']
    except:
        print("No text is available in table indexed {} row {} col {}".format(table_ix, row_ix, col_ix))
        return
    return text_val.strip()

def get_link_from_gdoc_table_cell(dict, table_ix, row_ix, col_ix):
    """
    Input:
    dict : dict
    table_ix : int
    row_ix : int
    col_ix : int
    Output:
    link_val : str
    Abstracts parsing of the document json to identify the necessary table cells from
    json doc content (dict), table index (obtained from get_table_ix_from_gdoc), the row
    of the table and the column of the table.  It returns the hyperlink in a particular cell
    """
    try:
        link_val = dict['body']['content'][table_ix]['table']['tableRows'][row_ix]['tableCells'][col_ix]['content'][0]['paragraph']['elements'][0]['textRun']['textStyle']['link']['url']
    except:
        print("No link is available in table indexed {} row {} col {}".format(table_ix, row_ix, col_ix))
        return
    return link_val.strip()

def get_total_gdoc_table_rows(dict,table_ix):
    """
    Input:
    dict : dict
    table_ix : int
    Output:
    rows : int
    Returns the total number of rows in a table, by taking in json document content, and table index
    """
    rows = len(dict['body']['content'][table_ix]['table']['tableRows'])
    return rows

#google calendar API

def delete_all_scheduled_gcal_events(cal_id, cal_service):
    """
    Input:
    cal_id : str
    cal_service: obj
    Output:
    None
    This function allows to automate the runs, by making the google sheet with the events the
    ultimate truth. This function can eventually have the added feature of only deleting events
    that are tagged a certain way.  Currently it deletes all the events in the calendar with cal_id
    it also requires calendar service to be passed as an object
    """
    # based on this quickstart script: https://developers.google.com/calendar/api/quickstart/python
    events_result = cal_service.events().list(calendarId=cal_id, singleEvents=True).execute()
    events = events_result.get('items', [])
    print("there are {} events to be deleted".format(len(events)))
    for old_event in events:
        print("The event being deleted has id {}".format(old_event['id']))
        cal_service.events().delete(calendarId=cal_id, eventId=old_event['id']).execute()

def add_event_to_gcal(event, cal_service, cal_id):
    """
    Input:
    event : MainEvent or TaskEvent obj
    cal_service: obj
    cal_id : str
    Output:
    None
    Receives a premade event object, which may have an google doc attachement and adds it
    to the calendar with cal_id
    """
    event_obj = cal_service.events().insert(calendarId=cal_id, body=event, supportsAttachments=True).execute()
    print('Event created: %s' % (event_obj.get('htmlLink')))

def set_gcal_event_time_str(date_str):
    """
    Input:
    date_str : str
    Output:
    time_lst : list of string
    this is a helper function to create the necessary format of the time and date for the event,
    takes in a string with the following format yymmdd
    """
    #https://stackoverflow.com/questions/22526635/list-of-acceptable-google-calendar-api-time-zones
    newstr = '20'+date_str[:2] + '-'+date_str[2:4]+'-' +date_str[4:]
    start = newstr+'T09:00:00-04:00'
    stop = newstr +'T17:00:00-04:00'
    time_lst =[start, stop]
    return time_lst

def create_gcal_event_from_template(summary, date, file_id, drive_service, description):
    """
    Input:
    summary : str
    date : str
    file_id : str
    drive_service : obj
    description : str
    Output :
    event : dict (json)
    Takes in event summary (name of the event), the date when it should be scheduled,
    description and drive service, as well as the file id of the attachment.  These necessary
    parameters can be obtained through the MainEvent and EventTask classes
    """
    file = get_gdrive_file(file_id, drive_service)
    date_list = set_gcal_event_time_str(date)
    #Additional discussion of the format and including attachments is discussed here:
    #https://developers.google.com/calendar/api/guides/create-events
    event = {
        'summary': summary,
        'description': description,
        'start': {
        'dateTime': date_list[0], #https://datatracker.ietf.org/doc/html/rfc3339
        'timeZone': 'America/New_York',
        },
        'end': {
        'dateTime': date_list[1],
        'timeZone': 'America/New_York',
        },
        'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=1'
        ],
        'attachments': [{
        'fileUrl': file['alternateLink'],
        'mimeType': file['mimeType'],
        'title': file['title']
        }]
    }
    return event
