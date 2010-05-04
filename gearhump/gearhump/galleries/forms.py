from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from gearhump.galleries import models

class GalleryForm(forms.ModelForm):
  class Meta:
    model = models.Gallery
    fields = ('name', 'description')
    widgets = {
      'name': forms.TextInput(attrs={'size': 64}),
      'description': forms.Textarea(attrs={'cols': 60}),
    }

  def create(self, member):
    gallery = self.save(commit=False)
    gallery.member = member
    gallery.save()
    return gallery

def delete_label(photo):
  return mark_safe('<img src="' + settings.MEDIA_URL + photo.thumb() + '" />')

class DeletePhotosForm(forms.Form):
  def __init__(self, photos, *args, **kwargs):
    super(DeletePhotosForm, self).__init__(*args, **kwargs)
    self.choices = [(p.id, delete_label(p)) for p in photos]
    field = forms.MultipleChoiceField(choices=self.choices, label='',
                                      widget=forms.CheckboxSelectMultiple)
    self.fields['to_delete'] = field

  def hide(self):
    self.fields['to_delete'].widget = forms.MultipleHiddenInput(
      choices=self.choices)

  def deleted_ids(self):
    return self.cleaned_data['to_delete']

class CommentForm(forms.ModelForm):
  body = forms.CharField(label='',
                         widget=forms.Textarea(attrs={'cols': 60, 'rows': 6}))

  class Meta:
    model = models.Comment
    fields = ('body',)

  def create(self, member, gallery):
    comment = self.save(commit=False)
    comment.member = member
    comment.gallery = gallery
    comment.save()
