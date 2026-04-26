using './main.bicep'

param projectName = 'loreforge'
param environment = 'dev'
param location = 'westus2'
param postgresAdminUser = 'loreforgeadmin'
param postgresAdminPassword = readEnvironmentVariable('POSTGRES_ADMIN_PASSWORD')
param containerImageTag = 'latest'
