import datetime
from datetime import timedelta

class MainEvent:
    """
    A class used to represent the Main Event, meaning the event to which
    the more minor tasks are leading up.  This event would be added to the
    Scheduled Events spreadsheet.

    ...

    Attributes
    ------------
    name : str
        The name of the event as it is read form the gsheet
    doc_link:
        Full link to the gdoc that contains the documentaiton on how to run the event
    date: str
        Six digit string with yymmdd format

    Methods
    ----------
    get_doc_id()
        Returns the gdoc id extracted from the doc_link
    get_event_date()
        Returns the date attributed (this is overloaded in the child class)
    get_description()
        Returns a blank sring (this is overloaded in the child class)
    display()
        Prints the event object
    """

    def __init__(self,  name, doc_link, date):
        self.name = name
        self.doc_link = doc_link
        self.date =date

    def get_doc_id(self):
        link = self.doc_link.split('/')[-2]
        return link

    def get_event_date(self):
        return self.date

    def get_description(self):
        return ''

    def display(self):
        str = "The event name is "+self.name+" scheduled on "+self.date
        print(str)


class EventTask(MainEvent):
    """
    The class is used to represent a smaller task, which is different from the main
    event.  This task is scheduled relative to the main event and is typically not standalone.
    These Event Tasks are seens in the gdoc documentation for the Main Task with links
    to their respective docs

    ...
    Attributes:
    ------------
    Inherits name : str, doc_link : str, and date : str from MainEvent
    Notes:
    1. doc_link is now just doc_id
    2. date is initially set to empty string and is calculated and reset by get_event_date()

    parent_id : str
        Dash separated event name of the Main Event and the date string of when this event is
        scheduled
    when_marker : int
        The when_marker is set to -1 for tasks that need to occur before the Main Event and
        to 1 for tasks that occur after the main event
    time_len : str
        The attribute contains the number of days before/after main event.  This value is
        calculated from the string in the gdoc that typically has a number of time followed by
        time units (days, weeks, months). The calculation is done by convert_to_days() module
        method, that is not part of the class

    Methods
    ----------
    get_doc_id()
        Overloaded method of the parent, returns doc_link attribute
    get_event_date()
        Calculates the date when the task must be completed, it parses the parent_id
        attribute for the scheduled date, ensuring that the formatting is correct. It then
        determines if the time delta should be positive or negative based on the when_marker
        it subtracts/adds time_len to the parent scheduled date
    get_description()
        Returns description string that can be used in the event description on the calendar,
        this is only relevant to Event Tasks and not Main Events, as the description references
        in large part the related Main Event
    display()
        Augments the string created in the get_description() and prints it
    """
    def __init__(self,   name, doc_link, date, parent_id, when_marker, time_len):
        super().__init__(name, doc_link, date)
        self.parent_id = parent_id
        self.when_marker = when_marker
        self.time_len = time_len

    def get_doc_id(self):
            return self.doc_link

    def get_event_date(self):
        #get date from parent_id
        if not self.date:
            tmp=self.parent_id.split('-')[-1]
            year = int( '20' + tmp[:2])
            month = int(tmp[2:4])
            day = int(tmp[-2:])
            parent_date = datetime.datetime(year=year, month= month, day= day)
            self.date = parent_date + timedelta(days=(self.when_marker*int(self.time_len)))
            self.date = self.date.strftime('%y%m%d')
        return self.date

    def get_description(self):
        disp_str = "Event: " + self.name + " \ncomplete " + str(self.time_len) + " days "
        if self.when_marker < 0:
            disp_str = disp_str + "before "
        else:
            disp_str = disp_str + "after "
        disp_str = disp_str + "the event " + self.parent_id
        return disp_str

    def display(self):
        disp_str = self.get_description()  + " on " + self.get_event_date()
        print(disp_str)

#Module methods that are not part of the classes
def standardize_date(mydate):
    """
    Inputs:
    mydate : str - obtained from gdoc
    Output:
    newdate : str - formatted string
    Checks to see if the passed date has forward slashes "/", if so it assumes that
    the user likely put the date in mm/dd/yyyy format, but allows that it also be
    m/d/yyyy or m/d/yy depending on the date value.  It reformats the date into
    yymmdd pattern, adding leading zeros to month or day when necessary,
    """
    if "/" in mydate:
        mydate_list = mydate.split("/")
        day = mydate_list[1]
        month =  mydate_list[0]
        year = mydate_list[2][-2:]
        newdate = year.zfill(2) + month.zfill(2) + day.zfill(2)
    else:
        newdate=mydate
    return newdate

def create_task_parent_id(name, date):
    """
    Input:
    name : str - from gdoc
    date : str - entered by user and therefore is not standard
    Output:
    event_id : str
    Creates parent_id for Task Event or for a dicitonary key by taking event name
    replacing spaces with dashes "-" and cancatenating standardized date from standardize_date().
    """
    event_id = name.replace(" ","-")+"-"+standardize_date(date)
    return event_id

def convert_to_days(time_list):
    """
    Input:
    time_list : list, time_list[0] - contains the number of time increments, time_list[1] units
    Output:
    days : int - total number of days before or after Main Event
    This function converts a string with a number and associated units, to an integer representing
    total days.
    """
    units = time_list[1]
    num = time_list[0]
    if units.lower().find('day') !=-1:
        days = int(num)
    elif units.lower().find('week') !=-1:
        days = int(num) * 7
    elif units.lower().find('month') !=-1:
        days = int(num) *30
    else:
        print("This time increment is not definied, defaults to a month prior")
        days = 30
    return days
