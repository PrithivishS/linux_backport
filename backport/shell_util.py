import subprocess

# should subsume some of the duplicate code in git_utils.py over time
def shell_cmd(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    return (result.returncode, result.stdout.decode('latin-1'))

def poll_shell_cmd(cmd, shell_args, line_fn, state):
    cmd = shutil.which(cmd)
    shell_args = shlex.split(shell_args)
    cmd = [ cmd] + shell_args
    shell_args = ' '.join(shell_args)
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    # Create empty buffers and a polling object
    poll = select.poll()
    poll.register(process.stdout, select.POLLIN)
    poll.register(process.stderr, select.POLLIN)

    # Continuously poll the stdout and stderr streams to capture output as it
    # appears
    spew = []
    while process.poll() is None:
        rlist, _, _ = select.select([process.stdout, process.stderr], [], [])
        for stream in rlist:
            line = stream.readline().decode().rstrip("\n")
            spew.append(line)
            line_fn(line, state)
          
    return spew
              
