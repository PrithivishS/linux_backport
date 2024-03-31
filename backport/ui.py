

def confirm(prompt, legal_response_list):
    tmp = input(prompt)
    if tmp in legal_response_list:
        return tmp
    else:
        return ''
    
