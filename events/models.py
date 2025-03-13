from django.db import models
from wagtail.admin.panels.field_panel import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


# Create your models here.

class HomePage(Page):
    body = RichTextField(blank=True)
    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]