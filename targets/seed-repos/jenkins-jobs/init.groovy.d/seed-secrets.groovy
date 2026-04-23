/**
 * seed-secrets.groovy
 * Runs at Jenkins startup (init.groovy.d/) — seeds fixture credentials for lab
 * Chain: supplies GT-JNK-004 stored cred (minio-deploy) used by deploy-prod job
 */
import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.*
import hudson.util.Secret

def instance = Jenkins.getInstance()
def domain = Domain.global()
def store = instance.getExtensionList(
    'com.cloudbees.plugins.credentials.SystemCredentialsProvider'
)[0].getStore()

// Fixture: MinIO deploy credentials (access-key → minio-open service)
// This is the stored credential that GT-JNK-004 measures Leviathan detecting
def minioCredential = new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    'minio-deploy',
    'MinIO finance-private deploy key (fixture lab canary)',
    'AKIAFAKE1234567890AB',
    'sFakeSecretKeyForLabCanary1234567890xxxxx'
)

// Fixture: Vault root token (dev mode static root token)
def vaultTokenCredential = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    'vault-root-token',
    'Vault dev mode root token (fixture)',
    Secret.fromString('root-dev-token-deliberate')
)

// Fixture: Gitea platform org token
def giteaTokenCredential = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    'gitea-platform-token',
    'Gitea platform org access token (fixture)',
    Secret.fromString('gitea-admin-fixture-token-abc123')
)

store.addCredentials(domain, minioCredential)
store.addCredentials(domain, vaultTokenCredential)
store.addCredentials(domain, giteaTokenCredential)

instance.save()

println('[seed-secrets] Fixture credentials seeded successfully')
