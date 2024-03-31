

def confirm(prompt, legal_response_list): #: core_util, @io
    tmp = input(prompt)
    if tmp in legal_response_list:
        return tmp
    else:
        return ''
    
