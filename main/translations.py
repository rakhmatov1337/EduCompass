from modeltranslation.translator import TranslationOptions, register
from main.models import Banner


@register(Banner)
class BannerTranslationOptions(TranslationOptions):
    fields = ("image",)
