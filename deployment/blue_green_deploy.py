import time
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from paramiko import SSHClient, AutoAddPolicy

SUBSCRIPTION_ID = "1ef3481e-bfe1-4160-aeeb-862132dc8f0e"
RESOURCE_GROUP = "rgvm"
LB_NAME = "lb"
BACKENDPOOL_NAME = "lbbackeend"

#Public IP
BLUE_PUBLIC_IP = "13.71.17.38"
GREEN_PUBLIC_IP = "4.213.34.38"

#Private IP
BLUE_PRIVATE_IP = "172.16.0.4"
GREEN_PRIVATE_IP = "172.16.1.4"

#LB IP
LB_PUBLIC_IP = "98.70.244.206"

# Docker run command
DOCKER_IMAGE = "acrfrontend.azurecr.io/myfrontend:latest"
DOCKER_RUN_COMMAND = f"sudo docker pull {DOCKER_IMAGE} && sudo docker stop app || true && sudo docker rm app || true && sudo docker run -d --name app -p 80:80 {DOCKER_IMAGE}"

SSH_USER = "azureuser"
SSH_PASSWORD = "Azureuser@123"

# SSH Deploy to Green VM


def deploy_to_green():
    print("Deploying to green")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(GREEN_PUBLIC_IP, username=SSH_USER, password=SSH_PASSWORD, timeout=10)
    stdin, stdout, stderr = ssh.exec_command(DOCKER_RUN_COMMAND)
    print(stdout.read().decode())
    ssh.close()
    print("Deployment to GREEN Completed")

# Health Check


def check_health():
    import requests
    try:
        res = requests.get(f"http://{LB_PUBLIC_IP}", timeout=10)
        return res.status_code == 200
    except:
        return False

# Switch Traffic to Green


def switch_to_green():
    credential = DefaultAzureCredential()
    network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)

    print("Switching traffic to Green VM..")
    lbr = network_client.load_balancers.get(RESOURCE_GROUP, LB_NAME)
    backend_pool = list(lbr.backend_address_pools)[0]

    # Remove BlueIP and Add GreenIP
    backend_pool.backend_addresses = [
        {"ip_address": GREEN_PRIVATE_IP}
    ]

    network_client.load_balancers.begin_create_or_update(
        RESOURCE_GROUP, LB_NAME, lbr
    ).result()

    print("Traffic switched to Green succesfully")

# Roolback


def rollback_to_blue():
    print("Deployment fail")
    credential = DefaultAzureCredential()
    network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)

    lbr = network_client.load_balancers.get(RESOURCE_GROUP, LB_NAME)
    backend_pool = list(lbr.backend_address_pools)[0]

    backend_pool.backend_addresses = [{"ip_address": BLUE_PRIVATE_IP}]

    network_client.load_balancers.begin_create_or_update(
        RESOURCE_GROUP, LB_NAME, lbr
    ).result()

    print("Rolled back to Blue")


# Main Workflow
if __name__ == "__main__":
     deploy_to_green()

     print("Checking Green health...")
     time.sleep(10)

     if check_health():
        switch_to_green()
    else:
        rollback_to_blue()
     
    
    
    
  