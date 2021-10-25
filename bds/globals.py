from app.auth.models import Role



SUBSCRIBER_ROLE = Role.find_one_by_name(name="Subscriber")
MESSENGER_ROLE = Role.find_one_by_name(name="Messenger")
