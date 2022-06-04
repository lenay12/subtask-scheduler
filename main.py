from __future__ import print_function
import os

import gsuite
import event
from event import MainEvent
from event import EventTask

# set working dirctory, could be pulled out into config file
os.chdir("C:/Users/Len/Documents/GitHub/goog_api_test/midterm")


# These global variables could be a part of a config file
MAIN_EVENT_SHEET_ID = '1Fme8IXX5gmOqtrsJrMtIFO7YEVohBFgae49cJbDxSQ8'
CALENDAR_ID ='ifkvu9ip2slqml42kiofdah138@group.calendar.google.com'

#Functions that use both gsuite and event module stayed in main.py
#-------------------------------------------------------------------------------------
def create_event_task(doc_dict, table_ix, row_ix, parent_id):
    """
    Input:
    doc_dict : dict
    table_ix : int
    row_ix : int
    parent_id : str
    Output:
    event_task : EventTask obj
    The function reads gdoc to obtain event information such as name, doc_link, extracts link_id
    (this part can be inproved by adjusting the class), determines the when_marker and time_lens.
    Once all these values are obtained and processed from the gdoc, the EventTask is created.
    The date attribute of the EventTask is set to blank initially.
    """
    tmp_name = gsuite.get_text_from_gdoc_table_cell(doc_dict, table_ix, row_ix,1)
    tmp_link = gsuite.get_link_from_gdoc_table_cell(doc_dict,  table_ix, row_ix,1)
    link_id = tmp_link.split("/")[-2]
    when_tmp = gsuite.get_text_from_gdoc_table_cell(doc_dict,  table_ix, 0,2)
    if when_tmp.lower().find('before') !=-1:
        marker_tmp = -1
    else:
        marker_tmp = 1
    tmp_time = event.convert_to_days(gsuite.get_text_from_gdoc_table_cell(doc_dict,  table_ix, row_ix,2).split(" "))
    event_task = EventTask(tmp_name, link_id, '', parent_id, marker_tmp, tmp_time)
    return event_task

def update_child_task_dict(task_dict, doc_dict, table_ix, parent_id):
    """
    Input:
    task_dict : dict
    doc_dict : dict
    table_ix : int
    parent_id : str
    Output:
    task_dict : dict
    This function updates task_dict, the variable reference is passed as an input and
    then also returned as an output.  The function parses each table in the gdoc that contains
    tasks.  it creates a key to the dictionary by combining the TaskEvent.name | parent_id string
    """
    for row in range(1, gsuite.get_total_gdoc_table_rows(doc_dict, table_ix)):
        child_event_obj =  create_event_task(doc_dict, table_ix, row, parent_id)
        tmp_key = child_event_obj.name + '  |  ' + parent_id
        task_dict[tmp_key] = child_event_obj
    return task_dict

def schedule_event(my_event, drive_service, cal_service):
    """
    Input:
    my_event : MainEvent or TaskEvent obj
    drive_service : obj
    cal_service : obj
    Output :
    None
    This function creates a json event using a template and values proviced in the input, it
    adds the event to the calendar defined by the global constant at the top of hte file
    """
    cal_event = gsuite.create_gcal_event_from_template(my_event.name, my_event.get_event_date(), my_event.get_doc_id(), drive_service, my_event.get_description())
    gsuite.add_event_to_gcal(cal_event, cal_service, CALENDAR_ID)
    my_event.display()

def main():
    # obtain credentials and read the events spreadsheet (always the same)
    credentials = gsuite.get_my_credentials()
    result = gsuite.get_events_gsheet_content(credentials, MAIN_EVENT_SHEET_ID)

    #extract just the row data of the google sheet
    events_data =   gsuite.extract_gsheet_row_data(result)

    #create an empty dictionary for the Main Events listed in the spreadsheet, it's possible to
    # have the same type of event scheduled more than once
    my_events_dict ={}
    # process events data row by row, staring with row 2
    for row in events_data[1:]:
        #1st list contains the name and the link to the documentation
        event_name = gsuite.get_gsheet_formatted_value(row,0)
        event_docs = row['values'][0]['hyperlink']
        print("{} is documented here {}".format(event_name, event_docs))
        #All cells after (if any exist) contain scheduled dates
        # this if statement checks to see if any scheduled dates exist
        # creates an event instance by combining name and scheduled date
        #adds that instance to the myEvents_dict
        if(row['values'][1]):
            for ix, item in enumerate(row['values'][1:]):
                current_date = gsuite.get_gsheet_formatted_value(row,ix+1)
                event_id = event.create_task_parent_id(event_name, current_date)
                event_obj = MainEvent(event_name, event_docs, event.standardize_date(current_date))
                my_events_dict[event_id] = event_obj

    #Next we will check the documentation for each of the events.
    #These are documented in google docs therefore a new service is required for gdocs
    doc_service = gsuite.create_gdoc_service(credentials)
    #Each google doc contains tables that list out detailed tasks (with linked docs) needed to
    # run each event
    tasks_dict = {}
    for key, my_event in my_events_dict.items():
        # for each Main Event open its associated gdoc and get content
        doc_content = gsuite.get_gdoc_content(doc_service, my_event.get_doc_id())
        # find indices of the steps tables
        content_tbls_ix = gsuite.get_table_ix_from_gdoc(doc_content)
        # read each table and populate task_dict with tasks
        for tbl_ix in content_tbls_ix:
            tasks_dict=update_child_task_dict(tasks_dict, doc_content, tbl_ix,  key)

    # in order to schedule events we will need an instance of the calendar service
    cal_service = gsuite.build_gcal_service(credentials)
    # as well as google drive service, needed to add attachments to the events
    drive_service = gsuite.build_gdrive_service(credentials)
    # this application will be automated and run based on either a trigger or as a
    # scheduled event.  In order to start a fresh we will first need to delete the currently scheduled
    #events, this can be augmented by adding a tag to auto scheduled events, and only
    #deleting those
    gsuite.delete_all_scheduled_gcal_events(CALENDAR_ID, cal_service)

    # schedule all Main Events stored in my_events_dict
    for k, i in my_events_dict.items():
        schedule_event(i, drive_service, cal_service)
    #schedule Task Events stored in tasks_dict
    for k, i in tasks_dict.items():
        schedule_event(i, drive_service, cal_service)

if __name__ == '__main__':
    main()
