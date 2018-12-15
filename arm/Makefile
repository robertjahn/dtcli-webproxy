default: help

# dont edit these unless you adjust the ARM template parameters.json file too
resourceGroupLocation = eastus
resourceGroupName = rjahn-dtcli-proxy
containerName = dtcli-webproxy

# edit subscription.txt file with your value
$(eval subscriptionId=`cat subscription.txt`)
deploymentName = ContainerDeploy

help:
	@echo Current values to be used in scripts.  Fix if not correct
	@echo " subscriptionId="$(subscriptionId)
	@echo " resourceGroupLocation"=$(resourceGroupLocation)
	@echo " resourceGroupName"=$(resourceGroupName)
	@echo " deploymentName"=$(deploymentName)
	@echo " containerName"=$(containerName)

container_deploy:
	@echo Deploying....
	./deploy.sh -i $(subscriptionId) -g $(resourceGroupName) -n $(deploymentName) -l $(resourceGroupLocation)
	@echo Getting current Containers...
	az container list -o table
	@echo Done

container_remove:
	@echo Getting current Containers...
	az container list -o table
	@echo About to remove $(containerName)
	az container delete -n $(containerName) -g $(resourceGroupName)
	@echo Getting current Containers...
	az container list -o table
	@echo Done

group_deploy:
	@echo Getting current Resource Groups...
	 az group list -o table
	@echo About to deploy $(resourceGroupName)
	az group create -g $(resourceGroupName) -l $(resourceGroupLocation)
	@echo Getting current Resource Groups...
	 az group list -o table
	@echo Done

group_remove:
	@echo Getting current Resource Groups...
	 az group list -o table
	@echo About to remove $(resourceGroupName)
	az group delete -g $(resourceGroupName)
	@echo Getting current Resource Groups...
	az group list -o table
	@echo Done