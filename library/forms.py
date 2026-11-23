from django import forms

from .models import Book, Subject, TeacherProfile


class TeacherBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('subject', 'title', 'author', 'description', 'file')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'file': forms.ClearableFileInput(attrs={'accept': '.pdf,.epub,.doc,.docx,.txt,.rtf,.djvu'}),
        }

    def __init__(self, *args, teacher: TeacherProfile, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(
            pk__in=teacher.subjects.values('pk'),
            is_active=True,
            institution__is_active=True,
        ).select_related('institution').order_by('institution__name', 'title')
        self.fields['subject'].empty_label = 'Оберіть дисципліну'
