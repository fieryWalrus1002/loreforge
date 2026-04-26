// Loreforge infrastructure
// Deploy: az deployment group create --resource-group <rg> --template-file infra/main.bicep --parameters infra/main.bicepparam

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short name used to derive all resource names.')
param projectName string = 'loreforge'

@description('Environment tag (dev, prod).')
param environment string = 'dev'

@description('PostgreSQL administrator username.')
param postgresAdminUser string = 'loreforgeadmin'

@description('PostgreSQL administrator password.')
@secure()
param postgresAdminPassword string

@description('Container image tag to deploy.')
param containerImageTag string = 'latest'

// ── Naming ───────────────────────────────────────────────────────────────────

var prefix = '${projectName}-${environment}'
var acrName = '${projectName}${environment}acr'              // no hyphens allowed
var postgresName = '${prefix}-pg'
var logAnalyticsName = '${prefix}-logs'
var containerEnvName = '${prefix}-env'
var containerJobName = '${prefix}-worker'
var storageAccountName = '${projectName}${environment}${uniqueString(resourceGroup().id)}'
var dbName = 'loreforge'

// ── Log Analytics (observability for Container Apps) ─────────────────────────

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ── Azure Container Registry ──────────────────────────────────────────────────

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: true
  }
}

// ── Storage Account (Data Lake Gen2 landing zone) ────────────────────────────

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource rawContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'raw-data'
}

resource canonicalContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'canonical-data'
}

// ── PostgreSQL Flexible Server ────────────────────────────────────────────────

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: postgresName
  location: location
  sku: {
    name: 'Standard_B1ms'   // burstable, lowest cost tier
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: postgresAdminUser
    administratorLoginPassword: postgresAdminPassword
    version: '16'
    storage: { storageSizeGB: 32 }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: { mode: 'Disabled' }
  }
}

resource postgresDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgres
  name: dbName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Allow Azure services (including Container Apps) to reach the DB
resource postgresFirewallAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = {
  parent: postgres
  name: 'allow-azure-services'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ── Container Apps Environment ────────────────────────────────────────────────

resource containerEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ── Container Apps Job (batch worker) ────────────────────────────────────────

var databaseUrl = 'postgresql://${postgresAdminUser}:${postgresAdminPassword}@${postgres.properties.fullyQualifiedDomainName}/${dbName}?sslmode=require'

resource workerJob 'Microsoft.App/jobs@2024-03-01' = {
  name: containerJobName
  location: location
  properties: {
    environmentId: containerEnv.id
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 300
      replicaRetryLimit: 1
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: '${acr.properties.loginServer}/loreforge-worker:${containerImageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              value: databaseUrl
            }
          ]
        }
      ]
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output acrLoginServer string = acr.properties.loginServer
output postgresHost string = postgres.properties.fullyQualifiedDomainName
output storageAccountName string = storageAccount.name
output workerJobName string = workerJob.name
