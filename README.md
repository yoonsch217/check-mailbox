This is a tool to read emails in an inbox and filter emails that match a certain rule, using python3.    
When matched, the emails can be forwarded to others or written as github issues.

### HOW TO

1. Copy `config.ini.template` file to `config.ini` and fill out the file.
2. `python3 run.py`


### WHAT HAPPENS

1. Log in to IMAP server with given account and password.
2. Read a checkpoint file and find out the last email that has been checked before. 
3. Read emails that were sent after the checkpoint.
4. Read each email and checks whether it matches a certain rule.
5. If it matches the rule, forward the email to a receiver and create a github issue with the email content.
6. After reading all the new emails, update the checkpoint file so that the next execution doesn't read already seen emails.

---

python3   
IMAP/SMTP   
Github REST API   