import json
import uuid

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


@task
def set_os_env(c, project_name, fb_page_access_token, fb_verify_token, verbose=False):
    if not fb_verify_token:
        fb_verify_token = str(uuid.uuid4())
    r = c.run("az redis list-keys --resource-group {0}-gr --name {0}-rd".format(project_name),
              hide=None if verbose else "out", echo=verbose)
    res_dict = json.loads(r.stdout)
    c.run('az functionapp config appsettings set --name {0}-fn --resource-group {0}-gr --settings '
          'FB_VERIFY_TOKEN="{1}" FB_PAGE_ACCESS_TOKEN="{2}" REDIS_HOST="{3}" REDIS_PASSWD="{4}"'.format(
            project_name,
            fb_verify_token,
            fb_page_access_token,
            "{}-rd.redis.cache.windows.net".format(project_name),
            res_dict["primaryKey"]
          ), hide=None if verbose else "out", echo=verbose)


@task
def deploy(c, project_name, fb_page_access_token=None, fb_verify_token=None, skip_resources_creation=False,
           verbose=False):
    if not fb_page_access_token and not skip_resources_creation:
        print("'deploy' did not receive required positional arguments: '--fb-page-access-token'\n"
              "You can skip --fb-page-access-token only if use --skip-resources-creation")
        return 1

    if not skip_resources_creation:
        try:
            _create_resources(c, project_name, verbose)
        except DeploymentError as e:
            delete_resources(c, project_name)
            raise e
        set_os_env(c, project_name, fb_page_access_token, fb_verify_token, verbose)

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
        if s["name"] in ("REDIS_HOST", "REDIS_PASSWD", "FB_VERIFY_TOKEN", "FB_PAGE_ACCESS_TOKEN"):
            res[s["name"]] = s["value"]
    res["WEBHOOK_URL"] = "https://{}-fn.azurewebsites.net/api/webhook".format(project_name)
    print("\n\n".join(map(lambda k: "{} = {}".format(k, res[k]), res)))
