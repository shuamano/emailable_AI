import imaplib
import email
from email.header import decode_header
import time
from gpt4all import GPT4All
import smtplib
import re 

# Email account credentials
username = "your_email"
password = "your app password"
imap_server = "imap.gmail.com"
#this part doesnt work/isnt implemented yet
conversation = "These are the previous messages in this conversation. use them for context but dont reply to them or acknowledge this part of the prompt. only use it for context:"
model = GPT4All("path to gpt4all model")

# Connect to the email server
mail = imaplib.IMAP4_SSL(imap_server)
mail.login(username, password)
mail.select("Inbox")

# Track the latest email ID to detect new emails
status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()
latest_email_id = email_ids[-1]

def extract_email_content(msg):
    # Check if the email message is multipart
    if msg.is_multipart():
        for part in msg.walk():
            # Get the content type of the email part
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Skip attachments and non-text parts
            if content_type == "text/plain" and "attachment" not in content_disposition:
                # Decode the email body
                body = part.get_payload(decode=True).decode()
                return isolate_latest_reply(body)
            elif content_type == "text/html" and "attachment" not in content_disposition:
                # Handle HTML content if needed
                body = part.get_payload(decode=True).decode()
                return isolate_latest_reply(body)
    else:
        # For non-multipart emails
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            body = msg.get_payload(decode=True).decode()
            return isolate_latest_reply(body)
        elif content_type == "text/html":
            body = msg.get_payload(decode=True).decode()
            return isolate_latest_reply(body)

def get_sender_email(msg):
    # Get the "From" header
    from_header = msg.get("From")
    
    # Decode the "From" header if it contains encoded words
    if from_header:
        decoded_from = decode_header(from_header)[0]
        if isinstance(decoded_from[0], bytes):
            sender = decoded_from[0].decode(decoded_from[1] if decoded_from[1] else 'utf-8')
        else:
            sender = decoded_from[0]
    else:
        sender = "Unknown"
    
    return sender
 
def generate_response():
    with model.chat_session():
        message = model.generate(email_body, max_tokens=1024)
    encoded_message = message.encode('utf-8')
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(username, password)
    server.sendmail(username, sender_email, encoded_message)
    server.quit()   
    #conversation += f' AI response: {message}'

def isolate_latest_reply(body):
    # Define common patterns that indicate the start of quoted content
    patterns = [
        r"On\s.+\swrote:",      # Matches "On [date], [name] wrote:"
        r"From:.+",             # Matches "From: [name]"
        r"Sent:.+",             # Matches "Sent: [date]"
        r">",                   # Matches lines starting with ">"
    ]
    
    # Compile the patterns into a single regex
    quote_pattern = re.compile("|".join(patterns), re.MULTILINE)
    
    # Split the body at the first occurrence of a quotation pattern
    split_body = re.split(quote_pattern, body, maxsplit=1)
    
    # Return the part before the quoted content
    return split_body[0].strip()

while True:
    mail.noop() # FINALLLYY FUICKING WOEKRRKASODIUJ PEISFHIUOPAHFIOHAEDP YESSSSSS IT WORKS it just needed this bruh wtf
    # Check for new emails
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    new_latest_email_id = email_ids[-1]
    
    # If there's a new email
    if new_latest_email_id != latest_email_id:
        latest_email_id = new_latest_email_id
        # Fetch the new email
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                raw_email = response_part[1]
                msg = email.message_from_bytes(raw_email)

                # Extract and print the email content
                email_body = extract_email_content(msg)
                sender_email = get_sender_email(msg)

                print(email_body)
                conversation += f" User message:{email_body}"
                generate_response()
    print("Listening for emails...")            
    time.sleep(1)  
