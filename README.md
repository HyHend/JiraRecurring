# JiraRecurring
Automatically create recurring tasks in Jira

### What does it do?
Creates recurring issues within JIRA when:
- Title of the issue contains [RECURRING]
- Task description contains recurring_settings[active, schedule_type, scedule, times_recurred]
 
Now a new issue will be made even if the last is not yet done.
 - Note: [RECURRING] will be renamed to [RECURRED]. So there should only be one [RECURRING] in the "tree". (For any given task)

### Example task descriptions:
The following will create a recurring version of the task containing this in the description:
```recurring_settings:[
active:1
schedule_type:interval
schedule:1
times_recurred:0]
```

The following will create a task on Monday, Wednesday and Friday
```recurring_settings:[
active:1
schedule_type:weekday
schedule:1,3,5
times_recurred:0]
```

### Script usage:
`python3 jira_recurring.py http://uri:port username password`

Will run once and based on current information create recurring tasks.
Create a daily cronjob (for example at 03:00), now your recurring tasks will always be up to date.