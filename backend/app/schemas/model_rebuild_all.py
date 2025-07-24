# Import only the schemas that need model_rebuild
from .user import UserInDB, UserProfile
from .subscription import SubscriptionResponse, SubscriptionWithUser

# Now we can properly resolve forward references
UserInDB.model_rebuild()
UserProfile.model_rebuild()
SubscriptionResponse.model_rebuild()
SubscriptionWithUser.model_rebuild() 