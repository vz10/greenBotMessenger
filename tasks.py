import json
import os
import random
import string
import uuid

from invoke.watchers import Responder
from invoke import task


class DeploymentError(Exception):
    def __init__(self, message):
        super(DeploymentError, self).__init__("Deployment error: ".format(message))


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
          "az redis create --resource-group {0}-gr --location westus --name {0}-rd --sku Basic --vm-size C0"),
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
            raise DeploymentError("Can't create resources")


@task
def delete_resources(c, project_name, verbose=False):
    responder = Responder(
        pattern=r"Are you sure you want to perform this operation? (y/n):",
        response="y\n",
    )
    c.run("az group delete --name {}-gr".format(project_name),
          watchers=[responder],
          pty=True,
          hide=None if verbose else "out",
          echo=verbose)


def _add_deployment_user(c, project_name, user=None, password=None, verbose=False):
    user = user or "{}_du".format(project_name)
    password = password or _gen_password(21)
    r = c.run("az functionapp deployment user set --user-name {} --password {}".format(user, password),
              hide=None if verbose else "out", echo=verbose)
    if r.ok:
        with open('.deployment.json', 'w') as f:
            json.dump({"user": user, "password": password, "project_name": project_name}, f)
        print("Successfully created deployment user '{}'".format(user))
    else:
        raise DeploymentError("Can't create deployment user for uploading")


def _add_az_repo(c, project_name, user=None, password=None, verbose=False):
    if not os.path.exists('.deployment.json'):
        _add_deployment_user(c, project_name, user, password, verbose)
    r = c.run("az functionapp deployment source config-local-git --name {0}-fn "
              "--resource-group {0}-gr".format(project_name),
              hide=None if verbose else "out", echo=verbose)
    if r.ok:
        res_dict = json.loads(r.stdout)
        r = c.run("git config remote.azure.url", hide=None if verbose else "out", echo=verbose, warn=True)
        if r.stdout:  # remote exists - update url
            c.run("git remote set-url azure {}".format(res_dict["url"]),
                  hide=None if verbose else "out", echo=verbose)
        else:
            c.run("git remote add azure {}".format(res_dict["url"]),
                  hide=None if verbose else "out", echo=verbose)
    else:
        raise DeploymentError("Can't add git remote url for Azure")


@task
def set_os_env(c, project_name, fb_page_access_token, fb_verify_token, verbose=False):
    if not fb_verify_token:
        fb_verify_token = str(uuid.uuid4())
    r = c.run("az redis list-keys --resource-group {0}-gr --name {0}-rd".format(project_name),
              hide=None if verbose else "out", echo=verbose)
    res_dict = json.loads(r.stdout)
    r = c.run('az functionapp config appsettings set --name {0}-fn --resource-group {0}-gr --settings '
              'FB_VERIFY_TOKEN="{1}" FB_PAGE_ACCESS_TOKEN="{2}" REDIS_HOST="{3}" REDIS_PASSWD="{4}"'.format(
                project_name,
                fb_verify_token,
                fb_page_access_token,
                "{}-rd.redis.cache.windows.net".format(project_name),
                res_dict["primaryKey"]
              ), hide=None if verbose else "out", echo=verbose)


@task
def update(c, verbose=False):
    with open('.deployment.json', 'r') as f:
        data = json.load(f)
    pattern = r"Password for 'https://{}@{}-fn.scm.azurewebsites.net': ".format(data["user"], data["project_name"])
    responder = Responder(
        # Password for 'https://testmsgbot05_du@testmsgbot05-fn.scm.azurewebsites.net':
        pattern=pattern,
        response=data["password"] + "\n"
    )
    r = c.run("git push azure master", watchers=[responder], pty=True, hide=None if verbose else "out", echo=verbose)


@task
def deploy(c, project_name, fb_page_access_token, fb_verify_token=None, user=None, password=None,
           skip_resources_creation=False, verbose=False, force=False):
    if os.path.exists('.deployment.json') and not force:
        print("Project already have been deployed. "
              "Use 'invoke update' to apply changes or run with key --force to create new deployment")
        return 1
    if not skip_resources_creation:
        try:
            _create_resources(c, project_name, verbose)
            set_os_env(c, project_name, fb_page_access_token, fb_verify_token, verbose)
        except DeploymentError as e:
            delete_resources(c, project_name)
            raise e

    # using "deployment local git" https://docs.microsoft.com/en-us/azure/app-service/app-service-deploy-local-git
    _add_az_repo(c, project_name, user, password, verbose)
    update(c, verbose)


@task
def show_config(c, project_name, verbose=False):
    r = c.run("az functionapp config appsettings list"
              " --name {0}-fn --resource-group {0}-gr".format(project_name),
              hide=None if verbose else "out", echo=verbose)
    if r.ok:
        res = {}
        for s in json.loads(r.stdout):
            if s["name"] in ("REDIS_HOST", "REDIS_PASSWD", "FB_VERIFY_TOKEN", "FB_PAGE_ACCESS_TOKEN"):
                res[s["name"]] = s["value"]
        res["WEBHOOK_URL"] = "https://{}-fn.azurewebsites.net/api/webhook".format(project_name)
        print("\n\n".join(map(lambda k: "{} = {}".format(k, res[k]), res)))
