#!/usr/bin/env python
# vim:fileencoding=utf-8
from __future__ import unicode_literals
import swapper
from django import forms
from django.forms import modelformset_factory
from django.urls import reverse
try:
    from dal.autocomplete import FutureModelForm, TaggingSelect2
    AUTOCOMPLETE_LIGHT_INSTALLED = True
except ImportError:
    FutureModelForm = forms.ModelForm
    AUTOCOMPLETE_LIGHT_INSTALLED = False
from django.utils.translation import ugettext_lazy as _
Image = swapper.load_model('imagestore', 'Image')
Album = swapper.load_model('imagestore', 'Album')


class ImageForm(FutureModelForm):
    class Meta:
        model = Image
        # exclude = ('user', 'order')
        exclude = ('user', 'album')

    def __init__(self, user, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        # self.fields['album'].queryset = Album.objects.filter(user=user)
        # self.fields['album'].required = True

        if AUTOCOMPLETE_LIGHT_INSTALLED:
            self.fields['tags'].widget = TaggingSelect2(
                url=reverse('imagestore:tag-autocomplete'))

ImageFormSet = modelformset_factory(Image, exclude=('user', 'album'), extra = 8)

class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        exclude = ('user', 'created', 'updated', 'order')
        labels = {
            'tripreport': _('Trip Report --- Note: Markdown formatting is supported for this field'),
            'head': _('Cover Photo'),
            'brief': _('Brief Description'),
        }

    def __init__(self, *args, **kwargs):
        super(AlbumForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs and kwargs['instance']:
            self.fields['head'].queryset = Image.objects.filter(album=kwargs['instance'])
        else:
            self.fields['head'].widget = forms.HiddenInput()
