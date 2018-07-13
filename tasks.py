import json
import uuid

from config import FB_PAGE_ACCESS_TOKEN
import requests
from invoke.watchers import Responder
from invoke import task


class DeploymentError(Exception):
    def __init__(self, message):
        super(DeploymentError, self).__init__("Deployment error: ".format(message))


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
         "--storage-account {0}st"),
    )
    for command in commands:
        r = c.run(command[1].format(project_name),
                  hide=None if verbose else "out", echo=verbose)
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


@task
def set_os_env(c, project_name, fb_page_access_token, fb_verify_token, db_url, db_password, verbose=False):
    if not fb_verify_token:
        fb_verify_token = str(uuid.uuid4())
    r = c.run("az redis list-keys --resource-group {0}-gr --name {0}-rd".format(project_name),
              hide=None if verbose else "out", echo=verbose)
    res_dict = json.loads(r.stdout)
    c.run('az functionapp config appsettings set --name {0}-fn --resource-group {0}-gr --settings '
          'FB_VERIFY_TOKEN="{1}" FB_PAGE_ACCESS_TOKEN="{2}" REDIS_HOST="{3}" REDIS_PASSWD="{4}" '
          'DB_URL="{5}" DB_PASSWORD="{6}"'.format(
        project_name,
        fb_verify_token,
        fb_page_access_token,
        "{}-rd.redis.cache.windows.net".format(project_name),
        res_dict["primaryKey"],
        db_url,
        db_password
    ), hide=None if verbose else "out", echo=verbose)


@task
def deploy(c, project_name, fb_page_access_token=None, fb_verify_token=None, skip_resources_creation=False,
           db_url=None, db_password=None, verbose=False):
    if not skip_resources_creation:
        if not (fb_page_access_token and db_url and db_password):
            print("'deploy' did not receive some of required arguments: "
                  "--fb-page-access-token, --db-url, --db-password\n"
                  "You can skip those arguments only if use --skip-resources-creation")
            return 1

        try:
            _create_resources(c, project_name, verbose)
        except DeploymentError as e:
            delete_resources(c, project_name)
            raise e
        set_os_env(c, project_name, fb_page_access_token, fb_verify_token, db_url, db_password, verbose)

    c.run("zip -FSr greenBotMessenger.zip .", hide=None if verbose else "out", echo=verbose)
    c.run("az functionapp deployment source config-zip --src greenBotMessenger.zip "
          "--name {0}-fn  --resource-group {0}-gr --debug".format(project_name),
          hide=None if verbose else "out", echo=verbose)


@task
def show_config(c, project_name, verbose=False):
    r = c.run("az functionapp config appsettings list"
              " --name {0}-fn --resource-group {0}-gr".format(project_name),
              hide=None if verbose else "out", echo=verbose)

    res = {}
    for s in json.loads(r.stdout):
        if s["name"] in ("REDIS_HOST", "REDIS_PASSWD", "FB_VERIFY_TOKEN", "FB_PAGE_ACCESS_TOKEN",
                         "DB_URL", "DB_PASSWORD"):
            res[s["name"]] = s["value"]
    res["WEBHOOK_URL"] = "https://{}-fn.azurewebsites.net/api/webhook".format(project_name)
    print("\n\n".join(map(lambda k: "{} = {}".format(k, res[k]), res)))


@task
def setup_fb_greeting(c, fb_page_access_token, verbose=False):
    request_body_greeting = {
        "greeting": {
            "locale": "default",
            "text": "Welcome, {{user_full_name}}! Let's grow something!"
        }
    }

    request_body_get_started = {
        "get_started": {"payload": "get_started"}
    }

    res = requests.post(url="https://graph.facebook.com/v2.6/me/messenger_profile",
                        params={"access_token": fb_page_access_token},
                        headers={'content-type': 'application/json'},
                        data=json.dumps(request_body_greeting))
    if verbose:
        print res.content

    res = requests.post(url="https://graph.facebook.com/v2.6/me/messenger_profile",
                        params={"access_token": fb_page_access_token},
                        headers={'content-type': 'application/json'},
                        data=json.dumps(request_body_get_started))
    if verbose:
        print res.content
