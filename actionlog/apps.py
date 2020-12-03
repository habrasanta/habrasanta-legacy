from django.apps import AppConfig


class ActionLogConfig(AppConfig):
    name = "actionlog"
    verbose_name = "Журнал действий"

    def ready(self):
        import actionlog.signals
