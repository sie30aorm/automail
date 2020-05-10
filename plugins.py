import getpass
import requests
from json.decoder import JSONDecodeError
import subprocess as sub

# -----------------------------------------------------------------------
def weather(lines):
# -----------------------------------------------------------------------
    city_id = str(5391959)
    url = "https://api.openweathermap.org/data/2.5/forecast?id="
    api_key = "your api key here"
    res = requests.get(url + city_id + "&APPID=" + api_key + "&mode=json")
    if res.status_code != 200:
        return "Oops, code was " + code
    try:
        j = res.json()
    except JSONDecodeError:
        return "JSON decode error: \n" + res.text
    try:
        main = j["city"]["list"][0]["weather"][0]["main"]
        description = j["city"]["list"][0]["weather"][0]["description"]
    except Exception as e:
        return str(e) + "\n" + r.text
    return "The weather is: \n%s: %s" % (main, description)

# -----------------------------------------------------------------------
def exec_cmd(cmds):
# -----------------------------------------------------------------------
    param = cmds[2]
    """exec_cmd: executes a command with subprocess
    """
    try:
        p = sub.run(param, shell=True, timeout=20, stdout=sub.PIPE, stderr=sub.PIPE)
    except sub.TimeoutExpired:
        return "Command timed out.  "
    return '''Command exited with code %s
Stdout:
%s
Stderr:
%s
''' % (p.returncode, p.stdout.decode(), p.stderr.decode())

# -----------------------------------------------------------------------
def runscript(lines):
# -----------------------------------------------------------------------
    """
    Writes input to disk and executes it.  Returns any errors.
    IMPORTANT:
    Before running, make sure file 'script' exists and is executable.
    """
    try:
        f = open("script", "w")
        count = 0
        for i in lines:
            if count is 0 or i is 1:
                count = count + 1
                continue
            f.write(i + "\n")
            count = count + 1
        f.close()
        p = sub.run("./script", shell=True, timeout=timeout, stdout=sub.PIPE, stderr=sub.PIPE)
        r = """Script finished!
Return code: %s
Stdout:
%s
Stderr:
%s
""" % (p.returncode, p.stdout.decode(), p.stderr.decode())
    except Exception as e:
        return "Error: \n" + str(e)
    return r

# -----------------------------------------------------------------------
commands = {"exec":exec_cmd, "script":runscript, "weather":weather}
# -----------------------------------------------------------------------
