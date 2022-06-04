# subtask-scheduler
uses google api to add events to google calendar

This project is prototyping the idea of adding events, which have documented tasks (subtasks) that need to be completed in order to successfully run the event

## What's included in the project

We keep track of the main events that require scheduling in the [Scheduled Events google spreadsheet](https://docs.google.com/spreadsheets/d/1Fme8IXX5gmOqtrsJrMtIFO7YEVohBFgae49cJbDxSQ8/edit#gid=0) the sheet has a header row, the name and the link to the documentation of the event in the first column, and all dates when the event will be scheduled in the subsequent columns

Clicking on each event will take you to the detailed documentation of what the event should be.  For example Summer Camp documentation looks like [this](https://docs.google.com/document/d/1L_HFWqTVGjgLVNXgbGlMLP17pOeAmCS7IoQEoQVPDZg/edit).  These tables contain subtasks required to run the event stored in "Preparation" and "Aftermath" tables.  As the names imply, the tasks will need to be completed some amount of time before or after the event.

The scheduled events go to the [following google calendar](https://calendar.google.com/calendar/ical/ifkvu9ip2slqml42kiofdah138%40group.calendar.google.com/public/basic.ics)

## What's not included, but necessary

I am not including credentials.json as that will expose my data publicly.  This can be obtained for your application through the GCP by setting up OAuth2 for a service account, and downloading client_secret.json from your OAuth 2.0 Client ID.  Please make sure to add http://localhost:8080 to Authorized JavaScript origins and http://localhost:8080 to the Authorized redirect URIs.  Additionally, when working on any of the Google API Quickstart scripts, [for example](https://developers.google.com/calendar/api/quickstart/python) change the port number from 0 to 8080 in order to get it to work.

## How to run

Assuming that you have created your own credentials.json, which allow you the access to your own set of google docs, sheets and calendars.  Include credentials.json in the same directory as the rest of the files.  Simply, run main.py.

