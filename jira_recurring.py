from jira import JIRA
import sys
import re
from datetime import datetime, timezone, timedelta
from dateutil import parser

#https://jira.readthedocs.io/en/master/examples.html

# Creates recurring issues within JIRA
# - Title of the issue contains [RECURRING]
# - Task description contains recurring_settings[active, schedule_type, scedule, times_recurred]
# - A new issue will be made even if the last is not yet done. Therefore you notice you're skipping
# - Note: [RECURRING] will be renamed to [RECURRED]. So there should only be one [RECURRING]
# - For each issue title, only one recurring issue will be created (otherwise it'll be recursive)

# Example task description:
# recurring_settings:[
# active:1
# schedule_type:interval
# schedule:1
# times_recurred:0]

# Note: schedule_type allows interval or weekday
# Interval is in days since last issue creation
# weekdays is a comma separated list 1,2,3,4,5,6,7 where monday is 1. It'll recur on these days

def checkIssueShouldRecur(issue, settings):
  if settings['schedule_type'] == "weekday" or settings['schedule_type'] == "weekdays":
    current_weekday = datetime.today().weekday()
    if current_weekday in settings['schedule'].split(","):
        return True
    return False
  elif settings['schedule_type'] == "interval":
    created = parser.parse(issue.fields.created)
    now = datetime.now(timezone.utc)
    if created <= (now - timedelta(days=int(settings['schedule']))):
      return True
    return False
  else:
    print("Warn: Invalid schedule type: {0}. Skipping issue: {1}.".format(settings['schedule_type'], issue.summary))
    return False

try:
  server = sys.argv[1]
  username = sys.argv[2]
  password = sys.argv[3]
except:
  print("ERROR: Expected cmd parameters [server, username, password]. Exiting now.")
  exit()

jira = JIRA(
  server=server, 
  basic_auth=(username, password))

# Find all issues reported by the admin
issues = jira.search_issues("assignee={0}".format(username), maxResults=9999)
print("Found {0} issues for user {1}.".format(len(issues), username))

# Filter all issues with [RECURRING] in the title
recurring_issues = list(filter(lambda x: "[RECURRING]" in x.fields.summary, issues))

# For each recurring issue, check if it should recur and recur
for issue in recurring_issues:  
  print("Info: Handling issue: ".format(issue.fields.summary))

  # Retrieve settings from issue description
  m = re.search("recurring_settings:\[.*\]", issue.fields.description.replace("\n","|").replace("\r",""))
  if m:
    # Rewrite syntax to splittable settings
    settings = m.group(0)
    settings = settings.replace("recurring_settings:[","")
    settings = settings.replace("]","")

    # Split and replace empty parts
    settings = settings.split("|")
    if settings[0] == "":
      del settings[0] # empty element

    # Settings to settings dict
    settings = dict(list(map(lambda x: (x.split(":")[0].strip(),x.split(":")[1].strip()), settings)))
  else:
    print("Warn: [RECURRING] issue found without settings: {0}".format(issue.fields.summary))
    continue # Skip this issue, continue loop

  print(settings)

  # Increment times_recurred
  try:
    new_description = issue.fields.description.replace("times_recurred:{0}".format(settings["times_recurred"]),"times_recurred:{0}".format(int(settings["times_recurred"])+1))
  except:
    print("Warn: Times recurred is missing from settings. Init as 1.")
    new_description = issue.fields.description.replace("]",", times_recurred:1]")

  if checkIssueShouldRecur(issue, settings):
    # Create a new issue
    issue_dict ={
      "project": {"id":issue.fields.project.id},
      "issuetype": {"name":issue.fields.issuetype.name},
      "assignee": {"name":issue.fields.assignee.name},
      "summary": issue.fields.summary,
      "description": new_description,
      "timetracking": {"originalEstimate":issue.fields.timetracking.originalEstimate},
    }
    new_issue = jira.create_issue(fields=issue_dict)
    print(new_issue)

    # Alter old issue summary
    summary = issue.fields.summary.replace("[RECURRING]","[RECURRED]")
    issue.update(summary=summary)

    print("Created recurring issue: {0}".format(issue.fields.summary))
  else:
    print("Info: Issue should not yet recur. Skipping: {0}".format(issue.fields.summary))
