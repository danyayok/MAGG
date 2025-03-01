from django.db import models

# Create your models here.
from django.db import models

class uploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')  # Папка, куда будут сохраняться файлы
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name