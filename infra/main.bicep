// This Bicep file defines the infrastructure for Loreforge
// To deploy this Bicep file, use the following command in the Azure CLI:
// az deployment group create --resource-group LoreForge-RG --template-file main.bicep

param location string = 'westus'
param storageName string = 'loreforge${uniqueString(resourceGroup().id)}'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS' // Low cost for testing
  }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true // This turns a basic disk into a "Data Lake Gen2"
  }
}

output storageId string = storageAccount.id

