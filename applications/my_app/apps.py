from django.apps import AppConfig


class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "applications.my_app"


    def ready(self):
        import applications.my_app.signals 