import constants
import traceback

def get_error_msgs(session_state):
    display_msg = \
        'OH NO! AN ERROR HAS OCCURRED!\n\n' \
        f'Please report the issue: \n\n' \
        '1. Click the Download Error Message button below\n\n' \
        f'2. Send an email to [{constants.EMAIL}](mailto:{constants.EMAIL}) with the downloaded file attached.\n\n' \
        '3. Put "Car Gen App Error" the email subject line\n\n' \
        '4. In the body of the email, put your CP Slack username and a detailed description of how to recreate the issue\n\n' \
        '5. The admin will reach out on Slack to confirm receipt and fix the issue as soon as possible.\n\n'
    
    traceback_msg = str(f'Session_state:\n{session_state}\n\nError:\n{traceback.format_exc()}')
    return display_msg, traceback_msg