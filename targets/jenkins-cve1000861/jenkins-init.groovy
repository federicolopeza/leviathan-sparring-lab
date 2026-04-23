import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

// Disable setup wizard
instance.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)

// Seed admin:admin (intentional weak credentials for lab)
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "admin")
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(true)  // intentional: anonymous read enabled
instance.setAuthorizationStrategy(strategy)

instance.save()
