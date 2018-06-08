import json
import os
import random
import string
import uuid

from invoke.watchers import Responder
from invoke import task


def _gen_password(n):
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(random.choice(alphabet) for i in range(n))
        # check password satisfies azure requirements or generate a new one
        if (any(x.isupper() for x in password) and
            any(x.islower() for x in password) and
            any(x.isdigit() for x in password)):
            return password


def _create_resources(c, project_name, verbose=False):
    commands = (
         ("Resource Group",
          # location westus is used because requests comes from Menlo Park, California, US
          "az group create --name {}-gr --location westus"),
         ("Storage",
          "az storage account create --name {0}st --location westus --resource-group {0}-gr --sku Standard_LRS"),
         ("Redis",
          "az redis create --resource-group {0}-gr --location westus --name {0}-rd --sku Standard --vm-size C1"),
         ("Function App",
          "az functionapp create --resource-group {0}-gr --name {0}-fn --consumption-plan-location westus "
          "--storage-account {0}st --deployment-local-git"),
    )
    for command in commands:
        r = c.run(command[1].format(project_name),
                  hide=None if verbose else "out",  echo=verbose)
        if r.ok:
            print("Successfully created {}".format(command[0]))
        else:
            return False


@task
def delete_resources(c, project_name, verbose=False):
    responder = Responder(
        pattern=r"Are you sure you want to perform this operation? (y/n):",
        response="y\n",
    )
    c.run("az group delete --name {}-gr".format(project_name),
          watchers=[responder],
          hide=None if verbose else "out",
          echo=verbose)


@task
def make_venv(c, pythonpath="/usr/bin/python2.7", verbose=False):
    r = c.run("{} --version".format(pythonpath), hide="both")
    if not (r.ok or r.stdout.lower().startswith("python 2.7")):
        print("Specify correct path to python 2.7 in --pythonpath parameter")
        return False
    commands = ["virtualenv --python={} ./venv".format(pythonpath),
                ". ./venv/bin/pip install -r requirements.txt"]
    if os.path.isfile("./venv/bin/activate"):
        # re-create venv to ensure python version is correct and there is no unwanted packages
        commands.insert(0, "rm -rf ./venv")
    for command in commands:
        r = c.run(command,
                  hide=None if verbose else "out", echo=verbose)
        if not r.failed or r.stderr:
            return False
    return True


def _add_az_repo(c, project_name, verbose=False):
    r = c.run("az functionapp deployment source show --name {}-fn --resource-group {}-gr".format(project_name),
              hide=None if verbose else "out", echo=verbose)
    if r.ok:
        res_json = json.loads(r.stdout)
        "git remote add azure {}".format(res_json["repoUrl"])


@task
def set_os_env(c, project_name, fb_page_acess_token, fb_verify_token, verbose=False):
    if not fb_page_acess_token:
        fb_page_acess_token = str(uuid.uuid4())
    r = c.run("az redis list-keys --resource-group {0}-gr --name {0}-rd".format(),
              hide=None if verbose else "out", echo=verbose)
    r = c.run('az functionapp config appsettings set --name {0}-fn --resource-group {0}-gr --settings '
              'FB_VERIFY_TOKEN="{1}" FB_PAGE_ACCESS_TOKEN="{2}" REDIS_HOST="{3}" REDIS_PASSWD="{4}"'.format(
                project_name,
                fb_verify_token,
                fb_page_acess_token,
                "{}-rd.".format(project_name)
              ), hide=None if verbose else "out", echo=verbose)


@task
def update(c, project_name, pythonpath="/usr/bin/python2.7", verbose=False):
    if make_venv(c, project_name, pythonpath, verbose):
        r = c.run("git push azure master",
                  hide=None if verbose else "out", echo=verbose)


@task
def deploy(c, project_name, fb_page_acess_token, fb_verify_token, user, password, pythonpath="/usr/bin/python2.7",
           verbose=False):
    if not user:
        user = "{}_du".format(project_name)
    if not password:
        password = _gen_password(21)
    r = c.run("az functionapp deployment user set --user-name {} --password {}".format(user, password),
              hide=None if verbose else "out", echo=verbose)
    if r.ok:
        print("Successfully created deployment user '{}'".format(user))
    else:
        return False
    if not _create_resources(c, project_name, verbose):
        delete_resources(project_name)
    # using "deployment local git" https://docs.microsoft.com/en-us/azure/app-service/app-service-deploy-local-git
    _add_az_repo(c, project_name, verbose)
    set_os_env(c, project_name, fb_page_acess_token, fb_verify_token)
    update(c, project_name, pythonpath, verbose)


@task
def show_config(c, project_name):
    r = c.run("az functionapp config appsettings list"
              " --name {}-fn --resource-group {}-gr".format(project_name), hide='both')
    if r.ok:
        res = {}
        for s in json.loads(r.stdout):
            if s["name"] in ("REDIS_HOST", "REDIS_PASSWD", "FB_VERIFY_TOKEN", "FB_PAGE_ACCESS_TOKEN"):
                res[s["name"]] = s["value"]
        print("\n\n".join(map(lambda k: "{} = {}".format(k, res[k]), res)))
