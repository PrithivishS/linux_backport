import subprocess
import pdb
import threading

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
              
def build(state): #: core
    pl.print_log("@@build", state)
    line_fn = lambda line, state: pl.print_log(line, state)
    prompt_to_set_or_alter_dict_val('build_cmd', state)
    if not state['build_cmd']:
        return

    # do it, ignore ret text(for now @ least)
    # assume build_cmd is of the form: <cmd> <arg string>
    L = state['build_cmd'].split(' ')
    shell_args = ' '.join(L[1:])
    spew = poll_shell_cmd(L[0], shell_args, line_fn, state)
    pl.print_log(spew, state)
    return spew

def old_build(state): #: obsolete? (or is build() spewing trash?)
    pl.print_log("@@build", state)
    line_fn = lambda line, state: pl.print_log(line, state)
    prompt_to_set_or_alter_dict_val('build_cmd', state)
    if not state['build_cmd']:
        return

    (ret, spew) = shell_cmd(state['build_cmd'])
    return spew

def do_async_cmd(cmd, key, state):
    (ret, out) = shell_cmd(cmd)
    if 'async_result' not in state:
        state['async_result'] = dict()
    state['async_result'][key] = out

# https://realpython.com/intro-to-python-threading
def async_shell_cmd(cmd, key, state):
    thrd = threading.Thread(target=do_async_cmd, args = (cmd, key, state),
                            daemon=True)
    thrd.start()
