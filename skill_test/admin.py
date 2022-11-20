from django.contrib import admin
from skill_test.models import Questions
from skill_test.models import Tests
from skill_test.models import Users
from skill_test.models import Batches
from skill_test.models import Results


admin.site.register(Questions)
admin.site.register(Tests)
admin.site.register(Users)
admin.site.register(Batches)
admin.site.register(Results)
